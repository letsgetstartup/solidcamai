// Version: UI-Fix-v2-Restored
(function () {
    const qs = new URLSearchParams(location.search);
    // Modified: Prefer localStorage for pairing result, fall back to QS or defaults
    const storedTenant = localStorage.getItem("tenant_id");
    const storedSite = localStorage.getItem("site_id");

    const tenant = qs.get("tenant") || storedTenant || "tenant_demo";
    const site = qs.get("site") || storedSite || "site_demo";
    const dev = qs.get("dev") === "1";

    const storedToken = localStorage.getItem("display_token");
    const displayToken = qs.get("display_token") || storedToken || "";

    // Modified: Use relative path for production (Firebase Rewrite)
    const API_BASE = "";

    const headers = {};
    if (dev) {
        headers["X-Dev-Role"] = "admin";
        headers["X-Dev-Tenant"] = tenant;
        headers["X-Dev-Site"] = site;
    }

    // STRICT AUTH CHECK
    if (!displayToken && !dev) {
        // If no token and not in dev mode, redirect to pairing
        window.location.href = "pairing.html";
        return;
    }

    if (displayToken) {
        headers["X-Display-Token"] = displayToken; // production PR will validate this token
    }

    const el = (id) => document.getElementById(id);

    function setConn(ok, msg) {
        const b = el("connBadge");
        if (!b) return;
        b.textContent = msg;
        b.style.borderColor = ok ? "rgba(25,195,125,0.7)" : "rgba(255,59,48,0.7)";
        b.style.color = ok ? "#e7eefc" : "#ff3b30";
    }

    function fmtTime(d) {
        const pad = (n) => String(n).padStart(2, "0");
        return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    }

    function shortTime(d) {
        if (!d || d === "—") return "—";
        try {
            const date = new Date(d);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        } catch (e) { return "—"; }
    }

    function fmtNum(val) {
        if (typeof val !== 'number') return "—";
        return val % 1 === 0 ? val : val.toFixed(1);
    }

    function updateClock() {
        const c = el("clock");
        if (c) c.textContent = fmtTime(new Date());
    }

    function severityRank(sev) {
        const s = (sev || "").toUpperCase();
        if (s === "CRITICAL") return 4;
        if (s === "HIGH") return 3;
        if (s === "MEDIUM") return 2;
        return 1;
    }

    function renderFleet(fleet) {
        const r = el("fleetRow");
        if (!r) return;
        r.innerHTML = "";
        const pill = (label, val, cls) => {
            const d = document.createElement("div");
            d.className = `pill ${cls || ""}`;
            d.textContent = `${label}: ${val ?? "—"}`;
            return d;
        };
        r.appendChild(pill("Total", fleet.total, ""));
        r.appendChild(pill("Running", fleet.running, "ok"));
        r.appendChild(pill("Idle", fleet.idle, "warn"));
        r.appendChild(pill("Alarm", fleet.alarm, "bad"));
        r.appendChild(pill("Offline", fleet.offline, ""));
    }

    function renderAlerts(alerts) {
        const list = el("alertList");
        if (!list) return;
        list.innerHTML = "";
        const sorted = (alerts || []).slice().sort((a, b) => severityRank(b.severity) - severityRank(a.severity));
        const top = sorted.slice(0, 5);
        for (const a of top) {
            const li = document.createElement("li");
            li.className = "alertItem";
            const sev = (a.severity || "INFO").toUpperCase();
            const msg = a.message || a.type || "Alert";
            const m = a.machine_id ? `Machine: ${a.machine_id}` : "";
            const ts = a.ts || a.timestamp || "";
            li.innerHTML = `
        <div class="alertTop">
          <div class="alertSev ${sev}">${sev}</div>
          <div class="alertMeta">${shortTime(ts)}</div>
        </div>
        <div class="alertMsg">${msg}</div>
        <div class="alertMeta">${m}</div>
      `;
            list.appendChild(li);
        }
    }

    function renderMachines(machines) {
        const grid = el("tileGrid");
        if (!grid) return;
        grid.innerHTML = "";
        const arr = (machines || []).slice();
        // Stable ordering for wallboard
        arr.sort((a, b) => String(a.display_name || a.machine_id).localeCompare(String(b.display_name || b.machine_id)));

        for (const m of arr) {
            const t = document.createElement("div");
            const st = (m.status || "OFFLINE").toUpperCase();
            t.className = "tile";
            const name = m.display_name || m.machine_id || "Machine";
            const lastSeen = m.last_seen || "—";
            const metrics = m.metrics || {};
            const spindle = metrics.spindle_load ?? "—";
            const feed = metrics.feed_rate ?? "—";
            const order = (m.erp && m.erp.production_order) ? m.erp.production_order : "—";
            const due = (m.erp && m.erp.due_date) ? m.erp.due_date : "—";

            t.innerHTML = `
        <div class="tileHead">
          <div class="tileName">${name}</div>
          <div class="state ${st}">${st}</div>
        </div>
        <div class="tileBody">
          <div class="row"><span>Last seen</span><span>${shortTime(lastSeen)}</span></div>
          <div class="row"><span>Spindle</span><span>${fmtNum(metrics.spindle_load)}</span></div>
          <div class="row"><span>Feed</span><span>${fmtNum(metrics.feed_rate)}</span></div>
          <div class="row"><span>Order</span><span>${order}</span></div>
          <div class="row"><span>Due</span><span>${shortTime(due)}</span></div>
        </div>
      `;
            grid.appendChild(t);
        }
    }

    function fmtHumanDate(d) {
        if (!d || d === "—") return "—";
        try {
            const date = new Date(d);
            if (isNaN(date.getTime())) return "—";

            // If the input string is just YYYY-MM-DD (length 10), return just the date
            // to avoid timezone shifts on midnight
            if (typeof d === 'string' && d.length === 10) {
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }

            return date.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
        } catch (e) { return "—"; }
    }

    function renderOrders(orders) {
        const tbody = el("orderRows");
        if (!tbody) return;
        tbody.innerHTML = "";
        const top = (orders || []).slice(0, 12);
        for (const o of top) {
            const tr = document.createElement("tr");
            if (o.late) tr.className = "late";
            tr.innerHTML = `
        <td>${o.production_order || "—"}</td>
        <td>${o.resource_code || "—"}</td>
        <td>${o.item || "—"}</td>
        <td>${fmtHumanDate(o.due_date)}</td>
        <td>${o.operator_name || "—"}</td>
        <td>${o.status || "—"}</td>
      `;
            tbody.appendChild(tr);
        }
    }

    async function fetchSummary() {
        // Add cache buster to prevent stale data
        const url = `${API_BASE}/portal_api/v1/tenants/${encodeURIComponent(tenant)}/sites/${encodeURIComponent(site)}/bigscreen/summary?_cb=${Date.now()}`;
        const r = await fetch(url, { headers });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return await r.json();
    }

    function deriveKPIs(summary) {
        // Down = alarm + offline (simple)
        const f = summary.fleet || {};
        const down = (f.alarm || 0) + (f.offline || 0);
        const downEl = el("kpiDown");
        if (downEl) downEl.textContent = down;
        // Risk = late orders count
        const risk = (summary.orders || []).filter(o => o.late).length;
        const riskEl = el("kpiRisk");
        if (riskEl) riskEl.textContent = risk;
    }

    async function tick() {
        try {
            const s = await fetchSummary();
            setConn(true, "LIVE");
            const siteLine = el("siteLine");
            if (siteLine) siteLine.textContent = `Tenant: ${s.tenant_id || tenant} • Site: ${s.site_id || site}`;
            const stamp = el("stamp");
            if (stamp) stamp.textContent = `Updated: ${s.generated_at ? new Date(s.generated_at).toLocaleTimeString() : "—"}`;

            // Stale checks
            if (s.generated_at) {
                const last = new Date(s.generated_at);
                const ageSecs = (new Date() - last) / 1000;
                if (ageSecs > 60) {
                    setConn(false, `STALE (${Math.round(ageSecs)}s old)`);
                }
            }

            renderFleet(s.fleet || { total: 0, running: 0, idle: 0, alarm: 0, offline: 0 });
            renderAlerts(s.alerts || []);
            renderMachines(s.machines || []);
            renderOrders(s.orders || []);
            deriveKPIs(s);
        } catch (e) {
            setConn(false, "OFFLINE / ERROR");
            // Keep last good data on screen
            console.error(e);
        }
    }

    updateClock();
    setInterval(updateClock, 1000);

    // Near real-time best practice for wallboards: 2–5s refresh
    tick();
    setInterval(tick, 3000);
})();
