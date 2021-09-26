import datetime as dt
import os
import sqlite3
import threading
from time import sleep

import requests
import telebot
from dotenv import load_dotenv
from loguru import logger
from telebot import types

load_dotenv()
logger.add(
    "bot_debug.log",
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
BOT = telebot.TeleBot(TELEGRAM_TOKEN)

PHOTO_GOBLIN_HELLO = (
    "https://www.meme-arsenal.com/memes/990b461fea0832a44ab4f588e6cf37e0.jpg"
)
PHOTO_PEPE_THINKING = (
    "https://www.meme-arsenal.com/memes/8b3ef2c65d5763539e34a9bd5bff7b9d.jpg"
)
PHOTO_ERIC_THINKING = "https://i.ytimg.com/vi/yDly4gmLLHg/mqdefault.jpg"
GET_CHANNEL_BY_USERNAME = (
    "https://youtube.googleapis.com/youtube/v3/"
    "channels?part=snippet&forUsername="
)
GET_CHANNEL_BY_ID = (
    "https://youtube.googleapis.com/youtube/v3/channels?part=snippet&id="
)
SEARCH_VIDEO_BY_CHANNEL_ID = (
    "https://www.googleapis.com/youtube/v3/"
    "search?order=date&part=snippet&channelId="
)
SEARCH_BROKEN_CHANNEL = (
    "https://youtube.googleapis.com/youtube/v3/"
    "search?part=snippet&maxResults=5&q="
)
GET_CHANNEL_ID_FROM_VIDEO = (
    "https://youtube.googleapis.com/youtube/v3/videos?part=snippet&id="
)
YOUTUBE_URL = "https://www.youtube.com/watch?v="
DATE_FORMAT = "%d.%m.%Y"


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
    """Функция приветствует юзера и предлагает продолжить работу"""
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
    markup.add(types.InlineKeyboardButton(text="🐾 Продолжить"))
    msg = BOT.send_message(message.chat.id, "Продолжаем?", reply_markup=markup)
    BOT.register_next_step_handler(msg, process_step)


@logger.catch
@BOT.message_handler(commands=["menu"])
def selects_actions(message):
    """Функция отображает все кнопки меню и предлагает выбрать действие"""
    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    markup.add(types.InlineKeyboardButton(text="🍻 Смотреть контент"))
    markup.add(types.InlineKeyboardButton(text="📀 Добавить видео"))
    markup.add(types.InlineKeyboardButton(text="📹 Добавить канал"))
    markup.add(types.InlineKeyboardButton(text="👀 Показать все видео"))
    markup.add(types.InlineKeyboardButton(text="👀 Показать все каналы"))

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
    """Функция распределяет дальнейшие действия в зависимости
    от условия полученной команды"""
    if message.text == "🍻 Смотреть контент":
        BOT.send_message(
            message.chat.id, "Начинаем просмотр, хорошей зачилки."
        )
        sleep(1)
        post_videos_to_watch(message)
    elif message.text == "📀 Добавить видео":
        add_url_new_videos(message)
    elif message.text == "🐾 Продолжить":
        selects_actions(message)
    elif message.text == "👀 Показать все каналы":
        show_all_channels(message)
    elif message.text == "📹 Добавить канал":
        add_channel_url(message)
    elif message.text == "❌ Удалить канал":
        query_delete_channel(message)
    elif message.text == "👉 Отложить видео":
        deferral_video(message, video_url)
    elif message.text == "❌ Удалить видео":
        delete_video(message, video_url)
    elif message.text == "👉 Следующее видео":
        post_videos_to_watch(message)
    elif message.text == "👈 Вернуться в меню":
        selects_actions(message)
    elif message.text == "👀 Показать все видео":
        show_all_videos(message)
    elif message.text == "/start":
        start_message(message)
    elif message.text == "/menu":
        selects_actions(message)


@logger.catch
def show_all_videos(message):
    """Функция показывает все имеющиеся видео в БД"""
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "SELECT DISTINCT(video_url)\
        FROM channel_list\
        WHERE video_url NOT NULL\
        ORDER BY rating DESC"
    )
    (urls) = c.fetchall()

    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )

    if urls:
        all_urls = []
        for url in urls:
            all_urls.append("".join(url))
        for url in all_urls:
            BOT.send_message(message.chat.id, url)
        markup.add(types.InlineKeyboardButton(text="👈 Вернуться в меню"))
        BOT.send_message(
            message.chat.id,
            "Список окончен. Выберите действие:",
            reply_markup=markup,
        )
    else:
        markup.add(types.InlineKeyboardButton(text="👈 Вернуться в меню"))
        BOT.send_message(message.chat.id, "Нет видео.", reply_markup=markup)


