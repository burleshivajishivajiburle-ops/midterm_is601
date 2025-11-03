"""Command-line interface (REPL) for the advanced calculator application.

This module implements a decorator-driven command registry and a dynamic help
menu that automatically reflects the operations available from the calculator.
"""

from __future__ import annotations

import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, TextIO

from .calculator import Calculator
from .exceptions import (
    CalculatorError,
    FileOperationError,
    MementoError,
    ValidationError,
)

# ---------------------------------------------------------------------------
# Command registration infrastructure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CommandInfo:
    """Metadata describing a CLI command."""

    name: str
    handler: Callable[["CalculatorCLI", List[str]], str]
    description: str
    usage: str
    category: str = "general"
    aliases: tuple[str, ...] = ()


class CommandRegistry:
    """Decorator-based registry used to store CLI command metadata."""

    def __init__(self) -> None:
        self._commands: Dict[str, CommandInfo] = {}
        self._aliases: Dict[str, str] = {}

    def command(
        self,
        name: str,
        *,
        description: str,
        usage: Optional[str] = None,
        category: str = "general",
        aliases: Optional[Iterable[str]] = None,
    ) -> Callable[[Callable[["CalculatorCLI", List[str]], str]], Callable[["CalculatorCLI", List[str]], str]]:
        """Decorator that registers a CLI command."""

        def decorator(func: Callable[["CalculatorCLI", List[str]], str]) -> Callable[["CalculatorCLI", List[str]], str]:
            info = CommandInfo(
                name=name,
                handler=func,
                description=description,
                usage=usage or name,
                category=category,
                aliases=tuple(aliases or ()),
            )
            self._commands[name] = info
            for alias in info.aliases:
                self._aliases[alias] = name
            return func

        return decorator

    def resolve(self, command_name: str) -> Optional[CommandInfo]:
        """Return command information for the provided name or alias."""

        if command_name in self._commands:
            return self._commands[command_name]
        resolved = self._aliases.get(command_name)
        if resolved:
            return self._commands.get(resolved)
        return None

    def iter_commands(self, *, category: Optional[str] = None) -> Iterable[CommandInfo]:
        """Yield registered commands optionally filtered by category."""

        for info in self._commands.values():
            if category and info.category != category:
                continue
            yield info


# ---------------------------------------------------------------------------
# Help menu using the decorator design pattern
# ---------------------------------------------------------------------------


class HelpProvider:
    """Base component for help menu decorators."""

    def get_entries(self) -> Dict[str, str]:
        return {}


class HelpDecorator(HelpProvider):
    """Decorator base class forwarding to an underlying provider."""

    def __init__(self, provider: HelpProvider) -> None:
        self._provider = provider

    def get_entries(self) -> Dict[str, str]:
        return dict(self._provider.get_entries())


class CommandHelpDecorator(HelpDecorator):
    """Decorator that adds registered command descriptions to the help menu."""

    def __init__(self, provider: HelpProvider, commands: Iterable[CommandInfo]) -> None:
        super().__init__(provider)
        self._commands = list(commands)

    def get_entries(self) -> Dict[str, str]:
        entries = super().get_entries()
        for info in self._commands:
            entries[info.usage] = info.description
        return entries


class OperationHelpDecorator(HelpDecorator):
    """Decorator that adds calculator operations to the help menu dynamically."""

    OPERATION_DESCRIPTIONS: Dict[str, str] = {
        "add": "Add two numbers",
        "subtract": "Subtract the second number from the first",
        "multiply": "Multiply two numbers",
        "divide": "Divide the first number by the second",
        "power": "Raise the first number to the power of the second",
        "root": "Calculate the nth root of a number",
        "modulus": "Compute the remainder of a division",
        "int_divide": "Integer division (floor of a/b)",
        "percent": "Percentage of one number with respect to another",
        "abs_diff": "Absolute difference between two numbers",
    }

    def __init__(self, provider: HelpProvider, calculator: Calculator) -> None:
        super().__init__(provider)
        self._calculator = calculator

    def get_entries(self) -> Dict[str, str]:
        entries = super().get_entries()
        for operation in self._calculator.get_available_operations():
            description = self.OPERATION_DESCRIPTIONS.get(
                operation,
                f"Perform the '{operation}' operation",
            )
            entries[f"{operation} <a> <b>"] = description
        return entries


