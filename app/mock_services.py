"""
Mock external vendor security and compliance service.
Simulates a real-world enterprise vendor risk intelligence API (e.g., Whistic, OneTrust, SecurityScorecard).
Supports intentional outage/timeout simulation for resilience testing.
"""
from typing import Dict, Any, Optional
import time

MOCK_VENDOR_REGISTRY: Dict[str, Dict[str, Any]] = {
    "atlassian": {
        "vendor_name": "Atlassian Inc.",
        "soc2_status": "SOC2_TYPE_II",
        "soc2_valid_until": "2027-11-30",
        "gdpr_compliant": True,
        "risk_tier": "LOW",
        "active_master_services_agreement": True,
        "data_residency_options": ["US", "EU"],
        "notes": "Verified enterprise vendor with ongoing enterprise agreement."
    },
    "salesforce": {
        "vendor_name": "Salesforce Inc.",
        "soc2_status": "SOC2_TYPE_II",
        "soc2_valid_until": "2027-12-31",
        "gdpr_compliant": True,
        "risk_tier": "LOW",
        "active_master_services_agreement": True,
        "data_residency_options": ["US", "EU", "APAC"],
        "notes": "Standard enterprise vendor."
    },
    "figma": {
        "vendor_name": "Figma",
        "soc2_status": "SOC2_TYPE_II",
        "soc2_valid_until": "2027-08-31",
        "gdpr_compliant": True,
        "risk_tier": "LOW",
        "active_master_services_agreement": True,
        "data_residency_options": ["US"],
        "notes": "Design platform approved for internal design teams."
    },
    "github": {
        "vendor_name": "GitHub / Microsoft",
        "soc2_status": "SOC2_TYPE_II",
        "soc2_valid_until": "2027-10-31",
        "gdpr_compliant": True,
        "risk_tier": "LOW",
        "active_master_services_agreement": True,
        "data_residency_options": ["US", "EU"],
        "notes": "Core code repository platform."
    },
    "datadog": {
        "vendor_name": "Datadog Inc.",
        "soc2_status": "SOC2_TYPE_II",
        "soc2_valid_until": "2027-05-31",
        "gdpr_compliant": True,
        "risk_tier": "LOW",
        "active_master_services_agreement": True,
        "data_residency_options": ["US", "EU"],
        "notes": "Monitoring infrastructure partner."
    },
    "asana": {
        "vendor_name": "Asana, Inc.",
        "soc2_status": "SOC2_TYPE_II",
        "soc2_valid_until": "2027-04-30",
        "gdpr_compliant": True,
        "risk_tier": "LOW",
        "active_master_services_agreement": False,
        "data_residency_options": ["US", "EU"],
        "notes": "Project management platform; note company already licenses Jira."
    },
    "linear": {
        "vendor_name": "Linear Orbit, Inc.",
        "soc2_status": "SOC2_TYPE_II",
        "soc2_valid_until": "2027-06-15",
        "gdpr_compliant": True,
        "risk_tier": "LOW",
        "active_master_services_agreement": False,
        "data_residency_options": ["US"],
        "notes": "Modern issue tracker; pending MSA."
    },
    "cursor": {
        "vendor_name": "Anysphere (Cursor)",
        "soc2_status": "SOC2_TYPE_II",
        "soc2_valid_until": "2027-03-31",
        "gdpr_compliant": True,
        "risk_tier": "MEDIUM",
        "active_master_services_agreement": False,
        "data_residency_options": ["US"],
        "notes": "AI code editor; telemetry and prompt privacy agreement required."
    },
    "shadowai": {
        "vendor_name": "ShadowAI Labs Ltd.",
        "soc2_status": "NONE",
        "soc2_valid_until": None,
        "gdpr_compliant": False,
        "risk_tier": "HIGH",
        "active_master_services_agreement": False,
        "data_residency_options": ["UNKNOWN"],
        "notes": "Unregistered offshore AI wrapper. No SOC2 report or data retention policy."
    },
    "quickscrape": {
        "vendor_name": "QuickScrape Solutions",
        "soc2_status": "EXPIRED",
        "soc2_valid_until": "2024-01-10",
        "gdpr_compliant": False,
        "risk_tier": "CRITICAL",
        "active_master_services_agreement": False,
        "data_residency_options": ["UNKNOWN"],
        "notes": "Lapsed compliance certificate, critical vulnerability reported on scraper proxy."
    },
    "hyperwrite": {
        "vendor_name": "HyperWrite Tech",
        "soc2_status": "SOC2_TYPE_I",
        "soc2_valid_until": "2027-01-01",
        "gdpr_compliant": True,
        "risk_tier": "MEDIUM",
        "active_master_services_agreement": False,
        "data_residency_options": ["US"],
        "notes": "SOC2 Type I only; Type II in progress. Security review required."
    }
}

# Outage simulation state
_SIMULATE_GLOBAL_OUTAGE = False

def set_global_outage_simulation(enabled: bool):
    global _SIMULATE_GLOBAL_OUTAGE
    _SIMULATE_GLOBAL_OUTAGE = enabled

def is_global_outage():
    return _SIMULATE_GLOBAL_OUTAGE

class MockVendorServiceError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code

def query_vendor_security_api(vendor_query: str, simulate_failure: bool = False) -> Dict[str, Any]:
    """
    Mock external vendor API endpoint.
    Throws MockVendorServiceError(500) if simulate_failure or global outage is active.
    """
    if _SIMULATE_GLOBAL_OUTAGE or simulate_failure or "outage" in vendor_query.lower() or "timeout" in vendor_query.lower():
        time.sleep(0.05)
        raise MockVendorServiceError(
            "Mock Vendor Security Service 500: Gateway Timeout / Upstream Security API Unavailable",
            status_code=500
        )
    
    clean_query = vendor_query.strip().lower()
    
    # Exact or substring match
    for key, data in MOCK_VENDOR_REGISTRY.items():
        if key in clean_query or clean_query in key or clean_query in data["vendor_name"].lower():
            return {
                "status": "SUCCESS",
                "vendor_found": True,
                "data": data
            }
            
    # Generic unlisted vendor fallback
    return {
        "status": "SUCCESS",
        "vendor_found": False,
        "data": {
            "vendor_name": vendor_query,
            "soc2_status": "UNKNOWN",
            "soc2_valid_until": None,
            "gdpr_compliant": False,
            "risk_tier": "MEDIUM",
            "active_master_services_agreement": False,
            "data_residency_options": ["UNKNOWN"],
            "notes": "Vendor not found in corporate trust registry. Requires security vetting questionnaire."
        }
    }
