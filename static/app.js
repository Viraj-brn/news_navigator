document.addEventListener('DOMContentLoaded', () => {

    // --- State ---
    let currentTopic = '';
    let currentDepth = 'standard';
    let currentBriefing = null;
    let conversationHistory = [];

    // --- Elements ---
    const searchSection = document.getElementById('search-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const topicInput = document.getElementById('topic-input');
    const generateBtn = document.getElementById('generate-btn');
    const loadingState = document.getElementById('loading-state');
    const depthBtns = document.querySelectorAll('.depth-btn');
    const backBtn = document.getElementById('back-to-search');

    // Briefing Elements
    const bKicker = document.getElementById('b-kicker');
    const bHeadline = document.getElementById('b-headline');
    const bSynthesis = document.getElementById('b-synthesis');
    const bMetadata = document.getElementById('b-metadata');
    const bSections = document.getElementById('b-sections');
    const bKeyTerms = document.getElementById('b-keyterms');
    const bTermsGrid = document.getElementById('b-terms-grid');
    const bArticlesList = document.getElementById('b-articles-list');

    // Chat Elements
    const chatHistory = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');

    // --- Loading Texts ---
    const loadingTexts = [
        "Scanning top ET sources...",
        "Analyzing market data...",
        "Identifying key themes...",
        "Synthesizing intelligence...",
        "Formatting briefing document...",
        "Finalizing JSON structure..."
    ];
    let loadingInterval = null;

    // --- Events ---

    // Depth Selector
    depthBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            depthBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentDepth = btn.dataset.depth;
        });
    });

    // Generate Briefing
    const generateBriefing = async () => {
        const topic = topicInput.value.trim();
        if (!topic) return;

        currentTopic = topic;

        // UI Updates
        generateBtn.style.display = 'none';
        
        // Rebuild Loading State
        loadingState.innerHTML = `
            <div class="spinner-container">
                <div class="spinner"></div>
                <div class="spinner-inner"></div>
            </div>
            <p id="loading-text">Initializing parameters...</p>
        `;
        loadingState.style.display = 'flex';
        
        const loadingTextEl = document.getElementById('loading-text');
        let textIdx = 0;
        loadingInterval = setInterval(() => {
            loadingTextEl.textContent = loadingTexts[textIdx % loadingTexts.length];
            textIdx++;
        }, 1800);

        try {
            const response = await fetch('/api/navigator', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic: currentTopic, depth: currentDepth })
            });

            const data = await response.json();
            
            if (response.ok) {
                renderBriefing(data);
                showDashboard();
            } else {
                alert(data.detail || 'An error occurred.');
            }
        } catch (error) {
            console.error(error);
            alert('Failed to generate briefing. Please ensure the backend is running.');
        } finally {
            clearInterval(loadingInterval);
            generateBtn.style.display = 'flex';
            loadingState.style.display = 'none';
        }
    };

    generateBtn.addEventListener('click', generateBriefing);
    topicInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') generateBriefing();
    });

    // Back Button
    backBtn.addEventListener('click', () => {
        dashboardSection.classList.remove('show');
        dashboardSection.style.display = 'none';
        searchSection.style.display = 'flex';
        topicInput.value = '';
        currentBriefing = null;
        conversationHistory = [];
        chatHistory.innerHTML = `
            <div class="chat-msg ai-msg">
                Hello! I generated this briefing. What would you like to know more about?
            </div>
        `;
    });

    // Chat
    const askQuestion = async () => {
        const question = chatInput.value.trim();
        if (!question || !currentBriefing) return;

        // Add user msg to UI
        addChatMessage(question, 'user-msg');
        chatInput.value = '';

        // Add typing indicator
        const loadingId = 'loading-' + Date.now();
        const typingHtml = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        addChatMessage(typingHtml, 'ai-msg', loadingId);

        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    briefing: currentBriefing,
                    topic: currentTopic,
                    conversation_history: conversationHistory,
                    question: question
                })
            });

            const data = await response.json();
            
            // Remove loading indicator
            document.getElementById(loadingId).remove();

            if (response.ok) {
                // Typewriter effect for AI answer
                typeWriterEffect(data.answer, 'ai-msg');
                conversationHistory.push({ role: "user", content: question });
                conversationHistory.push({ role: "assistant", content: data.answer });
            } else {
                addChatMessage("Sorry, I couldn't get an answer.", 'ai-msg');
            }
        } catch (error) {
            console.error(error);
            document.getElementById(loadingId).remove();
            addChatMessage("Network error while asking question.", 'ai-msg');
        }
    };

    chatSendBtn.addEventListener('click', askQuestion);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') askQuestion();
    });

    // --- Helpers ---

    function showDashboard() {
        searchSection.style.display = 'none';
        dashboardSection.style.display = 'block';
        
        // Trigger reflow to restart animations
        void dashboardSection.offsetWidth;
        dashboardSection.classList.add('show');
    }

    function renderBriefing(data) {
        const { briefing, articles } = data;
        currentBriefing = briefing;

        bKicker.textContent = briefing.kicker || 'BRIEFING';
        bHeadline.textContent = briefing.headline || 'Intelligence Briefing';
        bSynthesis.textContent = briefing.synthesis || '';

        // Metadata
        bMetadata.innerHTML = '';
        if (briefing.metadata && briefing.metadata.length > 0) {
            briefing.metadata.forEach((meta, i) => {
                const badge = document.createElement('div');
                badge.className = 'meta-badge';
                badge.style.animationDelay = `${i * 0.1}s`;
                badge.style.animation = `popIn 0.5s forwards ${i * 0.1}s`;
                badge.style.opacity = '0';
                badge.innerHTML = `
                    <span class="meta-label">${meta.label}</span>
                    <span class="meta-val">${meta.value}</span>
                `;
                bMetadata.appendChild(badge);
            });
        }

        // Sections
        bSections.innerHTML = '';
        if (briefing.sections && briefing.sections.length > 0) {
            briefing.sections.forEach((sec, i) => {
                const secEl = document.createElement('div');
                secEl.className = 'brief-section';
                secEl.style.animationDelay = `${0.3 + (i * 0.15)}s`;
                secEl.style.animation = `slideUpFade 0.6s forwards ${0.3 + (i * 0.15)}s`;
                secEl.style.opacity = '0';
                secEl.style.transform = 'translateY(20px)';
                
                secEl.innerHTML = `
                    <h3 class="section-title"><span>${sec.icon || '📌'}</span> ${sec.title}</h3>
                    <div class="section-body">${sec.body}</div>
                `;
                bSections.appendChild(secEl);
            });
        }

        // Key Terms
        if (briefing.keyTerms && briefing.keyTerms.length > 0) {
            bKeyTerms.style.display = 'block';
            bTermsGrid.innerHTML = '';
            briefing.keyTerms.forEach(term => {
                const tEl = document.createElement('div');
                tEl.className = 'term-item';
                tEl.innerHTML = `
                    <span class="term-name">${term.term}</span>
                    <span class="term-def">${term.definition}</span>
                `;
                bTermsGrid.appendChild(tEl);
            });
        } else {
            bKeyTerms.style.display = 'none';
        }

        // Articles
        bArticlesList.innerHTML = '';
        if (articles && articles.length > 0) {
            articles.forEach((art, i) => {
                const li = document.createElement('li');
                li.className = 'article-item';
                li.style.animationDelay = `${0.5 + (i * 0.05)}s`;
                li.style.animation = `popIn 0.4s forwards ${0.5 + (i * 0.05)}s`;
                li.style.opacity = '0';
                
                li.innerHTML = `
                    <a href="${art.link}" target="_blank">${art.title}</a>
                    <div class="article-desc">${art.pubDate || 'Recent'} • ${art.source || 'News'}</div>
                `;
                bArticlesList.appendChild(li);
            });
        }
    }

    function addChatMessage(text, className, id = '') {
        const msg = document.createElement('div');
        msg.className = `chat-msg ${className}`;
        msg.innerHTML = text; // allow HTML for loading spinner
        if (id) msg.id = id;
        chatHistory.appendChild(msg);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return msg;
    }
    
    function typeWriterEffect(text, className) {
        const msgEl = document.createElement('div');
        msgEl.className = `chat-msg ${className}`;
        msgEl.style.minHeight = "40px"; // prevent jumping
        chatHistory.appendChild(msgEl);
        
        let i = 0;
        // Simple fast typing effect
        const speed = 10; 
        
        function type() {
            if (i < text.length) {
                msgEl.innerHTML += text.charAt(i);
                i++;
                chatHistory.scrollTop = chatHistory.scrollHeight;
                setTimeout(type, speed);
            }
        }
        type();
    }


    // ── News Sentinel ───────────────────────────────

    const sentinelToggle = document.getElementById('sentinel-toggle');
    const sentinelBody = document.getElementById('sentinel-body');
    const sentinelChevron = document.getElementById('sentinel-chevron');
    const sentinelAddBtn = document.getElementById('sentinel-add-btn');
    const sentinelList = document.getElementById('sentinel-list');
    const alertKeywordInput = document.getElementById('alert-keyword');
    const alertConditionInput = document.getElementById('alert-condition');

    // Toggle panel
    sentinelToggle.addEventListener('click', () => {
        const isOpen = sentinelBody.style.display !== 'none';
        sentinelBody.style.display = isOpen ? 'none' : 'block';
        sentinelChevron.classList.toggle('open', !isOpen);
        if (!isOpen) loadAlerts();
    });

    // Create alert
    sentinelAddBtn.addEventListener('click', async () => {
        const keyword = alertKeywordInput.value.trim();
        const condition = alertConditionInput.value.trim();
        if (!keyword || !condition) return;

        sentinelAddBtn.disabled = true;
        sentinelAddBtn.textContent = 'Creating...';

        try {
            const response = await fetch('/api/alerts/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ keyword, trigger_condition: condition })
            });

            if (response.ok) {
                alertKeywordInput.value = '';
                alertConditionInput.value = '';
                loadAlerts();
            } else {
                const data = await response.json();
                alert(data.detail || 'Failed to create alert.');
            }
        } catch (e) {
            console.error(e);
            alert('Network error creating alert.');
        } finally {
            sentinelAddBtn.disabled = false;
            sentinelAddBtn.innerHTML = '<i class="fa-solid fa-plus"></i> Create Alert';
        }
    });

    // Load alerts
    async function loadAlerts() {
        try {
            const response = await fetch('/api/alerts');
            const data = await response.json();

            sentinelList.innerHTML = '';

            if (!data.alerts || data.alerts.length === 0) {
                sentinelList.innerHTML = '<div class="sentinel-empty">No alerts yet. Create one above to start tracking events.</div>';
                return;
            }

            data.alerts.forEach((alert, i) => {
                const card = document.createElement('div');
                card.className = 'alert-card';
                card.style.animationDelay = `${i * 0.08}s`;
                card.innerHTML = `
                    <div class="alert-icon"><i class="fa-solid fa-bell"></i></div>
                    <div class="alert-info">
                        <div class="alert-keyword">${alert.keyword}</div>
                        <div class="alert-condition">${alert.trigger_condition}</div>
                    </div>
                    <button class="alert-delete-btn" data-id="${alert.id}" title="Delete alert">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                `;
                sentinelList.appendChild(card);
            });

            // Attach delete handlers
            sentinelList.querySelectorAll('.alert-delete-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const alertId = btn.dataset.id;
                    try {
                        await fetch(`/api/alerts/${alertId}`, { method: 'DELETE' });
                        loadAlerts();
                    } catch (err) {
                        console.error(err);
                    }
                });
            });

        } catch (e) {
            console.error(e);
            sentinelList.innerHTML = '<div class="sentinel-empty">Failed to load alerts.</div>';
        }
    }

});
