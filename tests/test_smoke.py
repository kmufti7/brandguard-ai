"""Smoke test: confirm brandguard imports and reports the expected version."""

import brandguard


def test_brandguard_imports_and_reports_version():
    assert brandguard.__version__ == "0.1.0"
