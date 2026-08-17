"""Tests for dataops_copilot."""

import pytest

from dataops_copilot.dataops_copilot import main


def test_main(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify the main entry point prints a greeting."""
    main()
    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out
