from flask import Flask, render_template, request
import requests
import json

app = Flask(__name__)

@app.route('/')
@app.route('/main')  # Главная страница
def main():
    return render_template('main.html')

def build_request(article):
    prompt = f"""
    ===Instruction
    Твоя задача на основании контекста привести доводы почему статья является фейком... 

    ===Context
    Статья: {article}
    
    ===Output
    Response must be JSON only without additional text
    {{
      "proof": "Объяснение" 
    }}

    ===Response
    """

    requestBody = {
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "system", "content": "You are ChatGPT, a helpful assistant."},
        {"role": "user", "content": prompt}
    ],
    "max_tokens": 500,
    "temperature": 0.7
    }

    url = 'https://api.proxyapi.ru/openai/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer sk-8hMBBWM4X1IjBUIKT4pfXAtqYInRTF44'
    }

    response = requests.post(url, headers=headers, json=requestBody)

    if response.status_code == 200:
        api_response = response.json()
        resp = api_response['choices'][0]['message']['content']
        resp_json = json.loads(resp)
        proof = resp_json['proof']
        return proof
    else:
        print({"error": "Ошибка при запросе к API"})

@app.route('/check', methods=['GET', 'POST'])  # Страница проверки текста
def check():
    if request.method == 'POST':
        article = request.form['article']  # Получаем текст статьи из формы

        data = {
            "article": article  # Передаем введенный текст статьи
        }

        # URL API
        url = "https://apitest-vh69sn31.b4a.run/predict"

        # Отправка POST-запроса
        response = requests.post(url, json=data)
        proof = None
        # Проверка ответа
        if response.status_code == 200:
            api_response = response.json()  # Получаем ответ от API в формате JSON
            if api_response.get("predicted_class") == "Фейк":
                proof = build_request(article=article)
            return render_template('check.html', article=article, proof=proof, api_response=api_response)
        else:
            return render_template('check.html', article=article, api_response={"error": "Ошибка при запросе к API"})

    return render_template('check.html')

if __name__ == "__main__":
    app.run()