# ---------------------------------------------------------------------------
# Calculator CLI implementation
# ---------------------------------------------------------------------------


class CalculatorCLI:
    """Interactive Read-Eval-Print loop for the calculator application."""

    registry = CommandRegistry()

    def __init__(
        self,
        *,
        calculator: Optional[Calculator] = None,
        input_stream: Optional[Iterable[str]] = None,
        output_stream: Optional[TextIO] = None,
    ) -> None:
        self.calculator = calculator or Calculator()
        self._input_stream = input_stream
        self._output_stream = output_stream or sys.stdout
        self._running = True

    # -------------------------- REPL control -----------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    def run(self) -> None:
        """Start an interactive REPL session."""

        self._print_startup_menu()
        input_iter = self._input_stream if self._input_stream is not None else self._stdin_iter()
        for line in input_iter:
            line = line.strip()
            if not line:
                continue
            response = self.execute_line(line)
            if response and self._output_stream:
                print(response, file=self._output_stream)
            if not self._running:
                break

    def _stdin_iter(self) -> Iterable[str]:
        while self._running:
            if self._output_stream:
                print("> ", end="", file=self._output_stream)
                self._output_stream.flush()
            try:
                line = sys.stdin.readline()
            except KeyboardInterrupt:  # pragma: no cover - user interrupt
                print("\nExiting...", file=self._output_stream)
                break
            if not line:
                break
            yield line

    # -------------------------- Command dispatch -------------------------

    def execute_line(self, line: str) -> str:
        """Execute a single CLI command and return the textual response."""

        line = line.strip()
        if not line:
            return ""
        try:
            tokens = shlex.split(line, posix=not sys.platform.startswith("win"))
        except ValueError as exc:
            return f"Error parsing command: {exc}"

        command_name = tokens[0].lower()
        args = tokens[1:]

        # First, look for a registered non-operation command
        command_info = self.registry.resolve(command_name)
        if command_info:
            try:
                return command_info.handler(self, args)
            except (CalculatorError, ValidationError, MementoError, FileOperationError) as exc:
                return f"Error: {exc}"
            except Exception as exc:  # pragma: no cover - unexpected failure
                return f"Unexpected error: {exc}"

        # Next, fall back to supported operations provided by the calculator
        if command_name in self.calculator.get_available_operations():
            try:
                return self._execute_operation(command_name, args)
            except (CalculatorError, ValidationError) as exc:
                return f"Error: {exc}"
            except Exception as exc:  # pragma: no cover - unexpected failure
                return f"Unexpected error: {exc}"

        return f"Unknown command '{command_name}'. Type 'help' to view available commands."

    # -------------------------- Command handlers -------------------------

    def _execute_operation(self, operation: str, args: List[str]) -> str:
        if len(args) != 2:
            return f"Usage: {operation} <number-a> <number-b>"

        try:
            operand_a = self._parse_number(args[0])
            operand_b = self._parse_number(args[1])
        except ValueError as exc:
            return f"Error: {exc}"

        result = self.calculator.calculate(operation, operand_a, operand_b)
        expression = result.get("expression") or f"{operand_a} {operation} {operand_b}"
        return f"{expression}"

    @registry.command(
        "history",
        description="Display the most recent calculations",
        usage="history [count]",
        category="utility",
    )
    def command_history(self, args: List[str]) -> str:
        count = 10
        if args:
            try:
                count = max(1, int(args[0]))
            except ValueError:
                return "Error: history count must be an integer"

        calculations = self.calculator.get_history(count)
        if not calculations:
            return "History is empty."

        lines = ["Recent calculations:"]
        for calc in calculations:
            expression = getattr(calc, "get_formatted_expression", None)
            if callable(expression):
                lines.append(f"  {calc.get_formatted_expression()}")
            else:
                lines.append(f"  {calc}")
        return "\n".join(lines)

    @registry.command(
        "clear",
        description="Clear history, memory, or all data",
        usage="clear [history|memory|all]",
        category="utility",
    )
    def command_clear(self, args: List[str]) -> str:
        target = args[0].lower() if args else "history"
        if target == "history":
            self.calculator.clear_history()
            return "History cleared."
        if target == "memory":
            self.calculator.clear_memory()
            return "Memory cleared."
        if target == "all":
            self.calculator.clear_all()
            return "Calculator state cleared."
        return "Error: clear expects 'history', 'memory', or 'all'"

    @registry.command(
        "undo",
        description="Undo the last calculation",
        category="utility",
    )
    def command_undo(self, args: List[str]) -> str:
        _ = args  # unused
        result = self.calculator.undo()
        return result["message"] if result else "Nothing to undo."

    @registry.command(
        "redo",
        description="Redo the last undone calculation",
        category="utility",
    )
    def command_redo(self, args: List[str]) -> str:
        _ = args
        result = self.calculator.redo()
        return result["message"] if result else "Nothing to redo."

    @registry.command(
        "save",
        description="Persist history to a CSV/JSON/Excel file",
        usage="save [path]",
        category="utility",
    )
    def command_save(self, args: List[str]) -> str:
        target = Path(args[0]) if args else Path(self.calculator.config.get_history_file_path())
        target.parent.mkdir(parents=True, exist_ok=True)
        self.calculator.export_history(str(target))
        return f"History saved to {target}"

    @registry.command(
        "load",
        description="Load history from a CSV/JSON/Excel file",
        usage="load <path>",
        category="utility",
    )
    def command_load(self, args: List[str]) -> str:
        if not args:
            return "Error: load expects a file path"
        target = Path(args[0])
        if not target.exists():
            return f"Error: file '{target}' does not exist"
        self.calculator.load_history(str(target))
        return f"History loaded from {target}"

    @registry.command(
        "help",
        description="Show available commands",
    )
    def command_help(self, args: List[str]) -> str:
        _ = args
        help_entries = self._build_help_entries()
        lines = ["Available commands:"]
        for usage, description in sorted(help_entries.items()):
            lines.append(f"  {usage}: {description}")
        return "\n".join(lines)

    @registry.command(
        "exit",
        description="Exit the calculator",
        aliases=("quit",),
    )
    def command_exit(self, args: List[str]) -> str:
        _ = args
        self._running = False
        return "Exiting calculator."

    # -------------------------- Helpers ----------------------------------

    def _parse_number(self, token: str) -> float:
        try:
            if token.lower() in {"inf", "+inf", "-inf", "nan"}:
                raise ValueError("Invalid numeric value")
            if any(char in token for char in ".eE"):
                value = float(token)
                return int(value) if value.is_integer() else value
            return int(token)
        except ValueError as exc:  # Re-raise with clearer messaging
            raise ValueError(f"'{token}' is not a valid number") from exc

    def _build_help_entries(self) -> Dict[str, str]:
        base = HelpProvider()
        base = CommandHelpDecorator(base, self.registry.iter_commands())
        base = OperationHelpDecorator(base, self.calculator)
        return base.get_entries()

    def _print_startup_menu(self) -> None:
        if not self._output_stream:
            return
        lines = self._build_startup_menu_lines()
        print("\n".join(lines), file=self._output_stream)

    def _build_startup_menu_lines(self) -> List[str]:
        operations = sorted(self.calculator.get_available_operations())
        operations_text = ", ".join(operations)

        command_names = sorted({info.name for info in self.registry.iter_commands()})
        commands_text = ", ".join(command_names) if command_names else ""

        lines: List[str] = [
            "Welcome to the Advanced Calculator REPL! Type 'exit' to quit.",
            f"Available operations: {operations_text}.",
        ]

        if commands_text:
            lines.append(f"Other commands: {commands_text}.")

        lines.append(
            f"Enter an operation ({operations_text}) and two numbers, or type a command such as 'help' for details."
        )
        return lines


__all__ = ["CalculatorCLI"]
