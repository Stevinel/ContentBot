# ContentBot

### «Контент помощник».
Это бот, благодаря которому больше не нужно искать свежий контент для просмотра видео с любимых каналов.
Раз  в две недели мы встречаемся с другом, чтобы выпить немного пива и посмотреть видео, которые искали вручную.
До создания бота, мы находили видео и кидали друг другу в личку с хэштегом #контент, а при встрече искали нужные нам видео, которые мы любим смотреть первостепенно, что потом стало надоедать.

Поэтому я решил написать бота, который будет делать всю рутину за нас.

### Что умеет бот?
- Парсить новые видео с любимых каналов
- Добавлять/Удалять каналы
- Показывать список всех каналов
- Показывать список всех видео накопленных за время
- Есть возможность добавлять видео вручную со сторонних каналов
- Есть кнопка "Смотреть контент", которая выводит по одному отсортированные по релевантности видео
- Есть возможность отложить видео на потом
- Есть возможность удалить видео после просмотра
- Хранение информации о каналах, видео, их рейтинге в базе данных.

### В чём плюс?
Теперь, мы можем экономить кучу времени и в целом не заходить на youtube для поиска контента и использовать дополнительные функции бота.
Всё что нам надо - добавить любимые каналы и бот сам соберёт для нас контент и отсортирует.

### Установка
1) Склонируйте репозиторий
   ```
    https://github.com/Stevinel/ContentBot
   ```
2) Добавьте свой .env файл в который укажите переменные
   ```
   TELEGRAM_TOKEN - токен вашего бота
   TELEGRAM_CHAT_ID - ваш телеграм id
   ```
   Необязательно, но можно добавить переменные, для запуска тестов.
   Получить цифры для переменных можно здесь > https://my.telegram.org/auth
   ```
   API_ID 
   API_HASH
   ```
3) Настройте пусть к файлу chromedriver
   ```
   В 41 строке в свойстве *executable_path* укажите путь до файла, если у вас Linux, оставьте как есть, если Windows, то допишите chromderiver.exe
   ```
4) После добавления переменных можно запустить бота в контейнере, выполнив команду
   ```
    docker-compose up
   ```
### Дополнительная информация
   Бот частично покрыт тестами(unittest). 
   Для запуска полуавтоматических тестов нужно
   1) Добавить переменные API_ID и API_HASH
   1) Добавить в базу 1 канал и 1 видео(вручную)
   2) Выполнить команду > python -m unittest tests/test_bot.py
   Тесты прогнят почти все возможности бота и проверят, соответствуют ли они требованиям.

### Используемый стек
* [Python]
* [Sqlite3]
* [Selenium-webdriver]
* [Telebot]
* [unittests]
* [Docker]
