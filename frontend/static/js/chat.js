const DEFAULT_MODEL = window.DEFAULT_MODEL || "qwen2.5:7b";
const FRONTEND_TIMEOUT_MS = (window.FRONTEND_TIMEOUT_SEC || 195) * 1000;

const messagesEl = document.getElementById("chat-messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const clearBtn = document.getElementById("clear-btn");
const webSearchToggle = document.getElementById("web-search-toggle");
const errorEl = document.getElementById("chat-error");
const loadingEl = document.getElementById("chat-loading");

function showError(msg) {
  errorEl.textContent = msg;
  errorEl.classList.remove("hidden");
}

function hideError() {
  errorEl.classList.add("hidden");
}

function setLoading(on, message) {
  loadingEl.textContent = message || "Thinking…";
  loadingEl.classList.toggle("hidden", !on);
  sendBtn.disabled = on;
}

function appendBubble(role, text) {
  const div = document.createElement("div");
  div.className = `chat-bubble ${role}`;
  div.innerHTML = `<strong>${role === "user" ? "You" : "Assistant"}</strong><p></p>`;
  div.querySelector("p").textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function renderMessages(messages) {
  messagesEl.innerHTML = "";
  if (!messages.length) {
    appendBubble(
      "assistant",
      "Hello — I am DavidAI running locally via Ollama. Ask anything to get started."
    );
    return;
  }
  messages.forEach((m) => appendBubble(m.role, m.content));
}

async function loadConversation() {
  try {
    const res = await fetch("/api/conversations");
    const data = await res.json();
    if (data.ok && data.messages?.length) {
      renderMessages(data.messages);
    }
  } catch (e) {
    console.warn("Could not load conversation", e);
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();
  const text = input.value.trim();
  if (!text) return;

  const useWebSearch = webSearchToggle?.checked ?? false;
  const loadingMessage = useWebSearch
    ? "Searching web and thinking…"
    : "Qwen is thinking. This may take up to 3 minutes.";

  appendBubble("user", text);
  input.value = "";
  setLoading(true, loadingMessage);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), FRONTEND_TIMEOUT_MS);
  const startedAt = performance.now();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        model: DEFAULT_MODEL,
        use_web_search: useWebSearch,
      }),
      signal: controller.signal,
    });
    const data = await res.json();
    const durationSec = ((performance.now() - startedAt) / 1000).toFixed(1);

    if (!res.ok || !data.ok) {
      console.warn(`Chat failed duration=${durationSec}s error=${data.error}`);
      showError(data.error || `Request failed (${res.status})`);
      return;
    }

    console.info(`Chat success duration=${durationSec}s search=${useWebSearch}`);
    appendBubble("assistant", data.message);
  } catch (err) {
    if (err.name === "AbortError") {
      showError("Request timed out. Try a shorter question.");
    } else {
      showError(err.message || "Network error — is Ollama running?");
    }
  } finally {
    clearTimeout(timeoutId);
    setLoading(false);
    input.focus();
  }
});

clearBtn.addEventListener("click", async () => {
  hideError();
  try {
    await fetch("/api/conversations/clear", { method: "POST" });
    renderMessages([]);
  } catch (e) {
    showError("Could not clear chat history.");
  }
});

loadConversation();
