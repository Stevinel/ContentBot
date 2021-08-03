import datetime as dt
import os
import sqlite3
import threading
from time import sleep

import telebot
from dotenv import load_dotenv
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from telebot import types

load_dotenv()
logger.add(
    'bot_debug.log', 
    format="{time} {level} {message}", 
    level="DEBUG", 
    rotation="10 MB", 
    compression="zip",
    )

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PHOTO_GOBLIN_HELLO = (
    "https://www.meme-arsenal.com/memes/990b461fea0832a44ab4f588e6cf37e0.jpg"
)
PHOTO_PEPE_THINKING = (
    "https://www.meme-arsenal.com/memes/8b3ef2c65d5763539e34a9bd5bff7b9d.jpg"
)
PHOTO_ERIC_THINKING = "https://i.ytimg.com/vi/yDly4gmLLHg/mqdefault.jpg"
DATE_FORMAT = "%d.%m.%Y"
BOT = telebot.TeleBot(TELEGRAM_TOKEN)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
logger.info('bot trying to find chromedriver')
try:
    DRIVER = webdriver.Chrome(
        "/root/code/chromedriver", 
        options=chrome_options)
except Exception as error:
    trouble = logger.error('invalid path to chromedriver')
    BOT.send_message(TELEGRAM_CHAT_ID, trouble)



__connection = None


@logger.catch
def get_connection():
    """Функция подключения к базе данных"""
    global __connection
    if __connection is None:
        __connection = sqlite3.connect("channels.db", check_same_thread=False)
    return __connection


