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
const setStatus = (value) => { const tag = byId("submission-state"); tag.textContent = value.replaceAll("_", " "); tag.className = `status-pill ${value === "ACCEPTED" ? "accepted" : /ERROR|WRONG|TIME/.test(value) ? "error" : ""}`; };

function card(tag, className) { const element = document.createElement(tag); element.className = className; return element; }
function renderProblems(items) {
  const list = byId("problem-list"); list.replaceChildren();
  if (!items.length) { list.textContent = "No matching problems."; return; }
  items.forEach((problem) => { const item = card("article", "problem-card"); const difficulty = card("span", `difficulty ${problem.difficulty.toLowerCase()}`); difficulty.textContent = problem.difficulty; const title = document.createElement("h3"); title.textContent = problem.title; const meta = card("p", "card-meta"); meta.textContent = `${problem.time_limit_ms} ms · ${problem.memory_limit_mb} MB`; item.append(difficulty, title, meta); item.addEventListener("click", () => selectProblem(problem)); list.append(item); });
}
function selectProblem(problem) {
  state.selectedProblem = problem;
  byId("workspace-title").textContent = problem.title;
  const difficulty = byId("problem-difficulty"); difficulty.textContent = problem.difficulty; difficulty.className = `difficulty ${problem.difficulty.toLowerCase()}`;
  byId("problem-description").textContent = problem.description;
  byId("time-limit").textContent = `${problem.time_limit_ms} ms`; byId("memory-limit").textContent = `${problem.memory_limit_mb} MB`;
  byId("selected-problem-label").textContent = problem.title; byId("submit-button").disabled = false;
  byId("source-code").value = byId("language").value === "cpp" ? "#include <iostream>\nusing namespace std;\n\nint main() {\n  // Write your solution\n  return 0;\n}" : "# Write your solution\n";
  location.hash = "workspace";
}
async function loadProblems() { try { state.problems = await request("/problems"); renderProblems(state.problems); } catch (error) { byId("problem-list").textContent = error.message; } }
function renderContests(contests) {
  const list = byId("contest-list"); list.replaceChildren();
  if (!contests.length) { list.textContent = "No contests have been scheduled yet."; return; }
  contests.forEach((contest) => { const item = card("article", "contest-card"); const title = document.createElement("h3"); title.textContent = contest.title; const date = card("p", "card-meta"); date.textContent = `${new Date(contest.starts_at).toLocaleString()} → ${new Date(contest.ends_at).toLocaleString()}`; const button = card("button", "button button-outline"); button.textContent = "View leaderboard"; button.addEventListener("click", () => loadLeaderboard(contest)); item.append(title, date, button); list.append(item); });
}
async function loadContests() { try { renderContests(await request("/contests")); } catch (error) { byId("contest-list").textContent = error.message; } }
async function loadLeaderboard(contest) { try { const entries = await request(`/contests/${contest.id}/leaderboard`); byId("leaderboard-title").textContent = `${contest.title} leaderboard`; const content = byId("leaderboard-content"); const table = document.createElement("table"); table.innerHTML = "<thead><tr><th>#</th><th>Participant</th><th>Score</th><th>Solved</th><th>Penalty</th></tr></thead>"; const body = document.createElement("tbody"); entries.forEach((entry) => { const row = document.createElement("tr"); [entry.rank, entry.username, entry.score, entry.solved, `${entry.penalty_seconds}s`].forEach((value) => { const cell = document.createElement("td"); cell.textContent = value; row.append(cell); }); body.append(row); }); table.append(body); content.replaceChildren(table); byId("leaderboard-card").classList.remove("hidden"); } catch (error) { alert(error.message); } }
async function submitSolution() {
  if (!state.token) { openAuth(); return; }
  const source_code = byId("source-code").value; if (!source_code.trim()) return;
  const button = byId("submit-button"); button.disabled = true; setStatus("QUEUED");
  try { const submission = await request("/submissions", { method: "POST", body: JSON.stringify({ problem_id: state.selectedProblem.id, language: byId("language").value, source_code }) }); pollSubmission(submission.id); }
  catch (error) { setStatus("SYSTEM_ERROR"); alert(error.message); button.disabled = false; }
}
async function pollSubmission(id) { try { const submission = await request(`/submissions/${id}`); setStatus(submission.status); if (["QUEUED", "RUNNING"].includes(submission.status)) return setTimeout(() => pollSubmission(id), 1200); if (submission.error_message) alert(submission.error_message); } catch (error) { setStatus("SYSTEM_ERROR"); } finally { if (!byId("submission-state").textContent.match(/QUEUED|RUNNING/)) byId("submit-button").disabled = false; } }
function openAuth() { byId("auth-error").textContent = ""; byId("auth-dialog").showModal(); }
function refreshAuth() { byId("auth-button").textContent = state.token ? "Sign out" : "Sign in"; }
async function submitAuth(event) { event.preventDefault(); const payload = { email: byId("auth-email").value, password: byId("auth-password").value }; if (state.isRegistering) payload.username = byId("auth-username").value; try { const result = await request(`/auth/${state.isRegistering ? "register" : "login"}`, { method: "POST", body: JSON.stringify(payload) }); state.token = result.access_token; localStorage.setItem("codearena_token", state.token); byId("auth-dialog").close(); refreshAuth(); } catch (error) { byId("auth-error").textContent = error.message; } }
byId("problem-search").addEventListener("input", (event) => renderProblems(state.problems.filter((problem) => problem.title.toLowerCase().includes(event.target.value.toLowerCase()))));
byId("language").addEventListener("change", () => state.selectedProblem && selectProblem(state.selectedProblem)); byId("submit-button").addEventListener("click", submitSolution);
byId("auth-button").addEventListener("click", () => { if (state.token) { localStorage.removeItem("codearena_token"); state.token = null; refreshAuth(); } else openAuth(); }); byId("close-auth").addEventListener("click", () => byId("auth-dialog").close());
byId("auth-form").addEventListener("submit", submitAuth); byId("toggle-auth").addEventListener("click", () => { state.isRegistering = !state.isRegistering; byId("auth-title").textContent = state.isRegistering ? "Create your account" : "Sign in"; byId("auth-submit").textContent = state.isRegistering ? "Create account" : "Sign in"; byId("toggle-auth").textContent = state.isRegistering ? "Already registered? Sign in" : "Need an account? Register"; byId("username-field").style.display = state.isRegistering ? "flex" : "none"; });
byId("close-leaderboard").addEventListener("click", () => byId("leaderboard-card").classList.add("hidden")); refreshAuth(); loadProblems(); loadContests();
