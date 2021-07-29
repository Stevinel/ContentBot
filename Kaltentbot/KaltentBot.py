import datetime as dt
import os
import re
from time import sleep
import time
import telebot
import sqlite3
from dotenv import load_dotenv
from selenium import webdriver

load_dotenv()
from telebot import types
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()


TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PHOTO_GOBLIN_HELLO = 'https://www.meme-arsenal.com/memes/990b461fea0832a44ab4f588e6cf37e0.jpg'
PHOTO_PEPE_THINKING = 'https://www.meme-arsenal.com/memes/8b3ef2c65d5763539e34a9bd5bff7b9d.jpg'
PHOTO_ERIC_THINKING = 'https://i.ytimg.com/vi/yDly4gmLLHg/mqdefault.jpg'
DRIVER = webdriver.Chrome(executable_path="C:\Dev\KaltentBot\KaltentBot\chromedriver.exe")
DATE_FORMAT = '%d.%m.%Y'
BOT = telebot.TeleBot(TELEGRAM_TOKEN)


__connection = None

def get_connection():
    """Функция подключения к базе данных"""
    global __connection
    if __connection is None:
        __connection = sqlite3.connect('channels.db', check_same_thread=False)
    return __connection


def init_db(force: bool = False):
    """Функция инициализации БД"""
    conn = get_connection()
    c = conn.cursor()

    if force:
        c.execute('DROP TABLE IF EXISTS channel_list')

    c.execute("""
        CREATE TABLE IF NOT EXISTS channel_list (
        id INTEGER PRIMARY KEY,
        title TEXT,
        url TEXT,
        video_url,
        rating INTEGER
        )
        """)
    conn.commit()


@BOT.message_handler(commands=['add_channel_url'])
def add_channel_url(message):
    """Функция ввода ссылки"""
    msg = BOT.send_message(message.chat.id, "Введите ссылку на канал.")
    BOT.register_next_step_handler(msg, add_channel_raiting)


def add_channel_raiting(message):
    """Функция ввода ссылки"""
    if message.text.startswith('https://www.youtube.com/') or message.text.startswith("https://youtube.com/"):
        msg = BOT.send_message(message.chat.id, f"Введите рейтинг канала от 1 до 10\n"
        f"Видео будут упорядочены по рейтингу канала от высшего к меньшему.")
        url = message.text
        BOT.register_next_step_handler(msg, add_channel, url)
    else:
        msg = BOT.send_message(message.chat.id, "Вы ввели неправильную ссылку, начните заново.")
        BOT.register_next_step_handler(msg, add_channel_raiting)

def add_channel(message, url):
    """Функция добавления нового канала"""    
            
    if url.startswith('https://www.youtube.com/') or url.startswith("https://youtube.com/") and 0 < int(message.text) <= 10:
        conn = get_connection()
        c = conn.cursor()
        BOT.send_photo(message.chat.id, photo=PHOTO_ERIC_THINKING, caption='Я думаю...') 
        title_link = url
        rating = message.text
        DRIVER.get(title_link)
        sleep(3)
        title = DRIVER.find_element_by_css_selector('#channel-header #channel-name #text').text
        c.execute("INSERT INTO channel_list (url, title, rating) VALUES (?, ?, ?);", (url, title, rating))
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        BOT.send_message(message.chat.id, f"Канал '{title}' добавлен в базу.", reply_markup=markup)
        markup.add(telebot.types.InlineKeyboardButton(text='Вернуться в меню'))
        conn.commit()
        

    else:
        BOT.send_message(message.chat.id, "Вы ввели неправильную ссылку начните заново.")
        BOT.register_next_step_handler(message, selects_actions)


