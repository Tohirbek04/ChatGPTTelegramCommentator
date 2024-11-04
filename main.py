from telethon.sync import TelegramClient
import requests
from dotenv import load_dotenv
import os
import time
import json
import re

load_dotenv()


class Telegram_Commentator:
    def __init__(self):
        # List of post URLs to comment on
        self.posts: list = [
            'https://t.me/pulatov_kh/2577',
            'https://t.me/pulatov_kh/2576',
            # 'https://t.me/pulatov_kh/2574',
            # 'https://t.me/pulatov_kh/2570'
        ]
        self.openrouter_api_key = os.getenv("OpenAI_token")
        self.api_id: int = os.getenv('Api_id')
        self.api_hash: str = os.getenv('Api_hash')
        self.owner_ID: str = os.getenv('Owner_id')
        self.client = None
        self.your_site_url = "https://your-site-url.com"  # Replace with your site's URL
        self.your_site_name = "Your Site Name"  # Replace with your site's name

    def start_telegram_client(self):
        self.client = TelegramClient('session_name', self.api_id, self.api_hash)
        self.client.start()

    def generate_comment(self, post_text):
        # Add analysis context to understand the post
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "HTTP-Referer": self.your_site_url,
            "X-Title": self.your_site_name,
            "Content-Type": "application/json"
        }

        # To analyze the tone and key points of the post
        sentiment_analysis = "Yakuniy talqin: Ushbu post ijobiymi yoki salbiy? Qanday asosiy fikrlar bor?"

        data = {
            "model": "openai/gpt-4-turbo-preview",
            "messages": [
                {
                    "role": "system",
                    "content": "Вы патриот России и девушка. Пишите осмысленные человекоподобные яркие комментарии до 11 слов."
                },
                {
                    "role": "user",
                    "content": f"Проанализируйте этот пост и создайте комментарий в таком же контексте. Пост: {post_text}\n{sentiment_analysis}"
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
            else:
                return "Даже не знаю, что тут сказать...."
        except Exception as e:
            print(f"Ошибка при генерации комментария: {e}")
            return "test"

    def write_comments_in_telegram(self):
        for post_url in self.posts:
            try:
                # Extract channel name and post ID from the URL
                match = re.match(r'https?://t\.me/([^/]+)/(\d+)', post_url)
                if not match:
                    print(f"Неверный URL поста: {post_url}")
                    continue
                channel_name = match.group(1)
                post_id = int(match.group(2))

                # Get the channel entity
                channel_entity = self.client.get_entity(channel_name)

                # Get the message (post)
                post = self.client.get_messages(channel_entity, ids=post_id)

                if post:
                    output = self.generate_comment(post.raw_text)
                    try:
                        time.sleep(25)
                        self.client.send_message(entity=channel_entity, message=output, comment_to=post_id)
                        self.client.send_message(f'{self.owner_ID}',
                                                 f'Комментарий отправлен!\nСсылка на пост: <a href="{post_url}">{channel_name}</a>\nСам пост: {post.raw_text[:90]}\nНаш коммент: {output}',
                                                 parse_mode="html")
                        print('Успешно отправлен комментарий, проверьте личные сообщения')
                    except Exception as e:
                        self.client.send_message(f'{self.owner_ID}',
                                                 f"Ошибка при отправке комментария к посту '{post_url}': {e}")
                        print('Ошибка, проверьте личные сообщения')
                    finally:
                        time.sleep(25)
                else:
                    print(f"Не удалось получить пост с ID {post_id} из канала {channel_name}")
            except Exception as e:
                self.client.send_message(f'{self.owner_ID}', f"Ошибка при обработке поста '{post_url}': {e}")
                print("Ошибка, проверьте личные сообщения")
                continue

    def run(self):
        self.start_telegram_client()
        self.write_comments_in_telegram()


# Run the script
if __name__ == "__main__":
    AI_commentator = Telegram_Commentator()
    AI_commentator.run()
