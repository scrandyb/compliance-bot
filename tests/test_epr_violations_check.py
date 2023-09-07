"""Tests the EPR violotations detection logic"""

from compliance_bot.exceptions import ComplianceViolationException

def test_always_passes():
    assert True

def test_raise_ComplianceViolationException():
    raise ComplianceViolationException("This test is working as intended!")
