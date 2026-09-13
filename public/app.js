const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const send = document.querySelector("#send");
const sessionId = crypto.randomUUID();

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[character]);
}

function markdown(value) {
  return escapeHtml(value)
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/^- (.*)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/\n/g, "<br>");
}

function addMessage(text, role, result) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const content = document.createElement("div");
  content.className = "content";
  content.innerHTML = `<p>${markdown(text)}</p>`;
  article.append(content);
  if (result?.sources?.length) {
    const details = document.createElement("div");
    details.className = "details";
    details.innerHTML = `<strong>Knowledge-base sources</strong><ul>${result.sources.map((source) => `<li><a href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">${escapeHtml(source.title)}</a></li>`).join("")}</ul>`;
    article.append(details);
  }
  if (result?.currentInfo?.length) {
    const tools = document.createElement("div");
    tools.className = "tool-status";
    tools.textContent = result.currentInfo.map((item) => item.ok ? `MCP: ${item.kind} via ${item.provider}` : `MCP: ${item.kind} unavailable`).join(" · ");
    article.append(tools);
  }
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

for (const button of document.querySelectorAll(".suggestions button")) {
  button.addEventListener("click", () => { input.value = button.textContent; input.focus(); });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  addMessage(message, "user");
  input.value = "";
  send.disabled = true;
  const pending = document.createElement("article");
  pending.className = "message assistant pending";
  pending.textContent = "Planning…";
  messages.append(pending);
  try {
    const response = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message, sessionId }) });
    const result = await response.json();
    pending.remove();
    if (!response.ok) throw new Error(result.error || "Request failed.");
    addMessage(result.answer, "assistant", result);
  } catch (error) {
    pending.remove();
    addMessage(error instanceof Error ? error.message : "Unable to contact the assistant.", "assistant");
  } finally {
    send.disabled = false;
    input.focus();
  }
});
