const state = {
  projectId: "",
  activeRepository: "",
  isReady: false,
};

const elements = {
  healthStatus: document.querySelector("#healthStatus"),
  repoForm: document.querySelector("#repoForm"),
  repoUrl: document.querySelector("#repoUrl"),
  analyzeButton: document.querySelector("#analyzeButton"),
  repoState: document.querySelector("#repoState"),
  statusTrack: document.querySelector("#statusTrack"),
  activeRepo: document.querySelector("#activeRepo"),
  projectId: document.querySelector("#projectId"),
  indexStatus: document.querySelector("#indexStatus"),
  chunkCount: document.querySelector("#chunkCount"),
  messages: document.querySelector("#messages"),
  chatForm: document.querySelector("#chatForm"),
  chatInput: document.querySelector("#chatInput"),
  sendButton: document.querySelector("#sendButton"),
};

function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderMarkdown(markdown) {
  const escaped = escapeHtml(markdown.trim());
  const withBlocks = escaped.replace(/```([\s\S]*?)```/g, (_, code) => {
    return `<pre><code>${code.trim()}</code></pre>`;
  });

  return withBlocks
    .split(/\n{2,}/)
    .map((block) => {
      if (block.startsWith("<pre>")) {
        return block;
      }

      return `<p>${block.replace(/\n/g, "<br>").replace(/`([^`]+)`/g, "<code>$1</code>")}</p>`;
    })
    .join("");
}

function setStatusRows(mode) {
  const rows = [...elements.statusTrack.querySelectorAll(".status-row")];
  rows.forEach((row) => row.classList.remove("active", "done"));

  if (mode === "running") {
    rows[0].classList.add("done");
    rows[1].classList.add("active");
    rows[2].classList.add("active");
  }

  if (mode === "done") {
    rows.forEach((row) => row.classList.add("done"));
  }
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Something went wrong. Please try again.");
  }

  return data;
}

function appendMessage(role, content, sources = []) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const sourceHtml = sources.length
    ? `<div class="sources">
        <h3>Sources</h3>
        <div class="source-list">
          ${sources
            .map((source) => {
              const name = source.file_path || source.file_name || "Source";
              const lines =
                source.start_line && source.end_line
                  ? ` Lines ${source.start_line}-${source.end_line}`
                  : "";
              return `<span class="source-chip">${escapeHtml(name)}${escapeHtml(lines)}</span>`;
            })
            .join("")}
        </div>
      </div>`
    : "";

  article.innerHTML = `
    <div class="message-bubble">
      ${role === "assistant" ? renderMarkdown(content) : `<p>${escapeHtml(content)}</p>`}
      ${sourceHtml}
    </div>
  `;

  elements.messages.appendChild(article);
  elements.messages.scrollTop = elements.messages.scrollHeight;

  return article;
}

function setChatEnabled(enabled) {
  state.isReady = enabled;
  elements.chatForm.classList.toggle("disabled", !enabled);
  elements.chatInput.disabled = !enabled;
  elements.sendButton.disabled = !enabled;
}

function setRepositoryLoading(isLoading) {
  elements.analyzeButton.disabled = isLoading;
  elements.repoUrl.disabled = isLoading;
  elements.analyzeButton.querySelector("span").textContent = isLoading
    ? "Analyzing"
    : "Analyze Repository";
}

async function checkHealth() {
  try {
    await requestJson("/api/health");
    elements.healthStatus.textContent = "Backend online";
    elements.healthStatus.classList.add("ready");
  } catch {
    elements.healthStatus.textContent = "Backend unavailable";
    elements.healthStatus.classList.add("error");
  }
}

elements.repoForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const repoUrl = elements.repoUrl.value.trim();
  if (!repoUrl) {
    return;
  }

  setRepositoryLoading(true);
  setChatEnabled(false);
  elements.statusTrack.hidden = false;
  setStatusRows("running");
  elements.repoState.textContent = "Analyzing repository";
  elements.repoState.className = "repo-state";

  try {
    const data = await requestJson("/api/repository", {
      method: "POST",
      body: JSON.stringify({ repo_url: repoUrl }),
    });

    state.projectId = data.project_id;
    state.activeRepository = `${data.owner}/${data.repository}`;

    elements.activeRepo.textContent = state.activeRepository;
    elements.projectId.textContent = data.project_id;
    elements.indexStatus.textContent = data.already_exists
      ? "Already indexed"
      : "Ready";
    elements.chunkCount.textContent = data.chunks || "-";
    elements.repoState.textContent = data.already_exists
      ? "Repository already indexed"
      : "Repository ready";
    elements.repoState.className = "repo-state ready";
    setStatusRows("done");
    setChatEnabled(true);
    appendMessage("assistant", data.message);
    elements.chatInput.focus();
  } catch (error) {
    elements.repoState.textContent = "Repository error";
    elements.repoState.className = "repo-state error";
    elements.indexStatus.textContent = "Error";
    appendMessage("assistant", error.message);
  } finally {
    setRepositoryLoading(false);
  }
});

elements.chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = elements.chatInput.value.trim();
  if (!query || !state.isReady) {
    return;
  }

  appendMessage("user", query);
  elements.chatInput.value = "";
  elements.chatInput.style.height = "auto";
  elements.sendButton.disabled = true;

  const loading = appendMessage("assistant", "Thinking through the retrieved code...");
  loading.classList.add("loading");

  try {
    const data = await requestJson("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        project_id: state.projectId,
        query,
      }),
    });

    loading.remove();
    appendMessage("assistant", data.answer, data.sources || []);
  } catch (error) {
    loading.remove();
    appendMessage("assistant", error.message);
  } finally {
    elements.sendButton.disabled = false;
    elements.chatInput.focus();
  }
});

elements.chatInput.addEventListener("input", () => {
  elements.chatInput.style.height = "auto";
  elements.chatInput.style.height = `${elements.chatInput.scrollHeight}px`;
});

elements.chatInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    elements.chatForm.requestSubmit();
  }
});

checkHealth();
