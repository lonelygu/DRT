from flask import Flask, render_template, request
from settings import DB_NAME
import requests
import json
import sqlite3
from urllib.parse import urlparse


app = Flask(__name__)

@app.route('/')
@app.route('/main')  # Главная страница
def main():
    return render_template('main.html')

@app.route('/base')  # Главная страница
def base():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT links.name, links.url, links.truth
        FROM links;
    """)
    rows = cursor.fetchall()
    db_response = [
        {"name": row[0], "url": row[1], "truth": "Фейк" if row[2] == 1 else "Правда" if row[2] == 0 else "Неизвестно"}
        for row in rows
    ]
    conn.close()
    return render_template('base.html', resources=db_response)

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

def save_to_database(source, is_fake):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM links WHERE url = ?', (source,))
    link = cursor.fetchone()

    if link is None:
        cursor.execute('INSERT INTO links (name, url, truth) VALUES (?, ?, ?)', (source, source, 2))
        link_id = cursor.lastrowid
    else:
        link_id = link[0]

    cursor.execute('SELECT id FROM stats WHERE link_id = ?', (link_id,))
    stat = cursor.fetchone()

    if stat is None:
        if is_fake:
            cursor.execute('INSERT INTO stats (link_id, fake_count, not_fake_count) VALUES (?, ?, ?)', (link_id, 1, 0))
        else:
            cursor.execute('INSERT INTO stats (link_id, fake_count, not_fake_count) VALUES (?, ?, ?)', (link_id, 0, 1))
    else:
        if is_fake:
            cursor.execute('UPDATE stats SET fake_count = fake_count + 1 WHERE link_id = ?', (link_id,))
        else:
            cursor.execute('UPDATE stats SET not_fake_count = not_fake_count + 1 WHERE link_id = ?', (link_id,))

    cursor.execute('SELECT id, fake_count, not_fake_count FROM stats WHERE link_id IN (SELECT id FROM links WHERE truth = 2)')
    records = cursor.fetchall()

    for record in records:
        total_count = record[1] + record[2]
        if total_count > 10:
            fake_percentage = record[1] / total_count
            if fake_percentage > 0.9:
                cursor.execute('UPDATE links SET truth = 1 WHERE id = ?', (record[0],))
            else:
                cursor.execute('UPDATE links SET truth = 0 WHERE id = ?', (record[0],))

    conn.commit()
    conn.close()

@app.route('/check', methods=['GET', 'POST'])  # Страница проверки текста
def check():
    if request.method == 'POST':
        article = request.form['article']  # Получаем текст статьи из формы
        source = request.form['source-input']
        if source:
            parsed_url = urlparse(source)
            if parsed_url.netloc == "t.me":
                source = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            else:
                source = f"{parsed_url.scheme}://{parsed_url.netloc}"

        data = {
            "article": article  # Передаем введенный текст статьи
        }

        # URL API
        url = "https://fastapi-service:5000/predict"

        # Отправка POST-запроса
        response = requests.post(url, json=data)
        proof = None
        # Проверка ответа
        if response.status_code == 200:
            api_response = response.json()  # Получаем ответ от API в формате JSON
            if api_response.get("predicted_class") == "Фейк":
                if source:
                    save_to_database(source, is_fake=True)
                proof = build_request(article=article)
            else:
                if source:
                    save_to_database(source, is_fake=False)
            return render_template('check.html', article=article, proof=proof, api_response=api_response)
        else:
            return render_template('check.html', article=article, api_response={"error": "Ошибка при запросе к API"})

    return render_template('check.html')

if __name__ == "__main__":
    app.run(port=3000)
