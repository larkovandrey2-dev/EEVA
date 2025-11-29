import os

import requests
import json
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('API_KEY')


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
        system_text = "Ты — опытный копирайтер банковского приложения. Твоя задача — писать короткие, цепляющие пуш-уведомления (до 15 слов). Используй 1 эмодзи. Тон: дружелюбный, но уверенный. Не используй слова 'Уважаемый клиент' или 'Предлагаем вам'."

        user_text = f"""
        Вводные данные:
        - Сегмент клиента: {segment}
        - Триггер (почему предлагаем): {context_trigger}
        - Обоснование: {reason}
        - Продукт: {product_name}

        Напиши текст уведомления, чтобы клиент захотел нажать.
        """

        prompt = {
            "modelUri": "gpt://b1gcbn4fh3ils5usalqv/yandexgpt-5-pro/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,  # Креативность (0.7 - оптимально)
                "maxTokens": 100
            },
            "messages": [
                {"role": "system", "text": system_text},
                {"role": "user", "text": user_text}
            ]
        }

        try:
            # Делаем запрос с таймаутом 3 секунды (чтобы UI не вис)
            response = requests.post(self.url, headers=self.headers, json=prompt, timeout=3)

            if response.status_code != 200:
                print(f"⚠️ YaGPT Error: {response.status_code} - {response.text}")
                return self._fallback(product_name)

            result = response.json()
            text = result['result']['alternatives'][0]['message']['text']
            return text.strip().replace('"', '')

        except Exception as e:
            print(f"⚠️ YaGPT Exception: {e}")
            return self._fallback(product_name)

    def _fallback(self, product_name):
        """Заглушка, если API не ответил"""
        return f"Специально для вас: {product_name}. Узнайте подробности!"