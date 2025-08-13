/**
 * Healthcare Voice AI Assistant - Professional Frontend JavaScript
 * Handles voice recording, chat functionality, and UI interactions
 */

class HealthcareVoiceAI {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.conversationId = null;
        this.currentVoice = 'elevenlabs';
        this.autoPlay = true;
        this.volume = 0.8;
        this.rate = 1.0;
        this.isProcessing = false;
        
        // Initialize the application
        this.initializeElements();
        this.bindEvents();
        this.loadSettings();
        this.initializeConversation();
        this.showApp();
    }

    /**
     * Initialize DOM elements
     */
    initializeElements() {
        // App container
        this.app = document.getElementById('app');
        
        // Voice controls
        this.recordBtn = document.getElementById('recordBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusIcon = document.getElementById('statusIcon');
        this.statusText = document.getElementById('statusText');
        this.recordingVisualizer = document.getElementById('recordingVisualizer');
        
        // Chat elements
        this.chatMessages = document.getElementById('chatMessages');
        this.textInput = document.getElementById('textInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.exportBtn = document.getElementById('exportBtn');
        this.printBtn = document.getElementById('printBtn');
        
        // Settings elements
        this.settingsBtn = document.getElementById('settingsBtn');
        this.settingsOverlay = document.getElementById('settingsOverlay');
        this.closeSettings = document.getElementById('closeSettings');
        this.voiceSelect = document.getElementById('voiceSelect');
        this.voiceSpeed = document.getElementById('voiceSpeed');
        this.voiceVolume = document.getElementById('voiceVolume');
        this.speedValue = document.getElementById('speedValue');
        this.volumeValue = document.getElementById('volumeValue');
        this.themeSelect = document.getElementById('themeSelect');
        this.autoPlayToggle = document.getElementById('autoPlayToggle');
        this.notificationsToggle = document.getElementById('notificationsToggle');
        this.saveHistoryToggle = document.getElementById('saveHistoryToggle');
        this.analyticsToggle = document.getElementById('analyticsToggle');
        this.resetSettings = document.getElementById('resetSettings');
        this.saveSettings = document.getElementById('saveSettings');
        
        // Help elements
        this.helpBtn = document.getElementById('helpBtn');
        this.helpOverlay = document.getElementById('helpOverlay');
        this.closeHelp = document.getElementById('closeHelp');
        this.closeHelpBtn = document.getElementById('closeHelpBtn');
        
        // Quick actions
        this.actionBtns = document.querySelectorAll('.action-btn');
        
        // Disclaimer
        this.disclaimerBanner = document.querySelector('.disclaimer-banner');
        this.closeDisclaimer = document.getElementById('closeDisclaimer');
        
        // Audio player
        this.audioPlayer = document.getElementById('audioPlayer');
        
        // Debug: Log all elements found
        console.log('Elements initialized:', {
            app: this.app,
            recordBtn: this.recordBtn,
            chatMessages: this.chatMessages,
            textInput: this.textInput
        });
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Voice recording events
        this.recordBtn.addEventListener('click', () => this.startRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.clearBtn.addEventListener('click', () => this.clearConversation());
        
        // Chat events
        this.sendBtn.addEventListener('click', () => this.sendTextMessage());
        this.textInput.addEventListener('keydown', (e) => this.handleTextInput(e));
        this.exportBtn.addEventListener('click', () => this.exportChat());
        this.printBtn.addEventListener('click', () => this.printChat());
        
        // Settings events
        this.settingsBtn.addEventListener('click', () => this.showSettings());
        this.closeSettings.addEventListener('click', () => this.hideSettings());
        this.saveSettings.addEventListener('click', () => this.saveSettings());
        this.resetSettings.addEventListener('click', () => this.resetSettings());
        
        // Help events
        this.helpBtn.addEventListener('click', () => this.showHelp());
        this.closeHelp.addEventListener('click', () => this.hideHelp());
        this.closeHelpBtn.addEventListener('click', () => this.hideHelp());
        
        // Quick action events
        this.actionBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleQuickAction(e));
        });
        
        // Disclaimer events
        this.closeDisclaimer.addEventListener('click', () => this.hideDisclaimer());
        
        // Settings change events
        this.voiceSpeed.addEventListener('input', (e) => this.updateSpeedValue(e));
        this.voiceVolume.addEventListener('input', (e) => this.updateVolumeValue(e));
        
        // Panel overlay clicks
        this.settingsOverlay.addEventListener('click', (e) => {
            if (e.target === this.settingsOverlay) this.hideSettings();
        });
        this.helpOverlay.addEventListener('click', (e) => {
            if (e.target === this.helpOverlay) this.hideHelp();
        });
    }

    /**
     * Show the main application
     */
    showApp() {
        // The loading screen is removed, so the app is immediately visible
        this.app.style.display = 'block';
        this.app.style.animation = 'fadeIn 0.5s ease-out';
    }

    /**
     * Initialize conversation
     */
    initializeConversation() {
        this.conversationId = this.generateId();
        this.updateStatus('ready', 'Ready to listen');
    }

    /**
     * Start voice recording
     */
    async startRecording() {
        try {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                this.showNotification('Your browser does not support audio recording', 'error');
                return;
            }

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                await this.processAudio(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.updateRecordingUI();
            this.showNotification('Recording started', 'info');

        } catch (error) {
            console.error('Error starting recording:', error);
            this.showNotification('Failed to start recording. Please check microphone permissions.', 'error');
        }
    }

    /**
     * Stop voice recording
     */
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.updateRecordingUI();
            this.showNotification('Processing your voice input...', 'info');
        }
    }

    /**
     * Update recording UI
     */
    updateRecordingUI() {
        if (this.isRecording) {
            this.recordBtn.style.display = 'none';
            this.stopBtn.style.display = 'flex';
            this.recordingVisualizer.style.display = 'block';
            this.updateStatus('recording', 'Recording...');
        } else {
            this.recordBtn.style.display = 'flex';
            this.stopBtn.style.display = 'none';
            this.recordingVisualizer.style.display = 'none';
            this.updateStatus('processing', 'Processing...');
        }
    }

    /**
     * Process audio input
     */
    async processAudio(audioBlob) {
        try {
            this.updateStatus('processing', 'Transcribing audio...');
            
            // Create FormData for file upload
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            
            // Send to transcription API
            const response = await fetch('/api/voice/transcribe', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.text) {
                this.addUserMessage(result.text);
                await this.getAIResponse(result.text);
            } else {
                this.showNotification('Could not transcribe audio. Please try again.', 'warning');
            }

        } catch (error) {
            console.error('Error processing audio:', error);
            this.showNotification('Failed to process audio. Please try again.', 'error');
        } finally {
            this.updateStatus('ready', 'Ready to listen');
        }
    }

    /**
     * Send text message
     */
    async sendTextMessage() {
        const text = this.textInput.value.trim();
        if (!text) return;

        this.addUserMessage(text);
        this.textInput.value = '';
        await this.getAIResponse(text);
    }

    /**
     * Handle text input events
     */
    handleTextInput(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendTextMessage();
        }
    }

    /**
     * Get AI response
     */
    async getAIResponse(userMessage) {
        try {
            this.updateStatus('processing', 'Getting AI response...');
            this.isProcessing = true;

            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: userMessage,
                    conversation_id: this.conversationId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.response) {
                this.addAssistantMessage(result.response);
                
                // Auto-play audio if enabled
                if (this.autoPlay) {
                    await this.playAudioResponse(result.response);
                }
            }

        } catch (error) {
            console.error('Error getting AI response:', error);
            this.showNotification('Failed to get AI response. Please try again.', 'error');
        } finally {
            this.isProcessing = false;
            this.updateStatus('ready', 'Ready to listen');
        }
    }

    /**
     * Play audio response
     */
    async playAudioResponse(text) {
        try {
            const response = await fetch('/api/voice/synthesize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    voice_id: this.currentVoice,
                    speed: this.rate,
                    volume: this.volume
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            
            this.audioPlayer.src = audioUrl;
            this.audioPlayer.volume = this.volume;
            this.audioPlayer.playbackRate = this.rate;
            
            await this.audioPlayer.play();

        } catch (error) {
            console.error('Error playing audio:', error);
            this.showNotification('Failed to play audio response', 'warning');
        }
    }

    /**
     * Add user message to chat
     */
    addUserMessage(text) {
        const messageElement = this.createMessageElement('user', text);
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    /**
     * Add assistant message to chat
     */
    addAssistantMessage(text) {
        const messageElement = this.createMessageElement('assistant', text);
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    /**
     * Create message element
     */
    createMessageElement(type, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const header = document.createElement('div');
        header.className = 'message-header';
        
        const sender = document.createElement('span');
        sender.className = 'sender';
        sender.textContent = type === 'user' ? 'You' : 'Healthcare AI Assistant';
        
        const timestamp = document.createElement('span');
        timestamp.className = 'timestamp';
        timestamp.textContent = this.getCurrentTime();
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.innerHTML = this.formatMessageText(text);
        
        header.appendChild(sender);
        header.appendChild(timestamp);
        content.appendChild(header);
        content.appendChild(messageText);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        return messageDiv;
    }

    /**
     * Format message text (convert URLs to links, etc.)
     */
    formatMessageText(text) {
        // Convert URLs to clickable links
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        text = text.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
        
        // Convert line breaks to HTML
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }

    /**
     * Handle quick action buttons
     */
    handleQuickAction(event) {
        const question = event.currentTarget.dataset.question;
        if (question) {
            this.addUserMessage(question);
            this.getAIResponse(question);
        }
    }

    /**
     * Clear conversation
     */
    clearConversation() {
        if (confirm('Are you sure you want to clear the conversation?')) {
            this.chatMessages.innerHTML = '';
            this.conversationId = this.generateId();
            this.addWelcomeMessage();
            this.showNotification('Conversation cleared', 'info');
        }
    }

    /**
     * Add welcome message
     */
    addWelcomeMessage() {
        const welcomeMessage = `
            <p>Hello! I'm your professional healthcare AI assistant. I can help you with:</p>
            <ul>
                <li>Medical information and explanations</li>
                <li>Health guidelines and best practices</li>
                <li>Understanding medical terms</li>
                <li>General wellness advice</li>
            </ul>
            <p><strong>Important:</strong> I provide educational information only. Always consult healthcare professionals for medical advice.</p>
            <p>Click the microphone button or type your question below to get started.</p>
        `;
        
        const messageElement = this.createMessageElement('assistant', welcomeMessage);
        this.chatMessages.appendChild(messageElement);
    }

    /**
     * Export chat
     */
    exportChat() {
        const messages = Array.from(this.chatMessages.children).map(msg => {
            const type = msg.classList.contains('user') ? 'User' : 'AI Assistant';
            const text = msg.querySelector('.message-text').textContent;
            const time = msg.querySelector('.timestamp').textContent;
            return `[${time}] ${type}: ${text}`;
        }).join('\n\n');
        
        const blob = new Blob([messages], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `healthcare-ai-chat-${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showNotification('Chat exported successfully', 'success');
    }

    /**
     * Print chat
     */
    printChat() {
        const printWindow = window.open('', '_blank');
        const messages = Array.from(this.chatMessages.children).map(msg => {
            const type = msg.classList.contains('user') ? 'User' : 'AI Assistant';
            const text = msg.querySelector('.message-text').textContent;
            const time = msg.querySelector('.timestamp').textContent;
            return `<div style="margin-bottom: 20px; padding: 10px; border: 1px solid #ccc; border-radius: 5px;">
                <strong>[${time}] ${type}:</strong><br>
                ${text}
            </div>`;
        }).join('');
        
        printWindow.document.write(`
            <html>
                <head>
                    <title>Healthcare AI Chat</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .header { text-align: center; margin-bottom: 30px; }
                        .disclaimer { background: #fff3cd; padding: 15px; border: 1px solid #ffeaa7; border-radius: 5px; margin-bottom: 20px; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Healthcare AI Assistant - Chat History</h1>
                        <p>Generated on: ${new Date().toLocaleString()}</p>
                    </div>
                    <div class="disclaimer">
                        <strong>Medical Disclaimer:</strong> This AI provides educational information only. Always consult healthcare professionals for medical advice.
                    </div>
                    ${messages}
                </body>
            </html>
        `);
        
        printWindow.document.close();
        printWindow.print();
    }

    /**
     * Show settings panel
     */
    showSettings() {
        this.settingsOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    /**
     * Hide settings panel
     */
    hideSettings() {
        this.settingsOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    /**
     * Show help panel
     */
    showHelp() {
        this.helpOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    /**
     * Hide help panel
     */
    hideHelp() {
        this.helpOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    /**
     * Hide disclaimer banner
     */
    hideDisclaimer() {
        this.disclaimerBanner.style.display = 'none';
        localStorage.setItem('disclaimerHidden', 'true');
    }

    /**
     * Update status indicator
     */
    updateStatus(status, text) {
        this.statusIndicator.className = `status-indicator ${status}`;
        this.statusText.textContent = text;
        
        // Update icon based on status
        const iconMap = {
            'ready': 'fa-microphone',
            'recording': 'fa-microphone',
            'processing': 'fa-spinner fa-spin'
        };
        
        if (iconMap[status]) {
            this.statusIcon.className = `fas ${iconMap[status]}`;
        }
    }

    /**
     * Update speed value display
     */
    updateSpeedValue(event) {
        this.speedValue.textContent = `${event.target.value}x`;
        this.rate = parseFloat(event.target.value);
    }

    /**
     * Update volume value display
     */
    updateVolumeValue(event) {
        const volume = parseFloat(event.target.value);
        this.volumeValue.textContent = `${Math.round(volume * 100)}%`;
        this.volume = volume;
    }

    /**
     * Load user settings
     */
    loadSettings() {
        const settings = JSON.parse(localStorage.getItem('healthcareAISettings')) || {};
        
        this.currentVoice = settings.voice || 'elevenlabs';
        this.autoPlay = settings.autoPlay !== undefined ? settings.autoPlay : true;
        this.volume = settings.volume || 0.8;
        this.rate = settings.rate || 1.0;
        
        // Apply settings to UI
        this.voiceSelect.value = this.currentVoice;
        this.voiceSpeed.value = this.rate;
        this.voiceVolume.value = this.volume;
        this.autoPlayToggle.checked = this.autoPlay;
        this.notificationsToggle.checked = settings.notifications !== undefined ? settings.notifications : true;
        this.saveHistoryToggle.checked = settings.saveHistory !== undefined ? settings.saveHistory : true;
        this.analyticsToggle.checked = settings.analytics || false;
        this.themeSelect.value = settings.theme || 'light';
        
        this.updateSpeedValue({ target: { value: this.rate } });
        this.updateVolumeValue({ target: { value: this.volume } });
        
        // Apply theme
        this.applyTheme(settings.theme || 'light');
        
        // Check disclaimer status
        if (localStorage.getItem('disclaimerHidden') === 'true') {
            this.disclaimerBanner.style.display = 'none';
        }
    }

    /**
     * Save user settings
     */
    saveSettings() {
        const settings = {
            voice: this.voiceSelect.value,
            autoPlay: this.autoPlayToggle.checked,
            notifications: this.notificationsToggle.checked,
            saveHistory: this.saveHistoryToggle.checked,
            analytics: this.analyticsToggle.checked,
            theme: this.themeSelect.value,
            volume: this.volume,
            rate: this.rate
        };
        
        localStorage.setItem('healthcareAISettings', JSON.stringify(settings));
        
        // Apply settings
        this.currentVoice = settings.voice;
        this.autoPlay = settings.autoPlay;
        this.applyTheme(settings.theme);
        
        this.showNotification('Settings saved successfully', 'success');
        this.hideSettings();
    }

    /**
     * Reset settings to defaults
     */
    resetSettings() {
        if (confirm('Are you sure you want to reset all settings to defaults?')) {
            localStorage.removeItem('healthcareAISettings');
            this.loadSettings();
            this.showNotification('Settings reset to defaults', 'info');
        }
    }

    /**
     * Apply theme
     */
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Trigger animation
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Auto-remove
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    /**
     * Scroll chat to bottom
     */
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    /**
     * Get current time
     */
    getCurrentTime() {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    /**
     * Generate unique ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check for browser compatibility
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Your browser does not support audio recording. Please use a modern browser.');
        return;
    }

    // Initialize the voice AI assistant
    window.healthcareAI = new HealthcareVoiceAI();

    // Add some helpful console messages
    console.log('Healthcare Voice AI Assistant initialized');
    console.log('Use window.healthcareAI to access the assistant instance');
});

// Add notification styles dynamically
const notificationStyles = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        max-width: 300px;
        word-wrap: break-word;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .notification.show {
        transform: translateX(0);
    }

    .notification-info {
        background: #3b82f6;
    }

    .notification-success {
        background: #10b981;
    }

    .notification-warning {
        background: #f59e0b;
    }

    .notification-error {
        background: #ef4444;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);
