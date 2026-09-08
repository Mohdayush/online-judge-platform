const API = "/api/v1";
const state = { token: localStorage.getItem("codearena_token"), problems: [], selectedProblem: null, isRegistering: false };
const byId = (id) => document.getElementById(id);
const request = async (path, options = {}) => {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`${API}${path}`, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "Request failed");
  return body;
};
const setStatus = (value) => {
  const tag = byId("submission-state"); tag.textContent = value.replaceAll("_", " ");
  tag.className = `status-pill ${value === "ACCEPTED" ? "accepted" : /ERROR|WRONG|TIME/.test(value) ? "error" : ""}`;
};
const card = (tag, className) => { const element = document.createElement(tag); element.className = className; return element; };

function renderProblems(items) {
  const list = byId("problem-list"); list.replaceChildren();
  if (!items.length) { list.textContent = "No matching problems."; return; }
  items.forEach((problem) => {
    const item = card("article", "problem-card"); const difficulty = card("span", `difficulty ${problem.difficulty.toLowerCase()}`); difficulty.textContent = problem.difficulty;
    const title = document.createElement("h3"); title.textContent = problem.title; const meta = card("p", "card-meta"); meta.textContent = `${problem.time_limit_ms} ms · ${problem.memory_limit_mb} MB`;
    item.append(difficulty, title, meta); item.addEventListener("click", () => selectProblem(problem)); list.append(item);
  });
}
function selectProblem(problem) {
  state.selectedProblem = problem; byId("workspace-title").textContent = problem.title;
  const difficulty = byId("problem-difficulty"); difficulty.textContent = problem.difficulty; difficulty.className = `difficulty ${problem.difficulty.toLowerCase()}`;
  byId("problem-description").textContent = problem.description; byId("time-limit").textContent = `${problem.time_limit_ms} ms`; byId("memory-limit").textContent = `${problem.memory_limit_mb} MB`;
  byId("selected-problem-label").textContent = problem.title; byId("submit-button").disabled = false;
  byId("source-code").value = byId("language").value === "cpp" ? "#include <iostream>\nusing namespace std;\n\nint main() {\n  return 0;\n}" : "# Write your solution\n";
  location.hash = "workspace";
}
async function loadProblems() { try { state.problems = await request("/problems"); renderProblems(state.problems); } catch (error) { byId("problem-list").textContent = error.message; } }

function renderContests(contests) {
  const list = byId("contest-list"); list.replaceChildren();
  if (!contests.length) { list.textContent = "No contests have been scheduled yet."; return; }
  contests.forEach((contest) => {
    const item = card("article", "contest-card"); const title = document.createElement("h3"); title.textContent = contest.title;
    const description = card("p", "muted"); description.textContent = contest.description || "Timed programming contest";
    const date = card("p", "card-meta"); date.textContent = `${new Date(contest.starts_at).toLocaleString()} → ${new Date(contest.ends_at).toLocaleString()}`;
    const actions = card("div", "editor-actions"); const register = card("button", "button button-outline"); register.textContent = "Register"; register.addEventListener("click", async () => { try { if (!state.token) return openAuth(); const result = await request(`/contests/${contest.id}/register`, { method: "POST" }); register.textContent = result.status === "already_registered" ? "Registered" : "Registered ✓"; } catch (e) { alert(e.message); } });
    const leaderboard = card("button", "button"); leaderboard.textContent = "Leaderboard"; leaderboard.addEventListener("click", () => loadLeaderboard(contest)); actions.append(register, leaderboard); item.append(title, description, date, actions); list.append(item);
  });
}
async function loadContests() { try { renderContests(await request("/contests")); } catch (error) { byId("contest-list").textContent = error.message; } }
async function loadLeaderboard(contest) {
  try { const entries = await request(`/contests/${contest.id}/leaderboard`); byId("leaderboard-title").textContent = `${contest.title} leaderboard`;
    const content = byId("leaderboard-content"); const table = document.createElement("table"); table.innerHTML = "<thead><tr><th>#</th><th>Participant</th><th>Score</th><th>Solved</th><th>Penalty</th></tr></thead>";
    const body = document.createElement("tbody"); entries.forEach((entry) => { const row = document.createElement("tr"); [entry.rank, entry.username, entry.score, entry.solved, `${entry.penalty_seconds}s`].forEach((value) => { const cell = document.createElement("td"); cell.textContent = value; row.append(cell); }); body.append(row); }); table.append(body); content.replaceChildren(table); byId("leaderboard-card").classList.remove("hidden");
  } catch (error) { alert(error.message); }
}
async function submitSolution() {
  if (!state.token) return openAuth(); if (!state.selectedProblem) return;
  const source_code = byId("source-code").value; if (!source_code.trim()) return;
  const button = byId("submit-button"); button.disabled = true; setStatus("QUEUED");
  try { const submission = await request("/submissions", { method: "POST", body: JSON.stringify({ problem_id: state.selectedProblem.id, language: byId("language").value, source_code }) }); await pollSubmission(submission.id); }
  catch (error) { setStatus("SYSTEM_ERROR"); alert(error.message); button.disabled = false; }
}
async function pollSubmission(id) {
  try { const submission = await request(`/submissions/${id}`); setStatus(submission.status);
    if (["QUEUED", "RUNNING"].includes(submission.status)) return setTimeout(() => pollSubmission(id), 1200);
    if (submission.error_message) alert(submission.error_message);
    await loadProfile();
  } catch (error) { setStatus("SYSTEM_ERROR"); } finally { if (!["QUEUED", "RUNNING"].includes(byId("submission-state").textContent.replaceAll(" ", "_"))) byId("submit-button").disabled = false; }
}

