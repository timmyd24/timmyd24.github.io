from flask import Flask, jsonify, request, render_template
import openai

app = Flask(__name__)

# OpenAI API Key
openai.api_key = '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'

# Pre-created assistant and thread IDs
ASSISTANT_ID = 'asst_9a6yDuEuNxDaZFcSkIIySRIx'
THREAD_ID =

# Route: login page
@app.route('/')
def login():
    return render_template('login.html')

# Route: home page with the chatbot
@app.route('/chat')
def home():
    return render_template('index.html')

# Route to handle the frontend request
@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form['user_input']

    try:
        # Adds a message to the existing thread
        message_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": user_input}
            ]
        )

        # Retrieves the assistant's message
        bot_response = message_response['choices'][0]['message']['content']

        return jsonify({'response': bot_response})

    except Exception as e:
        print(f"Error in request to the assistant: {str(e)}")
        return jsonify({'response': 'Sorry, an error occurred in the request.'})

if __name__ == '__main__':
    app.run(debug=True)
