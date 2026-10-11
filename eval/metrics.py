"""
Evaluation metrics calculation for Procurement Copilot architectures.
Measures:
1. Recommendation Accuracy (%)
2. Evidence Grounding (%)
3. Policy Compliance (%)
4. Tool Call Efficiency (average tool calls count)
5. Latency (seconds)
6. Token Cost (USD)
"""
from typing import Dict, Any, List
from app.models import ProcurementRecommendation

def evaluate_single_run(case: Dict[str, Any], output: ProcurementRecommendation) -> Dict[str, Any]:
    expected = case.get("expected", {})
    
    # 1. Recommendation Accuracy
    expected_rec = expected.get("recommendation")
    rec_match = (output.recommendation == expected_rec)

    # 2. Evidence Grounding:
    # Verify every evidence item is rooted in a verified source and has non-empty factual content
    valid_sources = {"software_catalog", "team_budget", "vendor_security", "policy"}
    grounded_items = 0
    total_items = len(output.evidence)
    for ev in output.evidence:
        if ev.source in valid_sources and len(ev.fact.strip()) > 10:
            grounded_items += 1
    grounding_score = (grounded_items / max(1, total_items)) * 100.0

    # 3. Policy Compliance:
    # Check if all expected mandatory approvals are present in approvals_required
    expected_approvals = expected.get("approvals_required", [])
    if not expected_approvals:
        policy_compliant = True
    else:
        policy_compliant = all(req in output.approvals_required for req in expected_approvals)

    # Check risk flag keywords if specified
    risk_keyword = expected.get("risk_flag_keyword")
    if risk_keyword:
        risk_found = any(risk_keyword.lower() in rf.lower() for rf in output.risk_flags)
        if not risk_found:
            # Also check if it was surfaced in evidence facts
            risk_found = any(risk_keyword.lower() in ev.fact.lower() for ev in output.evidence)
        policy_compliant = policy_compliant and risk_found

    tool_calls_count = len(output.tool_calls) if output.tool_calls else 0
    latency_sec = (output.execution_time_ms or 0.0) / 1000.0
    token_cost = output.token_usage.estimated_cost_usd if output.token_usage else 0.0
    total_tokens = output.token_usage.total_tokens if output.token_usage else 0

    return {
        "case_id": case["id"],
        "category": case["category"],
        "rec_match": rec_match,
        "grounding_score": grounding_score,
        "policy_compliant": policy_compliant,
        "tool_calls_count": tool_calls_count,
        "latency_sec": latency_sec,
        "total_tokens": total_tokens,
        "token_cost_usd": token_cost
    }

def aggregate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(results)
    if n == 0:
        return {}

    accuracy = sum(1 for r in results if r["rec_match"]) / n * 100.0
    avg_grounding = sum(r["grounding_score"] for r in results) / n
    compliance = sum(1 for r in results if r["policy_compliant"]) / n * 100.0
    avg_tool_calls = sum(r["tool_calls_count"] for r in results) / n
    avg_latency = sum(r["latency_sec"] for r in results) / n
    avg_tokens = sum(r["total_tokens"] for r in results) / n
    total_cost = sum(r["token_cost_usd"] for r in results)

    return {
        "total_cases": n,
        "recommendation_accuracy_pct": round(accuracy, 2),
        "evidence_grounding_pct": round(avg_grounding, 2),
        "policy_compliance_pct": round(compliance, 2),
        "avg_tool_calls": round(avg_tool_calls, 2),
        "avg_latency_sec": round(avg_latency, 4),
        "avg_tokens": round(avg_tokens, 1),
        "total_token_cost_usd": round(total_cost, 6)
    }
