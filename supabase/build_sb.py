"""Build the Supabase edition of Portal Board from the artifact's index.html.
usage: python3 build_sb.py <src index.html> <out portal-board.html> <supabase url> <anon key>
"""
import sys, re
src, out, SB_URL, SB_KEY = sys.argv[1:5]
s = open(src).read()

def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:90], s.count(a))
    s = s.replace(a, b)

def rep_between(start, end, new):
    global s
    i = s.index(start); j = s.index(end, i)
    s = s[:i] + new + s[j:]

# ---------------- CSS ----------------
rep('details summary {', '''.tag-new { display: inline-block; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: #fff; background: var(--orange-text); border-radius: 3px; padding: 1px 5px; margin-left: 4px; vertical-align: 1px; }
tr.is-new td:first-child { box-shadow: inset 3px 0 0 var(--orange); }
.whoami { margin-left: auto; display: flex; gap: 10px; align-items: center; color: var(--head-muted); font-size: 12.5px; }
.whoami button { background: transparent; color: var(--surface); border-color: rgba(255, 255, 255, .35); }
.whoami button:hover { color: var(--surface); border-color: var(--orange); }
.auth { min-height: 70vh; display: grid; place-items: center; padding-block: 32px; }
.auth form { width: min(380px, 100%); background: var(--surface); border: 1px solid var(--line); border-top: 4px solid var(--orange); border-radius: 8px; padding: 20px; display: grid; gap: 12px; }
.auth input { font: inherit; color: var(--ink); background: var(--surface); border: 1px solid var(--line-strong); border-radius: 6px; padding: 0 10px; height: var(--ctl-h); width: 100%; }
.auth .err { color: var(--bad); font-size: 13px; min-height: 1em; }
.uploads { display: grid; gap: 6px; font-size: 13px; align-content: start; }
#sidePanel { align-content: start; }
.uploads .u { display: flex; justify-content: space-between; gap: 10px; border-bottom: 1px solid var(--line); padding-bottom: 6px; }
.uploads .u b { font-weight: 600; }
.preview { display: grid; gap: 10px; }
.preview .big { font-family: var(--display); font-size: 26px; font-weight: 700; color: var(--accent); }
details summary {''')

# ---------------- header: who is signed in ----------------
rep('''      <a href="#rankings" data-view="rankings">Position rankings</a>
    </nav>''', '''      <a href="#rankings" data-view="rankings">Position rankings</a>
    </nav>
    <div class="whoami" id="whoami" hidden><span id="whoEmail"></span><button class="small" id="signOut">Sign out</button></div>''')

# ---------------- sign-in screen ----------------
rep('''  <div id="loading" class="loading">''', '''  <div class="auth" id="auth" hidden>
    <form id="authForm" autocomplete="on" onsubmit="return false">
      <h2>Staff sign in</h2>
      <p class="note">Use the email and password your program set up for you in Supabase.</p>
      <label class="field"><span>Email</span><input type="email" id="authEmail" autocomplete="username" required></label>
      <label class="field"><span>Password</span><input type="password" id="authPass" autocomplete="current-password" required></label>
      <span class="err" id="authErr"></span>
      <button class="primary" type="submit" id="authGo">Sign in</button>
    </form>
  </div>
  <div id="loading" class="loading">''')

# ---------------- portal HTML ----------------
rep_between('  <!-- PORTAL -->', '  <!-- RANKINGS -->', '''  <!-- PORTAL -->
  <section class="view" id="view-portal" hidden>
    <div style="display:grid;gap:4px"><h2>Transfer portal list</h2><p class="lede">Drop in a CSV or Excel file of names and schools. Every list you add is saved for the whole staff. Players already on the board are kept as they are, and players added by the latest list are marked New. Each row is matched to the 2026 stats by school and a fuzzy name match that handles typos, nicknames, accents and "Last, First" order.</p></div>
    <div class="grid2">
      <div class="panel">
        <div class="drop" id="drop">
          <strong>Drop a CSV or XLSX here</strong>
          <span class="note">Needs a name column (or first and last name columns) and a school column. Other columns are kept with the row.</span>
          <div class="row" style="justify-content:center;align-items:center">
            <button class="primary" id="pickFile">Choose file</button>
          </div>
          <input type="file" id="fileIn" accept=".csv,.xlsx,.xls,.tsv,.txt" hidden>
        </div>
        <details><summary>Or paste rows instead</summary>
          <div style="display:grid;gap:8px;margin-top:8px">
            <textarea id="pasteIn" placeholder="Name,School&#10;Hope Leyba,Colorado&#10;Powell, Leena	UCLA"></textarea>
            <div><button id="pasteGo">Check pasted rows</button></div>
          </div>
        </details>
      </div>
      <div class="panel" id="sidePanel"></div>
    </div>
    <div class="summary" id="matchSummary"></div>
    <div class="tablewrap"><table id="mTable"></table></div>
    <div class="row" id="portalActions" hidden>
      <button id="copyPortal">Copy matched players for Excel</button>
      <button id="toRankings" class="primary">Rank portal players by position</button>
    </div>
  </section>

''')