@logger.catch
def show_all_channels(message):
    """Функция показывает все имеющиеся каналы в БД"""
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "SELECT DISTINCT(title)\
        FROM channel_list\
        WHERE title NOT NULL AND url NOT NULL\
        ORDER BY rating DESC"
    )
    (channel_names) = c.fetchall()

    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    markup.add(types.InlineKeyboardButton(text="📹 Добавить канал"))
    markup.add(types.InlineKeyboardButton(text="❌ Удалить канал"))
    markup.add(types.InlineKeyboardButton(text="👈 Вернуться в меню"))

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
def add_channel_url(message):
    """Функция ожидает ссылку на канал и переходит к функции
    ввода рейтинга для канала"""
    msg = BOT.send_message(message.chat.id, "Введите ссылку на канал.")
    BOT.register_next_step_handler(msg, add_channel_raiting)


@logger.catch
def add_channel_raiting(message):
    """Функция проверяет корректность ссылки на канал, если всё верно,
    то переходит к следующей функции добавления канала"""
    if message.text.startswith(
        "https://www.youtube.com/"
    ) or message.text.startswith("https://youtube.com/"):
        msg = BOT.send_message(
            message.chat.id,
            "Введите рейтинг канала от 1 до 10\n"
            "Видео будут упорядочены по рейтингу канала.",
        )
        channel_url = message.text
        BOT.register_next_step_handler(msg, add_channel, channel_url)
    else:
        BOT.send_message(
            message.chat.id, "Вы ввели неправильные данные, начните заново."
        )


@logger.catch
def add_channel(message, channel_url):
    """Функция Добавляет новый канала в БД"""
    conn = get_connection()
    c = conn.cursor()

    try:
        if (
            channel_url.startswith("https://www.youtube.com/")
            or channel_url.startswith("https://youtube.com/")
            and 0 < int(message.text) <= 10
        ):
            BOT.send_photo(
                message.chat.id,
                photo=PHOTO_ERIC_THINKING,
                caption="Я думаю...",
            )
            rating = message.text
            if len(channel_url.split("/")):
                cut_link = channel_url.split("/")[4:]
            eng_channel_name = cut_link[0]
            name_lenght = len(eng_channel_name)

            if name_lenght < 24:
                response = requests.get(
                    GET_CHANNEL_BY_USERNAME
                    + eng_channel_name
                    + "&key="
                    + GOOGLE_API_KEY
                )
            else:
                response = requests.get(
                    GET_CHANNEL_BY_ID
                    + eng_channel_name
                    + "&key="
                    + GOOGLE_API_KEY
                )
            sleep(1)
            if "items" not in response:
                response = requests.get(
                    SEARCH_BROKEN_CHANNEL
                    + eng_channel_name
                    + "&key="
                    + GOOGLE_API_KEY
                )
                channel_name = response.json()["items"][0]["snippet"][
                    "channelTitle"
                ]
            else:
                channel_name = response.json()["items"][0]["snippet"]["title"]

            c.execute(
                "SELECT DISTINCT(title)\
                FROM channel_list\
                WHERE title NOT NULL\
                ORDER BY rating DESC"
            )

            (all_channels) = c.fetchall()
            channels_name = []
            for name in all_channels:
                channels_name.append("".join(name))
            if channel_name not in channels_name:
                c.execute(
                    "INSERT INTO channel_list(url, title, rating)\
                    VALUES (?, ?, ?);",
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
                markup.add(
                    types.InlineKeyboardButton(text="👈 Вернуться в меню")
                )
                conn.commit()
            else:
                BOT.send_message(message.chat.id, "Канал уже есть в базе")
    except:
        BOT.send_message(message.chat.id, "Вы ввели неправильные данные")


@logger.catch
def query_delete_channel(message):
    """Функция ожидает название канала для удаления и переходит
    к следующей функции, которая удаляет канал"""
    msg = BOT.send_message(
        message.chat.id,
        "Введите канал для удаления:",
    )
    BOT.register_next_step_handler(msg, delete_channel)


@logger.catch
def delete_channel(message):
    """Функция удаляет канал из базы данных"""
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
            "DELETE FROM channel_list WHERE title IN (?) AND url NOT NULL;", (channel_name,)
        )
        BOT.send_message(message.chat.id, f"Канал '{channel_name}' удалён.")
        conn.commit()
    else:
        BOT.send_message
        (message.chat.id, "В вашей базе нет такого канала, начните заново.")


