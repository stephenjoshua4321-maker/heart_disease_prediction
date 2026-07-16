// Enterprise Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Theme Toggle
    const themeToggle = document.getElementById('themeToggle');
    themeToggle.addEventListener('click', function(e) {
        e.preventDefault();
        document.body.classList.toggle('dark-mode');
        const icon = this.querySelector('i');
        if (document.body.classList.contains('dark-mode')) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
            this.innerHTML = '<i class="fas fa-sun"></i> Light Mode';
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
            this.innerHTML = '<i class="fas fa-moon"></i> Dark Mode';
        }
    });
    
    // Age progress bar
    const ageInput = document.querySelector('input[name="Age"]');
    if (ageInput) {
        ageInput.addEventListener('input', function() {
            const age = parseInt(this.value) || 0;
            const progress = Math.min((age / 100) * 100, 100);
            document.querySelector('.age-progress').style.width = progress + '%';
            
            // Update target heart rate
            if (age > 0) {
                const targetHR = 220 - age;
                document.querySelector('.target-hr').textContent = 
                    `Target Max HR: ${targetHR} bpm`;
            }
        });
    }
    
    // BP Gauge
    const bpInput = document.querySelector('input[name="BP"]');
    if (bpInput) {
        bpInput.addEventListener('input', function() {
            const bp = parseInt(this.value) || 120;
            const progress = Math.min((bp / 200) * 100, 100);
            document.querySelector('.bp-gauge .gauge-fill').style.width = progress + '%';
            
            // Color code based on BP level
            const gauge = document.querySelector('.bp-gauge .gauge-fill');
            if (bp < 120) {
                gauge.style.background = 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)';
            } else if (bp < 130) {
                gauge.style.background = 'linear-gradient(135deg, #fad0c4 0%, #ff9a9e 100%)';
            } else {
                gauge.style.background = 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
            }
        });
    }
    
    // Cholesterol indicator
    const cholesterolInput = document.querySelector('input[name="Cholesterol"]');
    if (cholesterolInput) {
        cholesterolInput.addEventListener('input', function() {
            const value = parseInt(this.value) || 0;
            const indicator = document.querySelector('.cholesterol-indicator');
            
            if (value < 200) {
                indicator.innerHTML = '✅ Normal';
                indicator.style.color = 'green';
            } else if (value < 240) {
                indicator.innerHTML = '⚠️ Borderline High';
                indicator.style.color = 'orange';
            } else {
                indicator.innerHTML = '❌ High';
                indicator.style.color = 'red';
            }
        });
    }
    
    // Voice Input
    const startVoiceBtn = document.getElementById('startVoice');
    if (startVoiceBtn) {
        startVoiceBtn.addEventListener('click', function() {
            this.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Listening...';
            this.disabled = true;
            
            // Simulate voice recognition (in production, use Web Speech API)
            setTimeout(() => {
                const transcript = "Age 55, male, chest pain type 2, blood pressure 130...";
                document.querySelector('.voice-transcript').innerHTML = 
                    `<div class="alert alert-success">Recognized: ${transcript}</div>`;
                this.innerHTML = '<i class="fas fa-microphone"></i> Start Speaking';
                this.disabled = false;
                
                // Auto-fill form with recognized data
                autoFillForm(transcript);
            }, 3000);
        });
    }
    
    // File Upload with Drag & Drop
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    
    if (dropZone && fileInput) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            dropZone.classList.add('highlight');
        }
        
        function unhighlight() {
            dropZone.classList.remove('highlight');
        }
        
        dropZone.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        }
        
        fileInput.addEventListener('change', function() {
            handleFiles(this.files);
        });
        
        function handleFiles(files) {
            dropZone.innerHTML = '<i class="fas fa-spinner fa-spin fa-3x"></i><p>Processing...</p>';
            
            // Simulate file processing
            setTimeout(() => {
                dropZone.innerHTML = `
                    <i class="fas fa-check-circle fa-3x text-success"></i>
                    <p>Files uploaded successfully!</p>
                    <small>Extracted data from PDF reports</small>
                `;
            }, 2000);
        }
    }
    
    // Wearable Sync
    const syncWearable = document.getElementById('syncWearable');
    if (syncWearable) {
        syncWearable.addEventListener('click', function() {
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
            this.disabled = true;
            
            // Simulate sync
            setTimeout(() => {
                // Fetch latest data from API
                fetch('/api/wearable-data')
                    .then(response => response.json())
                    .then(data => {
                        showNotification('Wearable data synced successfully!', 'success');
                        autoFillFromWearable(data);
                        this.innerHTML = '<i class="fas fa-sync"></i> Sync Now';
                        this.disabled = false;
                    });
            }, 2000);
        });
    }
    
    // AI Chatbot
    const chatInput = document.getElementById('chatInput');
    const sendMessage = document.getElementById('sendMessage');
    const voiceMessage = document.getElementById('voiceMessage');
    const chatContainer = document.getElementById('chatContainer');
    
    if (sendMessage && chatInput) {
        sendMessage.addEventListener('click', function() {
            sendChatMessage();
        });
        
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
    
    if (voiceMessage) {
        voiceMessage.addEventListener('click', function() {
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            // Simulate voice input
            setTimeout(() => {
                chatInput.value = "What is my risk of heart disease?";
                this.innerHTML = '<i class="fas fa-microphone"></i>';
                sendChatMessage();
            }, 2000);
        });
    }
    
    function sendChatMessage() {
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message
        addChatMessage(message, 'user');
        chatInput.value = '';
        
        // Show typing indicator
        const typingId = showTypingIndicator();
        
        // Get AI response
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                context: getUserContext()
            })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator(typingId);
            addChatMessage(data.response, 'bot');
        })
        .catch(error => {
            removeTypingIndicator(typingId);
            addChatMessage("I'm having trouble connecting. Please try again.", 'bot');
        });
    }
    
    function addChatMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        messageDiv.innerHTML = `
            <div class="message-content">
                ${message}
            </div>
        `;
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message bot';
        typingDiv.id = id;
        typingDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-circle-notch fa-spin"></i> AI is thinking...
            </div>
        `;
        chatContainer.appendChild(typingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return id;
    }
    
    function removeTypingIndicator(id) {
        const element = document.getElementById(id);
        if (element) {
            element.remove();
        }
    }
    
    // Multi-language Support
    document.querySelectorAll('.language-select').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const lang = this.dataset.lang;
            
            // Get page text and translate
            const textToTranslate = document.body.innerText;
            
            fetch('/api/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: textToTranslate,
                    lang: lang
                })
            })
            .then(response => response.json())
            .then(data => {
                showNotification(`Language changed to ${this.textContent}`, 'info');
                // In production, you would update the DOM with translated text
            });
        });
    });
    
    // Form Validation with Animation
    const form = document.getElementById('predictionForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const inputs = form.querySelectorAll('input[required], select[required]');
            
            inputs.forEach(input => {
                if (!input.value) {
                    isValid = false;
                    input.classList.add('is-invalid');
                    shake(input);
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showNotification('Please fill all required fields', 'error');
            } else {
                showNotification('Analyzing with AI...', 'info');
            }
        });
    }
    
    // Reset Form
    const resetBtn = document.getElementById('resetForm');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            form.reset();
            showNotification('Form reset successfully', 'success');
        });
    }
    
    // Helper Functions
    function shake(element) {
        element.style.animation = 'shake 0.5s';
        setTimeout(() => {
            element.style.animation = '';
        }, 500);
    }
    
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} notification`;
        notification.innerHTML = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            animation: slideIn 0.5s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.5s ease-out';
            setTimeout(() => {
                notification.remove();
            }, 500);
        }, 3000);
    }
    
    function autoFillForm(transcript) {
        // Simulate auto-filling form from voice transcript
        const inputs = {
            'Age': '55',
            'Sex': '1',
            'Chest pain type': '2',
            'BP': '130',
            'Cholesterol': '210'
        };
        
        for (let [name, value] of Object.entries(inputs)) {
            const input = document.querySelector(`[name="${name}"]`);
            if (input) {
                input.value = value;
                input.dispatchEvent(new Event('input'));
            }
        }
    }
    
    function autoFillFromWearable(data) {
        // Auto-fill form from wearable data
        if (data.heart_rate) {
            const hrInput = document.querySelector('input[name="Max HR"]');
            if (hrInput) hrInput.value = data.heart_rate;
        }
        
        if (data.blood_pressure) {
            const bpInput = document.querySelector('input[name="BP"]');
            if (bpInput) bpInput.value = data.blood_pressure;
        }
        
        showNotification('Form updated with wearable data!', 'success');
    }
    
    function getUserContext() {
        // Get current form data for context
        const context = {};
        document.querySelectorAll('[name]').forEach(input => {
            context[input.name] = input.value;
        });
        return JSON.stringify(context);
    }
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .highlight {
        background: rgba(102, 126, 234, 0.1);
        border-color: #667eea;
    }
`;
document.head.appendChild(style);