"""
FastAPI Server for AI Procurement Copilot.
Exposes endpoints for single/two-agent evaluation, side-by-side comparison,
benchmark runner, human review actions, and interactive UI.
"""
import os
import json
import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models import ProcurementRequest, ProcurementRecommendation, HumanReviewAction
from app.agents.single_agent import run_single_agent
from app.agents.two_agent import run_two_agent
from app.mock_services import set_global_outage_simulation, is_global_outage
from eval.benchmark_cases import BENCHMARK_CASES
from eval.run_eval import run_evaluation

app = FastAPI(
    title="AI Procurement Request Copilot",
    description="Enterprise Human-in-the-Loop Procurement Decision Support with Architecture A & B comparison",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory audit log for human review actions
AUDIT_LOG: List[Dict[str, Any]] = []

@app.post("/api/evaluate", response_model=ProcurementRecommendation)
def evaluate_request(request: ProcurementRequest, simulate_outage: bool = False):
    """
    Evaluates a procurement request using the requested architecture (A or B).
    """
    arch = request.architecture or "ARCHITECTURE_A"
    outage = simulate_outage or is_global_outage()

    if arch == "ARCHITECTURE_B":
        return run_two_agent(request, simulate_outage=outage)
    else:
        return run_single_agent(request, simulate_outage=outage)

@app.post("/api/compare")
def compare_architectures(request: ProcurementRequest, simulate_outage: bool = False):
    """
    Runs BOTH Architecture A and Architecture B side-by-side on the exact same request.
    """
    outage = simulate_outage or is_global_outage()
    req_a = request.model_copy(update={"architecture": "ARCHITECTURE_A"})
    req_b = request.model_copy(update={"architecture": "ARCHITECTURE_B"})

    start_a = time.time()
    rec_a = run_single_agent(req_a, simulate_outage=outage)
    dur_a = (time.time() - start_a) * 1000.0

    start_b = time.time()
    rec_b = run_two_agent(req_b, simulate_outage=outage)
    dur_b = (time.time() - start_b) * 1000.0

    delta_latency = dur_b - dur_a
    tok_a = rec_a.token_usage.total_tokens if rec_a.token_usage else 0
    tok_b = rec_b.token_usage.total_tokens if rec_b.token_usage else 0

    return {
        "architecture_a": rec_a,
        "architecture_b": rec_b,
        "comparison": {
            "recommendation_agreement": rec_a.recommendation == rec_b.recommendation,
            "latency_delta_ms": round(delta_latency, 2),
            "faster_architecture": "Architecture A (Single Agent)" if dur_a < dur_b else "Architecture B (Two-Agent)",
            "tokens_arch_a": tok_a,
            "tokens_arch_b": tok_b,
            "tool_calls_arch_a": len(rec_a.tool_calls) if rec_a.tool_calls else 0,
            "tool_calls_arch_b": len(rec_b.tool_calls) if rec_b.tool_calls else 0
        }
    }

@app.get("/api/presets")
def get_benchmark_presets():
    """
    Returns pre-loaded test case scenarios for quick UI testing.
    """
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "category": c["category"],
            "request": c["request"],
            "simulate_outage": c.get("simulate_outage", False),
            "expected": c.get("expected")
        }
        for c in BENCHMARK_CASES
    ]

@app.get("/api/benchmarks")
def get_benchmark_results():
    """
    Retrieves stored benchmark evaluation summary.
    """
    results_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "eval", "results.json")
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # If not yet run, execute now
    return run_evaluation()

@app.post("/api/benchmarks/run")
def trigger_benchmark_run():
    """
    Executes the 20 benchmark test cases on demand.
    """
    return run_evaluation()

@app.post("/api/decision")
def record_human_decision(action: HumanReviewAction):
    """
    Records a human reviewer's final decision in the audit trail.
    """
    record = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "request_id": action.request_id,
        "decision": action.decision,
        "target_escalation": action.target_escalation,
        "notes": action.notes or "No notes provided",
        "reviewer": action.reviewer
    }
    AUDIT_LOG.insert(0, record)
    return {"status": "SUCCESS", "record": record, "total_records": len(AUDIT_LOG)}

@app.get("/api/decisions")
def get_audit_log():
    return AUDIT_LOG

@app.post("/api/outage-toggle")
def toggle_outage(enabled: bool):
    set_global_outage_simulation(enabled)
    return {"outage_simulation_active": is_global_outage()}

@app.get("/api/outage-status")
def get_outage_status():
    return {"outage_simulation_active": is_global_outage()}

# Static files mounting
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "AI Procurement Copilot API is running. Static UI not yet deployed."}