def show_all_channels(message):
    """Функция просмотра всех каналов"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT(title) FROM channel_list WHERE title NOT NULL")
    (result) = c.fetchall()
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.InlineKeyboardButton(text='Добавить канал'))
    markup.add(telebot.types.InlineKeyboardButton(text='Удалить канал'))
    markup.add(telebot.types.InlineKeyboardButton(text='Вернуться в меню'))
    
    if result:
        BOT.send_message(message.chat.id, f"Список всех каналов:\n")
        for title in result:
            BOT.send_message(message.chat.id, f"{''.join(title)}")
        BOT.send_message(message.chat.id, 'Выберите действие', reply_markup=markup)
    else:
        BOT.send_message(message.chat.id, "У вас не добавлены каналы.")
        BOT.register_next_step_handler(message, selects_actions)


def query_delete_channel(message):
    """Функция удаления канала"""
    msg = BOT.send_message(message.chat.id, "Введите канал для удаления:",)
    BOT.register_next_step_handler(msg, delete_channel)


def delete_channel(message):
    """Функция удаления канала из базы"""
    conn = get_connection()
    c = conn.cursor()
    title = message.text
    c.execute("SELECT title FROM channel_list")
    (base) = c.fetchall()
    all_titles = []
    for name in base:
        all_titles.append("".join(name))
    if title in all_titles:
        c.execute("DELETE FROM channel_list WHERE title IN (?);", (title,))
        BOT.send_message(message.chat.id, f"Канал '{title}' удалён.")
        conn.commit()
    else:
        BOT.send_message(message.chat.id, "В вашей базе нет такого канала.")
        BOT.register_next_step_handler(message, delete_channel)
    
    
@BOT.message_handler(commands=['start'])
def start_message(message):
    """Функция приветствия"""
    BOT.send_photo(message.chat.id, photo=PHOTO_GOBLIN_HELLO, 
    caption=f'Привет, калтэнтеры!\n'
    f'Сегодня {dt.date.today().strftime(DATE_FORMAT)}\n'
    'Cмотрите описание бота и используйте команды.\n')
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.InlineKeyboardButton(text='Продолжить'))
    msg = BOT.send_message(message.chat.id, "Продолжаем?", reply_markup=markup)
    BOT.register_next_step_handler(msg, process_step)


@BOT.message_handler(commands=['menu'])
def selects_actions(message):
    """Функция меню с выбором действий"""
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.InlineKeyboardButton(text='Смотреть калтент'))
    markup.add(telebot.types.InlineKeyboardButton(text='Добавить видео'))
    markup.add(telebot.types.InlineKeyboardButton(text='Показать все каналы'))
    msg = BOT.send_photo(message.chat.id, photo=PHOTO_PEPE_THINKING, caption='Чего желаете?', reply_markup=markup)
    BOT.register_next_step_handler(msg, process_step)


@BOT.message_handler(content_types=['text'])
def process_step(message, url = None):
    """Функция распределения действий"""
    if  message.text == 'Смотреть калтент':
        BOT.send_message(message.chat.id, "Начинаем просмотр, хорошей зачилки.")
        sleep(2)
        post_videos_to_watch(message)
    elif message.text == 'Добавить видео':
        new_videos(message)
    elif message.text == 'Продолжить':
        selects_actions(message)
    elif message.text == 'Показать все каналы':
        show_all_channels(message)
    elif message.text == 'Добавить канал':
        add_channel_url(message)
    elif message.text == 'Удалить канал':
        query_delete_channel(message)
    elif message.text == 'Отложить видео':
        deferral_video(message, url)
    elif message.text == 'Удалить видео':
        delete_video(message, url)
    elif message.text == 'Следующее видео':
        post_videos_to_watch(message)
    elif message.text == 'Вернуться в меню':
        selects_actions(message)

    
def new_videos(message):
    """Функция добавления новых видео"""
    BOT.send_message(message.chat.id, "Отправьте ссылку на видео, я добавлю его в базу.")
    BOT.register_next_step_handler(message, add_new_video)


def add_new_video(message):
    """Функция добавления нового видео в базу"""
    conn = get_connection()
    c = conn.cursor()
    
    if message.text.startswith('https://www.youtube.com/watch') or message.text.startswith("https://youtu.be/"):
        BOT.send_photo(message.chat.id, photo=PHOTO_ERIC_THINKING, caption='Я думаю...') 
        video_url = message.text
        DRIVER.get(video_url)
        sleep(2)
        c.execute("INSERT INTO channel_list (video_url) VALUES (?);", (video_url,))
        BOT.send_message(message.chat.id, "Видео добавлено.")
        conn.commit()
    else:
        BOT.send_message(message.chat.id, "Вы отправили неверную ссылку, начните сначала.")



@sched.scheduled_job('interval', seconds=3600)
def new_video_from_channel(): 
    """Функция проверки новых видео на канале и добавления их в базу"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT url FROM channel_list WHERE url NOT NULL")
    (urls) = c.fetchall()

    all_urls = []
    for url in urls:
        all_urls.append("".join(url))

    for url in all_urls:
        DRIVER.get(url + "/videos")
        date_of_publication = DRIVER.find_elements_by_xpath("//span[@class='style-scope ytd-grid-video-renderer']")[1].text
        videos = DRIVER.find_elements_by_id("video-title")
        if date_of_publication == "1 час назад":
            for i in range(len(videos)):
                new_video = videos[i].get_attribute('href')
                channel_name = DRIVER.find_element_by_css_selector('#channel-header #channel-name #text').text
                c.execute("INSERT INTO channel_list (video_url, title) VALUES (?, ?);", (new_video, channel_name))
                c.execute("CREATE TABLE query_channel AS SELECT title, rating FROM channel_list GROUP BY title HAVING rating NOT NULL")
                c.execute("UPDATE channel_list SET rating = (SELECT rating FROM query_channel WHERE channel_list.title = query_channel.title)")
                c.execute("DROP TABLE query_channel")
                conn.commit()
                break
    