async function loadProfile() {
  const panel = byId("profile-card"); const history = byId("submission-history");
  if (!state.token) { panel.innerHTML = '<p class="muted">Sign in to see your profile, statistics, and recent submissions.</p>'; history.replaceChildren(); return; }
  try {
    const [user, stats, submissions] = await Promise.all([request("/users/me"), request("/users/me/stats"), request("/users/me/submissions?limit=10")]);
    panel.innerHTML = `<h3>${escapeHtml(user.username)}</h3><p class="muted">${escapeHtml(user.email)} · ${escapeHtml(user.role)}</p><div class="stats"><div><strong>${stats.solved_problems}</strong><span>Solved</span></div><div><strong>${stats.accepted_submissions}</strong><span>Accepted</span></div><div><strong>${stats.total_submissions}</strong><span>Submissions</span></div></div>`;
    const table = document.createElement("table"); table.innerHTML = "<thead><tr><th>ID</th><th>Problem</th><th>Language</th><th>Status</th><th>Time</th></tr></thead>"; const body = document.createElement("tbody");
    submissions.forEach((s) => { const row = document.createElement("tr"); [s.id, s.problem_id, s.language, s.status.replaceAll("_", " "), s.execution_time_ms ? `${s.execution_time_ms} ms` : "—"].forEach((v) => { const cell = document.createElement("td"); cell.textContent = v; row.append(cell); }); body.append(row); }); table.append(body); history.replaceChildren(table);
  } catch (error) { panel.textContent = error.message; }
}
function escapeHtml(value) { const div = document.createElement("div"); div.textContent = value; return div.innerHTML; }
function openAuth() { byId("auth-error").textContent = ""; byId("auth-dialog").showModal(); }
function refreshAuth() { byId("auth-button").textContent = state.token ? "Sign out" : "Sign in"; loadProfile(); }
async function submitAuth(event) {
  event.preventDefault(); const payload = { email: byId("auth-email").value, password: byId("auth-password").value }; if (state.isRegistering) payload.username = byId("auth-username").value;
  try { const result = await request(`/auth/${state.isRegistering ? "register" : "login"}`, { method: "POST", body: JSON.stringify(payload) }); state.token = result.access_token; localStorage.setItem("codearena_token", state.token); byId("auth-dialog").close(); refreshAuth(); }
  catch (error) { byId("auth-error").textContent = error.message; }
}
byId("problem-search").addEventListener("input", (event) => renderProblems(state.problems.filter((p) => p.title.toLowerCase().includes(event.target.value.toLowerCase()))));
byId("language").addEventListener("change", () => state.selectedProblem && selectProblem(state.selectedProblem)); byId("submit-button").addEventListener("click", submitSolution);
byId("auth-button").addEventListener("click", () => { if (state.token) { localStorage.removeItem("codearena_token"); state.token = null; refreshAuth(); } else openAuth(); });
byId("close-auth").addEventListener("click", () => byId("auth-dialog").close()); byId("auth-form").addEventListener("submit", submitAuth);
byId("toggle-auth").addEventListener("click", () => { state.isRegistering = !state.isRegistering; byId("auth-title").textContent = state.isRegistering ? "Create your account" : "Sign in"; byId("auth-submit").textContent = state.isRegistering ? "Create account" : "Sign in"; byId("toggle-auth").textContent = state.isRegistering ? "Already registered? Sign in" : "Need an account? Register"; byId("username-field").style.display = state.isRegistering ? "flex" : "none"; });
byId("close-leaderboard").addEventListener("click", () => byId("leaderboard-card").classList.add("hidden")); refreshAuth(); loadProblems(); loadContests();
