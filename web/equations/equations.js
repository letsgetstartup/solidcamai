/* 
 * Equations Lab JS
 * Handles chat-like UX, BigQuery API calls, and dynamic chart rendering.
 */

let chart = null;

function addMessage(role, text) {
    const wrap = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `msg ${role === 'user' ? 'user' : 'bot'}`;
    div.textContent = text;
    wrap.appendChild(div);
    wrap.scrollTop = wrap.scrollHeight;
}

function renderVisualization(viz) {
    const vizBox = document.getElementById('viz');
    const title = document.getElementById('viz-title');
    const canvas = document.getElementById('viz-canvas');

    if (!viz) {
        vizBox.style.display = 'none';
        if (chart) { chart.destroy(); chart = null; }
        return;
    }

    vizBox.style.display = 'block';
    title.textContent = viz.title || 'Visualization';

    if (chart) chart.destroy();
    chart = new Chart(canvas.getContext('2d'), {
        type: viz.type,
        data: viz.data,
        options: viz.options || {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                }
            },
            scales: {
                y: { ticks: { color: '#94a3b8' }, grid: { color: '#1f2a3a' } },
                x: { ticks: { color: '#94a3b8' }, grid: { color: '#1f2a3a' } }
            }
        }
    });
}

function getRangeTimestamps(hours) {
    const end = new Date();
    const start = new Date(Date.now() - (Number(hours) * 3600 * 1000));
    return { start: start.toISOString(), end: end.toISOString() };
}

async function runEquation() {
    const tenant = document.getElementById('tenant').value.trim();
    const site = document.getElementById('site').value.trim();
    const rangeHrs = document.getElementById('range').value;
    const groupBy = document.getElementById('group_by').value;
    const equation = document.getElementById('equation').value.trim();

    if (!equation) return;

    // Reset UI
    const sendBtn = document.getElementById('send');
    sendBtn.disabled = true;
    sendBtn.textContent = 'Analyzing...';

    addMessage('user', equation);

    const timeRange = getRangeTimestamps(rangeHrs);
    const url = `/equations_api/v1/tenants/${encodeURIComponent(tenant)}/sites/${encodeURIComponent(site)}/eval`;

    const body = {
        equation,
        time_range: timeRange,
        group_by: groupBy
    };

    const headers = {
        'Content-Type': 'application/json',
        'X-Dev-Tenant': tenant,
        'X-Dev-Site': site,
        'X-Dev-Role': 'admin'
    };

    try {
        const res = await fetch(url, {
            method: 'POST',
            headers,
            body: JSON.stringify(body)
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
            addMessage('bot', `Error: ${data.error || res.statusText}`);
            if (data.allowed_vars) {
                addMessage('bot', `Available variables: ${data.allowed_vars.join(', ')}`);
            }
            renderVisualization(null);
            return;
        }

        addMessage('bot', data.answer || 'Analysis complete.');
        if (data.visualization) {
            renderVisualization(data.visualization);
        } else {
            renderVisualization(null);
        }

    } catch (e) {
        addMessage('bot', `Network error: ${e.message}`);
        renderVisualization(null);
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Run Analysis';
        document.getElementById('equation').value = '';
        document.getElementById('equation').style.height = 'auto';
    }
}

// Event Listeners
document.getElementById('send').addEventListener('click', runEquation);

document.getElementById('equation').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        runEquation();
    }
});

// Auto-resize textarea
document.getElementById('equation').addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});
