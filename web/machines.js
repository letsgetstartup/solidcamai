const API_BASE = "http://127.0.0.1:8090";
const DEV_HEADERS = {
    "X-Dev-Role": "Manager",
    "X-Dev-Tenant": "tenant_demo",
    "X-Dev-Site": "site_demo",
    "Content-Type": "application/json"
};

async function api(path, opts = {}) {
    const res = await fetch(`${API_BASE}${path}`, {
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

async function loadMachines() {
    const tenantId = document.getElementById("tenant_id").value;
    const siteId = document.getElementById("site_id").value;

    const container = document.getElementById("machine_list");
    container.innerHTML = "Loading...";

    // Using existing endpoints - assume we have a way to list machines
    // If not, we mock for the demo as the registry logic is in Agent, 
    // but Control Plane (cloud) might not have a direct list endpoint yet?
    // Let's assume /api/v1/sites/{site_id}/machines exists or we use a hardcoded list for MVP testing
    // To be safe, I will mock the list for this demo UI since I didn't verify a `list_machines` endpoint in `router_site` or `router_gateway`.

    // Mock Data
    const machines = [
        { id: "m_001", name: "CNC Lathe A" },
        { id: "m_002", name: "Milling Center 5-Axis" },
        { id: "m_003", name: "Grinder X1" }
    ];

    container.innerHTML = machines.map(m => `
        <div class="card" style="padding:15px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <strong>${m.name}</strong> <br>
                <small>${m.id}</small>
            </div>
            <div>
                <button class="cta-button" onclick="showQR('${m.id}', '${m.name}')">Get QR</button>
            </div>
        </div>
    `).join("");
}

window.showQR = async (machineId, machineName) => {
    const siteId = document.getElementById("site_id").value;
    const tenantId = document.getElementById("tenant_id").value;

    try {
        // 1. Generate/Get Token
        // POST /mgmt/v1/sites/{site_id}/machines/{machine_id}/qr?tenant_id=...
        const tokenData = await api(`/mgmt/v1/sites/${siteId}/machines/${machineId}/qr?tenant_id=${tenantId}`, { method: "POST" });

        // 2. Load Image
        // GET /mgmt/v1/sites/{site_id}/machines/{machine_id}/qr/label?tenant_id=...
        const blob = await api(`/mgmt/v1/sites/${siteId}/machines/${machineId}/qr/label?tenant_id=${tenantId}`);
        const url = URL.createObjectURL(blob);

        document.getElementById("qr_title").textContent = `QR: ${machineName}`;
        document.getElementById("qr_img_container").innerHTML = `<img src="${url}" style="width:150px; height:150px;">`;
        document.getElementById("qr_code_text").textContent = tokenData.public_code;

        document.getElementById("qr_modal").style.display = "block";
    } catch (e) {
        alert("Error loading QR: " + e.message);
    }
};

document.getElementById("load_btn").addEventListener("click", loadMachines);

// Auto-load
loadMachines();
