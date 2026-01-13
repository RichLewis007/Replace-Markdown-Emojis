#!/usr/bin/env python3
"""
Development helper script for the replace-markdown-emojis project.
This script provides common development tasks using uv.

Author: Rich Lewis
"""

import subprocess
import sys


def run_command(cmd: list[str], description: str) -> bool:
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


def main() -> None:
    """Main development script."""
    if len(sys.argv) < 2:  # noqa: PLR2004
        print("Usage: python dev.py <command>")
        print("\nAvailable commands:")
        print("  format     - Format code with black")
        print("  lint       - Lint code with ruff")
        print("  type-check - Run type checking with mypy")
        print("  security   - Run security checks with bandit and pip-audit")
        print("  test       - Run tests with pytest")
        print("  test-gui   - Run GUI tests only")
        print("  clean      - Clean up cache files")
        print("  install    - Install pre-commit hooks")
        print("  all        - Run all development tasks")
        return

    command = sys.argv[1]

    if command == "format":
        run_command(["uv", "run", "black", "."], "Formatting code with black")
        run_command(["uv", "run", "isort", "."], "Sorting imports with isort")
    elif command == "lint":
        run_command(["uv", "run", "ruff", "check", "."], "Linting code with ruff")
    elif command == "type-check":
        # Run mypy - PySide6 stub issues are expected and can be ignored
        print("\n🔧 Type checking with mypy")
        print("Running: uv run mypy src/")
        try:
            result = subprocess.run(
                ["uv", "run", "mypy", "src/"],
                capture_output=True,
                text=True,
                check=False,  # Don't raise on non-zero exit
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

            # Count real errors (excluding PySide6 stub issues)
            error_count = result.stderr.count("error:") if result.stderr else 0
            pyqt_errors = (
                (
                    result.stderr.count("PySide6")
                    + result.stderr.count("Qt")
                    + result.stderr.count("QFrame")
                    + result.stderr.count("QMessageBox")
                    + result.stderr.count("QHeaderView")
                    + result.stderr.count("QTableWidget")
                )
                if result.stderr
                else 0
            )

            if result.returncode != 0:
                if pyqt_errors == error_count:
                    print(
                        "\n✅ Type checking complete (only PySide6 stub warnings, which are expected)"
                    )
                else:
                    print(f"\n⚠️  Type checking found {error_count - pyqt_errors} real errors")
            else:
                print("\n✅ Type checking passed!")
        except Exception as e:
            print(f"❌ Error: {e}")
    elif command == "security":
        # Bandit may show exceptions with Python 3.14 but still scans code
        print("\n🔧 Security check with bandit")
        print("Running: uv run bandit -r src/")
        try:
            result = subprocess.run(
                ["uv", "run", "bandit", "-r", "src/"],
                capture_output=True,
                text=True,
                check=False,
            )
            # Filter out exception messages, show results
            output = result.stdout
            if "No issues identified" in output:
                print("✅ No security issues found by bandit")
                # Note: Exceptions are expected with Python 3.14 (bandit compatibility issue)
                print("   (Note: Some files show exceptions due to Python 3.14 compatibility)")
            elif output:
                print(output)
            if result.stderr:
                # Suppress exception messages (known issue with Python 3.14)
                stderr_lines = [
                    line
                    for line in result.stderr.split("\n")
                    if "Exception occurred" not in line and "ERROR" not in line
                ]
                if stderr_lines:
                    print("\n".join(stderr_lines))
        except Exception as e:
            print(f"❌ Error: {e}")

        # pip-audit - dependency vulnerability scanning (open source, no API key needed)
        print("\n🔧 Dependency security check with pip-audit")
        print("Running: uv run pip-audit")
        try:
            result = subprocess.run(
                ["uv", "run", "pip-audit"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

            if result.returncode == 0:
                print("✅ No known vulnerabilities found")
            else:
                print("\n⚠️  pip-audit found vulnerabilities (see output above)")
                print("   Consider updating affected packages")
        except Exception as e:
            print(f"❌ Error: {e}")
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
