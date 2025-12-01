// Fonction pour envoyer un message
async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Afficher le message de l'utilisateur
    displayUserMessage(message);
    
    // Vider l'input
    input.value = '';
    
    // Afficher l'indicateur de frappe
    showTypingIndicator();
    
    try {
        // Envoyer la requête au backend Flask
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // Cacher l'indicateur de frappe
        hideTypingIndicator();
        
        // Afficher la réponse du bot avec suggestions
        displayBotMessage(data.response, data.suggestions || []);
        
    } catch (error) {
        console.error('Erreur:', error);
        hideTypingIndicator();
        displayBotMessage('Désolé, une erreur s\'est produite. Veuillez réessayer.', []);
    }
}

// Fonction pour afficher un message utilisateur
function displayUserMessage(message) {
    const chatMessages = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${escapeHtml(message)}</p>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Fonction pour afficher un message du bot
function displayBotMessage(message, suggestions = []) {
    const chatMessages = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    let suggestionsHtml = '';
    if (suggestions.length > 0) {
        suggestionsHtml = '<div class="suggestions">';
        suggestions.forEach(suggestion => {
            suggestionsHtml += `<button class="suggestion-btn" onclick="sendSuggestion('${escapeHtml(suggestion)}')">${escapeHtml(suggestion)}</button>`;
        });
        suggestionsHtml += '</div>';
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${formatMessage(message)}</p>
            ${suggestionsHtml}
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Fonction pour formater le message (gère les emojis et le formatage)
function formatMessage(message) {
    // Remplace les sauts de ligne par des <br>
    message = escapeHtml(message);
    message = message.replace(/\n/g, '<br>');
    
    // Gère le gras avec **texte**
    message = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    return message;
}

// Fonction pour échapper le HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Fonction pour envoyer une suggestion
function sendSuggestion(suggestion) {
    const input = document.getElementById('userInput');
    input.value = suggestion;
    sendMessage();
}

// Fonction pour afficher l'indicateur de frappe
function showTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    typingIndicator.style.display = 'block';
    scrollToBottom();
}

// Fonction pour cacher l'indicateur de frappe
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    typingIndicator.style.display = 'none';
}

// Fonction pour scroller vers le bas
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

// Gérer la touche Entrée
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// Focus sur l'input au chargement
window.addEventListener('load', () => {
    document.getElementById('userInput').focus();
});