from aiogram import Bot, Dispatcher
from aiogram.types import Message, BotCommand, BotCommandScopeDefault
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters import Command

from telegramtoken import token

import asyncio
import requests
import json

text = ("Мы представляем вам сервис: FactSeeker\nНи для кого не секрет, что актуальность проблемы распространения фейков в интернете в наше время достигла своего пика."
        " Все мы ежедневно сталкиваемся с ложными новостями, и не всегда задумываемся, насколько негативно, они могут повлиять на наше общество."
        " А ведь известно множество случаев по всему миру, когда люди верили и распространяли фейковые новости, тем самым провоцируя межнациональные конфликты или финансовые кризисы.")

async def set_commands(bot: Bot):
    commands = [
        BotCommand(
            command="start",
            description="Начало работы",

        ),
        BotCommand(
            command="check",
            description="Проверка текста",

        )

    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

# Buttons_common
def button_builder(Button):
    keyboard_builder = ReplyKeyboardBuilder()
    for button_name in Button:
        keyboard_builder.button(text=button_name)
    return keyboard_builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

async def get_start(message: Message, bot: Bot):
    await set_commands(bot)
    await asyncio.sleep(0.5)
    await message.answer(f"Здравствуйте {message.from_user.first_name} {text}\n Вы можете проверить любую информацию с помощью /check $info")


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

async def get_truth(message: Message, bot: Bot):
    article = message.text  # Получаем текст статьи
    if message.text.strip() != "/check":
        # Формируем данные для отправки на API
        data = {
            "article": article
        }

        url = "https://fakeapi-49bf0c6b.b4a.run/predict"
        try:
            # Отправляем запрос к API
            response = requests.post(url, json=data)
            proof = None
            # Проверяем ответ
            if response.status_code == 200:
                api_response = response.json()
                if api_response.get("predicted_class") == "Фейк":
                    proof = build_request(article=article)
                    result_text = f"⚠️ Эта статья выглядит как фейк.\n\nОбъяснение: {proof}"
                else:
                    result_text = "✅ Эта статья не является фейком."
            else:
                result_text = "Произошла ошибка при обращении к API. Попробуйте снова позже."
        except Exception as e:
            result_text = f"Произошла ошибка при запросе к API:{e}"
    else:
        result_text = "Введите текст после /check"

    # Отправляем результат обратно пользователю
    await message.answer(result_text)


async def start():
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.message.register(get_start, Command(commands=["start"]))
    dp.message.register(get_truth, Command(commands=["check"]))
    try:
        await dp.start_polling(bot, allowed_updates=['message', 'callback_query'])
    except asyncio.exceptions.CancelledError:
        print("Программа завершена")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(start())