# ---------------- portal tag helper used in Players / Rankings ----------------
rep('''function playerCell(p, sub) {''', '''function portalTag(p) { return portalIds.has(p.id) ? `<span class="tag-portal">Portal</span>${newIds.has(p.id) ? `<span class="tag-new">New</span>` : ""}` : ""; }
function playerCell(p, sub) {''')
s = s.replace('${portalIds.has(p.id) ? `<span class="tag-portal">Portal</span>` : ""}', '${portalTag(p)}')
assert s.count('${portalTag(p)}') == 2

# ---------------- state ----------------
rep('''  portal: { rows: [], headers: [], map: {}, results: [], overrides: store.get("overrides", {}), filter: "", fileName: "" }''',
    '''  portal: { filter: "" }''')
rep('let portalIds = new Set();', 'let portalIds = new Set();\nlet newIds = new Set();')

# ---------------- data load from Supabase ----------------
rep('''async function loadData() {
  let text = null;
  if (window.EMBEDDED_CSV) text = window.EMBEDDED_CSV;
  else {
    const r = await fetch("power4_wsoc_2026_player_stats.csv");
    if (!r.ok) throw new Error("Could not load stats file (" + r.status + ")");
    text = await r.text();
  }
  const rows = parseCSV(text); const h = rows.shift();''', '''const COLMAP = { "Conference": "conference", "Team": "team", "Last Name": "last_name", "First Name": "first_name", "Position": "position", "GP": "gp", "GS": "gs", "MIN": "min", "G": "g", "A": "a", "PTS": "pts", "SH": "sh", "SOG": "sog", "YC": "yc", "RC": "rc", "GW": "gw", "PK": "pk", "PK ATT": "pk_att", "GK GP": "gk_gp", "GK GS": "gk_gs", "GK MIN": "gk_min", "GA": "ga", "GAA": "gaa", "SV": "sv", "SV%": "sv_pct", "W": "w", "L": "l", "T": "t", "SHO": "sho", "SF": "sf", "Source": "source" };
async function fetchAll(table, cols, order) {
  const out = []; const size = 1000;
  for (let from = 0; ; from += size) {
    let q = sb.from(table).select(cols).range(from, from + size - 1);
    if (order) q = q.order(order, { ascending: true });
    const { data, error } = await q;
    if (error) throw new Error(error.message);
    out.push(...data);
    if (data.length < size) return out;
  }
}
const byDbId = new Map();
async function loadData() {
  const dbRows = await fetchAll("players", "*", "id");
  if (!dbRows.length) throw new Error("No players found. Ask the person who set up Supabase to load the stats.");
  const h = Object.keys(COLMAP);
  const rows = dbRows.map(r => h.map(k => r[COLMAP[k]] == null ? "" : String(r[COLMAP[k]])));''')
rep('''  TEAMS = [...new Set(P.map(p => p.team))].sort();
}''', '''  P.forEach((p, i) => { p.dbId = dbRows[i].id; byDbId.set(p.dbId, p); });
  TEAMS = [...new Set(P.map(p => p.team))].sort();
}''')

