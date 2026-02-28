const API_BASE = (localStorage.getItem("BHARATASSIST_API") || "http://localhost:8000").replace(/\/$/, "");

function qs(id) {
  return document.getElementById(id);
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return await res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = "";
    try {
      const j = await res.json();
      detail = j.detail ? ` - ${JSON.stringify(j.detail)}` : "";
    } catch {}
    throw new Error(`POST ${path} failed: ${res.status}${detail}`);
  }
  return await res.json();
}

function addBubble(container, role, text) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  div.textContent = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

async function initChatPage() {
  const chat = qs("chat");
  const apiStatus = qs("apiStatus");
  const message = qs("message");
  const sendBtn = qs("sendBtn");
  const clearBtn = qs("clearBtn");
  const sessionId = qs("sessionId");

  if (!chat || !apiStatus || !message || !sendBtn || !clearBtn || !sessionId) return;

  addBubble(chat, "assistant", "Hi! Tell me your age, annual income (INR), state, and occupation to check schemes.");

  try {
    await apiGet("/health");
    apiStatus.textContent = "online";
    apiStatus.className = "status ok";
  } catch {
    apiStatus.textContent = "offline";
    apiStatus.className = "status bad";
  }

  clearBtn.addEventListener("click", () => {
    chat.innerHTML = "";
    addBubble(chat, "assistant", "Chat cleared. Ask a new question.");
  });

  async function send() {
    const text = (message.value || "").trim();
    if (!text) return;
    message.value = "";
    addBubble(chat, "user", text);
    sendBtn.disabled = true;
    try {
      const resp = await apiPost("/chat", {
        message: text,
        session_id: (sessionId.value || "").trim() || null,
      });
      if (!sessionId.value && resp.session_id) sessionId.value = resp.session_id;
      addBubble(chat, "assistant", resp.reply);
    } catch (e) {
      addBubble(chat, "assistant", `Error: ${e.message}`);
    } finally {
      sendBtn.disabled = false;
    }
  }

  sendBtn.addEventListener("click", send);
  message.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) send();
  });
}

function renderSchemeCard(s) {
  const benefits = (s.benefits || []).map((b) => `<li>${escapeHtml(b)}</li>`).join("");
  const docs = (s.documents_required || []).map((d) => `<li>${escapeHtml(d)}</li>`).join("");
  const rules = (s.matched_rules || []).map((r) => `<span class="pill">${escapeHtml(r)}</span>`).join(" ");

  return `
    <div class="scheme">
      <h3>${escapeHtml(s.name)} <span class="pill">${escapeHtml(s.id)}</span></h3>
      <p>${escapeHtml(s.description || "")}</p>
      ${rules ? `<div style="display:flex; gap:8px; flex-wrap:wrap; margin: 6px 0 10px;">${rules}</div>` : ""}
      ${benefits ? `<div class="hint" style="margin: 0 0 6px;">Benefits</div><ul>${benefits}</ul>` : ""}
      ${docs ? `<div class="hint" style="margin: 10px 0 6px;">Documents</div><ul>${docs}</ul>` : ""}
    </div>
  `;
}

