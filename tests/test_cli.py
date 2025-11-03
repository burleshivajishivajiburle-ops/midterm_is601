"""Tests for the command-line interface layer."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from app.cli import CalculatorCLI


@pytest.fixture
def cli(calculator):
    """Create a CLI instance bound to a test calculator."""
    return CalculatorCLI(calculator=calculator)


def test_cli_executes_operation_successfully(cli):
    response = cli.execute_line("add 2 3")
    assert response == "2 + 3 = 5"


def test_cli_reports_usage_for_missing_operands(cli):
    response = cli.execute_line("add 5")
    assert response == "Usage: add <number-a> <number-b>"


def test_cli_rejects_unknown_command(cli):
    response = cli.execute_line("foobar 1 2")
    assert response == "Unknown command 'foobar'. Type 'help' to view available commands."


def test_cli_help_includes_operations(cli):
    response = cli.execute_line("help")
    assert "help: Show available commands" in response
    assert "add <a> <b>: Add two numbers" in response


def test_cli_history_outputs_recent_calculations(cli):
    cli.execute_line("add 5 4")
    cli.execute_line("multiply 3 2")

    response = cli.execute_line("history 2")

    assert "Recent calculations:" in response
    # Most recent calculation should appear in the history output
    assert any("3 * 2 = 6" in line for line in response.splitlines())
    assert any("5 + 4 = 9" in line for line in response.splitlines())


def test_cli_undo_and_redo_commands(cli):
    cli.execute_line("add 10 2")
    undo_message = cli.execute_line("undo")
    redo_message = cli.execute_line("redo")

    assert undo_message == "Successfully undone last calculation"
    assert redo_message == "Successfully redone calculation"


def test_cli_save_and_load_history(tmp_path: Path, cli):
    cli.execute_line("add 8 2")
    target = tmp_path / "history.csv"

    save_message = cli.execute_line(f"save {target}")
    assert target.exists()
    assert target.name in save_message

    load_message = cli.execute_line(f"load {target}")
    assert "History loaded from" in load_message
    assert target.name in load_message


def test_cli_run_consumes_iterable_input(calculator):
    output = io.StringIO()
    cli = CalculatorCLI(calculator=calculator, input_stream=["add 1 2", "exit"], output_stream=output)

    cli.run()

    output_lines = output.getvalue().strip().splitlines()
    assert output_lines[0] == "Welcome to the Advanced Calculator REPL! Type 'exit' to quit."
    assert any(line.startswith("Available operations:") for line in output_lines)
    assert any("1 + 2 = 3" == line for line in output_lines)
    assert "Exiting calculator." in output_lines[-1]


def test_cli_startup_menu_lists_operations(cli):
    lines = cli._build_startup_menu_lines()

    assert lines[0] == "Welcome to the Advanced Calculator REPL! Type 'exit' to quit."
    assert any("add" in line for line in lines if line.startswith("Available operations:"))
    assert any("help" in line for line in lines if line.startswith("Other commands:"))
    assert any(line.startswith("Enter an operation (") for line in lines)


def test_cli_flags_invalid_number(cli):
    response = cli.execute_line("add NaN 2")
    assert response == "Error: 'NaN' is not a valid number"
