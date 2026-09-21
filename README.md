# 🌩️ Stormatter

**Stormatter** is a Python-based formatter for STORM files, designed for simplicity, flexibility, and integration into development workflows.

---

## 🚀 Features

- 🖥️ Command-line interface for formatting `.dat` files
- 🔧 Supports both tab and space indentation
- 📦 Optional handling of section blocks (`begin IDENT` / `end IDENT`)
- 🐍 Installable as a Python package with an executable CLI
- 🔁 Easy integration into projects or CI pipelines

---

## 📦 Installation

**install repository:**

```bash
pip install git+https://github.com/dcott7/stormatter
```

## 🕹️Usage

### Basic CLI

```bash
stormatter ./path/to/file.dat
```

#### This formats the file in place. Pass a directory instead of a file to format every `.dat` file under it (recursively).

```bash
stormatter --test ./path/to/file.dat
```

#### `--test` prints the formatted result to stdout instead of writing it back (single files only).

### CLI Options
- **-t**, **--tabsize** <number>: Number of spaces per indentation level (default: 4, used unless --tabs is set)
- **--tabs**: Use tabs instead of spaces for indentation (default: spaces)
- **--no-section-blocks**: Do not treat begin IDENT / end IDENT as block delimiters (default: on)
- **--max-line-length** <number>: Wrap lines before they exceed this width when possible (default: 100, 0 disables wrapping)
- **--brace-style** <preserve|kr|allman>: Configure brace placement style (default: preserve)
- **--empty-lines** <collapse|single|preserve>: How to handle blank lines from the source (default: single)
- **--test**: Print the formatted result to stdout instead of writing it back to the file (not supported for a directory input)
- **--no-cache**: Ignore and do not update the on-disk format cache used to skip already-formatted files
- **--cache-dir** <path>: Directory to store the format cache in (default: `~/.cache/stormatter`, or `$XDG_CACHE_HOME/stormatter`)
- **--help**: print out the help page

### CLI Example
   ```bash
   stormatter -t 2 --tabs --no-section-blocks data/tests/test.dat
   ```

## ✨ Current Formatter Behavior

1. Normalize whitespace between tokens - Multiple spaces are reduced to a single space.
2. Reduce/normalize newline characters - Multiple blank lines collapse to a single line break, and how many blank lines (if any) survive is controlled by `--empty-lines` (collapse, single, or preserve).
3. Format leading whitespace - Ensures consistent indentation at the start of lines.
4. Optional line wrapping - When `--max-line-length` is set, the formatter breaks at available whitespace boundaries when a line would otherwise exceed the limit.
5. Optional brace style - Supports preserved input style, K&R (`kr`), or Allman (`allman`) brace placement.
6. Section block formatting - When enabled (the default), `begin IDENT` / `end IDENT` pairs are always placed on their own line and change the indentation level.

## Planned Future Updates
### Key-value alignment:
- Target sections like “type” files or similar structures.
- Align values vertically so that all = or : tokens (or other delimiters) line up for readability.
- For example turning this:
    ```text
    name: "Alice"
    age: 30
    city: "New York"
    home_state: CA
    ```
    into this:
    ```text
    after:
    name:       "Alice"
    age :       30
    city:       "New York"
    home_state: CA
    ```
