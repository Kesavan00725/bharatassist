// API Base URL configuration
// For production deployment, set in browser console:
// localStorage.setItem("BHARATASSIST_API", "https://bharatassist-backend-xxxxx.a.run.app");
// OR set environment variable during deployment
const API_BASE = (
  localStorage.getItem("BHARATASSIST_API") ||
  process.env.REACT_APP_API_BASE ||
  "http://localhost:8000"
).replace(/\/$/, "");

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
    } catch { }
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

function renderScoreMeter(score) {
  const filled = Math.round((score / 100) * 12);
  const bars = Array(12)
    .fill(0)
    .map((_, i) => `<div class="score-bar ${i < filled ? "filled" : ""}"></div>`)
    .join("");
  return `
    <div class="score-display">
      <div class="score-number">${score}/100</div>
      <div class="score-bars">${bars}</div>
      <div class="score-label">${score >= 80 ? "Excellent" : score >= 60 ? "Good" : score >= 40 ? "Fair" : "Poor"}</div>
    </div>
  `;
}

function renderBestMatchCard(scheme) {
  if (!scheme) return "";
  const benefits = (scheme.benefits || []).map((b) => `<li>${escapeHtml(b)}</li>`).join("");
  const docs = (scheme.documents_required || []).map((d) => `<li>${escapeHtml(d)}</li>`).join("");
  const officialLink = scheme.official_link ? `<a href="${scheme.official_link}" target="_blank" class="btn btn-primary" style="margin-top: 16px;">Visit Official Website</a>` : "";

  return `
    <div class="best-match-card">
      <div class="best-match-badge">BEST MATCH</div>
      <h2>${escapeHtml(scheme.name)}</h2>
      <p class="scheme-id">${escapeHtml(scheme.id)}</p>
      ${renderScoreMeter(scheme.score)}
      <p class="scheme-desc">${escapeHtml(scheme.description || "")}</p>

      ${benefits ? `
        <div class="section">
          <h4>Key Benefits</h4>
          <ul>${benefits}</ul>
        </div>
      ` : ""}

      ${docs ? `
        <div class="section">
          <h4>Required Documents</h4>
          <ul>${docs}</ul>
        </div>
      ` : ""}

      ${scheme.reasons ? `
        <div class="section">
          <h4>Why You Match</h4>
          <ul>${scheme.reasons.map((r) => `<li>${escapeHtml(r)}</li>`).join("")}</ul>
        </div>
      ` : ""}

      ${officialLink}
    </div>
  `;
}

function renderSchemeCard(scheme, showScore = false) {
  const benefits = (scheme.benefits || []).map((b) => `<li>${escapeHtml(b)}</li>`).join("");
  const docs = (scheme.documents_required || []).map((d) => `<li>${escapeHtml(d)}</li>`).join("");
  const rules = (scheme.reasons || []).map((r) => `<span class="pill">${escapeHtml(r)}</span>`).join(" ");
  const officialLink = scheme.official_link || `#`;
  const linkDisplay = officialLink && officialLink !== "#" ? `<a href="${escapeHtml(officialLink)}" target="_blank" rel="noopener noreferrer" class="btn secondary" style="font-size: 12px; padding: 6px 12px; text-decoration: none;">📋 Official Site</a>` : "";

  return `
    <div class="scheme">
      <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
          <h3>${escapeHtml(scheme.name)} <span class="pill">${escapeHtml(scheme.id)}</span></h3>
          <p>${escapeHtml(scheme.description || "")}</p>
          ${linkDisplay}
        </div>
        ${showScore ? `<div style="text-align: right; font-size: 24px; font-weight: bold; color: var(--accent);">${scheme.score}</div>` : ""}
      </div>
      ${rules ? `<div style="display:flex; gap:8px; flex-wrap:wrap; margin: 6px 0 10px;">${rules}</div>` : ""}
      ${benefits ? `<div class="hint" style="margin: 0 0 6px;">Benefits</div><ul>${benefits}</ul>` : ""}
      ${docs ? `<div class="hint" style="margin: 10px 0 6px;">Documents</div><ul>${docs}</ul>` : ""}
    </div>
  `;
}

