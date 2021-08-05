import os
import unittest
from time import sleep

from dotenv import load_dotenv

load_dotenv()

from telethon import TelegramClient, events, sync

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")


class TestKaltentBot(unittest.TestCase):
    """Настройка теста, инициализация клиента"""

    @classmethod
    def setUpClass(cls):
        cls.client = TelegramClient("session_name", API_ID, API_HASH)
        cls.client.start()
        cls.client.run_until_disconnected

    def test_start_message_function(self):
        """Тест проверяет, верное ли сообщение возваращает бот
        при команде /start"""
        self.client.send_message("@KaltentBot", "/start")
        sleep(0.5)
        messages = self.client.get_messages("@KaltentBot")
        bttn_continue = messages[0].reply_markup.rows[0].buttons[0].text
        self.assertEqual("Продолжаем?", messages[0].message)
        self.assertEqual("🐾 Продолжить", bttn_continue)

    def test_selects_actions_function(self):
        """Тест проверяет, верное ли сообщение возваращает бот
        при команде /menu, а так же проверяет кнопки"""
        self.client.send_message("@KaltentBot", "/menu")
        sleep(0.5)
        messages = self.client.get_messages("@KaltentBot")
        bttn_watch_content = messages[0].reply_markup.rows[0].buttons[0].text
        bttn_add_video = messages[0].reply_markup.rows[1].buttons[0].text
        bttn_add_channel = messages[0].reply_markup.rows[2].buttons[0].text
        bttn_show_videos = messages[0].reply_markup.rows[3].buttons[0].text
        bttn_show_channels = messages[0].reply_markup.rows[4].buttons[0].text
        self.assertEqual("Чего желаете?", messages[0].message)
        self.assertEqual("🍻 Смотреть контент", bttn_watch_content)
        self.assertEqual("📀 Добавить видео", bttn_add_video)
        self.assertEqual("📹 Добавить канал", bttn_add_channel)
        self.assertEqual("👀 Показать все видео", bttn_show_videos)
        self.assertEqual("👀 Показать все каналы", bttn_show_channels)

    def test_show_all_videos_function(self):
        """Тест проверяет сообщение и кнопку при вызове функции
        показать все видео"""
        self.client.send_message("@KaltentBot", "👀 Показать все видео")
        sleep(3)
        messages = self.client.get_messages("@KaltentBot")
        self.assertEqual(
            "Список окончен. Выберите действие:", messages[0].message
        )
        bttn_go_back = messages[0].reply_markup.rows[0].buttons[0].text
        self.assertEqual("👈 Вернуться в меню", bttn_go_back)

    def test_show_all_channels_function(self):
        """Тест проверяет сообщение и кнопку при вызове функции
        показать все каналы"""
        self.client.send_message("@KaltentBot", "👀 Показать все каналы")
        sleep(4)
        messages = self.client.get_messages("@KaltentBot")
        self.assertEqual(
            "Список окончен. Выберите действие:", messages[0].message
        )
        bttn_add_channel = messages[0].reply_markup.rows[0].buttons[0].text
        bttn_del_channel = messages[0].reply_markup.rows[1].buttons[0].text
        bttn_go_back = messages[0].reply_markup.rows[2].buttons[0].text
        self.assertEqual("📹 Добавить канал", bttn_add_channel)
        self.assertEqual("❌ Удалить канал", bttn_del_channel)
        self.assertEqual("👈 Вернуться в меню", bttn_go_back)

    def test_query_delete_channel(self):
        self.client.send_message("@KaltentBot", "❌ Удалить канал")
        sleep(1)
        messages = self.client.get_messages("@KaltentBot")
        sleep(1)
        self.assertEqual("Введите канал для удаления:", messages[0].message)
        self.client.send_message("@KaltentBot", "A4")
        sleep(1)
        messages = self.client.get_messages("@KaltentBot")
        self.assertEqual("Канал 'A4' удалён.", messages[0].message)

    def test_add_channel(self):
        self.client.send_message("@KaltentBot", "📹 Добавить канал")
        sleep(1)
        messages = self.client.get_messages("@KaltentBot")
        sleep(1)
        self.assertEqual("Введите ссылку на канал.", messages[0].message)
        self.client.send_message(
            "@KaltentBot",
            "https://www.youtube.com/channel/UC2tsySbe9TNrI-xh2lximHA",
        )
        sleep(1)
        messages = self.client.get_messages("@KaltentBot")
        sleep(1)
        self.assertEqual(
           "Введите рейтинг канала от 1 до 10\n"
           "Видео будут упорядочены по рейтингу канала от высшего к меньшему.",
            messages[0].message,
        )
        self.client.send_message("@KaltentBot", "1")
        sleep(5)
        messages = self.client.get_messages("@KaltentBot")
        self.assertEqual("Канал 'A4' добавлен в базу.", messages[0].message)
        sleep(2)

    def test_post_videos_to_watch(self):
        self.client.send_message("@KaltentBot", "🍻 Смотреть контент")
        sleep(2)
        messages = self.client.get_messages("@KaltentBot")
        sleep(1.5)
        self.assertEqual("Выберите действие:", messages[0].message)
        bttn_cancel_video = messages[0].reply_markup.rows[0].buttons[0].text
        bttn_del_video = messages[0].reply_markup.rows[1].buttons[0].text
        bttn_go_back = messages[0].reply_markup.rows[2].buttons[0].text
        self.assertEqual("👉 Отложить видео", bttn_cancel_video)
        self.assertEqual("❌ Удалить видео", bttn_del_video)
        self.assertEqual("👈 Вернуться в меню", bttn_go_back)
