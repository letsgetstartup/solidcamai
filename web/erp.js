const API_BASE = "http://127.0.0.1:8090"; // adjust to your control plane base URL
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
    const txt = await res.text();
    let body;
    try { body = JSON.parse(txt); } catch { body = { raw: txt }; }
    if (!res.ok) throw new Error(body.error || body.message || `${res.status}: ${txt}`);
    return body;
}

async function refreshConnections() {
    const tenantId = document.getElementById("tenant_id").value.trim();
    const container = document.getElementById("connections");
    container.innerHTML = "<p>Loading...</p>";

    const conns = await api(`/api/v1/tenants/${tenantId}/erp/connections`);
    container.innerHTML = conns.map(c => `
    <div class="card" style="padding:15px; margin-bottom:10px;">
      <div><strong>${c.display_name}</strong> (${c.provider})</div>
      <div><code>${c.base_url}</code></div>
      <div style="margin-top:10px;">
        <button class="cta-button" data-action="test" data-id="${c.id}">Test</button>
        <button class="cta-button" data-action="sync" data-id="${c.id}">Sync Now</button>
      </div>
      <pre id="out_${c.id}" style="margin-top:10px; background:#111; color:#0f0; padding:10px; overflow:auto;"></pre>
    </div>
  `).join("");

    container.querySelectorAll("button").forEach(btn => {
        btn.addEventListener("click", async () => {
            const id = btn.getAttribute("data-id");
            const action = btn.getAttribute("data-action");
            const out = document.getElementById(`out_${id}`);
            out.textContent = "Working...";
            try {
                if (action === "test") {
                    const r = await api(`/api/v1/tenants/${tenantId}/erp/connections/${id}/test`, { method: "POST" });
                    out.textContent = JSON.stringify(r, null, 2);
                } else {
                    const r = await api(`/api/v1/tenants/${tenantId}/erp/connections/${id}/sync`, {
                        method: "POST",
                        body: JSON.stringify({ page_size: 200 })
                    });
                    out.textContent = JSON.stringify(r, null, 2);
                }
            } catch (e) {
                out.textContent = "ERROR: " + e.message;
            }
        });
    });
}

document.getElementById("create_btn").addEventListener("click", async () => {
    const tenantId = document.getElementById("tenant_id").value.trim();

    const payload = {
        provider: "sap_b1_service_layer",
        display_name: document.getElementById("display_name").value.trim(),
        base_url: document.getElementById("base_url").value.trim(),
        company_db: document.getElementById("company_db").value.trim(),
        username: document.getElementById("username").value.trim(),
        password: document.getElementById("password").value,
        verify_tls: true
    };

    await api(`/api/v1/tenants/${tenantId}/erp/connections`, {
        method: "POST",
        body: JSON.stringify(payload)
    });

    await refreshConnections();
});

refreshConnections().catch(err => {
    document.getElementById("connections").innerHTML = `<p style="color:red;">${err.message}</p>`;
});
