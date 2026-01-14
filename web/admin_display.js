(function () {
    const form = document.getElementById('display-form');
    const tokenSection = document.getElementById('token-section');
    const tokenVal = document.getElementById('token-val');
    const wallboardLink = document.getElementById('wallboard-link');

    // Assume Control Plane is on 8080 or 8000. Let's try to detect or use 8080 as a likely candidate.
    // However, if we are in firebase emulator, maybe it's 8081? 
    // Let's use 8080 for control plane (FastAPI) and 8081 for functions (Portal API).
    const CP_BASE = "http://127.0.0.1:8080";

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const tenant = document.getElementById('disp-tenant').value;
        const site = document.getElementById('disp-site').value;
        const name = document.getElementById('disp-name').value;

        try {
            const res = await fetch(`${CP_BASE}/displays`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tenant_id: tenant, site_id: site, name: name })
            });

            if (!res.ok) throw new Error(`Error: ${res.status}`);

            const data = await res.json();

            tokenVal.textContent = data.token;
            const fullUrl = `${window.location.origin}/bigscreen.html?tenant=${tenant}&site=${site}&display_token=${data.token}&dev=1`;
            wallboardLink.href = fullUrl;
            wallboardLink.textContent = fullUrl;
            tokenSection.style.display = 'block';

        } catch (err) {
            alert("Failed to create display. Ensure SIMCO Control Plane is running on " + CP_BASE);
            console.error(err);
        }
    });
})();
