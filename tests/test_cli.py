from pathlib import Path

import pytest

from stormatter.cli.format import (
    discover_dat_files,
    format_path,
    format_source,
    main,
)
from stormatter.formatting import FormatterConfig
from stormatter.utils import Cache

SOURCE = "(value) main() {\nreturn 10;\n}\n"
FORMATTED = "(value) main() {\n\treturn 10;\n}\n"


def test_discover_dat_files_recursive(tmp_path: Path) -> None:
    (tmp_path / "a.dat").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.dat").write_text("c")

    found = discover_dat_files(tmp_path)

    assert found == [tmp_path / "a.dat", sub / "c.dat"]


def test_format_source_uses_config() -> None:
    assert format_source(SOURCE, FormatterConfig(use_tabs=True)) == FORMATTED


def test_config_signature_changes_with_settings() -> None:
    base = FormatterConfig()
    same = FormatterConfig()
    different = FormatterConfig(use_tabs=True)
    different_empty_lines = FormatterConfig(empty_lines="preserve")

    assert base.signature() == same.signature()
    assert base.signature() != different.signature()
    assert base.signature() != different_empty_lines.signature()


def test_main_respects_empty_lines_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    file_path = tmp_path / "a.dat"
    file_path.write_text("value a = 1;\n\n\nvalue b = 2;\n")

    main(["--test", "--empty-lines", "preserve", str(file_path)])

    assert capsys.readouterr().out == "value a = 1;\n\n\nvalue b = 2;\n\n"


def test_format_path_stdout_mode_does_not_write(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    file_path = tmp_path / "a.dat"
    file_path.write_text(SOURCE)

    status = format_path(
        file_path, FormatterConfig(use_tabs=True), in_place=False, cache=None
    )

    assert status == "reformatted"
    assert file_path.read_text() == SOURCE  # untouched on disk
    assert capsys.readouterr().out == FORMATTED + "\n"


def test_format_path_in_place_writes_and_reports_unchanged_on_second_call(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "a.dat"
    file_path.write_text(SOURCE)
    config = FormatterConfig(use_tabs=True)

    first = format_path(file_path, config, in_place=True, cache=None)
    assert first == "reformatted"
    assert file_path.read_text() == FORMATTED

    second = format_path(file_path, config, in_place=True, cache=None)
    assert second == "unchanged"


def test_format_path_skips_via_cache_when_unchanged(tmp_path: Path) -> None:
    file_path = tmp_path / "a.dat"
    file_path.write_text(SOURCE)
    config = FormatterConfig(use_tabs=True)
    cache = Cache.load(tmp_path / "cache.pickle")

    first = format_path(file_path, config, in_place=True, cache=cache)
    assert first == "reformatted"

    # Without persisting/reloading the cache, is_changed should now see the
    # freshly-formatted file's info and skip re-formatting it entirely.
    second = format_path(file_path, config, in_place=True, cache=cache)
    assert second == "skipped"


def test_format_path_cache_survives_save_and_reload(tmp_path: Path) -> None:
    file_path = tmp_path / "a.dat"
    file_path.write_text(SOURCE)
    config = FormatterConfig(use_tabs=True)
    cache_file = tmp_path / "cache.pickle"

    cache = Cache.load(cache_file)
    assert format_path(file_path, config, in_place=True, cache=cache) == "reformatted"
    cache.save()

    reloaded = Cache.load(cache_file)
    assert format_path(file_path, config, in_place=True, cache=reloaded) == "skipped"


def test_format_path_reformats_after_content_changes(tmp_path: Path) -> None:
    file_path = tmp_path / "a.dat"
    file_path.write_text(SOURCE)
    config = FormatterConfig(use_tabs=True)
    cache = Cache.load(tmp_path / "cache.pickle")

    assert format_path(file_path, config, in_place=True, cache=cache) == "reformatted"

    file_path.write_text("(value) other() {\nreturn 1;\n}\n")
    assert format_path(file_path, config, in_place=True, cache=cache) == "reformatted"


def test_format_path_cache_is_config_specific(tmp_path: Path) -> None:
    file_path = tmp_path / "a.dat"
    file_path.write_text(SOURCE)
    tabs_config = FormatterConfig(use_tabs=True)
    spaces_config = FormatterConfig(use_tabs=False, tab_display_size=4)

    tabs_cache = Cache.load(tmp_path / f"cache-{tabs_config.signature()}.pickle")
    assert (
        format_path(file_path, tabs_config, in_place=True, cache=tabs_cache)
        == "reformatted"
    )

    # A different config's cache (different file, matching the real CLI's
    # per-signature cache naming) has never seen this file, so it must not
    # be skipped even though the file itself hasn't changed since.
    spaces_cache = Cache.load(tmp_path / f"cache-{spaces_config.signature()}.pickle")
    assert (
        format_path(file_path, spaces_config, in_place=True, cache=spaces_cache)
        == "reformatted"
    )


def test_main_rejects_test_flag_for_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "a.dat").write_text(SOURCE)

    with pytest.raises(SystemExit):
        main(["--test", str(tmp_path)])

    assert "does not support --test" in capsys.readouterr().err


def test_main_default_writes_file_in_place(tmp_path: Path) -> None:
    file_path = tmp_path / "a.dat"
    file_path.write_text(SOURCE)

    main(["--tabs", "--cache-dir", str(tmp_path / "cache"), str(file_path)])

    assert file_path.read_text() == FORMATTED


def test_main_test_flag_prints_without_writing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    file_path = tmp_path / "a.dat"
    file_path.write_text(SOURCE)

    main(["--tabs", "--test", str(file_path)])

    assert file_path.read_text() == SOURCE  # untouched on disk
    assert capsys.readouterr().out == FORMATTED + "\n"


def test_main_errors_on_missing_path(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["/no/such/path.dat"])

    assert "No such file or directory" in capsys.readouterr().err


def test_main_formats_directory_in_place_and_caches(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    work_dir = tmp_path / "work"
    sub_dir = work_dir / "sub"
    sub_dir.mkdir(parents=True)
    (work_dir / "a.dat").write_text(SOURCE)
    (sub_dir / "b.dat").write_text(SOURCE)

    main(["--tabs", "--cache-dir", str(cache_dir), str(work_dir)])

    assert (work_dir / "a.dat").read_text() == FORMATTED
    assert (sub_dir / "b.dat").read_text() == FORMATTED
    assert list(cache_dir.glob("cache-*.pickle"))

    # Re-running with no changes should not touch either file's content.
    a_mtime = (work_dir / "a.dat").stat().st_mtime_ns
    b_mtime = (sub_dir / "b.dat").stat().st_mtime_ns
    main(["--tabs", "--cache-dir", str(cache_dir), str(work_dir)])
    assert (work_dir / "a.dat").stat().st_mtime_ns == a_mtime
    assert (sub_dir / "b.dat").stat().st_mtime_ns == b_mtime


def test_main_no_cache_flag_skips_caching(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    file_path = tmp_path / "a.dat"
    file_path.write_text(SOURCE)

    main(["--tabs", "--no-cache", "--cache-dir", str(cache_dir), str(file_path)])

    assert file_path.read_text() == FORMATTED
    assert not cache_dir.exists()