def post_videos_to_watch(message):
    """Функция выдачи видео для просмотра контента"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT video_url FROM channel_list WHERE video_url NOT NULL ORDER BY rating DESC")
    (urls) = c.fetchall()
    conn.commit()
    if urls:
        all_urls = []
        for url in urls:
            all_urls.append("".join(url))
        for url in all_urls:
            BOT.send_message(message.chat.id, url)
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(telebot.types.InlineKeyboardButton(text='Отложить видео'))
            markup.add(telebot.types.InlineKeyboardButton(text='Удалить видео'))
            markup.add(telebot.types.InlineKeyboardButton(text='Вернуться в меню'))
            msg = BOT.send_message(message.chat.id, "Выберите действие.", reply_markup=markup)
            BOT.register_next_step_handler(msg, process_step, url)
            break
    else:
        BOT.send_message(message.chat.id, "В базе не осталось видео для просморта.")
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(telebot.types.InlineKeyboardButton(text='Вернуться в меню'))
        BOT.send_message(message.chat.id, "Конец.", reply_markup=markup)
        BOT.register_next_step_handler(message, selects_actions)
    

def delete_video(message, url):
    """Функция удаления видео из базы"""
    conn = get_connection()
    c = conn.cursor()
    video_url = url
    c.execute("DELETE FROM channel_list WHERE video_url IN (?);", (video_url,))
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.InlineKeyboardButton(text='Следующее видео'))
    BOT.send_message(message.chat.id, f"Видео удалено.", reply_markup=markup)
    conn.commit()


def deferral_video(message, url):
    conn = get_connection()
    c = conn.cursor()
    video_url = url
    c.execute("UPDATE channel_list SET rating = Null WHERE video_url IN(?);", (video_url,))
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(telebot.types.InlineKeyboardButton(text='Следующее видео'))
    BOT.send_message(message.chat.id, f"Видео отложено.", reply_markup=markup)
    conn.commit()


if __name__ == "__main__":
    init_db()
    # new_video_from_channel()
    # sched.start()
    BOT.polling(none_stop=True)
