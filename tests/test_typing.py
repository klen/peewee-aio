"""Pytest wrapper around the compile-time typing checks."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

CHECKS = Path(__file__).with_name("typing_checks.py")


@pytest.mark.skipif(shutil.which("pyrefly") is None, reason="pyrefly is not installed")
def test_public_api_types():
    pyrefly = shutil.which("pyrefly")
    assert pyrefly
    result = subprocess.run(  # noqa: S603
        [pyrefly, "check", str(CHECKS)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
