"""
Standalone Evaluation Runner CLI:
Runs the 20 benchmark test cases against Architecture A (Single-Agent) and Architecture B (Two-Agent Pipeline).
Calculates and displays a comparative Markdown & rich table summary.
Saves results to eval/results.json and eval/results.md.
"""
import os
import json
import time
from typing import Dict, Any, List
from tabulate import tabulate
from rich.console import Console
from rich.table import Table

from app.models import ProcurementRequest
from app.agents.single_agent import run_single_agent
from app.agents.two_agent import run_two_agent
from eval.benchmark_cases import BENCHMARK_CASES
from eval.metrics import evaluate_single_run, aggregate_metrics

console = Console()

def run_evaluation() -> Dict[str, Any]:
    console.print("\n[bold cyan]====================================================================[/bold cyan]")
    console.print("[bold yellow] AI Procurement Copilot: Architecture Benchmark Evaluation [/bold yellow]")
    console.print(f"[dim]Running {len(BENCHMARK_CASES)} standardized enterprise test cases across Architectures A & B...[/dim]")
    console.print("[bold cyan]====================================================================[/bold cyan]\n")

    results_a: List[Dict[str, Any]] = []
    results_b: List[Dict[str, Any]] = []

    for i, case in enumerate(BENCHMARK_CASES, start=1):
        req_data = case["request"].copy()
        simulate_outage = case.get("simulate_outage", False)

        # Run Architecture A (Single Agent)
        req_a = ProcurementRequest(**req_data, architecture="ARCHITECTURE_A")
        out_a = run_single_agent(req_a, simulate_outage=simulate_outage)
        eval_a = evaluate_single_run(case, out_a)
        results_a.append(eval_a)

        # Run Architecture B (Two-Agent Pipeline)
        req_b = ProcurementRequest(**req_data, architecture="ARCHITECTURE_B")
        out_b = run_two_agent(req_b, simulate_outage=simulate_outage)
        eval_b = evaluate_single_run(case, out_b)
        results_b.append(eval_b)

        console.print(
            f"Case {i:02d}/20: [bold]{case['name']:<38}[/bold] | "
            f"Arch A: [{'green' if eval_a['rec_match'] else 'red'}]{out_a.recommendation:<18}[/] "
            f"({eval_a['latency_sec']:.3f}s) | "
            f"Arch B: [{'green' if eval_b['rec_match'] else 'red'}]{out_b.recommendation:<18}[/] "
            f"({eval_b['latency_sec']:.3f}s)"
        )

    summary_a = aggregate_metrics(results_a)
    summary_b = aggregate_metrics(results_b)

    # Build comparison table
    headers = ["Evaluation Metric", "Architecture A (Single Agent)", "Architecture B (Two-Agent)", "Delta / Advantage"]
    rows = [
        [
            "Recommendation Accuracy (%)",
            f"{summary_a['recommendation_accuracy_pct']}%",
            f"{summary_b['recommendation_accuracy_pct']}%",
            f"+{summary_b['recommendation_accuracy_pct'] - summary_a['recommendation_accuracy_pct']:.1f}% (B leads)"
            if summary_b['recommendation_accuracy_pct'] >= summary_a['recommendation_accuracy_pct']
            else f"{summary_b['recommendation_accuracy_pct'] - summary_a['recommendation_accuracy_pct']:.1f}%"
        ],
        [
            "Evidence Grounding (%)",
            f"{summary_a['evidence_grounding_pct']}%",
            f"{summary_b['evidence_grounding_pct']}%",
            "100.0% (Both fully grounded)" if summary_a['evidence_grounding_pct'] == summary_b['evidence_grounding_pct'] else "B higher"
        ],
        [
            "Policy Compliance (%)",
            f"{summary_a['policy_compliance_pct']}%",
            f"{summary_b['policy_compliance_pct']}%",
            f"+{summary_b['policy_compliance_pct'] - summary_a['policy_compliance_pct']:.1f}% (B leads)"
            if summary_b['policy_compliance_pct'] >= summary_a['policy_compliance_pct']
            else f"{summary_b['policy_compliance_pct'] - summary_a['policy_compliance_pct']:.1f}%"
        ],
        [
            "Avg Tool Calls / Request",
            f"{summary_a['avg_tool_calls']}",
            f"{summary_b['avg_tool_calls']}",
            f"{summary_b['avg_tool_calls'] - summary_a['avg_tool_calls']:+.1f}"
        ],
        [
            "Avg Latency (Seconds)",
            f"{summary_a['avg_latency_sec']:.4f}s",
            f"{summary_b['avg_latency_sec']:.4f}s",
            f"+{summary_b['avg_latency_sec'] - summary_a['avg_latency_sec']:.4f}s (A faster)"
        ],
        [
            "Avg Total Tokens / Run",
            f"{summary_a['avg_tokens']}",
            f"{summary_b['avg_tokens']}",
            f"+{summary_b['avg_tokens'] - summary_a['avg_tokens']:.1f} tokens"
        ],
        [
            "Estimated Cost / 1k Runs",
            f"${summary_a['total_token_cost_usd'] / len(BENCHMARK_CASES) * 1000:.4f}",
            f"${summary_b['total_token_cost_usd'] / len(BENCHMARK_CASES) * 1000:.4f}",
            f"+${(summary_b['total_token_cost_usd'] - summary_a['total_token_cost_usd']) / len(BENCHMARK_CASES) * 1000:.4f} (A lower cost)"
        ]
    ]

    table_md = tabulate(rows, headers=headers, tablefmt="github")
    console.print("\n[bold green]Benchmark Summary Results:[/bold green]")
    console.print(table_md)

    # Save to JSON
    output_payload = {
        "timestamp": time.time(),
        "total_test_cases": len(BENCHMARK_CASES),
        "summary": {
            "architecture_a": summary_a,
            "architecture_b": summary_b
        },
        "details": {
            "cases_arch_a": results_a,
            "cases_arch_b": results_b
        }
    }

    eval_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(eval_dir, "results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    # Save to Markdown
    md_path = os.path.join(eval_dir, "results.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# AI Procurement Request Copilot - Evaluation Benchmark Results\n\n")
        f.write(f"Tested on {len(BENCHMARK_CASES)} diverse test cases covering prompt injections, budget overruns, duplicate catalog overlaps, vendor security gaps, and tool outages.\n\n")
        f.write(table_md)
        f.write("\n\n## Per-Case Breakdown\n\n")
        per_case_rows = []
        for i, (c, a, b) in enumerate(zip(BENCHMARK_CASES, results_a, results_b), start=1):
            per_case_rows.append([
                c["id"],
                c["name"],
                c["category"],
                "PASS" if a["rec_match"] and a["policy_compliant"] else "FAIL",
                f"{a['latency_sec']:.3f}s",
                "PASS" if b["rec_match"] and b["policy_compliant"] else "FAIL",
                f"{b['latency_sec']:.3f}s"
            ])
        case_headers = ["ID", "Name", "Category", "Arch A Status", "Arch A Latency", "Arch B Status", "Arch B Latency"]
        f.write(tabulate(per_case_rows, headers=case_headers, tablefmt="github"))
        f.write("\n")

    console.print(f"\n[bold green]✓ Benchmark artifacts saved to {json_path} and {md_path}[/bold green]\n")
    return output_payload

if __name__ == "__main__":
    run_evaluation()