async function initChatPage() {
  const chat = qs("chat");
  const apiStatus = qs("apiStatus");
  const message = qs("message");
  const sendBtn = qs("sendBtn");
  const clearBtn = qs("clearBtn");
  const sessionId = qs("sessionId");

  if (!chat || !apiStatus || !message || !sendBtn || !clearBtn || !sessionId) return;

  // Load persisted session ID from localStorage
  const savedSessionId = localStorage.getItem("BHARATASSIST_SESSION_ID");
  if (savedSessionId) sessionId.value = savedSessionId;

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
      if (!sessionId.value && resp.session_id) {
        sessionId.value = resp.session_id;
        localStorage.setItem("BHARATASSIST_SESSION_ID", resp.session_id);
      }
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

async function initEligibilityPage() {
  const checkBtn = qs("checkBtn");
  const loadSchemesBtn = qs("loadSchemesBtn");
  const bestMatchContainer = qs("bestMatchContainer");
  const eligibleList = qs("eligibleList");
  const notEligibleList = qs("notEligibleList");
  const verifyBtn = qs("verifyBtn");
  const verifyOut = qs("verifyOut");

  if (!checkBtn || !loadSchemesBtn || !eligibleList || !notEligibleList || !verifyBtn || !verifyOut) return;

  function getEligibilityPayload() {
    const age = qs("age").value;
    const income = qs("income").value;
    const isRural = qs("isRural")?.checked;

    return {
      age: age ? Number(age) : null,
      income_inr: income ? Number(income) : null,
      state: (qs("state").value || "").trim() || null,
      category: (qs("category").value || "").trim() || null,
      gender: (qs("gender").value || "").trim() || null,
      occupation: (qs("occupation").value || "").trim() || null,
      is_disabled: qs("isDisabled")?.checked ? true : null,
      rural: isRural || null,
    };
  }

  async function checkEligibility() {
    if (bestMatchContainer) bestMatchContainer.innerHTML = "";
    eligibleList.innerHTML = "";
    notEligibleList.innerHTML = "";
    checkBtn.disabled = true;

    try {
      const resp = await apiPost("/check-eligibility", getEligibilityPayload());

      // Show best match if available
      if (bestMatchContainer && resp.best_match) {
        bestMatchContainer.innerHTML = renderBestMatchCard(resp.best_match);
      }

      // Show eligible schemes
      if (resp.eligible_schemes && resp.eligible_schemes.length > 0) {
        eligibleList.innerHTML = resp.eligible_schemes
          .map((s) => renderSchemeCard(s, true))
          .join("");
      } else {
        eligibleList.innerHTML = `<div class="hint">No eligible schemes found. Try updating your information.</div>`;
      }

      // Show not eligible schemes
      if (resp.not_eligible_schemes && resp.not_eligible_schemes.length > 0) {
        notEligibleList.innerHTML = resp.not_eligible_schemes
          .map((s) => renderSchemeCard(s, true))
          .join("");
      } else {
        notEligibleList.innerHTML = `<div class="hint">—</div>`;
      }
    } catch (e) {
      eligibleList.innerHTML = `<div class="hint">Error: ${escapeHtml(e.message)}</div>`;
    } finally {
      checkBtn.disabled = false;
    }
  }

  async function loadSchemes() {
    if (bestMatchContainer) bestMatchContainer.innerHTML = "";
    eligibleList.innerHTML = "";
    notEligibleList.innerHTML = "";
    loadSchemesBtn.disabled = true;
    try {
      const resp = await apiGet("/schemes");
      const schemes = resp.schemes || [];
      eligibleList.innerHTML = schemes.map((s) => renderSchemeCard(s, false)).join("") || `<div class="hint">No schemes found.</div>`;
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

// Floating Chat Widget
class FloatingChatWidget {
  constructor() {
    this.isOpen = false;
    this.sessionId = localStorage.getItem("BHARATASSIST_SESSION_ID");
    this.init();
  }

  init() {
    // Create widget HTML
    const widget = document.createElement("div");
    widget.id = "floating-chat-widget";
    widget.innerHTML = `
      <div class="floating-chat-btn" id="floating-chat-btn">
        <span class="chat-icon">💬</span>
      </div>
      <div class="floating-chat-box" id="floating-chat-box" style="display: none;">
        <div class="floating-chat-header">
          <h3>Chat with BharatAssist</h3>
          <button class="close-chat" id="close-chat-btn">×</button>
        </div>
        <div class="floating-chat-messages" id="floating-chat-messages"></div>
        <div class="floating-chat-input">
          <textarea id="floating-chat-input" placeholder="Ask about schemes..." rows="2"></textarea>
          <button id="floating-chat-send" class="btn" style="width: 100%; margin-top: 8px;">Send</button>
        </div>
      </div>
    `;
    document.body.appendChild(widget);

    // Inject widget styles
    this.injectStyles();

    // Attach event listeners
    document.getElementById("floating-chat-btn").addEventListener("click", () => this.toggle());
    document.getElementById("close-chat-btn").addEventListener("click", () => this.close());
    document.getElementById("floating-chat-send").addEventListener("click", () => this.sendMessage());
    document.getElementById("floating-chat-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) this.sendMessage();
    });

    // Initial greeting
    this.addMessage("assistant", "Hi! Ask me about government schemes. I can help you check eligibility and answer questions.");
  }

  injectStyles() {
    const style = document.createElement("style");
    style.textContent = `
      #floating-chat-widget {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
        font-family: inherit;
      }

      .floating-chat-btn {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, rgba(96,165,250,.6), rgba(94,234,212,.5));
        border: 2px solid rgba(96,165,250,0.4);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        box-shadow: 0 4px 16px rgba(96,165,250,0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
      }

      .floating-chat-btn::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 50%;
        background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
        animation: shine 3s infinite;
      }

      @keyframes shine {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }

      .floating-chat-btn:hover {
        transform: scale(1.15);
        box-shadow: 0 8px 24px rgba(96,165,250,0.4);
        border-color: rgba(96,165,250,0.6);
      }

      .floating-chat-btn:active {
        transform: scale(0.95);
      }

      .floating-chat-box {
        position: absolute;
        bottom: 80px;
        right: 0;
        width: 360px;
        max-width: 90vw;
        height: 500px;
        background: rgba(18,26,51,0.95);
        border: 1px solid rgba(96,165,250,0.2);
        border-radius: 16px;
        display: flex;
        flex-direction: column;
        box-shadow: 0 12px 40px rgba(0,0,0,0.4);
        animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
      }

      @keyframes slideUp {
        from {
          opacity: 0;
          transform: translateY(20px) scale(0.95);
        }
        to {
          opacity: 1;
          transform: translateY(0) scale(1);
        }
      }

      .floating-chat-header {
        padding: 16px 18px;
        border-bottom: 1px solid rgba(96,165,250,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(135deg, rgba(96,165,250,0.05), transparent);
      }

      .floating-chat-header h3 {
        margin: 0;
        font-size: 15px;
        color: var(--text);
        font-weight: 600;
      }

      .close-chat {
        background: none;
        border: none;
        color: var(--muted);
        font-size: 24px;
        cursor: pointer;
        padding: 4px 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
        border-radius: 6px;
      }

      .close-chat:hover {
        color: var(--text);
        background: rgba(96,165,250,0.1);
        transform: rotate(90deg);
      }

      .floating-chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 14px;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }

      .floating-chat-messages .bubble {
        max-width: 85%;
        padding: 10px 13px;
        border-radius: 12px;
        border: 1px solid var(--border);
        line-height: 1.4;
        font-size: 13.5px;
        word-wrap: break-word;
        animation: fadeInUp 0.2s ease-out;
      }

      .floating-chat-messages .bubble.user {
        align-self: flex-end;
        background: linear-gradient(135deg, rgba(96,165,250,.16), rgba(96,165,250,.08));
        border-color: rgba(96,165,250,0.2);
      }

      .floating-chat-messages .bubble.assistant {
        align-self: flex-start;
        background: linear-gradient(135deg, rgba(94,234,212,.12), rgba(94,234,212,.06));
        border-color: rgba(94,234,212,0.2);
      }

      .floating-chat-input {
        padding: 14px;
        border-top: 1px solid rgba(96,165,250,0.1);
        background: rgba(11,16,32,0.3);
        border-radius: 0 0 16px 16px;
      }

      #floating-chat-input {
        width: 100%;
        padding: 10px 12px;
        border-radius: 8px;
        border: 1px solid rgba(96,165,250,0.2);
        background: rgba(11,16,32,0.7);
        color: var(--text);
        outline: none;
        font-family: inherit;
        font-size: 13px;
        resize: none;
        transition: all 0.2s ease;
      }

      #floating-chat-input::placeholder {
        color: rgba(147, 164, 199, 0.6);
      }

      #floating-chat-input:focus {
        border-color: rgba(96,165,250,0.4);
        background: rgba(11,16,32,0.9);
        box-shadow: 0 0 0 2px rgba(96,165,250,0.1);
      }

      @media (max-width: 600px) {
        .floating-chat-box {
          width: calc(100vw - 20px);
          height: 400px;
          bottom: 80px;
        }
      }
    `;
    document.head.appendChild(style);
  }

  toggle() {
    this.isOpen ? this.close() : this.open();
  }

  open() {
    document.getElementById("floating-chat-box").style.display = "flex";
    this.isOpen = true;
    document.getElementById("floating-chat-input").focus();
  }

  close() {
    document.getElementById("floating-chat-box").style.display = "none";
    this.isOpen = false;
  }

  addMessage(role, text) {
    const container = document.getElementById("floating-chat-messages");
    const div = document.createElement("div");
    div.className = `bubble ${role}`;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  async sendMessage() {
    const input = document.getElementById("floating-chat-input");
    const text = (input.value || "").trim();
    if (!text) return;

    this.addMessage("user", text);
    input.value = "";
    document.getElementById("floating-chat-send").disabled = true;

    try {
      const resp = await apiPost("/chat", {
        message: text,
        session_id: this.sessionId,
      });
      if (!this.sessionId && resp.session_id) {
        this.sessionId = resp.session_id;
        localStorage.setItem("BHARATASSIST_SESSION_ID", this.sessionId);
      }
      this.addMessage("assistant", resp.reply);
    } catch (e) {
      this.addMessage("assistant", `Error: ${e.message}`);
    } finally {
      document.getElementById("floating-chat-send").disabled = false;
      input.focus();
    }
  }
}

// Initialize
initChatPage();
initEligibilityPage();
new FloatingChatWidget();

