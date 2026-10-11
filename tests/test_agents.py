import pytest
from app.models import ProcurementRequest
from app.agents.single_agent import run_single_agent
from app.agents.two_agent import run_two_agent

def test_single_agent_clean_approval():
    req = ProcurementRequest(
        employee_name="Tanu Sharma",
        department="Engineering",
        tool_name="Postman Pro",
        estimated_cost=2000.0,
        seat_count=5,
        vendor_name="Atlassian",
        justification="API testing tool",
        handles_customer_data=False
    )
    rec = run_single_agent(req)
    assert rec.recommendation == "APPROVE"
    assert "DIRECT_MANAGER" in rec.approvals_required
    assert len(rec.evidence) >= 4

def test_two_agent_clean_approval():
    req = ProcurementRequest(
        employee_name="Tanu Sharma",
        department="Engineering",
        tool_name="Postman Pro",
        estimated_cost=2000.0,
        seat_count=5,
        vendor_name="Atlassian",
        justification="API testing tool",
        handles_customer_data=False
    )
    rec = run_two_agent(req)
    assert rec.recommendation == "APPROVE"
    assert "DIRECT_MANAGER" in rec.approvals_required
    assert len(rec.evidence) >= 4

def test_missing_fields_request_more_info():
    req = ProcurementRequest(
        employee_name="Alice Smith",
        department="Marketing",
        tool_name="HubSpot",
        estimated_cost=None, # Missing cost
        seat_count=5,
        vendor_name="HubSpot",
        justification="Campaigns"
    )
    rec_a = run_single_agent(req)
    rec_b = run_two_agent(req)
    assert rec_a.recommendation == "REQUEST_MORE_INFO"
    assert "estimated_cost" in rec_a.missing_information
    assert rec_b.recommendation == "REQUEST_MORE_INFO"
    assert "estimated_cost" in rec_b.missing_information
