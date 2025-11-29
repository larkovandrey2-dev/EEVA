import os

import requests
import json
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('API_KEY')
CATALOG = "gpt://b1gcbn4fh3ils5usalqv/yandexgpt-5-pro/latest"

class YandexGPT:
    def __init__(self):
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.headers = {
            "Authorization": f"Api-Key {API_KEY}",
            "Content-Type": "application/json"
        }

    def generate_offer(self, segment, product_name, reason, context_trigger):
        """
        Генерирует короткий продающий пуш.
        """
        # ПРОМПТ - Это самое важное. Задаем роль дерзкого маркетолога.
        system_text = "Ты — опытный копирайтер банковского приложения. Твоя задача — писать короткие, цепляющие пуш-уведомления (до 15 слов). Тон: дружелюбный, но уверенный. Не используй слова 'Уважаемый клиент' или 'Предлагаем вам'."

        user_text = f"""
                Напиши текст для пуш-уведомления.

                ВВОДНЫЕ:
                1. Продукт: "{product_name}" (Пиши только про него!)
                2. Повод: {reason}
                3. Клиент: {segment}

                ЗАПРЕТЫ:
                - Не выдумывай кешбэк или проценты, если их нет в названии.
                - Не пиши "Уважаемый клиент".
                - Если повод "после АЗС", а продукт "Автокредит", свяжи их логически ("Заправляйтесь и обновите авто").
                """

        prompt = {
            "modelUri": CATALOG,
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": 100
            },
            "messages": [
                {"role": "system", "text": system_text},
                {"role": "user", "text": user_text}
            ]
        }

        try:
            response = requests.post(self.url, headers=self.headers, json=prompt, timeout=3)
            if response.status_code != 200:
                return f"Рекомендуем: {product_name}"

            result = response.json()
            text = result['result']['alternatives'][0]['message']['text']
            return text.strip().replace('"', '')

        except:
            return f"Ваше персональное предложение: {product_name}"