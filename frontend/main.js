// FILE: main.js

document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'https://data-wm3y.onrender.com/api';

    // UI Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const uploadSection = document.getElementById('upload-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const exportPdfBtn = document.getElementById('export-pdf-btn');
    const loader = document.getElementById('loader');
    const loaderText = document.getElementById('loader-text');

    // Chat Elements
    const floatingChatBtn = document.getElementById('floating-chat-btn');
    const openChatBtn = document.getElementById('open-chat-btn');
    const chatModal = document.getElementById('chat-modal');
    const closeChatModal = document.getElementById('close-chat-modal');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSubmit = document.getElementById('chat-submit');

    // --- File Upload Logic ---
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length) {
            handleFileUpload(files[0]);
        }
    });
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            handleFileUpload(fileInput.files[0]);
        }
    });

    async function handleFileUpload(file) {
        showLoader('Uploading and processing file...');
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'File upload failed');
            }

            uploadStatus.textContent = `✅ ${file.name} uploaded successfully!`;
            uploadStatus.style.color = 'var(--success-color)';

            // Reset chat window on new upload
            chatMessages.innerHTML = '';
            addChatMessage("Hello! I'm ready to answer questions about your new data. Ask me anything!", 'bot');
            
            await fetchAndDisplayDashboard();

        } catch (error) {
            console.error('Upload Error:', error);
            uploadStatus.textContent = `❌ Error: ${error.message}`;
            uploadStatus.style.color = 'var(--danger-color)';
            hideLoader();
        }
    }

    // --- Dashboard Data Fetching and Display ---
    async function fetchAndDisplayDashboard() {
        showLoader('Generating insights and charts...');
        try {
            const response = await fetch(`${API_BASE_URL}/dashboard`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to fetch dashboard data');
            }
            const data = await response.json();

            displayKPIs(data.kpis);
            displayAISummary(data.summary);
            renderCharts(data.charts);

            uploadSection.classList.add('hidden');
            dashboardSection.classList.remove('hidden');
            exportPdfBtn.disabled = false;

        } catch (error)
        {
            console.error('Dashboard Fetch Error:', error);
            uploadStatus.textContent = `❌ Error: ${error.message}`;
            uploadStatus.style.color = 'var(--danger-color)';
        } finally {
            hideLoader();
        }
    }

    function displayKPIs(kpis) {
        document.getElementById('kpi-total-sales').textContent = kpis.total_sales;
        document.getElementById('kpi-total-units').textContent = kpis.total_units_sold;
        document.getElementById('kpi-avg-satisfaction').textContent = kpis.average_satisfaction;
    }

    function displayAISummary(summary) {
        document.getElementById('ai-summary').textContent = summary;
    }

    function renderCharts(charts) {
    Plotly.newPlot('chart1', JSON.parse(charts.sales_by_product), {}, { responsive: true });
    Plotly.newPlot('chart2', JSON.parse(charts.sales_by_region), {}, { responsive: true });
    Plotly.newPlot('chart3', JSON.parse(charts.satisfaction_vs_units), {}, { responsive: true });
    Plotly.newPlot('chart4', JSON.parse(charts.units_by_region_product), {}, { responsive: true });
    Plotly.newPlot('chart5', JSON.parse(charts.avg_satisfaction_by_product), {}, { responsive: true });
    Plotly.newPlot('chart6', JSON.parse(charts.sales_vs_units_scatter), {}, { responsive: true });
    Plotly.newPlot('chart7', JSON.parse(charts.sales_efficiency_heatmap), {}, { responsive: true });
    }


    // --- Chat Logic ---
    function toggleChatModal() {
        chatModal.classList.toggle('hidden');
    }

    floatingChatBtn.addEventListener('click', toggleChatModal);
    openChatBtn.addEventListener('click', toggleChatModal);
    closeChatModal.addEventListener('click', toggleChatModal);

    chatSubmit.addEventListener('click', handleChatSubmit);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleChatSubmit();
        }
    });

    // --- MODIFIED handleChatSubmit function ---
    async function handleChatSubmit() {
        const message = chatInput.value.trim();
        if (!message) return;

        addChatMessage(message, 'user');
        chatInput.value = '';
        showLoader('Thinking...'); // More appropriate text

        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Chat request failed');
            }
            
            // The response body is now passed directly to addChatMessage
            const data = await response.json();
            addChatMessage(data, 'bot');

        } catch (error) {
            console.error('Chat Error:', error);
            addChatMessage({ answer: `Sorry, I encountered an error: ${error.message}`, type: 'text' }, 'bot');
        } finally {
            hideLoader();
        }
    }

    // --- MODIFIED addChatMessage function ---
    // This function is now smarter and can render different types of content.
    function addChatMessage(content, role) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', role);

        // Check if the content is a plot from the bot
        if (role === 'bot' && content.type === 'plot') {
            const botMessageText = document.createElement('p');
            botMessageText.textContent = "Here is the chart you requested:";

            const imageElement = document.createElement('img');
            imageElement.src = `data:image/png;base64,${content.image}`;
            imageElement.alt = 'Chatbot generated chart';
            imageElement.classList.add('chat-image'); // Add a class for styling
            
            messageElement.appendChild(botMessageText);
            messageElement.appendChild(imageElement);

        } else {
            // Handle regular text messages (from user or bot)
            // If content is an object (from bot), use content.answer. Otherwise, use content itself (from user).
            messageElement.textContent = typeof content === 'object' ? content.answer : content;
        }

        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll to the latest message
    }


    // --- PDF Export ---
    exportPdfBtn.addEventListener('click', async () => {
        showLoader('Generating PDF report...');
        try {
            const response = await fetch(`${API_BASE_URL}/export-pdf`);
            if (!response.ok) {
                throw new Error('Failed to generate PDF');
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'dashboard_report.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (error) {
            console.error('PDF Export Error:', error);
            alert('Could not generate PDF. Please try again.');
        } finally {
            hideLoader();
        }
    });

    // --- Loader Utilities ---
    function showLoader(text = 'Processing...') {
        loaderText.textContent = text;
        loader.classList.remove('hidden');
    }

    function hideLoader() {
        loader.classList.add('hidden');
    }
});
