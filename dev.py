#!/usr/bin/env python3
"""
Development helper script for the replace-markdown-emojis project.
This script provides common development tasks using uv.

Author: Rich Lewis
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print the result."""
    print(f"\n🔧 {description}")
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def main():
    """Main development script."""
    if len(sys.argv) < 2:
        print("Usage: python dev.py <command>")
        print("\nAvailable commands:")
        print("  format     - Format code with black")
        print("  lint       - Lint code with ruff")
        print("  type-check - Run type checking with mypy")
        print("  security   - Run security checks with bandit and safety")
        print("  test       - Run tests with pytest")
        print("  test-gui   - Run GUI tests only")
        print("  clean      - Clean up cache files")
        print("  install    - Install pre-commit hooks")
        print("  all        - Run all development tasks")
        return

    command = sys.argv[1]
    project_root = Path(__file__).parent

    if command == "format":
        run_command(["uv", "run", "black", "."], "Formatting code with black")
        run_command(["uv", "run", "isort", "."], "Sorting imports with isort")
    elif command == "lint":
        run_command(["uv", "run", "ruff", "check", "."], "Linting code with ruff")
    elif command == "type-check":
        run_command(["uv", "run", "mypy", "src/"], "Type checking with mypy")
    elif command == "security":
        run_command(["uv", "run", "bandit", "-r", "src/"], "Security check with bandit")
        run_command(["uv", "run", "safety", "check"], "Dependency security check with safety")
    elif command == "test":
        run_command(["uv", "run", "pytest"], "Running tests with pytest")
    elif command == "test-gui":
        run_command(["uv", "run", "pytest", "-m", "gui"], "Running GUI tests")
    elif command == "clean":
        run_command(
            ["find", ".", "-type", "d", "-name", "__pycache__", "-exec", "rm", "-rf", "{}", "+"],
            "Cleaning cache files",
        )
    elif command == "install":
        run_command(["uv", "run", "pre-commit", "install"], "Installing pre-commit hooks")
    elif command == "all":
        print("🚀 Running all development tasks...")
        success = True
        success &= run_command(["uv", "run", "black", "."], "Formatting code")
        success &= run_command(["uv", "run", "isort", "."], "Sorting imports")
        success &= run_command(["uv", "run", "ruff", "check", "."], "Linting code")
        success &= run_command(["uv", "run", "mypy", "src/"], "Type checking")
        success &= run_command(["uv", "run", "bandit", "-r", "src/"], "Security check")
        success &= run_command(["uv", "run", "pytest"], "Running tests")
        if success:
            print("\n✅ All tasks completed successfully!")
        else:
            print("\n❌ Some tasks failed!")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
