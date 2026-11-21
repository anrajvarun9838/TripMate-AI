const API_URL = "/api/travel";
const APPROVE_URL = "/api/travel/approve";

const AGENT_LABELS = {
  flight_agent: "✈️ Flights",
  hotel_agent: "🏨 Hotels",
  weather_agent: "🌦️ Weather",
  budget_agent: "💰 Budget",
  itinerary_agent: "🗓️ Itinerary"
};

const PLACEHOLDER_DEFAULT = "Ask anything about your trip...";
const PLACEHOLDER_REVIEW = "Type what to change, or approve the draft above...";

const state = {
  threadId: null,
  waitingForApproval: false,
  busy: false,
  statusTimer: null,
  approvalCard: null
};

const chatScroll = document.getElementById("chatScroll");
const messagesEl = document.getElementById("messages");
const welcomeEl = document.getElementById("welcome");
const inputEl = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const newChatBtn = document.getElementById("newChatBtn");

/* ---------------- Rendering helpers ---------------- */

function safeHtml(markdown) {
  const html = marked.parse(markdown || "");
  const template = document.createElement("template");
  template.innerHTML = html;

  template.content
    .querySelectorAll("script,style,iframe,object,embed,link,meta,form")
    .forEach((node) => node.remove());

  template.content.querySelectorAll("*").forEach((el) => {
    Array.from(el.attributes).forEach((attr) => {
      const name = attr.name.toLowerCase();
      const unsafeUrl =
        (name === "href" || name === "src") && /^\s*javascript:/i.test(attr.value);
      if (name.startsWith("on") || unsafeUrl) {
        el.removeAttribute(attr.name);
      }
    });
    if (el.tagName === "A") {
      el.target = "_blank";
      el.rel = "noopener noreferrer";
    }
  });

  return template.innerHTML;
}

function renderMarkdown(element, markdown) {
  if (typeof marked !== "undefined") {
    element.innerHTML = safeHtml(markdown);
  } else {
    element.textContent = markdown || "";
    element.style.whiteSpace = "pre-wrap";
  }
}

function scrollToBottom() {
  chatScroll.scrollTop = chatScroll.scrollHeight;
}

function hideWelcome() {
  welcomeEl.classList.add("hidden");
}

/* ---------------- Messages ---------------- */

function addUserMessage(text) {
  hideWelcome();
  const row = document.createElement("div");
  row.className = "msg user";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  row.appendChild(bubble);
  messagesEl.appendChild(row);
  scrollToBottom();
}

function createAiRow(extraClass = "") {
  const row = document.createElement("div");
  row.className = `msg ai ${extraClass}`.trim();

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "✈";

  const content = document.createElement("div");
  content.className = "content";

  row.appendChild(avatar);
  row.appendChild(content);
  messagesEl.appendChild(row);
  return { row, content };
}

function addAiMessage({ markdown, agents = [], badge = "", draft = false, pdf = false, isError = false }) {
  hideWelcome();
  const { content } = createAiRow(isError ? "error" : "");

  if (badge) {
    const badgeEl = document.createElement("span");
    badgeEl.className = `badge${draft ? " draft" : ""}`;
    badgeEl.textContent = badge;
    content.appendChild(badgeEl);
  }

  const body = document.createElement("div");
  body.className = "md";
  renderMarkdown(body, markdown);
  content.appendChild(body);

  if (agents.length) {
    const chips = document.createElement("div");
    chips.className = "chips";
    agents.forEach((agent) => {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = AGENT_LABELS[agent] || agent;
      chips.appendChild(chip);
    });
    content.appendChild(chips);
  }

  if (!isError) {
    content.appendChild(buildActions(markdown, pdf));
  }

  scrollToBottom();
  return content;
}

function buildActions(markdown, withPdf) {
  const actions = document.createElement("div");
  actions.className = "actions";

  const copyBtn = document.createElement("button");
  copyBtn.type = "button";
  copyBtn.className = "action-btn";
  copyBtn.textContent = "Copy";
  copyBtn.addEventListener("click", () => copyText(markdown, copyBtn));
  actions.appendChild(copyBtn);

  if (withPdf) {
    const pdfBtn = document.createElement("button");
    pdfBtn.type = "button";
    pdfBtn.className = "action-btn";
    pdfBtn.textContent = "Download PDF";
    pdfBtn.addEventListener("click", () => downloadPdf(markdown, pdfBtn));
    actions.appendChild(pdfBtn);
  }

  return actions;
}

