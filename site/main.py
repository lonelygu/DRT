from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route('/')
@app.route('/main')  # Главная страница
def main():
    return render_template('main.html')

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

        # Проверка ответа
        if response.status_code == 200:
            api_response = response.json()  # Получаем ответ от API в формате JSON
            return render_template('check.html', article=article, api_response=api_response)
        else:
            return render_template('check.html', article=article, api_response={"error": "Ошибка при запросе к API"})

    return render_template('check.html')

if __name__ == "__main__":
    app.run()