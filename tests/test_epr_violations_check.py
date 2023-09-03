from compliance_bot.epr_violations_check import ComplianceViolationException

def test_always_passes():
	assert True

def test_raise_ComplianceViolationException():
	raise ComplianceViolationException("This test is working as intended!")
