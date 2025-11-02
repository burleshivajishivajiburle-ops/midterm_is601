"""
Advanced Calculator REPL Interface.

This module provides a user-friendly command-line interface using the 
Read-Eval-Print Loop (REPL) pattern. It supports all calculator operations,
history management, undo/redo functionality, and various utility commands.
"""

import sys
import os
import traceback
from typing import Dict, List, Optional, Any, Callable
import argparse
from pathlib import Path

# Add the app directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.calculator import Calculator
from app.calculator_config import get_config, reset_config
from app.exceptions import CalculatorError, ValidationError, MementoError
from app.input_validators import InputValidator


class CalculatorREPL:
    """
    Read-Eval-Print Loop interface for the advanced calculator.
    
    Provides a user-friendly command-line interface with support for:
    - Mathematical calculations with multiple input formats
    - History management and search
    - Undo/redo operations
    - Configuration management
    - Help system and command completion
    """
    
    def __init__(self):
        """Initialize the REPL interface."""
        self.calculator = Calculator()
        self.running = True
        self.show_welcome = True
        
        # Command registry
        self.commands = {
            # Calculation commands
            "add": self._handle_calculation,
            "subtract": self._handle_calculation,
            "multiply": self._handle_calculation,
            "divide": self._handle_calculation,
            "power": self._handle_calculation,
            "root": self._handle_calculation,
            "modulus": self._handle_calculation,
            "int_divide": self._handle_calculation,
            "percent": self._handle_calculation,
            "abs_diff": self._handle_calculation,
            
            # History commands
            "history": self._handle_history,
            "clear": self._handle_clear,
            
            # Undo/Redo commands
            "undo": self._handle_undo,
            "redo": self._handle_redo,
            
            # File operations
            "save": self._handle_save,
            "load": self._handle_load,
            
            # Utility commands
            "help": self._handle_help,
            "exit": self._handle_exit,
            "quit": self._handle_exit,
            "stats": self._handle_stats,
            "operations": self._handle_operations,
            "config": self._handle_config,
        }
    
    def run(self) -> None:
        """Start the REPL interface."""
        if self.show_welcome:
            self._show_welcome()
        
        while self.running:
            try:
                # Get user input
                prompt = f"calc[{self.calculator.calculation_count}]> "
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Process the input
                self._process_input(user_input)
                
            except KeyboardInterrupt:
                print("\n\nUse 'exit' or 'quit' to terminate the calculator.")
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                if os.getenv("CALCULATOR_DEBUG"):
                    traceback.print_exc()
    
    def _process_input(self, user_input: str) -> None:
        """
        Process user input and execute appropriate commands.
        
        Args:
            user_input (str): Raw user input string
        """
        try:
            # Split input into parts
            parts = user_input.split()
            command = parts[0].lower()
            
            # Check if it's a direct calculation (e.g., "5 + 3")
            if self._is_calculation_expression(user_input):
                self._handle_calculation_expression(user_input)
                return
            
            # Check if it's a registered command
            if command in self.commands:
                self.commands[command](parts)
            else:
                # Try to parse as calculation command
                if len(parts) >= 3:
                    self._handle_calculation(parts)
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands.")
        
        except Exception as e:
            self._handle_error(e)
    
    def _is_calculation_expression(self, input_str: str) -> bool:
        """Check if input is a mathematical expression like '5 + 3'."""
        import re
        patterns = [
            r'^\s*[+-]?\d*\.?\d+\s*[+\-*/^%]\s*[+-]?\d*\.?\d+\s*$',
            r'^\s*[+-]?\d*\.?\d+\s*\*\*\s*[+-]?\d*\.?\d+\s*$',
            r'^\s*[+-]?\d*\.?\d+\s*//\s*[+-]?\d*\.?\d+\s*$',
        ]
        return any(re.match(pattern, input_str) for pattern in patterns)
    
    def _handle_calculation_expression(self, expression: str) -> None:
        """Handle mathematical expressions like '5 + 3'."""
        try:
            result = self.calculator.calculate_from_string(expression)
            self._display_calculation_result(result)
        except Exception as e:
            self._handle_error(e)
    
    def _handle_calculation(self, parts: List[str]) -> None:
        """
        Handle calculation commands.
        
        Args:
            parts (List[str]): Command parts [operation, operand1, operand2]
        """
        try:
            if len(parts) < 3:
                print("Usage: <operation> <operand1> <operand2>")
                print("Example: add 5 3")
                return
            
            operation = parts[0]
            operand1 = float(parts[1])
            operand2 = float(parts[2])
            
            result = self.calculator.calculate(operation, operand1, operand2)
            self._display_calculation_result(result)
            
        except ValueError:
            print("Error: Operands must be numeric values.")
        except Exception as e:
            self._handle_error(e)
    
    def _handle_history(self, parts: List[str]) -> None:
        """Handle history command."""
        try:
            count = 10  # default
            if len(parts) > 1:
                count = int(parts[1])
            
            history = self.calculator.get_history(count)
            
            if not history:
                print("No calculation history available.")
                return
            
            print(f"\n=== Last {len(history)} Calculations ===")
            for i, calc in enumerate(history, 1):
                timestamp = calc['timestamp'][:19]  # Remove microseconds
                expression = calc.get('expression', 'Unknown')
                print(f"{i:2d}. {timestamp} | {expression}")
            print()
            
        except ValueError:
            print("Error: History count must be a number.")
        except Exception as e:
            self._handle_error(e)
    
    def _handle_clear(self, parts: List[str]) -> None:
        """Handle clear command."""
        try:
            if len(parts) == 1:
                # Clear memory only
                self.calculator.clear_memory()
                print("Memory cleared.")
            else:
                clear_type = parts[1].lower()
                if clear_type == "memory":
                    self.calculator.clear_memory()
                    print("Memory cleared.")
                elif clear_type == "history":
                    self.calculator.clear_history()
                    print("History cleared.")
                elif clear_type == "all":
                    self.calculator.clear_all()
                    print("Everything cleared (memory, history, undo stack).")
                else:
                    print("Usage: clear [memory|history|all]")
        
        except Exception as e:
            self._handle_error(e)
    
    def _handle_undo(self, parts: List[str]) -> None:
        """Handle undo command."""
        try:
            if not self.calculator.can_undo():
                print("No operations available to undo.")
                return
            
            preview = self.calculator.get_undo_preview()
            if preview:
                print(f"Undoing: {preview}")
            
            result = self.calculator.undo()
            if result:
                print(f"✓ {result['message']}")
                if result['current_result'] is not None:
                    print(f"Current result: {result['current_result']}")
            
        except Exception as e:
            self._handle_error(e)
    
    def _handle_redo(self, parts: List[str]) -> None:
        """Handle redo command."""
        try:
            if not self.calculator.can_redo():
                print("No operations available to redo.")
                return
            
            preview = self.calculator.get_redo_preview()
            if preview:
                print(f"Redoing: {preview}")
            
            result = self.calculator.redo()
            if result:
                print(f"✓ {result['message']}")
                if result['current_result'] is not None:
                    print(f"Current result: {result['current_result']}")
            
        except Exception as e:
            self._handle_error(e)
    
    def _handle_save(self, parts: List[str]) -> None:
        """Handle save command."""
        try:
            if len(parts) < 2:
                print("Usage: save <filename> [format]")
                print("Formats: csv (default), json, excel")
                return
            
            filename = parts[1]
            format_type = parts[2] if len(parts) > 2 else "csv"
            
            self.calculator.export_history(filename, format_type)
            print(f"History saved to {filename} in {format_type} format.")
            
        except Exception as e:
            self._handle_error(e)
    
    def _handle_load(self, parts: List[str]) -> None:
        """Handle load command."""
        try:
            if len(parts) < 2:
                print("Usage: load <filename>")
                return
            
            filename = parts[1]
            if not Path(filename).exists():
                print(f"File not found: {filename}")
                return
            
            self.calculator.load_history(filename)
            print(f"History loaded from {filename}.")
            
        except Exception as e:
            self._handle_error(e)
    
    def _handle_stats(self, parts: List[str]) -> None:
        """Handle stats command."""
        try:
            stats = self.calculator.get_statistics()
            
            print("\n=== Calculator Statistics ===")
            
            # Session stats
            session = stats['session']
            print(f"Current Result: {session['current_result']}")
            print(f"Calculations This Session: {session['calculation_count']}")
            print(f"Last Calculation: {session['last_calculation'] or 'None'}")
            
            # History stats
            history = stats['history']
            print(f"\nTotal Calculations: {history['total_calculations']}")
            print(f"Success Rate: {history['success_rate']}%")
            print(f"Failed Calculations: {history['failed_calculations']}")
            
            if history['operations_count']:
                print("\nMost Used Operations:")
                for op, count in sorted(history['operations_count'].items(), 
                                      key=lambda x: x[1], reverse=True)[:5]:
                    print(f"  {op}: {count}")
            
            # Undo/Redo stats
            undo_redo = stats['undo_redo']
            print(f"\nUndo Available: {undo_redo['undo_available']}")
            print(f"Redo Available: {undo_redo['redo_available']}")
            print(f"Undo Stack Size: {undo_redo['undo_stack_size']}")
            
            print()
            
        except Exception as e:
            self._handle_error(e)
    
    def _handle_operations(self, parts: List[str]) -> None:
        """Handle operations command."""
        try:
            operations = self.calculator.get_available_operations()
            
            print("\n=== Available Operations ===")
            operation_descriptions = {
                "add": "Addition (a + b)",
                "subtract": "Subtraction (a - b)", 
                "multiply": "Multiplication (a * b)",
                "divide": "Division (a / b)",
                "power": "Exponentiation (a ** b)",
                "root": "Root (b-th root of a)",
                "modulus": "Modulus (a % b)",
                "int_divide": "Integer Division (a // b)",
                "percent": "Percentage (a as % of b)",
                "abs_diff": "Absolute Difference (|a - b|)"
            }
            
            for op in operations:
                desc = operation_descriptions.get(op, "Mathematical operation")
                print(f"  {op:<12} - {desc}")
            
            print("\nUsage Examples:")
            print("  add 5 3        # Command format")
            print("  5 + 3          # Mathematical format")
            print("  multiply 4 7   # Command format") 
            print("  4 * 7          # Mathematical format")
            print()
            
        except Exception as e:
            self._handle_error(e)
    
    def _handle_config(self, parts: List[str]) -> None:
        """Handle config command."""
        try:
            config = self.calculator.config
            summary = config.get_summary()
            
            print("\n=== Configuration Summary ===")
            print(f"Environment File: {summary.get('env_file', 'Not found')}")
            print(f"Log Directory: {summary['log_dir']}")
            print(f"History Directory: {summary['history_dir']}")
            print(f"Precision: {summary['precision']} decimal places")
            print(f"Max History Size: {summary['max_history_size']}")
            
            features = summary['features_enabled']
            print(f"\nFeatures Enabled:")
            print(f"  Logging: {features['logging']}")
            print(f"  Auto-save: {features['auto_save']}")
            print(f"  Undo/Redo: {features['undo_redo']}")
            
            dirs = summary['directories_exist']
            print(f"\nDirectories Status:")
            print(f"  Log Directory: {'✓' if dirs['log_dir'] else '✗'}")
            print(f"  History Directory: {'✓' if dirs['history_dir'] else '✗'}")
            print()
            
        except Exception as e:
            self._handle_error(e)
    
    def _handle_help(self, parts: List[str]) -> None:
        """Handle help command."""
        print("\n=== Advanced Calculator Help ===")
        print()
        print("CALCULATION COMMANDS:")
        print("  <operation> <a> <b>  - Perform calculation")
        print("  <a> <op> <b>         - Mathematical notation")
        print("  Examples: add 5 3, 5 + 3, multiply 4 7, 4 * 7")
        print()
        print("OPERATIONS:")
        print("  add, subtract, multiply, divide, power, root")
        print("  modulus, int_divide, percent, abs_diff")
        print()
        print("HISTORY COMMANDS:")
        print("  history [count]      - Show calculation history")
        print("  clear [type]         - Clear memory/history/all")
        print("  save <file> [format] - Export history (csv/json/excel)")
        print("  load <file>          - Import history")
        print()
        print("UNDO/REDO:")
        print("  undo                 - Undo last calculation")
        print("  redo                 - Redo undone calculation")
        print()
        print("UTILITY COMMANDS:")
        print("  stats                - Show calculator statistics")
        print("  operations           - List all available operations")
        print("  config               - Show configuration")
        print("  help                 - Show this help")
        print("  exit/quit            - Exit calculator")
        print()
        print("EXAMPLES:")
        print("  calc[0]> 5 + 3")
        print("  calc[1]> multiply 4 7")
        print("  calc[2]> undo")
        print("  calc[3]> history 5")
        print("  calc[4]> save results.csv")
        print()
    
    def _handle_exit(self, parts: List[str]) -> None:
        """Handle exit/quit command."""
        print("Goodbye!")
        self.running = False
    
    def _display_calculation_result(self, result: Dict[str, Any]) -> None:
        """Display calculation result in a user-friendly format."""
        if result['success']:
            print(f"= {result['result']}")
            if result.get('duration_ms'):
                print(f"  (completed in {result['duration_ms']:.2f}ms)")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    def _handle_error(self, error: Exception) -> None:
        """Handle and display errors appropriately."""
        if isinstance(error, ValidationError):
            print(f"Input Error: {error.message}")
            if error.expected_format:
                print(f"Expected: {error.expected_format}")
        elif isinstance(error, MementoError):
            print(f"Undo/Redo Error: {error.message}")
        elif isinstance(error, CalculatorError):
            print(f"Calculator Error: {error.message}")
        else:
            print(f"Error: {str(error)}")
    
    def _show_welcome(self) -> None:
        """Display welcome message."""
        print("=" * 60)
        print("🧮 ADVANCED CALCULATOR")
        print("=" * 60)
        print("Features: Operations • History • Undo/Redo • Auto-save • Logging")
        print()
        print("Type 'help' for commands or start calculating!")
        print("Examples: '5 + 3', 'multiply 4 7', 'history', 'undo'")
        print("=" * 60)
        print()


def main():
    """Main entry point for the calculator application."""
    parser = argparse.ArgumentParser(
        description="Advanced Calculator with REPL interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start interactive mode
  python main.py --no-welcome       # Start without welcome message
  python main.py --config .env      # Use specific config file
        """
    )
    
    parser.add_argument(
        "--no-welcome",
        action="store_true",
        help="Skip welcome message"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    try:
        # Set debug mode
        if args.debug:
            os.environ["CALCULATOR_DEBUG"] = "1"
        
        # Reset config if custom config file specified
        if args.config:
            reset_config()
            # This will be picked up by get_config()
            os.environ["CALCULATOR_CONFIG_FILE"] = args.config
        
        # Create and run REPL
        repl = CalculatorREPL()
        repl.show_welcome = not args.no_welcome
        repl.run()
        
    except KeyboardInterrupt:
        print("\nCalculator terminated by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()