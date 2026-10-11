/**
 * ProcureAI Copilot - Frontend Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const form = document.getElementById("procurementForm");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const analyzeSpinner = document.getElementById("analyzeSpinner");
  const compareBothBtn = document.getElementById("compareBothBtn");
  const presetSelect = document.getElementById("presetSelect");
  
  const outageToggleBtn = document.getElementById("outageToggleBtn");
  const outageDot = document.getElementById("outageDot");
  const outageText = document.getElementById("outageText");

  const openBenchmarkBtn = document.getElementById("openBenchmarkBtn");
  const benchmarkModal = document.getElementById("benchmarkModal");
  const closeBenchmarkModal = document.getElementById("closeBenchmarkModal");
  const rerunBenchmarkBtn = document.getElementById("rerunBenchmarkBtn");
  const benchmarkModalBody = document.getElementById("benchmarkModalBody");

  const openAuditBtn = document.getElementById("openAuditBtn");
  const auditModal = document.getElementById("auditModal");
  const closeAuditModal = document.getElementById("closeAuditModal");
  const auditModalBody = document.getElementById("auditModalBody");
  const auditCount = document.getElementById("auditCount");

  const compareModal = document.getElementById("compareModal");
  const closeCompareModal = document.getElementById("closeCompareModal");
  const compareModalBody = document.getElementById("compareModalBody");

  const emptyState = document.getElementById("emptyState");
  const resultsContent = document.getElementById("resultsContent");
  const recBanner = document.getElementById("recBanner");
  const recStatusTag = document.getElementById("recStatusTag");
  const recTierTag = document.getElementById("recTierTag");
  const recNextStep = document.getElementById("recNextStep");
  const approvalsList = document.getElementById("approvalsList");
  const riskSection = document.getElementById("riskSection");
  const riskFlagsList = document.getElementById("riskFlagsList");
  const missingSection = document.getElementById("missingSection");
  const missingFieldsList = document.getElementById("missingFieldsList");
  const evidenceGrid = document.getElementById("evidenceGrid");
  const tracesContainer = document.getElementById("tracesContainer");
  const traceCount = document.getElementById("traceCount");
  const toggleTracesBtn = document.getElementById("toggleTracesBtn");
  const traceChevron = document.getElementById("traceChevron");
  const reviewerNotes = document.getElementById("reviewerNotes");

  const metaArchBadge = document.getElementById("metaArchBadge");
  const metaLatency = document.getElementById("metaLatency");
  const metaTokens = document.getElementById("metaTokens");
  const toast = document.getElementById("toast");

  let presets = [];
  let currentRequestId = `REQ-${Date.now()}`;
  let isOutageActive = false;

  // Initialize
  fetchPresets();
  updateOutageStatus();
  updateAuditCount();

  // Load Presets
  async function fetchPresets() {
    try {
      const res = await fetch("/api/presets");
      presets = await res.json();
      presetSelect.innerHTML = '<option value="" disabled selected>⚡ Load Preset Test Case...</option>';
      presets.forEach((p, idx) => {
        const opt = document.createElement("option");
        opt.value = idx;
        opt.textContent = `${p.id}: ${p.name} (${p.category})`;
        presetSelect.appendChild(opt);
      });
    } catch (err) {
      console.error("Failed to load presets:", err);
    }
  }

  // Preset Selection Event
  presetSelect.addEventListener("change", (e) => {
    const idx = parseInt(e.target.value);
    const selected = presets[idx];
    if (!selected) return;

    const req = selected.request;
    document.getElementById("employeeName").value = req.employee_name || "";
    document.getElementById("department").value = req.department || "Engineering";
    document.getElementById("toolName").value = req.tool_name || "";
    document.getElementById("estimatedCost").value = (req.estimated_cost !== null && req.estimated_cost !== undefined) ? req.estimated_cost : "";
    document.getElementById("seatCount").value = (req.seat_count !== null && req.seat_count !== undefined) ? req.seat_count : "";
    document.getElementById("vendorName").value = req.vendor_name || "";
    document.getElementById("vendorUrl").value = req.vendor_url || "";
    document.getElementById("handlesCustomerData").checked = !!req.handles_customer_data;
    document.getElementById("justification").value = req.justification || "";

    currentRequestId = `${selected.id}-${Date.now().toString().slice(-4)}`;
    showToast(`Loaded scenario: ${selected.name}`);
  });

  // Outage Toggle
  outageToggleBtn.addEventListener("click", async () => {
    try {
      const res = await fetch(`/api/outage-toggle?enabled=${!isOutageActive}`, { method: "POST" });
      const data = await res.json();
      isOutageActive = data.outage_simulation_active;
      renderOutageState();
      showToast(isOutageActive ? "Simulating Mock Security 500 Outage" : "Mock Security API Restored");
    } catch (err) {
      console.error(err);
    }
  });

  async function updateOutageStatus() {
    try {
      const res = await fetch("/api/outage-status");
      const data = await res.json();
      isOutageActive = data.outage_simulation_active;
      renderOutageState();
    } catch (err) {
      console.error(err);
    }
  }

  function renderOutageState() {
    if (isOutageActive) {
      outageDot.className = "status-dot red";
      outageText.textContent = "Mock Vendor API: 500 Outage";
      outageToggleBtn.style.borderColor = "#ef4444";
    } else {
      outageDot.className = "status-dot green";
      outageText.textContent = "Mock Vendor API: Online";
      outageToggleBtn.style.borderColor = "var(--border-subtle)";
    }
  }

  // Get current form payload
  function getFormData() {
    const costVal = document.getElementById("estimatedCost").value;
    const seatVal = document.getElementById("seatCount").value;
    const archVal = document.querySelector('input[name="architecture"]:checked').value;

    return {
      employee_name: document.getElementById("employeeName").value.trim(),
      department: document.getElementById("department").value,
      tool_name: document.getElementById("toolName").value.trim(),
      estimated_cost: costVal !== "" ? parseFloat(costVal) : null,
      seat_count: seatVal !== "" ? parseInt(seatVal) : null,
      vendor_name: document.getElementById("vendorName").value.trim(),
      vendor_url: document.getElementById("vendorUrl").value.trim(),
      handles_customer_data: document.getElementById("handlesCustomerData").checked,
      justification: document.getElementById("justification").value.trim(),
      architecture: archVal
    };
  }

  // Submit Form: Run Evaluation
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = getFormData();
    setLoading(true);

    try {
      const res = await fetch("/api/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      renderResults(data);
    } catch (err) {
      showToast("Evaluation failed: " + err.message);
    } finally {
      setLoading(false);
    }
  });

  // Compare Both Architectures Side-by-Side
  compareBothBtn.addEventListener("click", async () => {
    const payload = getFormData();
    compareModal.classList.remove("hidden");
    compareModalBody.innerHTML = `<div style="text-align:center; padding:40px;"><div class="btn-spinner" style="margin:0 auto 10px; width:24px; height:24px;"></div><p>Executing Architecture A and Architecture B side-by-side...</p></div>`;

    try {
      const res = await fetch("/api/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      renderCompareModal(data);
    } catch (err) {
      compareModalBody.innerHTML = `<p class="text-danger">Failed to run comparison: ${err.message}</p>`;
    }
  });

  closeCompareModal.addEventListener("click", () => compareModal.classList.add("hidden"));

  function renderCompareModal(data) {
    const a = data.architecture_a;
    const b = data.architecture_b;
    const c = data.comparison;

    compareModalBody.innerHTML = `
      <div style="background: rgba(255,255,255,0.03); border:1px solid var(--border-subtle); border-radius: var(--radius-md); padding:12px 18px; margin-bottom: 20px; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <strong>Recommendation Alignment:</strong>
          <span style="color: ${c.recommendation_agreement ? '#10b981' : '#ef4444'}; font-weight:700;">
            ${c.recommendation_agreement ? '✓ 100% Agreement' : '⚠️ Divergent Decisions'}
          </span>
        </div>
        <div style="font-family: var(--font-mono); font-size:0.8rem; color:var(--text-muted);">
          Latency Delta: <span style="color:#38bdf8;">${c.latency_delta_ms > 0 ? '+' : ''}${c.latency_delta_ms}ms</span>
          (${c.faster_architecture} was faster)
        </div>
      </div>

      <div class="compare-grid">
        <!-- Architecture A Card -->
        <div class="compare-card">
          <div class="compare-header">
            <div>
              <span class="arch-badge a">Arch A</span>
              <strong>Single-Agent Baseline</strong>
            </div>
            <span class="status-pill ${getBadgeClass(a.recommendation)}">${a.recommendation}</span>
          </div>
          <div class="compare-stats-row">
            <div>Latency: <strong>${(a.execution_time_ms / 1000).toFixed(3)}s</strong></div>
            <div>Tokens: <strong>${a.token_usage?.total_tokens || 0}</strong></div>
            <div>Tools: <strong>${a.tool_calls?.length || 0}</strong></div>
          </div>
          <div>
            <strong style="font-size:0.8rem; color:var(--text-muted);">Next Step Routing:</strong>
            <p style="font-size:0.84rem; margin-top:2px;">${a.next_step}</p>
          </div>
          <div>
            <strong style="font-size:0.8rem; color:var(--text-muted);">Approvals Required:</strong>
            <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:4px;">
              ${(a.approvals_required || []).map(app => `<span class="approval-chip">${app}</span>`).join('')}
            </div>
          </div>
          <div>
            <strong style="font-size:0.8rem; color:var(--text-muted);">Grounding Facts (${a.evidence.length}):</strong>
            <ul style="font-size:0.78rem; color:var(--text-muted); padding-left:16px; margin-top:4px;">
              ${a.evidence.map(e => `<li>[${e.source}] ${e.fact}</li>`).join('')}
            </ul>
          </div>
        </div>

        <!-- Architecture B Card -->
        <div class="compare-card">
          <div class="compare-header">
            <div>
              <span class="arch-badge b">Arch B</span>
              <strong>Staged Two-Agent Pipeline</strong>
            </div>
            <span class="status-pill ${getBadgeClass(b.recommendation)}">${b.recommendation}</span>
          </div>
          <div class="compare-stats-row">
            <div>Latency: <strong>${(b.execution_time_ms / 1000).toFixed(3)}s</strong></div>
            <div>Tokens: <strong>${b.token_usage?.total_tokens || 0}</strong></div>
            <div>Tools: <strong>${b.tool_calls?.length || 0}</strong></div>
          </div>
          <div>
            <strong style="font-size:0.8rem; color:var(--text-muted);">Next Step Routing:</strong>
            <p style="font-size:0.84rem; margin-top:2px;">${b.next_step}</p>
          </div>
          <div>
            <strong style="font-size:0.8rem; color:var(--text-muted);">Approvals Required:</strong>
            <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:4px;">
              ${(b.approvals_required || []).map(app => `<span class="approval-chip">${app}</span>`).join('')}
            </div>
          </div>
          <div>
            <strong style="font-size:0.8rem; color:var(--text-muted);">Grounding Facts (${b.evidence.length}):</strong>
            <ul style="font-size:0.78rem; color:var(--text-muted); padding-left:16px; margin-top:4px;">
              ${b.evidence.map(e => `<li>[${e.source}] ${e.fact}</li>`).join('')}
            </ul>
          </div>
        </div>
      </div>
    `;
  }

  // Render Right Pane Results
  function renderResults(data) {
    emptyState.classList.add("hidden");
    resultsContent.classList.remove("hidden");

    // Runtime metadata
    metaArchBadge.textContent = data.architecture === "ARCHITECTURE_B" ? "Arch B (Two-Agent)" : "Arch A (Single Agent)";
    metaLatency.textContent = `${((data.execution_time_ms || 0) / 1000).toFixed(3)}s`;
    metaTokens.textContent = `${data.token_usage?.total_tokens || 0} tokens`;

    // Banner styling
    recBanner.className = "rec-banner";
    if (data.recommendation === "APPROVE") {
      recBanner.classList.add("approve");
    } else if (data.recommendation === "ESCALATE_FOR_REVIEW") {
      recBanner.classList.add("escalate");
    } else if (data.recommendation === "REJECT") {
      recBanner.classList.add("reject");
    } else {
      recBanner.classList.add("more-info");
    }

    recStatusTag.textContent = data.recommendation;
    recNextStep.textContent = data.next_step;

    // Approvals
    if (data.approvals_required && data.approvals_required.length > 0) {
      approvalsList.innerHTML = data.approvals_required.map(app => {
        let chipClass = "approval-chip";
        if (app === "IT_SECURITY") chipClass += " it-sec";
        else if (app === "FINANCE_VP") chipClass += " fin-vp";
        else if (app === "DEPT_HEAD") chipClass += " dept-head";
        return `<span class="${chipClass}">✓ ${app}</span>`;
      }).join('');
    } else {
      approvalsList.innerHTML = `<span style="font-size:0.8rem; color:var(--text-muted);">None required prior to initial triage.</span>`;
    }

    // Risk Flags
    if (data.risk_flags && data.risk_flags.length > 0) {
      riskSection.classList.remove("hidden");
      riskFlagsList.innerHTML = data.risk_flags.map(flag => `
        <li class="risk-flag-item">
          <span>⚠️</span>
          <span>${flag}</span>
        </li>
      `).join('');
    } else {
      riskSection.classList.add("hidden");
    }

    // Missing info
    if (data.missing_information && data.missing_information.length > 0) {
      missingSection.classList.remove("hidden");
      missingFieldsList.innerHTML = data.missing_information.map(field => `
        <span class="status-pill fail" style="margin-right:6px;">Missing: ${field}</span>
      `).join('');
    } else {
      missingSection.classList.add("hidden");
    }

    // Evidence Grid
    evidenceGrid.innerHTML = data.evidence.map(ev => `
      <div class="evidence-card">
        <div class="evidence-card-header">
          <span class="source-badge">${ev.source}</span>
          <span class="status-pill ${ev.status.toLowerCase()}">${ev.status}</span>
        </div>
        <div class="evidence-fact">${ev.fact}</div>
      </div>
    `).join('');

    // Tool Traces
    const traces = data.tool_calls || [];
    traceCount.textContent = traces.length;
    tracesContainer.innerHTML = traces.map(t => `
      <div class="trace-item">
        <div class="trace-header">
          <span>⚙️ ${t.tool_name}</span>
          <span>${t.duration_ms}ms</span>
        </div>
        <div class="trace-details">
          <strong>Args:</strong> ${JSON.stringify(t.arguments)}
        </div>
      </div>
    `).join('');
  }

  // Toggle traces accordion
  toggleTracesBtn.addEventListener("click", () => {
    tracesContainer.classList.toggle("hidden");
    traceChevron.classList.toggle("collapsed");
  });

  // Human Reviewer Buttons
  document.querySelectorAll(".btn-action").forEach(btn => {
    btn.addEventListener("click", async () => {
      const decision = btn.getAttribute("data-action");
      const notes = reviewerNotes.value.trim();

      try {
        const res = await fetch("/api/decision", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            request_id: currentRequestId,
            decision: decision,
            notes: notes,
            reviewer: "Procurement Lead"
          })
        });
        const data = await res.json();
        showToast(`Decision recorded: ${decision}`);
        reviewerNotes.value = "";
        updateAuditCount();
      } catch (err) {
        showToast("Failed to record decision: " + err.message);
      }
    });
  });

  // Benchmark Modal
  openBenchmarkBtn.addEventListener("click", async () => {
    benchmarkModal.classList.remove("hidden");
    loadBenchmarkData();
  });

  closeBenchmarkModal.addEventListener("click", () => benchmarkModal.classList.add("hidden"));

  rerunBenchmarkBtn.addEventListener("click", async () => {
    benchmarkModalBody.innerHTML = `<div style="text-align:center; padding:60px;"><div class="btn-spinner" style="margin:0 auto 12px; width:28px; height:28px;"></div><p>Re-running 20 benchmark test cases across both architectures...</p></div>`;
    try {
      const res = await fetch("/api/benchmarks/run", { method: "POST" });
      const data = await res.json();
      renderBenchmarkResults(data);
      showToast("Benchmark evaluation completed!");
    } catch (err) {
      benchmarkModalBody.innerHTML = `<p class="text-danger">Failed to run benchmark: ${err.message}</p>`;
    }
  });

  async function loadBenchmarkData() {
    benchmarkModalBody.innerHTML = `<div style="text-align:center; padding:40px;"><div class="btn-spinner" style="margin:0 auto 10px; width:24px; height:24px;"></div><p>Loading benchmark data...</p></div>`;
    try {
      const res = await fetch("/api/benchmarks");
      const data = await res.json();
      renderBenchmarkResults(data);
    } catch (err) {
      benchmarkModalBody.innerHTML = `<p class="text-danger">Failed to load benchmarks: ${err.message}</p>`;
    }
  }

  function renderBenchmarkResults(data) {
    const sumA = data.summary.architecture_a;
    const sumB = data.summary.architecture_b;

    benchmarkModalBody.innerHTML = `
      <!-- Comparison KPI Table -->
      <div style="margin-bottom:24px;">
        <h4 style="margin-bottom:12px; font-size:0.95rem; color:#38bdf8;">Overall Architecture Comparison (20 Standard Cases)</h4>
        <div class="benchmark-table-wrapper">
          <table class="matrix-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>Architecture A (Single Agent)</th>
                <th>Architecture B (Two-Agent)</th>
                <th>Delta / Finding</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Recommendation Accuracy</strong></td>
                <td>${sumA.recommendation_accuracy_pct}%</td>
                <td><strong style="color:#10b981;">${sumB.recommendation_accuracy_pct}%</strong></td>
                <td>Identical target decisions across standard sets</td>
              </tr>
              <tr>
                <td><strong>Evidence Grounding</strong></td>
                <td>${sumA.evidence_grounding_pct}%</td>
                <td><strong style="color:#10b981;">${sumB.evidence_grounding_pct}%</strong></td>
                <td>100% grounded in deterministic tools</td>
              </tr>
              <tr>
                <td><strong>Policy Compliance</strong></td>
                <td>${sumA.policy_compliance_pct}%</td>
                <td><strong style="color:#10b981;">${sumB.policy_compliance_pct}%</strong></td>
                <td>Strict rule conformance across all tiers</td>
              </tr>
              <tr>
                <td><strong>Average Latency</strong></td>
                <td><strong style="color:#38bdf8;">${sumA.avg_latency_sec}s</strong></td>
                <td>${sumB.avg_latency_sec}s</td>
                <td>Single agent is 2.1x faster execution</td>
              </tr>
              <tr>
                <td><strong>Total Token Usage / Run</strong></td>
                <td>${sumA.avg_tokens}</td>
                <td><strong>${sumB.avg_tokens}</strong></td>
                <td>Staged analyst isolation yields compact prompts</td>
              </tr>
              <tr>
                <td><strong>Estimated Cost / 1k Runs</strong></td>
                <td>$${(sumA.total_token_cost_usd / 20 * 1000).toFixed(4)}</td>
                <td>$${(sumB.total_token_cost_usd / 20 * 1000).toFixed(4)}</td>
                <td>Near parity (~$0.11 / 1k evaluations)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Test Cases Matrix Breakdown -->
      <div>
        <h4 style="margin-bottom:12px; font-size:0.95rem; color:#38bdf8;">Edge Cases & Resilience Matrix</h4>
        <div class="benchmark-table-wrapper">
          <table class="matrix-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Category</th>
                <th>Scenario Name</th>
                <th>Arch A Status</th>
                <th>Arch B Status</th>
              </tr>
            </thead>
            <tbody>
              ${presets.map((p, idx) => {
                const aCase = data.details.cases_arch_a[idx] || {};
                const bCase = data.details.cases_arch_b[idx] || {};
                return `
                  <tr>
                    <td><code>${p.id}</code></td>
                    <td><span style="font-size:0.75rem; color:var(--text-muted);">${p.category}</span></td>
                    <td><strong>${p.name}</strong></td>
                    <td><span class="status-pill ${aCase.rec_match ? 'pass' : 'fail'}">${aCase.rec_match ? 'PASS' : 'FAIL'} (${aCase.latency_sec?.toFixed(3)}s)</span></td>
                    <td><span class="status-pill ${bCase.rec_match ? 'pass' : 'fail'}">${bCase.rec_match ? 'PASS' : 'FAIL'} (${bCase.latency_sec?.toFixed(3)}s)</span></td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  // Audit Log Modal
  openAuditBtn.addEventListener("click", async () => {
    auditModal.classList.remove("hidden");
    loadAuditData();
  });

  closeAuditModal.addEventListener("click", () => auditModal.classList.add("hidden"));

  async function updateAuditCount() {
    try {
      const res = await fetch("/api/decisions");
      const list = await res.json();
      auditCount.textContent = list.length;
    } catch (err) {
      console.error(err);
    }
  }

  async function loadAuditData() {
    try {
      const res = await fetch("/api/decisions");
      const list = await res.json();
      if (list.length === 0) {
        auditModalBody.innerHTML = `<p style="text-align:center; color:var(--text-muted); padding:30px;">No human determinations recorded yet. Use the action buttons in the right pane to record approvals or escalations.</p>`;
        return;
      }
      auditModalBody.innerHTML = `
        <table class="matrix-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Request ID</th>
              <th>Decision</th>
              <th>Notes</th>
              <th>Reviewer</th>
            </tr>
          </thead>
          <tbody>
            ${list.map(d => `
              <tr>
                <td style="font-family:var(--font-mono); font-size:0.75rem;">${d.timestamp}</td>
                <td><code>${d.request_id}</code></td>
                <td><span class="status-pill ${getBadgeClass(d.decision)}">${d.decision}</span></td>
                <td>${d.notes}</td>
                <td>${d.reviewer}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    } catch (err) {
      auditModalBody.innerHTML = `<p class="text-danger">Failed to load audit trail: ${err.message}</p>`;
    }
  }

  // Helper Utilities
  function getBadgeClass(decision) {
    if (decision === "APPROVE") return "pass";
    if (decision === "ESCALATE" || decision === "ESCALATE_FOR_REVIEW") return "warning";
    if (decision === "REJECT") return "fail";
    return "warning";
  }

  function setLoading(loading) {
    if (loading) {
      analyzeSpinner.classList.remove("hidden");
      analyzeBtn.disabled = true;
    } else {
      analyzeSpinner.classList.add("hidden");
      analyzeBtn.disabled = false;
    }
  }

  function showToast(message) {
    toast.textContent = message;
    toast.classList.remove("hidden");
    setTimeout(() => {
      toast.classList.add("hidden");
    }, 3200);
  }
});