@logger.catch
def init_db(force: bool = False):
    """Функция создания БД"""
    conn = get_connection()
    c = conn.cursor()

    if force:
        c.execute("DROP TABLE IF EXISTS channel_list")

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS channel_list (
        id INTEGER PRIMARY KEY,
        title TEXT,
        url TEXT,
        video_url,
        rating INTEGER
        )
        """
    )
    conn.commit()


@logger.catch
@BOT.message_handler(commands=["start"])
def start_message(message):
    """Функция приветствия"""
    BOT.send_photo(
        message.chat.id,
        photo=PHOTO_GOBLIN_HELLO,
        caption=f"Привет, калтэнтеры!\n"
        f"Сегодня {dt.date.today().strftime(DATE_FORMAT)}\n"
        "Cмотрите описание бота и используйте команды.\n",
    )

    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    markup.add(telebot.types.InlineKeyboardButton(text="Продолжить"))
    msg = BOT.send_message(message.chat.id, "Продолжаем?", reply_markup=markup)
    BOT.register_next_step_handler(msg, process_step)


@logger.catch
@BOT.message_handler(commands=["menu"])
def selects_actions(message):
    """Функция меню с выбором действий"""
    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    markup.add(telebot.types.InlineKeyboardButton(text="Смотреть калтент"))
    markup.add(telebot.types.InlineKeyboardButton(text="Добавить видео"))
    markup.add(telebot.types.InlineKeyboardButton(text="Добавить канал"))
    markup.add(telebot.types.InlineKeyboardButton(text="Показать все видео"))
    markup.add(telebot.types.InlineKeyboardButton(text="Показать все каналы"))

    msg = BOT.send_photo(
        message.chat.id,
        photo=PHOTO_PEPE_THINKING,
        caption="Чего желаете?",
        reply_markup=markup,
    )
    BOT.register_next_step_handler(msg, process_step)


@logger.catch
@BOT.message_handler(content_types=["text"])
def process_step(message, video_url=None):
    """Функция распределения действий"""
    if message.text == "Смотреть калтент":
        BOT.send_message(
            message.chat.id, "Начинаем просмотр, хорошей зачилки."
        )
        sleep(1)
        post_videos_to_watch(message)
    elif message.text == "Добавить видео":
        add_url_new_videos(message)
    elif message.text == "Продолжить":
        selects_actions(message)
    elif message.text == "Показать все каналы":
        show_all_channels(message)
    elif message.text == "Добавить канал":
        add_channel_url(message)
    elif message.text == "Удалить канал":
        query_delete_channel(message)
    elif message.text == "Отложить видео":
        deferral_video(message, video_url)
    elif message.text == "Удалить видео":
        delete_video(message, video_url)
    elif message.text == "Следующее видео":
        post_videos_to_watch(message)
    elif message.text == "Вернуться в меню":
        selects_actions(message)
    elif message.text == "Показать все видео":
        show_all_videos(message)
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/menu":
        selects_actions(message)


@logger.catch
def show_all_videos(message):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT DISTINCT(video_url)\
        FROM channel_list\
        WHERE video_url NOT NULL\
        ORDER BY rating DESC"
    )
    (urls) = c.fetchall()

    if urls:
        all_urls = []
        for url in urls:
            all_urls.append("".join(url))
        for url in all_urls:
            BOT.send_message(message.chat.id, url)

            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True
            )
            markup.add(
                telebot.types.InlineKeyboardButton(text="Вернуться в меню")
            )

        BOT.send_message(
            message.chat.id,
            "Список окончен. Выберите действие:",
            reply_markup=markup,
        )
    else:
        markup = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True
        )
        markup.add(telebot.types.InlineKeyboardButton(text="Вернуться в меню"))
        BOT.send_message(message.chat.id, "Нет видео.", reply_markup=markup)


@logger.catch
def show_all_channels(message):
    """Функция просмотра всех каналов"""
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "SELECT DISTINCT(title)\
        FROM channel_list\
        WHERE title NOT NULL\
        ORDER BY rating DESC"
    )
    (channel_names) = c.fetchall()

    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    markup.add(telebot.types.InlineKeyboardButton(text="Добавить канал"))
    markup.add(telebot.types.InlineKeyboardButton(text="Удалить канал"))
    markup.add(telebot.types.InlineKeyboardButton(text="Вернуться в меню"))

    if channel_names:
        BOT.send_message(message.chat.id, "Список всех каналов:\n")
        for name in channel_names:
            BOT.send_message(message.chat.id, f"{''.join(name)}")
        BOT.send_message(
            message.chat.id,
            "Список окончен. Выберите действие:",
            reply_markup=markup,
        )
    else:
        BOT.send_message(message.chat.id, "У вас не добавлены каналы.")
        BOT.register_next_step_handler(message, selects_actions)


@logger.catch
@BOT.message_handler(commands=["add_channel_url"])
def add_channel_url(message):
    """Функция ввода ссылки"""
    msg = BOT.send_message(message.chat.id, "Введите ссылку на канал.")
    BOT.register_next_step_handler(msg, add_channel_raiting)


@logger.catch
def add_channel_raiting(message):
    """Функция ввода рейтинга и проверки ссылки"""
    if message.text.startswith(
        "https://www.youtube.com/"
    ) or message.text.startswith("https://youtube.com/"):
        msg = BOT.send_message(
            message.chat.id,
            "Введите рейтинг канала от 1 до 10\n"
            "Видео будут упорядочены по рейтингу канала от высшего к меньшему."
        )
        channel_url = message.text
        BOT.register_next_step_handler(msg, add_channel, channel_url)
    else:
        BOT.send_message(
            message.chat.id, "Вы ввели неправильную ссылку, начните заново."
        )


@logger.catch
def add_channel(message, channel_url):
    """Функция добавления нового канала"""
    conn = get_connection()
    c = conn.cursor()

    if (
        channel_url.startswith("https://www.youtube.com/")
        or channel_url.startswith("https://youtube.com/")
        and 0 < int(message.text) <= 10
    ):
        BOT.send_photo(
            message.chat.id, photo=PHOTO_ERIC_THINKING, caption="Я думаю..."
        )
        channel_url
        rating = message.text
        DRIVER.get(channel_url)
        sleep(1)

        channel_name = DRIVER.find_element_by_css_selector(
            "#channel-header #channel-name #text"
        ).text
        c.execute(
            "INSERT INTO channel_list (url, title, rating) VALUES (?, ?, ?);",
            (channel_url, channel_name, rating),
        )

        markup = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True
        )
        BOT.send_message(
            message.chat.id,
            f"Канал '{channel_name}' добавлен в базу.",
            reply_markup=markup,
        )
        markup.add(telebot.types.InlineKeyboardButton(text="Вернуться в меню"))
        conn.commit()
    else:
        BOT.send_message(
            message.chat.id, "Вы ввели неправильную ссылку начните заново."
        )


@logger.catch
def query_delete_channel(message):
    """Функция удаления канала"""
    msg = BOT.send_message(
        message.chat.id,
        "Введите канал для удаления:",
    )
    BOT.register_next_step_handler(msg, delete_channel)


@logger.catch
def delete_channel(message):
    """Функция удаления канала из базы"""
    conn = get_connection()
    c = conn.cursor()

    channel_name = message.text
    c.execute("SELECT title FROM channel_list WHERE title IS NOT NULL")
    (base) = c.fetchall()
    all_names = []
    for name in base:
        all_names.append("".join(name))
    if channel_name in all_names:
        c.execute(
            "DELETE FROM channel_list WHERE title IN (?);", (channel_name,)
        )
        BOT.send_message(message.chat.id, f"Канал '{channel_name}' удалён.")
        conn.commit()
    else:
        BOT.send_message(message.chat.id, "В вашей базе нет такого канала.")
        BOT.register_next_step_handler(message, delete_channel)


@logger.catch
def add_url_new_videos(message):
    """Функция добавления новых видео"""
    BOT.send_message(
        message.chat.id, "Отправьте ссылку на видео, я добавлю его в базу."
    )
    BOT.register_next_step_handler(message, add_new_video)


@logger.catch
def add_new_video(message):
    """Функция добавления нового видео в базу"""
    conn = get_connection()
    c = conn.cursor()

    if message.text.startswith(
        "https://www.youtube.com/watch"
    ) or message.text.startswith("https://youtu.be/"):
        BOT.send_photo(
            message.chat.id, photo=PHOTO_ERIC_THINKING, caption="Я думаю..."
        )
        video_url = message.text
        DRIVER.get(video_url)
        sleep(2)
        c.execute(
            "INSERT INTO channel_list (video_url) VALUES (?);", (video_url,)
        )
        BOT.send_message(message.chat.id, "Видео добавлено.")
        conn.commit()
    else:
        BOT.send_message(
            message.chat.id, "Вы отправили неверную ссылку, начните сначала."
        )


@logger.catch
def delete_video(message, video_url):
    """Функция удаления видео из базы"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM channel_list WHERE video_url IN (?);", (video_url,))

    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    markup.add(telebot.types.InlineKeyboardButton(text="Следующее видео"))

    BOT.send_message(message.chat.id, "Видео удалено.", reply_markup=markup)
    conn.commit()