@logger.catch
def add_url_new_videos(message):
    """Функция ожидаает ссылку с видео и переходит в функции,
    которая добавляет эту ссылку в БД"""
    BOT.send_message(
        message.chat.id, "Отправьте ссылку на видео, я добавлю его в базу."
    )
    BOT.register_next_step_handler(message, add_new_video)


@logger.catch
def add_new_video(message):
    """Функция добавляет новое видео в БД"""
    conn = get_connection()
    c = conn.cursor()

    if message.text.startswith(
        "https://www.youtube.com/watch"
    ) or message.text.startswith("https://youtu.be/"):
        BOT.send_photo(
            message.chat.id, photo=PHOTO_ERIC_THINKING, caption="Я думаю..."
        )
        sleep(1.5)
        video_url = message.text

        if len(message.text.split("/")):
            if "=" in message.text:
                cut_link = message.text.split("=")
                eng_channel_name = cut_link[1]
            else:
                cut_link = message.text.split("/")[3:]
                eng_channel_name = cut_link[0]

        response = requests.get(
            GET_CHANNEL_ID_FROM_VIDEO
            + eng_channel_name
            + "&key="
            + GOOGLE_API_KEY
        )
        channel_name = response.json()["items"][0]["snippet"]["channelTitle"]

        c.execute(
            "CREATE TABLE query_channel AS SELECT title, rating\
            FROM channel_list\
            GROUP BY title\
            HAVING rating NOT NULL"
        )
        c.execute(
            "INSERT INTO channel_list (title, video_url) VALUES (?, ?);",
            (channel_name, video_url),
        )
        c.executescript(
            "UPDATE channel_list\
            SET rating =\
            (SELECT rating FROM query_channel\
            WHERE channel_list.title = query_channel.title);\
            UPDATE channel_list\
            SET rating = 0\
            WHERE (rating IS NULL)"
        )
        c.execute("DROP TABLE query_channel")
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
    markup.add(types.InlineKeyboardButton(text="👉 Следующее видео"))

    BOT.send_message(message.chat.id, "Видео удалено.", reply_markup=markup)
    conn.commit()


@logger.catch
def deferral_video(message, video_url):
    """Функция пропустить видео"""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE channel_list SET rating = Null WHERE video_url IN(?);",
        (video_url,),
    )
    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    markup.add(types.InlineKeyboardButton(text="👉 Следующее видео"))

    BOT.send_message(message.chat.id, "Видео отложено.", reply_markup=markup)
    conn.commit()