# ---------------- portal logic ----------------
PORTAL_JS = r'''/* ---------- portal list (stored in Supabase) ---------- */
const HDR = { name: /^(player|player name|name|full name|athlete|athlete name|student athlete)$/i, first: /^(first|first name|firstname|given name|fname)$/i, last: /^(last|last name|lastname|surname|family name|lname)$/i, school: /(school|team|college|institution|university|previous|current|from|origin)/i };
const PT = { entries: [], uploads: [], latest: null, pending: null, saving: false };
const STATUS_DB = { ok: "matched", rev: "review", no: "not_found" };
const STATUS_UI = { matched: "ok", review: "rev", not_found: "no", picked: "man" };
function rawName(row, map) { return map.first !== "" && map.last !== "" && map.first != null ? `${row[map.first] ?? ""} ${row[map.last] ?? ""}`.trim() : String(row[map.name] ?? "").trim(); }
function rawSchool(row, map) { return map.school !== "" && map.school != null ? String(row[map.school] ?? "").trim() : ""; }
function entryKey(name, school) {
  const toks = normName(name).replace(/,/g, " ").split(" ").filter(Boolean).sort().join(" ");
  const team = resolveSchool(school).team;
  return toks + "|" + (team ? norm(team) : norm(school));
}
// stage a parsed file: detect columns, then wait for the user to confirm before saving
function stage(rows, fileName) {
  rows = rows.map(r => r.map(c => c == null ? "" : String(c).trim())).filter(r => r.some(c => c));
  if (!rows.length) { toast("That file has no rows"); return; }
  const h0 = rows[0];
  const looksHeader = h0.some(c => HDR.name.test(c) || HDR.first.test(c) || HDR.last.test(c) || HDR.school.test(c));
  const headers = looksHeader ? h0.map((c, i) => c || `Column ${i + 1}`) : h0.map((_, i) => `Column ${i + 1}`);
  const data = looksHeader ? rows.slice(1) : rows;
  const map = { name: "", first: "", last: "", school: "" };
  headers.forEach((h, i) => { for (const k of ["first", "last", "name", "school"]) if (map[k] === "" && HDR[k].test(h)) { map[k] = i; break; } });
  if (map.name === "" && map.first === "" && map.last === "") map.name = 0;
  if (map.school === "") map.school = headers.findIndex((_, i) => i !== map.name && i !== map.first && i !== map.last);
  if (map.school === -1) map.school = "";
  if (map.first !== "" && map.last !== "") map.name = "";
  PT.pending = { rows: data, headers, map, fileName };
  if (location.hash !== "#portal") location.hash = "portal"; else renderPortal();
}
function pendingPlan() {
  const pd = PT.pending, have = new Set(PT.entries.map(e => e.entry_key));
  const seen = new Set(), fresh = [], again = [];
  let blank = 0;
  pd.rows.forEach(r => {
    const nm = rawName(r, pd.map); if (!nm) { blank++; return; }
    const key = entryKey(nm, rawSchool(r, pd.map));
    if (seen.has(key)) return; seen.add(key);
    (have.has(key) ? again : fresh).push({ r, key, nm });
  });
  return { fresh, again, blank };
}
async function savePending() {
  if (PT.saving || !PT.pending) return;
  PT.saving = true; renderPortal();
  const pd = PT.pending, plan = pendingPlan();
  try {
    const { data: up, error: e1 } = await sb.from("portal_uploads").insert({ file_name: pd.fileName, row_count: plan.fresh.length + plan.again.length, new_row_count: plan.fresh.length }).select().single();
    if (e1) throw e1;
    const rows = plan.fresh.map(({ r, key, nm }) => {
      const m = matchRow(r, pd.map);
      const c = m.cands.find(c => c.p.id === m.pick);
      return { entry_key: key, raw_name: nm, raw_school: rawSchool(r, pd.map) || null, raw_row: Object.fromEntries(pd.headers.map((h, i) => [h, r[i] ?? ""])), first_upload_id: up.id, last_upload_id: up.id, player_id: m.pick != null ? P[m.pick].dbId : null, match_status: STATUS_DB[m.status], match_score: c ? Math.round(c.s * 1000) / 1000 : null };
    });
    for (let i = 0; i < rows.length; i += 500) { const { error } = await sb.from("portal_entries").insert(rows.slice(i, i + 500)); if (error) throw error; }
    const keys = plan.again.map(x => x.key);
    for (let i = 0; i < keys.length; i += 200) { const { error } = await sb.from("portal_entries").update({ last_upload_id: up.id }).in("entry_key", keys.slice(i, i + 200)); if (error) throw error; }
    PT.pending = null; $("#pasteIn").value = "";
    toast(`Added ${plan.fresh.length} new player${plan.fresh.length === 1 ? "" : "s"}`);
    S.portal.filter = plan.fresh.length ? "new" : "";
    await loadPortal();
  } catch (e) { toast("Couldn't save the list: " + (e.message || e)); }
  PT.saving = false; renderPortal();
}
async function loadPortal() {
  const [entries, uploads] = await Promise.all([fetchAll("portal_entries", "*", "id"), fetchAll("portal_uploads", "*", "id")]);
  uploads.sort((a, b) => b.id - a.id);
  PT.uploads = uploads; PT.latest = uploads[0] ? uploads[0].id : null;
  PT.entries = entries.map(e => {
    const auto = matchRow([e.raw_name, e.raw_school || ""], { name: 0, school: 1, first: "", last: "" });
    const p = e.player_id != null ? byDbId.get(e.player_id) : null;
    if (p && !auto.cands.find(c => c.p.id === p.id)) auto.cands.unshift({ p, s: nameScore(auto.inp, p) });
    return { ...e, auto, pick: p ? p.id : null, ui: STATUS_UI[e.match_status] || "no", isNew: e.first_upload_id === PT.latest };
  });
  updatePortalIds(); rerenderView();
}
function updatePortalIds() {
  const live = PT.entries.filter(e => e.pick != null);
  portalIds = new Set(live.map(e => e.pick));
  newIds = new Set(live.filter(e => e.isNew).map(e => e.pick));
  const c = $("#portalCount"); c.textContent = portalIds.size; c.hidden = !portalIds.size;
}
async function setPick(entry, pick, reset) {
  let body;
  if (reset) { const a = entry.auto; const c = a.cands.find(c => c.p.id === a.pick); body = { player_id: a.pick != null ? P[a.pick].dbId : null, match_status: STATUS_DB[a.status], match_score: c ? Math.round(c.s * 1000) / 1000 : null }; }
  else body = { player_id: pick != null ? P[pick].dbId : null, match_status: "picked" };
  const { error } = await sb.from("portal_entries").update(body).eq("id", entry.id);
  if (error) { toast("Couldn't save that change: " + error.message); return; }
  await loadPortal();
}
async function readFile(file) {
  const buf = await file.arrayBuffer();
  let rows;
  if (/\.(csv|txt|tsv)$/i.test(file.name)) {
    const text = new TextDecoder().decode(buf);
    const wb = XLSX.read(text, { type: "string", raw: true });
    rows = XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], { header: 1, defval: "", raw: false });
  } else {
    const wb = XLSX.read(buf, { type: "array" });
    rows = XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], { header: 1, defval: "", raw: false });
  }
  stage(rows, file.name);
}
const fmtDay = iso => { try { return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }); } catch (e) { return ""; } };

/* ---------- PORTAL view ---------- */
function renderSide() {
  const el = $("#sidePanel");
  if (PT.pending) {
    const pd = PT.pending, plan = pendingPlan();
    const opt = sel => `<option value="">(none)</option>` + pd.headers.map((h, i) => `<option value="${i}" ${String(sel) === String(i) ? "selected" : ""}>${esc(h)}</option>`).join("");
    el.innerHTML = `<h3>Check before saving</h3>
      <p class="note">${esc(pd.fileName)}: ${pd.rows.length} rows. Columns were detected from your headers; change one if it was read wrong.</p>
      <div class="mapping">${[["name", "Full name"], ["first", "First name"], ["last", "Last name"], ["school", "School"]].map(([k, l]) => `<label class="field"><span>${l}</span><select data-map="${k}">${opt(pd.map[k])}</select></label>`).join("")}</div>
      <div class="preview"><div><span class="big">${plan.fresh.length}</span> new player${plan.fresh.length === 1 ? "" : "s"} to add</div>
      <p class="note">${plan.again.length} already on the portal board will stay as they are.${plan.blank ? ` ${plan.blank} rows have no name and will be skipped.` : ""}</p></div>
      <div class="row"><button class="primary" id="saveList" ${PT.saving ? "disabled" : ""}>${PT.saving ? "Saving&hellip;" : plan.fresh.length ? `Add ${plan.fresh.length} to the portal list` : "Save this list"}</button><button id="cancelList" ${PT.saving ? "disabled" : ""}>Cancel</button></div>`;
    $$("[data-map]", el).forEach(s => s.onchange = () => { pd.map[s.dataset.map] = s.value === "" ? "" : +s.value; renderPortal(); });
    $("#saveList").onclick = savePending;
    $("#cancelList").onclick = () => { PT.pending = null; renderPortal(); };
    return;
  }
  el.innerHTML = `<h3>Lists added</h3>${PT.uploads.length ? `<div class="uploads">${PT.uploads.slice(0, 8).map((u, i) => `<div class="u"><span><b>${esc(u.file_name || "Pasted rows")}</b>${i === 0 ? `<span class="tag-new">Latest</span>` : ""}<br><span class="note">${esc(fmtDay(u.uploaded_at))}</span></span><span class="note" style="text-align:right">${u.new_row_count} new<br>${u.row_count} rows</span></div>`).join("")}</div>${PT.uploads.length > 8 ? `<p class="note">${PT.uploads.length - 8} older lists not shown.</p>` : ""}` : `<p class="note">No lists yet. The first file you add becomes the portal board.</p>`}`;
}
function renderPortal() {
  renderSide();
  const all = PT.entries;
  $("#portalActions").hidden = !all.length;
  if (!all.length) { $("#matchSummary").innerHTML = ""; $("#mTable").innerHTML = `<tbody><tr><td class="l" style="padding:24px;color:var(--muted)">No portal players yet. Choose a file to start the list.</td></tr></tbody>`; return; }
  const f = S.portal.filter;
  const counts = { ok: 0, rev: 0, no: 0, man: 0 }; all.forEach(e => counts[e.ui]++);
  const nNew = all.filter(e => e.isNew).length;
  const box = (k, n, t) => `<button class="stat ${k}" data-f="${k}" aria-pressed="${f === k}"><div class="n">${n}</div><div class="t">${t}</div></button>`;
  $("#matchSummary").innerHTML = box("", all.length, "On the board") + box("new", nNew, "New in latest list") + box("ok", counts.ok, "Matched") + box("man", counts.man, "Picked by staff") + box("rev", counts.rev, "Needs review") + box("no", counts.no, "Not found");
  $$("#matchSummary .stat").forEach(b => b.onclick = () => { S.portal.filter = S.portal.filter === b.dataset.f ? "" : b.dataset.f; renderPortal(); });
  const order = { rev: 0, no: 1, man: 2, ok: 3 };
  const list = all.filter(e => !f || (f === "new" ? e.isNew : e.ui === f)).sort((a, b) => (b.isNew - a.isNew) || order[a.ui] - order[b.ui] || a.id - b.id);
  const label = { ok: "Matched", rev: "Review", no: "Not found", man: "Picked" };
  const why = e => e.ui === "man" ? (e.pick == null ? "Staff marked no match" : "Picked by staff") : e.auto.why;
  $("#mTable").innerHTML = `<thead><tr><th class="l" data-nosort>Portal list</th><th class="l" data-nosort>School</th><th class="l" data-nosort>Status</th><th class="l" data-nosort>Matched player</th><th data-nosort>Match</th><th class="l" data-nosort>Pos</th><th data-nosort>MIN</th><th data-nosort>G</th><th data-nosort>A</th><th data-nosort>PTS/90</th><th data-nosort>SV%</th><th class="l" data-nosort>Added</th></tr></thead><tbody>` +
    list.map(e => {
      const p = e.pick != null ? P[e.pick] : null; const c = e.auto.cands.find(c => c.p.id === e.pick);
      const added = PT.uploads.find(u => u.id === e.first_upload_id);
      return `<tr class="${e.isNew ? "is-new" : ""}">
        <td class="l player">${esc(e.raw_name)}${e.isNew ? `<span class="tag-new">New</span>` : ""}</td>
        <td class="l">${esc(e.raw_school || "")}${e.auto.sch.team && norm(e.auto.sch.team) !== norm(e.raw_school) ? `<small class="note" style="display:block">read as ${esc(e.auto.sch.team)}</small>` : ""}</td>
        <td class="l"><span class="pill ${e.ui}">${label[e.ui]}</span><span class="why">${esc(why(e))}</span></td>
        <td class="l"><select data-pick="${e.id}" aria-label="Matched player for ${esc(e.raw_name)}">
          <option value="">No match</option>
          ${e.auto.cands.map(c => `<option value="${c.p.id}" ${c.p.id === e.pick ? "selected" : ""}>${esc(c.p.name)} &middot; ${esc(c.p.team)} &middot; ${esc(c.p.pos)} (${Math.round(c.s * 100)}%)</option>`).join("")}
        </select>${p ? `<button class="notebtn" data-note="${p.id}" title="Staff notes for ${esc(p.name)}">${NOTE_SVG}${notesFor(p).length ? notesFor(p).length : "Notes"}</button>` : ""}${e.ui === "man" ? ` <button class="link small" data-reset="${e.id}">Undo</button>` : ""}</td>
        <td class="num">${c ? Math.round(c.s * 100) + "%" : `<span class="na">&ndash;</span>`}</td>
        <td class="l">${p ? `<span class="pos">${esc(p.pos)}</span>` : ""}</td>
        <td class="num">${p ? fmt("MIN", p.MIN) : ""}</td><td class="num">${p ? fmt("G", p.G) : ""}</td><td class="num">${p ? fmt("A", p.A) : ""}</td><td class="num">${p ? fmt("PTS90", p.PTS90) : ""}</td><td class="num">${p && p.SVpct != null ? fmt("SVpct", p.SVpct) : ""}</td>
        <td class="l note">${esc(added ? fmtDay(added.uploaded_at) : "")}</td>
      </tr>`;
    }).join("") + `</tbody>`;
  const byId = new Map(all.map(e => [String(e.id), e]));
  $$("[data-pick]").forEach(s => s.onchange = () => setPick(byId.get(s.dataset.pick), s.value === "" ? null : +s.value));
  $$("[data-reset]").forEach(b => b.onclick = () => setPick(byId.get(b.dataset.reset), null, true));
}
function initPortal() {
  const drop = $("#drop"), fi = $("#fileIn");
  $("#pickFile").onclick = () => fi.click();
  fi.onchange = () => { if (fi.files[0]) readFile(fi.files[0]).catch(e => toast("Could not read that file: " + e.message)); fi.value = ""; };
  ["dragenter", "dragover"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", e => { const f = e.dataTransfer.files[0]; if (f) readFile(f).catch(er => toast("Could not read that file: " + er.message)); });
  $("#pasteGo").onclick = () => {
    const t = $("#pasteIn").value; if (!t.trim()) return;
    const rows = t.includes("\t") ? t.split(/\r?\n/).map(l => l.split("\t")) : parseCSV(t);
    stage(rows, "Pasted rows");
  };
  $("#copyPortal").onclick = () => {
    const cols = ["name", "team", "conf", "pos", "MIN", "GP", "GS", "G", "A", "PTS", "G90", "A90", "PTS90", "SH90", "SOGpct", "GAA", "SVpct"];
    const head = ["Player", "Team", "Conference", "Pos", "New", "MIN", "GP", "GS", "G", "A", "PTS", "G/90", "A/90", "PTS/90", "SH/90", "SOG%", "GAA", "SV%"];
    const cell = v => v == null ? "" : typeof v === "number" ? (Number.isInteger(v) ? v : v.toFixed(3)) : v;
    const lines = [head.join("\t"), ...[...portalIds].map(id => P[id]).map(p => [cell(p.name), p.team, p.conf, p.pos, newIds.has(p.id) ? "New" : "", ...cols.slice(4).map(k => cell(p[k]))].join("\t"))];
    const txt = lines.join("\n");
    navigator.clipboard.writeText(txt).then(() => toast(`Copied ${portalIds.size} players`)).catch(() => { $("#pasteIn").closest("details").open = true; $("#pasteIn").value = txt; $("#pasteIn").select(); toast("Copy blocked; the rows are selected in the paste box"); });
  };
  $("#toRankings").onclick = () => { S.r.scope = "portal"; location.hash = "rankings"; };
}

'''
rep_between('/* ---------- portal ingest ---------- */', '/* ---------- RANKINGS view ---------- */', PORTAL_JS)