function addApprovalCard(content, requestText) {
  const card = document.createElement("div");
  card.className = "approval-card";

  const title = document.createElement("div");
  title.className = "approval-title";
  title.textContent = "Review this draft";

  const text = document.createElement("p");
  text.className = "approval-text";
  text.textContent =
    requestText ||
    "Approve it to get the final plan, or type what you want changed in the message box below.";

  const buttons = document.createElement("div");
  buttons.className = "approval-actions";

  const approveBtn = document.createElement("button");
  approveBtn.type = "button";
  approveBtn.className = "btn primary";
  approveBtn.textContent = "✓ Approve plan";
  approveBtn.addEventListener("click", () => submitApproval(true, ""));

  const reviseBtn = document.createElement("button");
  reviseBtn.type = "button";
  reviseBtn.className = "btn ghost";
  reviseBtn.textContent = "✎ Request changes";
  reviseBtn.addEventListener("click", () => {
    inputEl.focus();
  });

  buttons.appendChild(approveBtn);
  buttons.appendChild(reviseBtn);
  card.appendChild(title);
  card.appendChild(text);
  card.appendChild(buttons);
  content.appendChild(card);

  state.approvalCard = card;
  scrollToBottom();
}

function resolveApprovalCard(label) {
  if (!state.approvalCard) return;
  state.approvalCard.classList.add("done");
  state.approvalCard.textContent = label;
  state.approvalCard = null;
}

/* ---------------- Thinking indicator ---------------- */

function showThinking(statusLines) {
  hideWelcome();
  const { row, content } = createAiRow();

  const wrap = document.createElement("div");
  wrap.className = "thinking";
  wrap.innerHTML = '<span class="dots"><i></i><i></i><i></i></span><span class="status-text"></span>';
  content.appendChild(wrap);

  const statusEl = wrap.querySelector(".status-text");
  let index = 0;
  statusEl.textContent = statusLines[0];

  state.statusTimer = setInterval(() => {
    index = Math.min(index + 1, statusLines.length - 1);
    statusEl.textContent = statusLines[index];
  }, 2600);

  scrollToBottom();
  return row;
}

function hideThinking(row) {
  if (state.statusTimer) {
    clearInterval(state.statusTimer);
    state.statusTimer = null;
  }
  if (row) row.remove();
}

/* ---------------- UI state ---------------- */

function setBusy(isBusy) {
  state.busy = isBusy;
  sendBtn.disabled = isBusy;
  newChatBtn.disabled = isBusy;
  document.querySelectorAll(".approval-card button").forEach((btn) => {
    btn.disabled = isBusy;
  });
}

function setReviewMode(isReview) {
  state.waitingForApproval = isReview;
  inputEl.placeholder = isReview ? PLACEHOLDER_REVIEW : PLACEHOLDER_DEFAULT;
}

function autoGrow() {
  inputEl.style.height = "auto";
  inputEl.style.height = `${Math.min(inputEl.scrollHeight, 200)}px`;
}

function resetChat() {
  messagesEl.innerHTML = "";
  welcomeEl.classList.remove("hidden");
  state.threadId = null;
  state.approvalCard = null;
  setReviewMode(false);
  inputEl.value = "";
  autoGrow();
  inputEl.focus();
}

/* ---------------- API flow ---------------- */

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await response.json();

  if (!response.ok || !data.success) {
    throw new Error(data.error || "Something went wrong. Please try again.");
  }
  return data;
}

