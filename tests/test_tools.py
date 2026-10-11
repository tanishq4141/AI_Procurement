import pytest
from app.tools import (
    check_software_catalog,
    check_team_budget,
    verify_vendor_security,
    evaluate_policy_rules
)

def test_software_catalog_exact_match():
    res = check_software_catalog("Jira Software")
    assert res["status"] == "FAIL"
    assert res["match_type"] == "EXACT_TOOL_EXISTS"
    assert "Jira Software" in res["matched_software"]

def test_software_catalog_capability_overlap():
    res = check_software_catalog("Asana Workflows")
    assert res["status"] == "WARNING"
    assert res["match_type"] == "CAPABILITY_OVERLAP"
    assert "Jira Software" in res["fact"]

def test_software_catalog_no_overlap():
    res = check_software_catalog("NovelCustomTool3000")
    assert res["status"] == "PASS"
    assert res["match_type"] == "NO_OVERLAP"

def test_team_budget_pass():
    # Engineering has $25,000 remaining
    res = check_team_budget("Engineering", 5000.0)
    assert res["status"] == "PASS"
    assert res["budget_available"] is True
    assert res["deficit"] == 0.0

def test_team_budget_fail_exceeded():
    # Marketing only has $1,500 remaining
    res = check_team_budget("Marketing", 4000.0)
    assert res["status"] == "FAIL"
    assert res["budget_available"] is False
    assert res["deficit"] == 2500.0

def test_team_budget_missing_cost():
    res = check_team_budget("Engineering", None)
    assert res["status"] == "FAIL"
    assert res["error"] == "MISSING_COST_PARAMETER"

def test_vendor_security_valid():
    res = verify_vendor_security("Atlassian")
    assert res["status"] == "PASS"
    assert res["soc2_status"] == "SOC2_TYPE_II"
    assert res["gdpr_compliant"] is True

def test_vendor_security_high_risk():
    res = verify_vendor_security("ShadowAI")
    assert res["status"] == "FAIL"
    assert res["risk_tier"] == "HIGH"
    assert res["soc2_status"] == "NONE"

def test_policy_rules_tier1():
    res = evaluate_policy_rules(
        estimated_cost=2000.0,
        budget_status="PASS",
        vendor_security_status="PASS",
        vendor_risk_tier="LOW",
        handles_customer_data=False,
        duplicate_match_type="NO_OVERLAP"
    )
    assert res["approvals_required"] == ["DIRECT_MANAGER"]

def test_policy_rules_tier3_and_security():
    res = evaluate_policy_rules(
        estimated_cost=30000.0,
        budget_status="PASS",
        vendor_security_status="WARNING",
        vendor_risk_tier="HIGH",
        handles_customer_data=True,
        duplicate_match_type="NO_OVERLAP"
    )
    assert "FINANCE_VP" in res["approvals_required"]
    assert "DEPT_HEAD" in res["approvals_required"]
    assert "IT_SECURITY" in res["approvals_required"]
