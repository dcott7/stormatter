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

## Usage

### Basic CLI

```bash
stormatter ./path/to/file.dat
```

#### This prints the formatted content to standard output.

### CLI Options
- #### -t, --tabsize <number>: Number of spaces per indentation level (default: 4, used only with --spaces)
- #### --spaces: Use spaces instead of tabs
- #### --section-blocks: Treat begin IDENT / end IDENT as block delimiters
- #### --help: print out the help page

### CLI Example
   ```bash
   stormatter -t 2 --spaces --section-blocks data/test.dat
   ```