"""
Deterministic and retrieval tools for the Procurement Copilot.
Adheres strictly to the PRD specification:
- Budget calculations are 100% deterministic Python arithmetic (NEVER relying on LLM arithmetic).
- Policy rules strictly map financial thresholds and mandatory approvals.
- Mock service calls handle outages/exceptions gracefully.
"""
import os
import json
import time
from typing import Dict, Any, List, Optional
from app.mock_services import query_vendor_security_api, MockVendorServiceError

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def _load_json(filename: str) -> Any:
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def check_software_catalog(tool_name: str, requested_category: Optional[str] = None) -> Dict[str, Any]:
    """
    Searches active internal software licenses matching the requested tool or capability
    to prevent redundant purchases.
    """
    catalog = _load_json("software_catalog.json")
    normalized_name = tool_name.strip().lower()
    
    # 1. Exact or direct substring match
    for item in catalog:
        if normalized_name in item["name"].lower() or item["name"].lower() in normalized_name:
            unused_seats = item["total_seats"] - item["active_seats"]
            return {
                "match_type": "EXACT_TOOL_EXISTS",
                "matched_software": item["name"],
                "category": item["category"],
                "active_seats": item["active_seats"],
                "total_seats": item["total_seats"],
                "unused_seats": unused_seats,
                "status": "FAIL",
                "fact": f"Exact software '{item['name']}' already licensed internally with {unused_seats} available unused seats out of {item['total_seats']} total.",
                "recommendation_hint": "Utilize existing corporate license seats before requesting new subscriptions."
            }

    # 2. Semantic capability / category overlap check (e.g., Asana/Monday/Linear -> Jira; Miro -> Figma; Meets/Teams -> Zoom)
    overlap_mappings = {
        "asana": "Jira Software",
        "monday": "Jira Software",
        "monday.com": "Jira Software",
        "linear": "Jira Software",
        "clickup": "Jira Software",
        "trello": "Jira Software",
        "miro": "Figma Enterprise",
        "mural": "Figma Enterprise",
        "sketch": "Figma Enterprise",
        "teams": "Slack Enterprise",
        "mattermost": "Slack Enterprise",
        "gitlab": "GitHub Enterprise Cloud",
        "bitbucket": "GitHub Enterprise Cloud",
        "new relic": "Datadog",
        "dynatrace": "Datadog",
        "coda": "Notion Enterprise",
        "confluence": "Notion Enterprise",
        "google meet": "Zoom Meetings Pro",
        "webex": "Zoom Meetings Pro",
        "power bi": "Tableau Server",
        "looker": "Tableau Server",
        "lastpass": "1Password Business",
        "bitwarden": "1Password Business",
        "hubspot": "Salesforce Sales Cloud"
    }

    for key, mapped_tool in overlap_mappings.items():
        if key in normalized_name:
            matched_item = next((i for i in catalog if i["name"].lower() == mapped_tool.lower()), None)
            if matched_item:
                unused_seats = matched_item["total_seats"] - matched_item["active_seats"]
                return {
                    "match_type": "CAPABILITY_OVERLAP",
                    "matched_software": matched_item["name"],
                    "category": matched_item["category"],
                    "active_seats": matched_item["active_seats"],
                    "total_seats": matched_item["total_seats"],
                    "unused_seats": unused_seats,
                    "status": "WARNING",
                    "fact": f"Equivalent enterprise solution '{matched_item['name']}' already deployed in '{matched_item['category']}' with {unused_seats} available seats.",
                    "recommendation_hint": f"Evaluate '{matched_item['name']}' before adopting '{tool_name}'."
                }

    # 3. No duplicate found
    return {
        "match_type": "NO_OVERLAP",
        "matched_software": None,
        "status": "PASS",
        "fact": f"No duplicate or overlapping software found in corporate catalog for '{tool_name}'.",
        "recommendation_hint": "Approved from software catalog deduplication standpoint."
    }