@logger.catch
def deferral_video(message, video_url):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE channel_list SET rating = Null WHERE video_url IN(?);",
        (video_url,),
    )

    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    markup.add(telebot.types.InlineKeyboardButton(text="Следующее видео"))

    BOT.send_message(message.chat.id, "Видео отложено.", reply_markup=markup)
    conn.commit()


@logger.catch
def post_videos_to_watch(message):
    """Функция выдачи видео для просмотра контента"""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT DISTINCT(video_url)\
        FROM channel_list\
        WHERE video_url NOT NULL\
        ORDER BY rating DESC"
    )
    (urls) = c.fetchall()

    if urls:
        all_urls = []
        for url in urls:
            all_urls.append("".join(url))
        for url in all_urls:
            BOT.send_message(message.chat.id, url)

            markup = types.ReplyKeyboardMarkup(
                one_time_keyboard=True, resize_keyboard=True
            )
            markup.add(
                telebot.types.InlineKeyboardButton(text="Отложить видео")
            )
            markup.add(
                telebot.types.InlineKeyboardButton(text="Удалить видео")
            )
            markup.add(
                telebot.types.InlineKeyboardButton(text="Вернуться в меню")
            )
            msg = BOT.send_message(
                message.chat.id, "Выберите действие:", reply_markup=markup
            )

            BOT.register_next_step_handler(msg, process_step, url)
            break
    else:
        BOT.send_message(
            message.chat.id, "В базе не осталось видео для просмотра."
        )

        markup = types.ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True
        )
        markup.add(telebot.types.InlineKeyboardButton(text="Вернуться в меню"))

        BOT.send_message(message.chat.id, "Конец.", reply_markup=markup)
        BOT.register_next_step_handler(message, selects_actions)


@logger.catch
def parsing_new_video_from_channel():
    """Функция проверки новых видео на канале и добавления их в базу"""
    threading.Timer(2400, parsing_new_video_from_channel).start()

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT url FROM channel_list WHERE url NOT NULL")
    (urls) = c.fetchall()

    all_urls = []
    for url in urls:
        all_urls.append("".join(url))

    for url in all_urls:
        logger.info("Bot trying to get videos")
        DRIVER.get(url + "/videos")
        logger.info("Bot trying to find elements on page by xpatch")
        date_of_publication = DRIVER.find_elements_by_xpath(
            "//span[@class='style-scope ytd-grid-video-renderer']"
        )[1].text
        logger.info("Bot trying to find elements by id")
        videos = DRIVER.find_elements_by_id("video-title")

        if (
            date_of_publication == "1 час назад"
            or date_of_publication == "1 hour ago"
        ):
            for attr in range(len(videos)):
                logger.info("Bot trying to get attribute href and add to bd")
                new_video = videos[attr].get_attribute("href")
                channel_name = DRIVER.find_element_by_css_selector(
                    "#channel-header #channel-name #text"
                ).text
                c.execute(
                    "CREATE TABLE query_channel AS SELECT title, rating\
                    FROM channel_list\
                    GROUP BY title\
                    HAVING rating NOT NULL"
                )
                c.execute(
                    "INSERT INTO channel_list (video_url, title)\
                    VALUES (?, ?);",
                    (new_video, channel_name),
                )
                c.execute(
                    "UPDATE channel_list\
                    SET rating =\
                    (SELECT rating FROM query_channel\
                    WHERE channel_list.title = query_channel.title)"
                )
                c.execute("DROP TABLE query_channel")
                sleep(3)
                logger.info("Bot added video and ready to work")
                conn.commit()
                break


if __name__ == "__main__":
    logger.info("Bot started work")
    while True:
        try:
            init_db()
            thread2 = threading.Thread(target=parsing_new_video_from_channel())
            thread2.start()
            sleep(5)
            thread1 = threading.Thread(target=BOT.polling(none_stop=True))
            thread1.start()
        except Exception as error:
            logger.error(error)
            BOT.send_message(TELEGRAM_CHAT_ID, f'Ошибка при запуске {error}')
            sleep(30)