async function sendNew(message) {
  addUserMessage(message);
  inputEl.value = "";
  autoGrow();

  setBusy(true);
  const thinking = showThinking([
    "Understanding your request...",
    "Checking with the right travel agents...",
    "Putting your answer together..."
  ]);

  try {
    const data = await postJson(API_URL, { message });
    hideThinking(thinking);
    state.threadId = data.thread_id;

    if (data.requires_approval) {
      const content = addAiMessage({
        markdown: data.itinerary || data.answer,
        agents: data.selected_agents || [],
        badge: "Draft itinerary",
        draft: true
      });
      addApprovalCard(content, data.approval_request);
      setReviewMode(true);
    } else if (data.mode === "chat") {
      addAiMessage({ markdown: data.answer, agents: data.selected_agents || [] });
    } else {
      addAiMessage({
        markdown: data.answer,
        agents: data.selected_agents || [],
        badge: "Final plan",
        pdf: true
      });
    }
  } catch (error) {
    hideThinking(thinking);
    addAiMessage({ markdown: `⚠️ ${error.message}`, isError: true });
  } finally {
    setBusy(false);
    inputEl.focus();
  }
}

async function submitApproval(approved, feedback) {
  if (!state.threadId || !state.waitingForApproval || state.busy) return;

  addUserMessage(approved ? "Looks good, please approve the plan." : feedback);
  inputEl.value = "";
  autoGrow();

  setBusy(true);
  const thinking = showThinking(
    approved
      ? ["Finalizing your itinerary...", "Polishing the final plan..."]
      : ["Reading your feedback...", "Updating the plan...", "Polishing the final plan..."]
  );

  try {
    const data = await postJson(APPROVE_URL, {
      thread_id: state.threadId,
      approved,
      feedback
    });

    hideThinking(thinking);
    resolveApprovalCard(approved ? "✓ Plan approved" : "✎ Changes requested");
    setReviewMode(false);

    addAiMessage({
      markdown: data.answer,
      agents: data.selected_agents || [],
      badge: "Final plan",
      pdf: true
    });
  } catch (error) {
    hideThinking(thinking);
    addAiMessage({ markdown: `⚠️ ${error.message}`, isError: true });
  } finally {
    setBusy(false);
    inputEl.focus();
  }
}

function handleSend() {
  const text = inputEl.value.trim();
  if (!text || state.busy) return;

  if (state.waitingForApproval) {
    // While a draft is waiting, the message box carries revision feedback.
    submitApproval(false, text);
  } else {
    sendNew(text);
  }
}

/* ---------------- Copy + PDF ---------------- */

function copyText(text, button) {
  navigator.clipboard
    .writeText(text)
    .then(() => {
      button.textContent = "Copied ✓";
      setTimeout(() => (button.textContent = "Copy"), 1400);
    })
    .catch(() => {
      button.textContent = "Copy failed";
      setTimeout(() => (button.textContent = "Copy"), 1400);
    });
}

function downloadPdf(markdown, button) {
  if (typeof html2pdf === "undefined") {
    button.textContent = "PDF unavailable";
    return;
  }

  const doc = document.createElement("div");
  doc.className = "pdf-doc";
  renderMarkdown(doc, markdown);

  const title = document.createElement("h1");
  title.textContent = "TripMate Travel Plan";
  doc.prepend(title);
  document.body.appendChild(doc);

  const oldLabel = button.textContent;
  button.textContent = "Preparing PDF...";
  button.disabled = true;

  const finish = () => {
    doc.remove();
    button.textContent = oldLabel;
    button.disabled = false;
  };

  html2pdf()
    .set({
      margin: 0.5,
      filename: "tripmate-travel-plan.pdf",
      image: { type: "jpeg", quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff" },
      jsPDF: { unit: "in", format: "a4", orientation: "portrait" },
      pagebreak: { mode: ["avoid-all", "css", "legacy"] }
    })
    .from(doc)
    .save()
    .then(finish)
    .catch(finish);
}

/* ---------------- Events ---------------- */

sendBtn.addEventListener("click", handleSend);
newChatBtn.addEventListener("click", resetChat);
inputEl.addEventListener("input", autoGrow);

inputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    handleSend();
  }
});

document.querySelectorAll(".suggestions button").forEach((button) => {
  button.addEventListener("click", () => {
    if (!state.busy && !state.waitingForApproval) {
      sendNew(button.dataset.prompt);
    }
  });
});

inputEl.focus();
