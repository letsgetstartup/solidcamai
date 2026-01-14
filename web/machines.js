// Production Gen 2 Function for QR
const QR_SERVICE_URL = "https://generate-qr-i6yvrrps6q-uc.a.run.app";

const DEV_HEADERS = {
    "X-Dev-Role": "Manager",
    "X-Dev-Tenant": "tenant_demo",
    "X-Dev-Site": "site_demo",
    "Content-Type": "application/json"
};

async function api(path, opts = {}) {
    // We assume path starts with /mgmt/... but our function is at root of the URL
    // So we just append the path to the service URL
    const url = `${QR_SERVICE_URL}${path}`;

    const res = await fetch(url, {
        ...opts,
        headers: { ...DEV_HEADERS, ...(opts.headers || {}) }
    });
    if (!res.ok) {
        const txt = await res.text();
        throw new Error(`${res.status}: ${txt}`);
    }
    // Return blob for images, json otherwise
    const contentType = res.headers.get("content-type");
    if (contentType && contentType.includes("image/")) {
        return res.blob();
    }
    return res.json();
}

const API_BASE = "https://portal-api-i6yvrrps6q-uc.a.run.app";

async function loadMachines() {
    const tenantId = document.getElementById("tenant_id").value;
    const siteId = document.getElementById("site_id").value;
    const container = document.getElementById("machine_list");

    container.innerHTML = '<div style="text-align:center; padding:20px; color:var(--muted);">Loading fleet data...</div>';

    try {
        const res = await fetch(`${API_BASE}/portal_api/v1/tenants/${tenantId}/sites/${siteId}/machines`);
        if (!res.ok) throw new Error("Failed to fetch machines");

        let machines = await res.json();

        // Deduplicate machines by machine_id
        const uniqueMachines = new Map();
        machines.forEach(m => {
            if (!uniqueMachines.has(m.machine_id)) {
                uniqueMachines.set(m.machine_id, m);
            }
        });
        machines = Array.from(uniqueMachines.values());

        if (machines.length === 0) {
            container.innerHTML = '<div style="text-align:center; padding:20px; color:var(--muted);">No machines found.</div>';
            return;
        }

        container.innerHTML = machines.map(m => `
            <div class="card" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:15px;">
                    <img src="assets/${m.machine_id.includes('fanuc') ? 'fanuc' : 'siemens'}.png" class="machine-img" onerror="this.src='assets/simco_ai_hero_logo.png'" style="width:50px; height:50px;">
                    <div>
                        <strong style="color:var(--text); font-size:1.1rem;">${m.machine_id}</strong>
                        <div style="display:flex; gap:10px; align-items:center; margin-top:4px;">
                            <span style="color:var(--muted); font-size:0.9rem;">${m.ip || 'No IP'}</span>
                            <span class="status-pill ${['ACTIVE', 'RUNNING'].includes((m.status || '').trim()) ? 'active' : ''}">
                                <div class="status-dot"></div> ${m.status || 'UNKNOWN'}
                            </span>
                        </div>
                    </div>
                </div>
                <button class="btn-manage" onclick="showQR('${m.machine_id}', '${m.machine_id}')">Generate QR</button>
            </div>
        `).join("");

    } catch (err) {
        container.innerHTML = `<div class="error-msg">Error: ${err.message}</div>`;
    }
}

window.showQR = async (machineId, machineName) => {
    const siteId = document.getElementById("site_id").value;
    const tenantId = document.getElementById("tenant_id").value;

    try {
        // 1. Generate/Get Token
        // POST /mgmt/v1/sites/{site_id}/machines/{machine_id}/qr?tenant_id=...
        const tokenData = await api(`/mgmt/v1/sites/${siteId}/machines/${machineId}/qr?tenant_id=${tenantId}`, { method: "POST" });

        // 2. Generate Image URL (Client-side / Public API)
        // We use the token (or full deep link URL) to generate the QR
        // Deep link format: https://solidcamal.web.app/mobile/link/m/{public_code}
        const deepLink = `https://solidcamal.web.app/mobile/link/m/${tokenData.public_code}`;
        const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(deepLink)}`;

        document.getElementById("qr_title").textContent = `QR: ${machineName}`;
        document.getElementById("qr_img_container").innerHTML = `<img src="${qrUrl}" style="width:150px; height:150px;">`;
        document.getElementById("qr_code_text").textContent = tokenData.public_code;

        document.getElementById("qr_modal").style.display = "block";
    } catch (e) {
        alert("Error loading QR: " + e.message);
    }
};

document.getElementById("load_btn").addEventListener("click", loadMachines);

// Auto-load
loadMachines();
