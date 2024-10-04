@echo off
call venv\Scripts\activate
set FLASK_APP=main.py
set API_KEY=YOUR-API-KEY
set ASSISTANT_NAME=ChatGPT
set IF_CONTEXT=true
set GPT_API_URL=https://api.openai.com
set GPT_MODEL=gpt-4o-2024-08-06
start http://127.0.0.1:5000
python main.py
@pause