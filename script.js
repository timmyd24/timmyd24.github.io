// script.js

// Conversation context
let messages = [];

const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const messagesContainer = document.getElementById('messages');

sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', function (e) {
  if (e.key === 'Enter') {
    sendMessage();
  }
});

function addMessage(role, content) {
  const messageElement = document.createElement('div');
  messageElement.classList.add('message', role);

  const textElement = document.createElement('div');
  textElement.classList.add('text');
  textElement.textContent = content;

  messageElement.appendChild(textElement);
  messagesContainer.appendChild(messageElement);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function sendMessage() {
  const content = userInput.value.trim();
  if (content === '') return;

  addMessage('user', content);
  messages.push({ role: 'user', content: content });
  userInput.value = '';

  // Loading indicator
  const loadingMessage = document.createElement('div');
  loadingMessage.classList.add('message', 'assistant');
  const loadingText = document.createElement('div');
  loadingText.classList.add('text');
  loadingText.textContent = '...';
  loadingMessage.appendChild(loadingText);
  messagesContainer.appendChild(loadingMessage);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  try {
    const response = await fetch('https://openai-assistant-backend.onrender.com', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        assistantId: 'asst_9a6yDuEuNxDaZFcSkIIySRIx',
        messages: messages,
      }),
    });

    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    const assistantMessage = data.message;
    messages.push({ role: 'assistant', content: assistantMessage });

    // Remove loading indicator and add actual message
    messagesContainer.removeChild(loadingMessage);
    addMessage('assistant', assistantMessage);
  } catch (error) {
    console.error('Error:', error);
    messagesContainer.removeChild(loadingMessage);
    addMessage('assistant', 'Sorry, an error occurred.');
  }
}
