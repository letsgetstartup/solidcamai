// Simco AI - Frontend Logic

document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    // const datasetSelect = document.getElementById('dataset-select'); // Removed

    // Real Data Starter Questions (Unified View)
    const STARTER_QUESTIONS = [
        "Show top 5 machines with the most ALARM events today.",
        "List all active ERP production orders.",
        "Which machine has the highest average Spindle Load in the last hour?",
        "Show me the event log for VMC-1.",
        "List all DOWNTIME events sorted by timestamp.",
        "Show latest telemetry status for all machines.",
        "Which machines exceed 80% Spindle Load?",
        "Count events by type for the last 24 hours.",
        "Show details for Order #ORD-101.",
        "Identify machines with no events in the last hour."
    ];

    // Topic-Based Content (Data-Backed)
    const TOPIC_CONTENT = {
        'efficiency': {
            alerts: [
                { level: 'critical', title: 'High Downtime', time: 'Live', desc: 'VMC-1 Stopped', query: 'Show DOWNTIME events for VMC-1 today.' },
                { level: 'warning', title: 'Low Output', time: '1h ago', desc: 'Lathe-2 Idle', query: 'Show event count for Lathe-2 in the last hour.' }
            ],
            insights: [
                { metric: 'Top 3', title: 'Most Active', sub: 'By Event Vol', query: 'Show top 3 machines by total event count.' },
                { metric: 'Idle', title: 'Inactive Machines', sub: 'No Data', query: 'List machines with no events in the last 24 hours.' }
            ]
        },
        'profitability': {
            alerts: [
                { level: 'critical', title: 'Order Update', time: 'Active', desc: 'New Orders', query: 'List all ERP orders created today.' },
                { level: 'warning', title: 'Deadline Risk', time: 'Today', desc: 'Due Soon', query: 'Show ERP orders due in the next 24 hours.' }
            ],
            insights: [
                { metric: 'Top 5', title: 'Largest Orders', sub: 'By Qty', query: 'Show top 5 ERP orders by quantity.' },
                { metric: 'Status', title: 'Order Breakdown', sub: 'Active/Done', query: 'Count ERP orders by status.' }
            ]
        },
        'health': {
            alerts: [
                { level: 'critical', title: 'Spindle Load', time: '2m ago', desc: 'VMC-3 High', query: 'Show Spindle Load telemetry for VMC-3.' },
                { level: 'warning', title: 'Vibration', time: '10m ago', desc: 'Lathe-1 Spike', query: 'Show Vibration telemetry for Lathe-1.' }
            ],
            insights: [
                { metric: 'Trend', title: 'Alarm Frequency', sub: 'Last 24h', query: 'Show trend of ALARM events over the last 24 hours.' },
                { metric: 'Log', title: 'Recent Errors', sub: 'All Machines', query: 'List the last 10 ALARM events.' }
            ]
        },
        'tools': {
            alerts: [
                { level: 'critical', title: 'Tool Change', time: '4m ago', desc: 'VMC-2 Tool #4', query: 'When was the last TOOL_CHANGE event on VMC-2?' },
                { level: 'warning', title: 'Usage limits', time: 'AM Shift', desc: 'High Cycle Count', query: 'Show machines with >100 cycles today.' }
            ],
            insights: [
                { metric: 'Log', title: 'Tool Events', sub: 'History', query: 'List all TOOL_CHANGE events sorted by time.' },
                { metric: 'Wear', title: 'Load Analysis', sub: 'Correlated', query: 'Show Spindle Load during last TOOL_CHANGE.' }
            ]
        },
        'workforce': {
            alerts: [
                { level: 'warning', title: 'Shift Start', time: '08:00', desc: 'Login Events', query: 'Show OPERATOR_LOGIN events today.' },
                { level: 'warning', title: 'Activity', time: 'Current', desc: 'Active Users', query: 'Who logged in recently?' }
            ],
            insights: [
                { metric: 'Log', title: 'Operator Log', sub: 'Audit', query: 'List all operator events for today.' },
                { metric: 'Perf', title: 'Cycles by User', sub: 'Est.', query: 'Count events grouped by Operator ID.' }
            ]
        },
        'energy': {
            alerts: [
                { level: 'critical', title: 'Power Spike', time: 'Now', desc: 'VMC-1 High', query: 'Show max power consumption for VMC-1 today.' },
                { level: 'warning', title: 'Usage', time: 'Shift 1', desc: 'Total Load', query: 'List all power telemetry readings.' }
            ],
            insights: [
                { metric: 'Peak', title: 'Energy Hog', sub: 'Max Load', query: 'Which machine has the highest peak power reading?' },
                { metric: 'Trend', title: 'Power Usage', sub: '24h', query: 'Show average power consumption by machine.' }
            ]
        },
        'quality': {
            alerts: [
                { level: 'critical', title: 'Part Count', time: 'Job #99', desc: 'Low Yield', query: 'Show PART_COMPLETE events for today.' },
                { level: 'warning', title: 'Cycle Time', time: 'Insp. 4', desc: 'Slow', query: 'Average cycle time between PART_COMPLETE events.' }
            ],
            insights: [
                { metric: 'Yield', title: 'Output', sub: '24h', query: 'Count PART_COMPLETE events by machine.' },
                { metric: 'Log', title: 'Quality Check', sub: 'Last 10', query: 'Show last 10 QC_CHECK events.' }
            ]
        }
    };

    // Render Logic defined later...


    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = (userInput.scrollHeight) + 'px';
    });

    // Helper: Show Follow-up Chips
    const showFollowUpQuestions = (questions) => {
        if (!questions || questions.length === 0) return;

        const container = document.createElement('div');
        container.className = 'follow-up-container';

        const label = document.createElement('div');
        label.className = 'follow-up-label';
        label.innerHTML = '<i class="fas fa-lightbulb"></i> Suggested Follow-ups:';
        container.appendChild(label);

        const chipsDiv = document.createElement('div');
        chipsDiv.className = 'chips-wrapper';

        questions.forEach(q => {
            const chip = document.createElement('button');
            chip.className = 'suggestion-chip';
            chip.textContent = q;
            chip.onclick = () => {
                userInput.value = q;
                handleSend(); // Auto-send when clicked
            };
            chipsDiv.appendChild(chip);
        });

        container.appendChild(chipsDiv);
        chatMessages.appendChild(container); // Append *after* the assistant message
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // Helper: Add Message
    const addMessage = (role, content) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.innerHTML = role === 'assistant' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'content';

        // Use marked.js if assistant, plain text if user (for safety)
        if (role === 'assistant') {
            contentDiv.innerHTML = marked.parse(content);
        } else {
            contentDiv.textContent = content;
        }

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(contentDiv);
        chatMessages.appendChild(msgDiv);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // Deep Reasoning Architecture - Hierarchical Logic
    const REASONING_STEPS = [
        {
            title: "Data Core Ingestion",
            explanation: "Accessing the Unified Shop Floor Dataset. Synchronizing real-time streams from Machines, Jobs, and Tooling systems to ensure a singular source of truth for the analysis."
        },
        {
            title: "Signal Stream Correlation",
            explanation: "Analyzing high-frequency Spindle Load and Vibration signals. Correlating sensor deviations with active Job IDs to pinpoint precise moments of mechanical variance."
        },
        {
            title: "Anomaly Pattern Matching",
            explanation: "Comparing current machine behavior against historical baselines. Identifying 'Signature' anomalies (e.g., thermal drift in VMC-3) that typically precede out-of-tolerance parts."
        },
        {
            title: "Financial Impact Modeling",
            explanation: "Calculating scrap cost by cross-referencing completed quantities with hourly machine rates and material costs. Determining the 'Invisible' cost of downtime during this event."
        },
        {
            title: "Root Cause Synthesis",
            explanation: "Aggregating all findings into a technical diagnostic. Evaluating if the variance is due to Tool Wear, Operator Error, or Machine Degradation (Event ID #401)."
        },
        {
            title: "Visualization & Report Tuning",
            explanation: "Selecting optimized chart parameters to highlight the most critical data correlations for the shop floor dashboard. Finalizing engineering recommendations."
        }
    ];

    let currentThinkingInterval;

    // Helper: Simulate Thinking (Hierarchical Accordion)
    const simulateThinking = (container) => {
        container.innerHTML = '';

        const reasoningBox = document.createElement('div');
        reasoningBox.className = 'reasoning-container loading';

        const header = document.createElement('div');
        header.className = 'reasoning-header';
        header.innerHTML = `
            <span><i class="fas fa-microchip"></i> Advanced Reasoning Engine</span>
            <i class="fas fa-chevron-down"></i>
        `;

        const content = document.createElement('div');
        content.className = 'reasoning-content';

        const log = document.createElement('div');
        log.className = 'reasoning-log';
        content.appendChild(log);

        reasoningBox.appendChild(header);
        reasoningBox.appendChild(content);
        container.appendChild(reasoningBox);

        header.onclick = () => reasoningBox.classList.toggle('collapsed');

        let stepIndex = 0;
        const addStep = () => {
            if (stepIndex >= REASONING_STEPS.length) {
                clearInterval(currentThinkingInterval);
                return;
            }

            const stepData = REASONING_STEPS[stepIndex];
            const stepContainer = document.createElement('div');
            stepContainer.className = 'reasoning-step';

            const title = document.createElement('div');
            title.className = 'reasoning-main-step';
            title.textContent = stepData.title;

            const detail = document.createElement('div');
            detail.className = 'reasoning-detail';
            detail.textContent = stepData.explanation;

            stepContainer.appendChild(title);
            stepContainer.appendChild(detail);
            log.appendChild(stepContainer);

            log.scrollTop = log.scrollHeight;
            stepIndex++;
        };

        addStep();
        currentThinkingInterval = setInterval(addStep, 1500); // Slower for readability
        return reasoningBox;
    };

    // Helper: Render Chart (visuals)
    const renderChart = (vizData) => {
        if (!vizData || !vizData.labels || !vizData.datasets || !Array.isArray(vizData.datasets)) {
            console.warn('Invalid or empty visualization data provided.');
            return;
        }

        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';

        const canvas = document.createElement('canvas');
        chartContainer.appendChild(canvas);

        chatMessages.appendChild(chartContainer);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to show chart

        // Big Screen Functional Palette (Strict Industrial)
        const VIBRANT_PALETTE = [
            '#3b82f6', // Helper Blue (Primary)
            '#19c37d', // OK Green
            '#ffb020', // Warn Orange
            '#ff3b30', // Bad Red
            '#a9b7d0', // Muted Blue-Grey
            '#e7eefc'  // Text White
        ];

        // Default Dark Theme Config (Matching Big Screen)
        Chart.defaults.color = '#a9b7d0'; // Muted text
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

        new Chart(canvas, {
            type: vizData.type || 'bar',
            data: {
                labels: vizData.labels,
                datasets: vizData.datasets.map((ds, index) => ({
                    ...ds,
                    borderWidth: 1,
                    // Force high-contrast colors; distribute palette among datasets
                    backgroundColor: VIBRANT_PALETTE.slice(index % VIBRANT_PALETTE.length),
                    borderColor: VIBRANT_PALETTE[index % VIBRANT_PALETTE.length],
                    pointBackgroundColor: VIBRANT_PALETTE[index % VIBRANT_PALETTE.length],
                    pointRadius: 3
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: vizData.title,
                        font: { size: 16, weight: '800' },
                        color: '#e7eefc' // Primary Text
                    },
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#FFFFD7',
                        bodyColor: '#FFFFFF',
                        borderColor: '#FFFFD7',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: 'rgba(255,255,255,0.8)',
                            font: { size: 11 }
                        },
                        grid: {
                            color: 'rgba(255,255,255,0.1)',
                            drawBorder: true
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: 'rgba(255,255,255,0.8)',
                            font: { size: 11 }
                        },
                        grid: {
                            color: 'rgba(255,255,255,0.1)',
                            drawBorder: true
                        }
                    }
                }
            }
        });
    };

    const handleSend = async () => {
        const question = userInput.value.trim();
        // const collection = datasetSelect.value; // Removed as per instruction

        if (!question) return;

        // Remove any existing follow-up containers to keep UI clean
        const existingFollowUps = document.querySelectorAll('.follow-up-container');
        existingFollowUps.forEach(el => el.remove());

        // UI state
        addMessage('user', question);
        userInput.value = '';
        userInput.style.height = 'auto';
        sendBtn.disabled = true;

        // Loading message with Thinking Process
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant loading';
        chatMessages.appendChild(loadingDiv);

        // Start Reasoning Simulation
        const startTime = performance.now();
        simulateThinking(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            // Function URL - In local testing it's usually localhost:5001/solidcam-f58bc/us-central1/ask_gemini
            // In production, we use the rewrite path /ask
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Tenant-ID': 'test_tenant' // Secure identity propagation
                },
                body: JSON.stringify({
                    question,
                    tenant_id: 'test_tenant',
                    site_id: 'test_site'
                })
            });

            const data = await response.json();

            // Stop Reasoning & Finalize UI
            clearInterval(currentThinkingInterval);

            const reasoningBox = loadingDiv.querySelector('.reasoning-container');
            if (reasoningBox) {
                reasoningBox.classList.remove('loading');
                reasoningBox.classList.add('collapsed'); // Collapse by default once done
                const headerSpan = reasoningBox.querySelector('.reasoning-header span');
                headerSpan.innerHTML = '<i class="fas fa-check-circle" style="color: #4CAF50"></i> Thought for ' + (Math.round(performance.now() - startTime) / 1000).toFixed(1) + 's';
            }

            loadingDiv.classList.remove('loading');

            if (data.answer) {
                addMessage('assistant', data.answer);

                // Render Chart and Follow-ups with isolated error handling
                try {
                    if (data.visualization && Object.keys(data.visualization).length > 0) {
                        renderChart(data.visualization);
                    }
                } catch (vizError) {
                    console.error('Visualization error:', vizError);
                }

                try {
                    if (data.follow_up && Array.isArray(data.follow_up)) {
                        showFollowUpQuestions(data.follow_up);
                    }
                } catch (followError) {
                    console.error('Follow-up rendering error:', followError);
                }
            } else if (data.error) {
                addMessage('assistant', `❌ Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Fetch error:', error);
            clearInterval(currentThinkingInterval);
            if (loadingDiv && loadingDiv.parentNode) {
                chatMessages.removeChild(loadingDiv);
            }
            addMessage('assistant', '❌ Failed to process the request. The AI might be temporarily overloaded.');
        } finally {
            sendBtn.disabled = false;
        }
    };

    // Initial Starter Quesitons Display
    const updateStarterQuestions = () => {
        // Strategy: If chat is empty, show them.
        if (chatMessages.children.length <= 1) { // 1 because of welcome message
            const starterContainer = document.querySelector('.starter-container');
            if (starterContainer) starterContainer.remove();

            if (STARTER_QUESTIONS.length > 0) {
                const container = document.createElement('div');
                container.className = 'starter-container follow-up-container';

                const label = document.createElement('div');
                label.className = 'follow-up-label';
                label.innerHTML = `<i class="fas fa-layer-group"></i> <b>Unified Analysis</b> - Try these complex inquiries:`;
                container.appendChild(label);

                const chipsDiv = document.createElement('div');
                chipsDiv.className = 'chips-wrapper';

                STARTER_QUESTIONS.forEach(q => {
                    const chip = document.createElement('button');
                    chip.className = 'suggestion-chip';
                    chip.textContent = q;
                    chip.onclick = () => {
                        userInput.value = q;
                        handleSend();
                    };
                    chipsDiv.appendChild(chip);
                });
                container.appendChild(chipsDiv);
                chatMessages.appendChild(container);
            }
        }
    };

    sendBtn.addEventListener('click', handleSend);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // Removed datasetSelect.addEventListener('change', ...) as per instruction

    // Init Logic
    // Add initial welcome message
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'message assistant';
    welcomeDiv.innerHTML = `<div class="avatar"><i class="fas fa-robot"></i></div><div class="content">Hello! I am **SolidCamAI**. I have full visibility into your **Machines, Jobs, Events, Tools, and Signals**.<br><br>Ask me complex questions that cross-reference your data!</div>`;
    chatMessages.appendChild(welcomeDiv);

    updateStarterQuestions();

    updateStarterQuestions();

    // Render Sidebars Dynamic
    const renderSidebar = (topicKey) => {
        const data = TOPIC_CONTENT[topicKey] || TOPIC_CONTENT['health'];

        // Alerts
        const alertsContainer = document.getElementById('live-alerts');
        alertsContainer.innerHTML = ''; // Clear existing
        if (alertsContainer && data.alerts) {
            data.alerts.forEach(alert => {
                const card = document.createElement('div');
                card.className = `alert-card ${alert.level}`;
                card.innerHTML = `
                    <div class="alert-header">
                        <span>${alert.title}</span>
                        <span class="alert-time">${alert.time}</span>
                    </div>
                    <div class="alert-desc">${alert.desc}</div>
                `;
                card.onclick = () => {
                    userInput.value = alert.query;
                    handleSend();
                };
                alertsContainer.appendChild(card);
            });
        }

        // Insights
        const adminContainer = document.getElementById('admin-insights');
        adminContainer.innerHTML = ''; // Clear existing
        if (adminContainer && data.insights) {
            data.insights.forEach(insight => {
                const card = document.createElement('div');
                card.className = 'admin-card';
                card.innerHTML = `
                    <div class="admin-title"><i class="fas fa-chart-line"></i> ${insight.title}</div>
                    <div class="admin-metric">${insight.metric}</div>
                    <div class="admin-sub">${insight.sub}</div>
                `;
                card.onclick = () => {
                    userInput.value = insight.query;
                    handleSend();
                };
                adminContainer.appendChild(card);
            });
        }
    };

    // Initialize with default
    renderSidebar('health');

    // Listener
    const topicSelect = document.getElementById('topic-select');
    if (topicSelect) {
        topicSelect.addEventListener('change', (e) => {
            renderSidebar(e.target.value);
            // Optional: Feedback in chat
            // addMessage('assistant', `Switched context to **${e.target.options[e.target.selectedIndex].text}**. Analyzing specific data streams...`);
        });
    }
});
