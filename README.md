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

#### This prints the formatted content to standard output.

### CLI Options
- **-t**, **--tabsize** <number>: Number of spaces per indentation level (default: 4, used only with --spaces)
- **--spaces**: Use spaces instead of tabs
- **--section-blocks**: Treat begin IDENT / end IDENT as block delimiters
- **--help**: print out the help page

### CLI Example
   ```bash
   stormatter -t 2 --spaces --section-blocks data/test.dat
   ```

## ✨ Current Formatter Behavior

1. Normalize whitespace between tokens - Multiple spaces are reduced to a single space.
2. Reduce/normalize newline characters - Blank lines are removed to condense the file.
3. Format leading whitespace - Ensures consistent indentation at the start of lines.

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