@logger.catch
def post_videos_to_watch(message):
    """Функция достаёт из базы все видео и выдаёт их в очереди по одному"""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT DISTINCT(video_url)\
        FROM channel_list\
        WHERE video_url NOT NULL\
        ORDER BY rating DESC"
    )
    (urls) = c.fetchall()
    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True
    )
    if urls:
        all_urls = []
        for url in urls:
            all_urls.append("".join(url))
        for url in all_urls:
            BOT.send_message(message.chat.id, url)

            markup.add(types.InlineKeyboardButton(text="👉 Отложить видео"))
            markup.add(types.InlineKeyboardButton(text="❌ Удалить видео"))
            markup.add(types.InlineKeyboardButton(text="👈 Вернуться в меню"))
            msg = BOT.send_message(
                message.chat.id, "Выберите действие:", reply_markup=markup
            )

            BOT.register_next_step_handler(msg, process_step, url)
            break
    else:
        BOT.send_message(
            message.chat.id, "В базе не осталось видео для просмотра."
        )

        markup.add(types.InlineKeyboardButton(text="👈 Вернуться в меню"))

        BOT.send_message(message.chat.id, "Конец.", reply_markup=markup)
        BOT.register_next_step_handler(message, selects_actions)


@logger.catch
def parsing_new_video_from_channel():
    """Функция достаёт из базы все имеющиеся каналы,
    проверяет есть ли на каналах новые видео"""
    threading.Timer(86400, parsing_new_video_from_channel).start()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT title, url FROM channel_list WHERE url NOT NULL")
    (channel_name_and_url) = c.fetchall()

    for title, url in channel_name_and_url:
        logger.info("Bot trying to get videos")
        sleep(2)
        if len(url.split("/")):
            cut_link = url.split("/")[4:]
        eng_channel_name = cut_link[0]
        name_lenght = len(eng_channel_name)
        if name_lenght < 24:
            get_channel_info = requests.get(
                GET_CHANNEL_BY_USERNAME
                + eng_channel_name
                + "&key="
                + GOOGLE_API_KEY
            )
        else:
            get_channel_info = requests.get(
                GET_CHANNEL_BY_ID + eng_channel_name + "&key=" + GOOGLE_API_KEY
            )
        if "items" not in get_channel_info:
            get_channel_info = requests.get(
                SEARCH_BROKEN_CHANNEL
                + eng_channel_name
                + "&key="
                + GOOGLE_API_KEY
            )
            channel_name = get_channel_info.json()["items"][0]["snippet"][
                "channelTitle"
            ]
            channel_id = get_channel_info.json()["items"][0]["snippet"][
                "channelId"
            ]
        else:
            channel_name = get_channel_info.json()["items"][0]["snippet"][
                "title"
            ]
            channel_id = get_channel_info.json()["items"][0]["id"]
        search_new_video = requests.get(
            SEARCH_VIDEO_BY_CHANNEL_ID
            + channel_id
            + "&maxResults=30&key="
            + GOOGLE_API_KEY
        )
        date_of_publication = search_new_video.json()["items"][0]["snippet"][
            "publishedAt"
        ][:10]
        video_id = search_new_video.json()["items"][0]["id"]
        video_id_in_broken_channels = search_new_video.json()["items"][1]["id"]
        if "videoId" in video_id:
            new_video = YOUTUBE_URL + video_id["videoId"]
        else:
            new_video = YOUTUBE_URL + video_id_in_broken_channels["videoId"]
        date_today = str(dt.date.today())
        if date_of_publication == date_today:
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
            sleep(1)
            logger.info("Bot added video")
            conn.commit()
        else:
            logger.info("No new videos were found")
    logger.info("Parsing done")


if __name__ == "__main__":
    logger.info("Bot started work")
    while True:
        try:
            init_db()
            thread2 = threading.Thread(target=parsing_new_video_from_channel())
            thread2.start()
            sleep(15)
            thread1 = threading.Thread(target=BOT.polling(none_stop=True))
            thread1.start()
        except Exception as error:
            logger.error(error)
            BOT.send_message(TELEGRAM_CHAT_ID, f"Error at startup {error}")
            sleep(30)
