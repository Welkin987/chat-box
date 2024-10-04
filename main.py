from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
import os
import json
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)

# Set up API key for the external GPT service
api_key = os.getenv("API_KEY")

# Get model, API URL, and assistant name from environment variables
model = os.getenv("GPT_MODEL")
api_url = os.getenv("GPT_API_URL")
assistant_name = os.getenv("ASSISTANT_NAME")
if_context = os.getenv("IF_CONTEXT")

headers = {
    "Authorization": f'Bearer {api_key}'
}

# Define function to get the current date for history file
def get_history_date():
    current_time = datetime.now()
    if current_time.hour < 4:
        current_time -= timedelta(days=1)
    return current_time.strftime("%Y%m%d")

# Load or create history file
history_folder = "history"
os.makedirs(history_folder, exist_ok=True)

history_date = get_history_date()
history_file_path = os.path.join(history_folder, f"{history_date}.json")

def initialize_conversation_history():
    history = []
    if assistant_name:
        prompt_path = os.path.join("assistants", assistant_name, "prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                system_prompt = f.read().strip()
                if system_prompt:
                    history.append({"role": "system", "content": system_prompt})
                    print(f"System prompt added to conversation history: {system_prompt}")
                else:
                    print("No system prompt found in the assistant folder.")
    return history

if os.path.exists(history_file_path):
    with open(history_file_path, 'r', encoding='utf-8') as f:
        conversation_history = json.load(f)
    print(f"Loaded existing conversation history from {history_file_path}")
else:
    conversation_history = initialize_conversation_history()
    with open(history_file_path, 'w', encoding='utf-8') as f:
        json.dump(conversation_history, f, ensure_ascii=False)
    print(f"Initialized new conversation history and saved to {history_file_path}")

@app.route('/assistants/<path:filename>')
def custom_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'assistants'), filename)

@app.route('/')
def index():
    print("Rendering index page...")
    return render_template('index.html', history=conversation_history, assistant_name=assistant_name)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        print("No message provided by the user.")
        return jsonify({'error': 'No message provided'}), 400

    # Add user message to conversation history
    conversation_history.append({"role": "user", "content": user_message})
    print(f"1/4 User message added to conversation history: {user_message}")

    try:
        # Prepare the request payload
        if if_context.lower() == 'true':
            messages = conversation_history
        else:
            messages = [msg for msg in conversation_history if msg['role'] == 'system'] + [conversation_history[-1]]
        
        params = {
            "messages": messages,
            "model": model
        }
        print("2/4 Sending request to GPT service...")
        # Make a request to the external GPT service
        response = requests.post(
            api_url,
            headers=headers,
            json=params,
            stream=False
        )
        print("3/4 Received response from GPT service.")
        response_data = response.json()

        # Extract AI response and add to conversation history
        ai_message = response_data['choices'][0]['message']['content']
        conversation_history.append({"role": "assistant", "content": ai_message})
        print(f"4/4 AI message added to conversation history: {ai_message}")

        # Save updated conversation history
        with open(history_file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, ensure_ascii=False)

        return jsonify({'message': ai_message})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/save', methods=['POST'])
def save():
    print("1/2 Saving conversation...")
    request_data = request.json
    filename = request_data.get('filename')
    if filename:
        archive_folder = "archive"
        os.makedirs(archive_folder, exist_ok=True)
        archive_file_path = os.path.join(archive_folder, filename)
        try:
            with open(archive_file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_history, f, ensure_ascii=False)
            print("2/2 Conversation saved successfully.")
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': False, 'error': 'No filename provided'}), 400

@app.route('/clear', methods=['POST'])
def clear():
    print("1/3 Clearing conversation...")
    try:
        global conversation_history
        conversation_history = initialize_conversation_history()
        with open(history_file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, ensure_ascii=False)
        print("2/3 Conversation cleared successfully.")
        print(f"3/3 New conversation history: {conversation_history}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True, port=5000)