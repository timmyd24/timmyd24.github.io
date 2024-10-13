// script.js

let messages = [];

const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');

sendButton.addEventListener('click', sendMessage);

userInput.addEventListener('keypress', function (e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

function addMessage(role, content) {
  const messageElement = document.createElement('div');
  messageElement.classList.add('message', role);

  const messageContent = document.createElement('div');
  messageContent.classList.add('message-content');
  messageContent.innerHTML = content;

  messageElement.appendChild(messageContent);
  chatHistory.appendChild(messageElement);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function sendMessage() {
  const content = userInput.value.trim();
  if (content === '') return;

  addMessage('user', content);
  messages.push({ role: 'user', content: content });
  userInput.value = '';
  userInput.style.height = 'auto';

  // Loading indicator
  const loadingMessage = document.createElement('div');
  loadingMessage.classList.add('message', 'assistant');

  const loadingContent = document.createElement('div');
  loadingContent.classList.add('message-content', 'loading-dots');
  loadingContent.textContent = 'Assistant is typing';

  loadingMessage.appendChild(loadingContent);
  chatHistory.appendChild(loadingMessage);
  chatHistory.scrollTop = chatHistory.scrollHeight;

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

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    const assistantMessage = data.message;
    messages.push({ role: 'assistant', content: assistantMessage });

    // Update the loading message with the assistant's response
    loadingContent.classList.remove('loading-dots');
    loadingContent.textContent = assistantMessage;
  } catch (error) {
    console.error('Error:', error);
    loadingContent.classList.remove('loading-dots');
    loadingContent.textContent = `Error: ${error.message}`;
  }
}

// Auto-resize the textarea
userInput.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = `${userInput.scrollHeight}px`;
});