# ---------------- staff notes on Supabase ----------------
NOTES_JS = r'''/* ---------- staff notes (Supabase table staff_notes) ---------- */
const NOTES = { me: null, byPlayer: new Map(), open: null, loaded: false };
function notesFor(p) { return NOTES.byPlayer.get(p.dbId) || []; }
async function loadNotes() {
  const rows = await fetchAll("staff_notes", "id, player_id, body, author_id, author_email, created_at", "id");
  const m = new Map();
  for (const n of rows) { if (!m.has(n.player_id)) m.set(n.player_id, []); m.get(n.player_id).push(n); }
  for (const arr of m.values()) arr.sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)));
  NOTES.byPlayer = m; NOTES.loaded = true;
  rerenderView();
}
function rerenderView() {
  if (!P.length) return;
  if (S.view === "players") renderPlayers(true); else if (S.view === "portal") renderPortal(); else renderRankings(true);
  if (NOTES.open != null) renderNoteList();
}
const fmtWhen = iso => { try { return new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }); } catch (e) { return ""; } };
function openNotes(id) {
  const p = P[id]; if (!p) return;
  NOTES.open = id;
  $("#noteTitle").textContent = p.name;
  $("#noteSub").textContent = `${p.team} · ${p.conf} · ${p.pos} · ${p.MIN != null ? Math.round(p.MIN).toLocaleString("en-US") + " min" : "no minutes"}${p.G != null ? ` · ${p.G} G, ${p.A} A` : ""}${p.SVpct != null ? ` · ${p.SVpct.toFixed(3).replace(/^0/, "")} SV%` : ""}`;
  $("#noteText").value = ""; $("#noteAdd").disabled = true;
  $("#noteModal").hidden = false;
  renderNoteList();
  setTimeout(() => $("#noteText").focus(), 0);
}
function closeNotes() { $("#noteModal").hidden = true; NOTES.open = null; }
function renderNoteList() {
  const p = P[NOTES.open]; if (!p) return;
  const list = notesFor(p);
  $("#noteStatus").textContent = "Shared with every signed-in staff member.";
  if (!list.length) { $("#noteList").innerHTML = `<p class="empty-w">${NOTES.loaded ? "No notes on this player yet." : "Loading notes&hellip;"}</p>`; return; }
  $("#noteList").innerHTML = list.map(n => {
    const who = n.author_id === NOTES.me ? "You" : (n.author_email || "Staff member");
    return `<article class="nitem"><p></p><div class="meta"><span>${esc(who)} &middot; ${esc(fmtWhen(n.created_at))}</span>${n.author_id === NOTES.me ? `<button class="link" data-delnote="${n.id}">Delete</button>` : ""}</div></article>`;
  }).join("");
  $$("#noteList .nitem p").forEach((el, i) => el.textContent = list[i].body);
}
async function addNote() {
  const p = P[NOTES.open]; const text = $("#noteText").value.trim();
  if (!p || !text) return;
  $("#noteAdd").disabled = true;
  const { error } = await sb.from("staff_notes").insert({ player_id: p.dbId, body: text.slice(0, 4000) });
  if (error) { $("#noteAdd").disabled = false; toast("Couldn't save the note: " + error.message); return; }
  $("#noteText").value = ""; toast("Note added"); await loadNotes();
}
async function deleteNote(id) {
  const { error } = await sb.from("staff_notes").delete().eq("id", id);
  if (error) { toast("Couldn't delete the note: " + error.message); return; }
  toast("Note deleted"); await loadNotes();
}
function initNoteUI() {
  document.addEventListener("click", e => {
    const b = e.target.closest("[data-note]"); if (b) { e.preventDefault(); openNotes(+b.dataset.note); return; }
    const d = e.target.closest("[data-delnote]"); if (d) { deleteNote(+d.dataset.delnote); return; }
  });
  $("#noteClose").onclick = closeNotes;
  $("#noteModal").addEventListener("click", e => { if (e.target.id === "noteModal") closeNotes(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !$("#noteModal").hidden) closeNotes(); });
  $("#noteText").addEventListener("input", e => { $("#noteAdd").disabled = !e.target.value.trim(); });
  $("#noteText").addEventListener("keydown", e => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); addNote(); } });
  $("#noteAdd").onclick = addNote;
}
// live updates: when another staff member adds a note or a list, refresh
function subscribeLive() {
  let tN, tP;
  sb.channel("portal-board")
    .on("postgres_changes", { event: "*", schema: "public", table: "staff_notes" }, () => { clearTimeout(tN); tN = setTimeout(loadNotes, 400); })
    .on("postgres_changes", { event: "*", schema: "public", table: "portal_entries" }, () => { clearTimeout(tP); tP = setTimeout(loadPortal, 800); })
    .subscribe();
}

'''
rep_between('/* ---------- staff notes ---------- */', '/* ---------- routing ---------- */', NOTES_JS)

