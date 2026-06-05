const state = {
  tweets: [],
  runCount: 0,
};

const els = {
  status: document.getElementById("status"),
  count: document.getElementById("tweet-count"),
  originalList: document.getElementById("original-list"),
  versions: document.getElementById("versions"),
  form: document.getElementById("prompt-form"),
  prompt: document.getElementById("prompt"),
  runButton: document.getElementById("run-button"),
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function metrics(tweet) {
  const m = tweet.metrics || {};
  return `reply ${m.reply_count || 0} / like ${m.like_count || 0} / repost ${m.retweet_count || 0}`;
}

function sourceLabel(tweet) {
  if (tweet.url) {
    return `<a href="${escapeHtml(tweet.url)}" target="_blank" rel="noreferrer">${escapeHtml(tweet.id)}</a>`;
  }
  return escapeHtml(tweet.id);
}

function setStatus(message) {
  els.status.textContent = message;
}

function renderOriginals() {
  els.count.textContent = `${state.tweets.length} tweets`;
  if (!state.tweets.length) {
    els.originalList.innerHTML = '<div class="tweet-row error">No non-reply tweets found.</div>';
    return;
  }
  els.originalList.innerHTML = state.tweets.map((tweet) => `
    <article class="tweet-row" data-id="${escapeHtml(tweet.id)}">
      <div class="meta">
        ${escapeHtml(formatDate(tweet.created_at))} · ${escapeHtml(tweet.kind)} ·
        ${sourceLabel(tweet)}
      </div>
      <div class="text">${escapeHtml(tweet.text)}</div>
      <div class="meta">${escapeHtml(metrics(tweet))}</div>
    </article>
  `).join("");
}

function ensureVersionsPlaceholder() {
  if (els.versions.children.length === 0) {
    els.versions.innerHTML = '<div class="empty-versions">Run a prompt to add a comparison column.</div>';
  }
}

function createVersionColumn(prompt) {
  if (els.versions.querySelector(".empty-versions")) {
    els.versions.innerHTML = "";
  }
  state.runCount += 1;
  const column = document.createElement("section");
  column.className = "version-column";
  column.dataset.run = String(state.runCount);
  column.innerHTML = `
    <div class="column-header">
      <strong class="version-title" title="${escapeHtml(prompt)}">${escapeHtml(prompt)}</strong>
      <span>Run ${state.runCount}</span>
    </div>
    <div class="version-list">
      ${state.tweets.map((tweet) => `
        <article class="version-row loading" data-id="${escapeHtml(tweet.id)}">Rewriting...</article>
      `).join("")}
    </div>
  `;
  els.versions.appendChild(column);
  column.scrollIntoView({ behavior: "smooth", inline: "end", block: "nearest" });
  return column;
}

function fillVersionColumn(column, versions) {
  const byId = new Map(versions.map((item) => [String(item.id), item.text]));
  for (const row of column.querySelectorAll(".version-row")) {
    const text = byId.get(row.dataset.id);
    row.classList.remove("loading", "error");
    row.innerHTML = text ? `<div class="text">${escapeHtml(text)}</div>` : '<div class="error">Missing rewrite.</div>';
  }
}

function showColumnError(column, message) {
  for (const row of column.querySelectorAll(".version-row")) {
    row.classList.remove("loading");
    row.classList.add("error");
    row.textContent = message;
  }
}

async function loadTweets() {
  try {
    const res = await fetch("/api/tweets");
    const payload = await res.json();
    if (!res.ok) throw new Error(payload.error || "Failed to load tweets");
    state.tweets = payload.tweets || [];
    renderOriginals();
    ensureVersionsPlaceholder();
    setStatus(`Loaded ${state.tweets.length} non-reply tweets`);
  } catch (error) {
    setStatus("Failed to load tweets");
    els.originalList.innerHTML = `<div class="tweet-row error">${escapeHtml(error.message)}</div>`;
  }
}

async function runPrompt(event) {
  event.preventDefault();
  const prompt = els.prompt.value.trim();
  if (!prompt || !state.tweets.length) return;
  const column = createVersionColumn(prompt);
  els.runButton.disabled = true;
  setStatus("Rewriting...");
  try {
    const res = await fetch("/api/rewrite", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        tweet_ids: state.tweets.map((tweet) => tweet.id),
      }),
    });
    const payload = await res.json();
    if (!res.ok) throw new Error(payload.error || "Rewrite failed");
    fillVersionColumn(column, payload.versions || []);
    setStatus(`Added run ${state.runCount}`);
  } catch (error) {
    showColumnError(column, error.message);
    setStatus("Rewrite failed");
  } finally {
    els.runButton.disabled = false;
  }
}

els.form.addEventListener("submit", runPrompt);
loadTweets();