async function initEligibilityPage() {
  const checkBtn = qs("checkBtn");
  const loadSchemesBtn = qs("loadSchemesBtn");
  const eligibleList = qs("eligibleList");
  const notEligibleList = qs("notEligibleList");
  const verifyBtn = qs("verifyBtn");
  const verifyOut = qs("verifyOut");

  if (!checkBtn || !loadSchemesBtn || !eligibleList || !notEligibleList || !verifyBtn || !verifyOut) return;

  function getEligibilityPayload() {
    const age = qs("age").value;
    const income = qs("income").value;
    return {
      age: age ? Number(age) : null,
      income_inr: income ? Number(income) : null,
      state: (qs("state").value || "").trim() || null,
      category: (qs("category").value || "").trim() || null,
      gender: (qs("gender").value || "").trim() || null,
      occupation: (qs("occupation").value || "").trim() || null,
      is_disabled: qs("isDisabled").checked ? true : null,
    };
  }

  async function checkEligibility() {
    eligibleList.innerHTML = "";
    notEligibleList.innerHTML = "";
    checkBtn.disabled = true;
    try {
      const resp = await apiPost("/eligibility", getEligibilityPayload());
      eligibleList.innerHTML = (resp.eligible || []).map(renderSchemeCard).join("") || `<div class="hint">No matches yet.</div>`;
      notEligibleList.innerHTML = (resp.not_eligible || []).map(renderSchemeCard).join("") || `<div class="hint">—</div>`;
    } catch (e) {
      eligibleList.innerHTML = `<div class="hint">Error: ${escapeHtml(e.message)}</div>`;
    } finally {
      checkBtn.disabled = false;
    }
  }

  async function loadSchemes() {
    eligibleList.innerHTML = "";
    notEligibleList.innerHTML = "";
    loadSchemesBtn.disabled = true;
    try {
      const resp = await apiGet("/schemes");
      const schemes = resp.schemes || [];
      eligibleList.innerHTML = schemes.map(renderSchemeCard).join("") || `<div class="hint">No schemes found.</div>`;
      notEligibleList.innerHTML = `<div class="hint">Loaded all schemes.</div>`;
    } catch (e) {
      eligibleList.innerHTML = `<div class="hint">Error: ${escapeHtml(e.message)}</div>`;
    } finally {
      loadSchemesBtn.disabled = false;
    }
  }

  async function verifyDocs() {
    verifyOut.style.display = "none";
    verifyOut.innerHTML = "";
    verifyBtn.disabled = true;
    try {
      const schemeId = (qs("schemeId").value || "").trim();
      const declared = (qs("declaredDocs").value || "")
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      if (!schemeId) throw new Error("Enter a scheme id (e.g. pm-kisan).");

      const pdf = qs("pdfFile").files && qs("pdfFile").files[0] ? qs("pdfFile").files[0] : null;

      let res;
      if (!pdf) {
        res = await apiPost("/verify", { scheme_id: schemeId, declared_documents: declared });
      } else {
        const fd = new FormData();
        fd.append("file", pdf);
        fd.append("req_json", JSON.stringify({ scheme_id: schemeId, declared_documents: declared }));

        const r = await fetch(`${API_BASE}/verify-pdf`, { method: "POST", body: fd });
        if (!r.ok) throw new Error(`POST /verify-pdf failed: ${r.status}`);
        res = await r.json();
      }

      const missing = (res.missing_declared || []).map((d) => `<li>${escapeHtml(d)}</li>`).join("");
      const found = res.pdf_found_keywords
        ? Object.entries(res.pdf_found_keywords)
            .map(([k, v]) => `<li>${escapeHtml(k)}: <span class="status ${v ? "ok" : "bad"}">${v ? "found" : "not found"}</span></li>`)
            .join("")
        : "";

      verifyOut.innerHTML = `
        <h3>${escapeHtml(res.scheme_name)} <span class="pill">${escapeHtml(res.scheme_id)}</span></h3>
        <p>${escapeHtml(res.verdict)}</p>
        <div class="hint" style="margin: 10px 0 6px;">Required</div>
        <ul>${(res.required_documents || []).map((d) => `<li>${escapeHtml(d)}</li>`).join("")}</ul>
        <div class="hint" style="margin: 10px 0 6px;">Missing (from declared)</div>
        <ul>${missing || "<li>None</li>"}</ul>
        ${found ? `<div class="hint" style="margin: 10px 0 6px;">PDF keyword scan</div><ul>${found}</ul>` : ""}
      `;
      verifyOut.style.display = "block";
    } catch (e) {
      verifyOut.innerHTML = `<p class="status bad">Error: ${escapeHtml(e.message)}</p>`;
      verifyOut.style.display = "block";
    } finally {
      verifyBtn.disabled = false;
    }
  }

  checkBtn.addEventListener("click", checkEligibility);
  loadSchemesBtn.addEventListener("click", loadSchemes);
  verifyBtn.addEventListener("click", verifyDocs);
}

initChatPage();
initEligibilityPage();