def check_team_budget(department: str, requested_cost: Optional[float], employee_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Pure deterministic budget validation.
    Performs precise floating point arithmetic and checks against departmental remaining allocation.
    NEVER delegates arithmetic to an LLM.
    """
    if requested_cost is None:
        return {
            "status": "FAIL",
            "budget_available": False,
            "fact": "Cost was not provided in the request. Deterministic budget evaluation cannot proceed.",
            "error": "MISSING_COST_PARAMETER"
        }

    budgets = _load_json("budgets.json")
    dept_normalized = department.strip().lower()

    dept_budget = next(
        (b for b in budgets if b["department"].lower() == dept_normalized or dept_normalized in b["department"].lower()),
        None
    )

    if not dept_budget:
        return {
            "status": "WARNING",
            "budget_available": False,
            "department": department,
            "fact": f"Department '{department}' not found in active budget records. Requires finance validation.",
            "error": "UNKNOWN_DEPARTMENT"
        }

    allocated = float(dept_budget["allocated_budget"])
    committed = float(dept_budget["committed_spend"])
    remaining = float(dept_budget["remaining_budget"])
    requested = float(requested_cost)

    # Deterministic check
    budget_available = requested <= remaining
    post_balance = remaining - requested
    deficit = max(0.0, requested - remaining)

    if budget_available:
        fact = (
            f"Department '{dept_budget['department']}' has ${remaining:,.2f} remaining in {dept_budget['fiscal_quarter']}. "
            f"Requested amount of ${requested:,.2f} leaves a surplus of ${post_balance:,.2f}."
        )
        status = "PASS"
    else:
        fact = (
            f"Department '{dept_budget['department']}' budget EXCEEDED. Remaining: ${remaining:,.2f}, "
            f"Requested: ${requested:,.2f}, Deficit: ${deficit:,.2f}."
        )
        status = "FAIL"

    return {
        "status": status,
        "department": dept_budget["department"],
        "fiscal_quarter": dept_budget["fiscal_quarter"],
        "allocated_budget": allocated,
        "committed_spend": committed,
        "remaining_budget": remaining,
        "requested_cost": requested,
        "budget_available": budget_available,
        "post_purchase_balance": post_balance,
        "deficit": deficit,
        "finance_poc": dept_budget.get("finance_poc"),
        "fact": fact
    }

def verify_vendor_security(vendor_name: Optional[str], simulate_outage: bool = False) -> Dict[str, Any]:
    """
    Retrieval / Mock API tool to check vendor compliance certifications and risk profiles.
    Includes defensive exception handling for outages/timeouts.
    """
    if not vendor_name or not vendor_name.strip():
        return {
            "status": "WARNING",
            "fact": "Vendor name was not specified in the request. Security audit cannot be confirmed.",
            "risk_tier": "HIGH",
            "soc2_status": "NONE",
            "gdpr_compliant": False,
            "error": "MISSING_VENDOR_NAME"
        }

    try:
        api_result = query_vendor_security_api(vendor_name, simulate_failure=simulate_outage)
        data = api_result["data"]
        soc2 = data.get("soc2_status")
        gdpr = data.get("gdpr_compliant", False)
        risk = data.get("risk_tier", "MEDIUM")
        msa = data.get("active_master_services_agreement", False)
        vendor_full = data.get("vendor_name", vendor_name)

        # Determine compliance status
        if soc2 == "SOC2_TYPE_II" and gdpr and risk == "LOW":
            status = "PASS"
            fact = f"Vendor '{vendor_full}' verified: SOC2 Type II active (valid until {data.get('soc2_valid_until')}), GDPR compliant, Risk Tier: LOW."
        elif soc2 == "EXPIRED" or risk == "CRITICAL":
            status = "FAIL"
            fact = f"Vendor '{vendor_full}' CRITICAL RISK: SOC2 is EXPIRED ({data.get('soc2_valid_until')}), Risk Tier: CRITICAL. {data.get('notes')}"
        elif soc2 == "NONE" or risk == "HIGH":
            status = "FAIL"
            fact = f"Vendor '{vendor_full}' HIGH RISK: No SOC2 certification on file, GDPR non-compliant. {data.get('notes')}"
        else:
            status = "WARNING"
            fact = f"Vendor '{vendor_full}' has status {soc2}, Risk Tier: {risk}. {data.get('notes')}"

        return {
            "status": status,
            "vendor_name": vendor_full,
            "soc2_status": soc2,
            "soc2_valid_until": data.get("soc2_valid_until"),
            "gdpr_compliant": gdpr,
            "risk_tier": risk,
            "active_msa": msa,
            "data_residency": data.get("data_residency_options", []),
            "notes": data.get("notes"),
            "fact": fact
        }
    except MockVendorServiceError as e:
        # Graceful outage resilience
        return {
            "status": "WARNING",
            "vendor_name": vendor_name,
            "soc2_status": "SERVICE_UNAVAILABLE",
            "gdpr_compliant": False,
            "risk_tier": "HIGH",
            "error": "MOCK_SERVICE_OUTAGE",
            "fact": f"Vendor security endpoint unavailable (HTTP 500/timeout). Fallback triggered: flagged for mandatory manual IT Security vetting."
        }
    except Exception as e:
        return {
            "status": "WARNING",
            "vendor_name": vendor_name,
            "soc2_status": "UNKNOWN",
            "gdpr_compliant": False,
            "risk_tier": "HIGH",
            "error": str(e),
            "fact": f"Unexpected error querying vendor security service: {str(e)}. Flagged for manual review."
        }

def evaluate_policy_rules(
    estimated_cost: Optional[float],
    budget_status: str,
    vendor_security_status: str,
    vendor_risk_tier: str,
    handles_customer_data: bool,
    duplicate_match_type: str
) -> Dict[str, Any]:
    """
    Pure deterministic validation of financial approval tiers and governance policy sign-offs.
    Strictly calculates the exact approvals required:
    - Tier 1 (<$5,000): DIRECT_MANAGER
    - Tier 2 ($5,000-$25,000): DIRECT_MANAGER, DEPT_HEAD
    - Tier 3 (>$25,000): DIRECT_MANAGER, DEPT_HEAD, FINANCE_VP
    - Security review triggers: IT_SECURITY
    - Budget overrun triggers: FINANCE_VP
    """
    rules = _load_json("rules.json")
    approvals: List[str] = []
    policy_facts: List[str] = []

    # 1. Financial tier threshold
    cost = estimated_cost if estimated_cost is not None else 0.0
    if cost < 5000.0:
        approvals.append("DIRECT_MANAGER")
        tier_name = "TIER_1 (<$5k)"
    elif 5000.0 <= cost <= 25000.0:
        approvals.extend(["DIRECT_MANAGER", "DEPT_HEAD"])
        tier_name = "TIER_2 ($5k-$25k)"
    else:
        approvals.extend(["DIRECT_MANAGER", "DEPT_HEAD", "FINANCE_VP"])
        tier_name = "TIER_3 (>$25k)"

    policy_facts.append(f"Financial threshold matches {tier_name}: requires {[a for a in approvals]}.")

    # 2. Security triggers
    needs_security = False
    if handles_customer_data:
        needs_security = True
        policy_facts.append("Tool accesses customer/sensitive data: mandatory IT_SECURITY sign-off triggered.")
    if vendor_security_status in ["FAIL", "WARNING"] or vendor_risk_tier in ["HIGH", "CRITICAL"]:
        needs_security = True
        policy_facts.append(f"Vendor risk ({vendor_risk_tier}) or compliance status ({vendor_security_status}): IT_SECURITY sign-off required.")

    if needs_security and "IT_SECURITY" not in approvals:
        approvals.append("IT_SECURITY")

    # 3. Budget overrun trigger
    if budget_status == "FAIL":
        if "FINANCE_VP" not in approvals:
            approvals.append("FINANCE_VP")
        policy_facts.append("Department budget exceeded: mandatory FINANCE_VP approval required.")

    # Deduplicate while preserving order
    unique_approvals = []
    for a in approvals:
        if a not in unique_approvals:
            unique_approvals.append(a)

    return {
        "status": "PASS" if budget_status == "PASS" and vendor_security_status == "PASS" else "WARNING",
        "approval_tier": tier_name,
        "approvals_required": unique_approvals,
        "fact": " | ".join(policy_facts)
    }