# ---------------- startup with sign-in ----------------
rep_between('(async function start() {', '</script>', r'''const SUPABASE_URL = "__SB_URL__";
const SUPABASE_ANON_KEY = "__SB_KEY__";
const sb = window.supabase ? window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY) : null;
let started = false;
async function startApp(session) {
  NOTES.me = session.user.id;
  $("#whoEmail").textContent = session.user.email || "";
  $("#whoami").hidden = false; $("#auth").hidden = true;
  if (started) return; started = true;
  $("#loading").hidden = false;
  try { await loadData(); }
  catch (e) {
    if (/No players found/.test(e.message) && window.SEED_PLAYERS) {
      $("#loading").innerHTML = `<div style="display:grid;gap:10px;justify-items:center"><b>The player stats aren't in Supabase yet.</b><span>This one-time step loads all ${window.SEED_PLAYERS.length.toLocaleString("en-US")} players from the 2026 season.</span><button class="primary" id="seedGo">Load the 2026 stats</button><span class="note" id="seedMsg"></span></div>`;
      $("#seedGo").onclick = async () => {
        $("#seedGo").disabled = true; $("#seedMsg").textContent = "Loading\u2026";
        const { data, error } = await sb.rpc("load_players_once", { rows: window.SEED_PLAYERS });
        if (error) { $("#seedMsg").textContent = "Couldn't load the stats: " + error.message; $("#seedGo").disabled = false; return; }
        $("#seedMsg").textContent = `Loaded ${data} players. Opening the board\u2026`;
        setTimeout(() => location.reload(), 800);
      };
    } else $("#loading").innerHTML = `Could not load player stats. ${esc(e.message)}`;
    started = false; return;
  }
  buildSchoolIndex();
  $("#loading").hidden = true;
  initPlayers(); initPortal(); initRankings(); initNoteUI();
  window.addEventListener("hashchange", route);
  route();
  try { await Promise.all([loadPortal(), loadNotes()]); } catch (e) { toast("Couldn't load portal list or notes: " + e.message); }
  subscribeLive();
}
function showSignIn() { $("#auth").hidden = false; $("#loading").hidden = true; $("#whoami").hidden = true; $$(".view").forEach(v => v.hidden = true); }
$("#authForm").addEventListener("submit", async e => {
  e.preventDefault();
  $("#authErr").textContent = ""; $("#authGo").disabled = true;
  const { data, error } = await sb.auth.signInWithPassword({ email: $("#authEmail").value.trim(), password: $("#authPass").value });
  $("#authGo").disabled = false;
  if (error) { $("#authErr").textContent = error.message === "Invalid login credentials" ? "That email and password don't match a staff account." : error.message; return; }
  startApp(data.session);
});
$("#signOut").onclick = async () => { await sb.auth.signOut(); location.reload(); };
(async () => {
  if (!sb) {
    $("#loading").innerHTML = `<div style="display:grid;gap:8px;justify-items:center;max-width:60ch;margin:0 auto"><b>Sign-in can't load here.</b><span>This page needs to open in a regular web browser with an internet connection. If you opened it inside Claude, download the file and open it in Safari, Chrome or Edge instead.</span></div>`;
    return;
  }
  $("#loading").hidden = true;
  const { data } = await sb.auth.getSession();
  if (data.session) startApp(data.session); else showSignIn();
})();
''')
s = s.replace("__SB_URL__", SB_URL).replace("__SB_KEY__", SB_KEY)
if len(sys.argv) > 5:
    import csv as _csv, json as _json
    COLS = [('conference','Conference','t'),('team','Team','t'),('last_name','Last Name','t'),('first_name','First Name','t'),('position','Position','t'),('source','Source','t'),
      ('gp','GP','i'),('gs','GS','i'),('min','MIN','n'),('g','G','i'),('a','A','i'),('pts','PTS','i'),('pts_per_g','PTS/G','n'),('sh','SH','i'),('sh_per_g','SH/G','n'),('sog','SOG','i'),('yc','YC','i'),('rc','RC','i'),('gw','GW','i'),('pk','PK','i'),('pk_att','PK ATT','i'),
      ('gk_gp','GK GP','i'),('gk_gs','GK GS','i'),('gk_min','GK MIN','n'),('ga','GA','i'),('gaa','GAA','n'),('sv','SV','i'),('sv_pct','SV%','n'),('w','W','i'),('l','L','i'),('t','T','i'),('sho','SHO','i'),('sf','SF','i')]
    def _v(x, t):
        x = (x or '').strip()
        if x == '': return None
        if t == 't': return x
        f = float(x); return int(f) if t == 'i' else f
    seed = [{k: _v(r[c], t) for k, c, t in COLS} for r in _csv.DictReader(open(sys.argv[5]))]
    seed = [{k: v for k, v in d.items() if v is not None} for d in seed]
    js = _json.dumps(seed, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    s = s.replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx', '<script>window.SEED_PLAYERS = ' + js + ';</script>\n<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx', 1)

# supabase-js before the app script
rep('<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>',
    """<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>\n<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"></script>\n<script>window.supabase || document.write('<script src="https://unpkg.com/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"><\\/script>');</script>""")
rep('<title>WSOC Portal Board</title>', '<title>WSOC Portal Board</title>\n<meta name="robots" content="noindex">')

assert 'S.portal.rows' not in s and 'initNotes' not in s and 'EMBEDDED_CSV' not in s, "leftover"
doc = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
       '<style>[hidden]{display:none!important}body{margin:0}img{max-width:100%}</style>\n'
       + s.replace('<header class="top">', '</head><body>\n<header class="top">', 1) + '\n</body></html>\n')
open(out, 'w').write(doc)
print("built", out, len(doc))
