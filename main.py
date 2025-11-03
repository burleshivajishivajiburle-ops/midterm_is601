"""Entry point for launching the Advanced Calculator CLI."""

from app import CalculatorCLI


def main() -> None:
    """Start the interactive calculator CLI."""
    try:
        CalculatorCLI().run()
    except KeyboardInterrupt:
        # Provide a clean newline when user hits Ctrl+C
        print("\nExiting calculator.")


if __name__ == "__main__":
    main()
