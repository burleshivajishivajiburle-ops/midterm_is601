# Advanced Calculator Application

A professional Python calculator featuring design patterns, comprehensive testing, and enterprise-grade architecture.

## Features

### Core Functionality
- **10 Arithmetic Operations**: add, subtract, multiply, divide, power, root, modulus, integer division, percentage, absolute difference
- **Command-Line Interface (REPL)**: Interactive shell with history, undo/redo, save/load
- **Calculation History**: Pandas-based persistence (CSV/JSON/Excel)
- **Undo/Redo**: Full memento pattern implementation
- **Configuration Management**: `.env` file support with validation

### Design Patterns
- **Factory Pattern**: Dynamic operation registration and creation
- **Memento Pattern**: State preservation for undo/redo
- **Observer Pattern**: Logging and auto-save hooks
- **Decorator Pattern**: Dynamic help menu generation
- **Builder Pattern**: Fluent calculation construction

### Optional Feature: Dynamic Help Menu
The CLI includes a decorator-based help system that automatically discovers and displays available operations from the factory, ensuring the help menu stays synchronized with registered operations without manual updates.

## Project Structure

```
project_root/
├── app/
│   ├── __init__.py
│   ├── calculator.py          # Main calculator with patterns
│   ├── calculation.py          # Calculation model
│   ├── calculator_config.py    # Configuration management
│   ├── calculator_memento.py   # Memento pattern for undo/redo
│   ├── cli.py                  # Command-line REPL interface
│   ├── exceptions.py           # Custom exceptions
│   ├── history.py              # Pandas-based history
│   ├── input_validators.py     # Input validation
│   ├── operations.py           # Factory pattern operations
│   └── logger.py               # Observer pattern logging
├── tests/                      # 306 comprehensive tests
├── .env                        # Environment configuration
├── requirements.txt
├── README.md
└── .github/
    └── workflows/
        └── python-app.yml      # CI/CD with coverage ≥90%
```

## Quick Start

### Installation

Create and activate a virtual environment:

**Windows PowerShell:**
```powershell
python -m venv .venv
& .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

**WSL / Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Command-Line Interface (REPL)

Start the interactive calculator:

```python
from app import CalculatorCLI

cli = CalculatorCLI()
cli.run()
```

**Available Commands:**
```
> add 5 3                  # Perform operations
8

> history 5                # View recent calculations
Recent calculations:
  5 + 3 = 8

> undo                     # Undo last calculation
Successfully undone last calculation

> redo                     # Redo undone calculation
Successfully redone calculation

> save history.csv         # Export history
History saved to history.csv

> load history.csv         # Import history
History loaded from history.csv

> help                     # View all commands (dynamic!)
Available commands:
  add <a> <b>: Add two numbers
  subtract <a> <b>: Subtract the second number from the first
  ...
  help: Show available commands
  exit: Exit the calculator

> exit                     # Exit REPL
Exiting calculator.
```

### Programmatic API

```python
from app import Calculator

calc = Calculator()

# Perform calculations
result = calc.calculate("add", 10, 5)
print(result["result"])  # 15

# Access history
history = calc.get_history(count=10)

# Undo/redo
calc.undo()
calc.redo()

# Export history
calc.export_history("calculations.csv", format="csv")
calc.load_history("calculations.csv")
```

## Testing

Run the full test suite (306 tests):

**Windows PowerShell:**
```powershell
& .venv/Scripts/python.exe -m pytest
```

**WSL / Linux / macOS:**
```bash
pytest
```

**Coverage is enabled by default** (see `pytest.ini`). Reports are generated in the terminal, as HTML in `htmlcov/`, and as XML in `coverage.xml`.

## CI/CD

GitHub Actions workflow (`.github/workflows/python-app.yml`):
- Installs dependencies and lints with flake8
- Runs 306 tests with **≥90% coverage enforcement**
- Uploads coverage artifacts (`coverage.xml` and `htmlcov/`)

## Configuration

Create a `.env` file in the project root to customize behavior:

```env
# History settings
CALCULATOR_MAX_HISTORY_SIZE=1000
CALCULATOR_HISTORY_FILE=calculator_history.csv

# Calculation settings
CALCULATOR_PRECISION=6
CALCULATOR_MAX_INPUT_VALUE=1000000000000000

# Logging
CALCULATOR_ENABLE_LOGGING=True
CALCULATOR_LOG_LEVEL=INFO
CALCULATOR_LOG_FILE=calculator.log

# Features
CALCULATOR_ENABLE_AUTO_SAVE=False
CALCULATOR_ENABLE_UNDO_REDO=True
```

## Architecture Highlights

- **Test Coverage**: 92.97% (306 tests covering all modules)
- **Design Patterns**: Factory, Memento, Observer, Decorator, Builder
- **Error Handling**: Custom exception hierarchy with descriptive messages
- **Data Persistence**: Pandas-based history with CSV/JSON/Excel support
- **Configuration**: Environment-based config with validation
- **CI/CD**: GitHub Actions with automated testing and coverage enforcement

## License

Educational project demonstrating advanced Python patterns and testing practices.
