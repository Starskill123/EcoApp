from gigachat import GigaChat
import openpyxl
import random
import telebot
from telebot.types import ReplyKeyboardMarkup
from icrawler.builtin import BingImageCrawler
import os

bot = telebot.TeleBot('токен телеграм бота')
key = 'токен gigachat'  # Ключ нейросети

image_dir = 'Директория/image'

default_message = '''Ты Экологический ассистент
Основная задача: предоставление точной и актуальной информации по вопросам биологии, экологии и охраны окружающей среды.
Функционал:
Идентификация растений и животных по описанию или изображению
Описание биологических характеристик видов
Информация о естественных ареалах обитания
Данные о природоохранном статусе видов
Сведения об экосистемах и их компонентах
Рекомендации по сохранению биоразнообразия
Экологические советы для повседневной жизни
Информация о природоохранных мероприятиях
Требования к ответам:
Научный подход с использованием актуальных данных
Простота изложения для понимания широкой аудиторией
Структурированность информации
Актуализация данных с учетом последних исследований
Предоставление ссылок на авторитетные источники
Учет региональных особенностей при необходимости
Формат работы:
Ответы на конкретные вопросы пользователей
Составление информационных справок
Подготовка рекомендаций
Анализ экологических ситуаций
Помощь в идентификации видов
Консультации по экологическим проблемам
Дополнительные возможности:
Помощь в составлении экологических проектов
Рекомендации по озеленению территорий
Советы по уходу за домашними растениями и животными
Информация о сезонных изменениях в природе
Данные о влиянии человеческой деятельности на экосистемы
Важно: при отсутствии точной информации необходимо указывать на необходимость проверки данных у специалистов или проведения дополнительных исследований.'''


# Обработчики команд
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Добро пожаловать в наш бот. Здесь вы можете узнать все об экологии!')


@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """Бот нужен для получения информации о растениях, животных, экосистемах и вопросах охраны окружающей среды.

Вот список доступных команд:
/start - Начало работы с ботом
/search - Поиск информации
/help - Посмотреть справку
/test - Викторина 

Автор бота: Слава Богатырев, Кира Лудина."""
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(commands=['search'])
def start_search(message):
    msg = bot.send_message(message.chat.id, "Введите ваш запрос:")
    bot.register_next_step_handler(msg, process_search_query)


def process_search_query(message):
    query = message.text
    if query.lower() == 'экология':
        bot.send_message(message.chat.id, 'Пожалуйста, подождите...')

    try:
        # Получаем ответ от GigaChat
        result = get_gigachat_response(query)
        bot.send_message(message.chat.id, result[0])

        if len(result) > 1 and result[1]:
            bot.send_photo(message.chat.id, open(result[1], 'rb'))
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")


def get_gigachat_response(query):
    with GigaChat(credentials=key, verify_ssl_certs=False) as giga:
        response = giga.chat(default_message + "\n\n" + query)
        txt = response.choices[0].message.content

        img_path = search_image(query)

        return [txt, img_path]  # Возвращаем только текст

def search_image(text):
    bing_crawler = BingImageCrawler(storage={'root_dir': image_dir})
    path = ""
    if not os.path.exists(image_dir + "/" + text + ".jpg"):  #Проверка есть ли такой файл в папке
        bing_crawler.crawl(keyword=text, max_num=1)  #Поиск изображения
        os.rename(image_dir + "/000001.jpg", image_dir + "/" + text + ".jpg")  #Изменение стандартного названия
    path = os.path.abspath(image_dir + "/" + text + ".jpg")  #Возврат пути до файла
    path = path.replace("\\", "/")
    return path  #Возврат пути до файла


# Загрузка вопросов из Excel
try:
    work_book = openpyxl.load_workbook("questions.xlsx")  # Загрузка файла таблицы
    questions_sheet = work_book.active  # Используем активный лист (вместо явного "sheet")

    # Подсчет количества вопросов
    count_questions = 0
    for row in questions_sheet.iter_rows(min_row=1, max_col=1):
        if row[0].value is not None:
            count_questions += 1

    print(f"Загружено {count_questions} вопросов из Excel-файла.")

except Exception as e:
    print(f"Ошибка при загрузке вопросов: {e}")
    count_questions = 0
    questions_sheet = None

# Хранение состояния пользователей
user_state = {}


def get_random_question():
    """Возвращает случайный вопрос из Excel-файла"""
    if count_questions == 0:
        return None

    n = random.randint(1, count_questions)  # Случайный выбор вопроса
    question_data = [
        questions_sheet[f'A{n}'].value,  # Вопрос
        str(questions_sheet[f'B{n}'].value).strip(),  # Вариант 1
        str(questions_sheet[f'C{n}'].value).strip(),  # Вариант 2
        str(questions_sheet[f'D{n}'].value).strip(),  # Вариант 3
        int(questions_sheet[f'E{n}'].value)  # Номер верного ответа (преобразуем в int)
    ]
    print(question_data)
    return question_data


@bot.message_handler(commands=['test'])
def start(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Начать викторину')
    bot.send_message(message.chat.id,
                     "Привет! Хочешь проверить свои знания?",
                     reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Начать викторину')
def start_quiz(message):
    if count_questions == 0:
        bot.send_message(message.chat.id, "Извините, вопросы не загружены. Попробуйте позже.")
        return

    user_state[message.chat.id] = {
        'score': 0,
        'total_questions': 0,
        'current_question': None
    }
    send_next_question(message.chat.id)


def send_next_question(chat_id):
    question_data = get_random_question()
    if not question_data:
        bot.send_message(chat_id, "Извините, не удалось загрузить вопрос.")
        return

    user_state[chat_id]['current_question'] = question_data
    user_state[chat_id]['total_questions'] += 1

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(*[question_data[i] for i in range(1, 4)])  # Добавляем варианты ответов

    bot.send_message(chat_id,
                     f"Вопрос:\n{question_data[0]}",
                     reply_markup=markup)


@bot.message_handler(func=lambda message: message.chat.id in user_state)
def check_answer(message):
    chat_id = message.chat.id
    current_state = user_state[chat_id]
    question_data = current_state['current_question']

    if not question_data:
        bot.send_message(chat_id, "Произошла ошибка. Начните викторину заново.")
        return

    # Проверяем, что ответ является одним из вариантов
    if message.text not in question_data[1:4]:
        bot.send_message(chat_id, "Пожалуйста, выберите один из предложенных вариантов.")
        return

    # Проверяем правильность ответа
    correct_answer_index = question_data[4] - 1  # Преобразуем в 0-based индекс
    correct_answer = question_data[correct_answer_index + 1]
    print(correct_answer)
    if message.text == correct_answer:
        current_state['score'] += 1
        feedback = "✅ Правильно!"
    else:
        feedback = f"❌ Неверно! Правильный ответ: {correct_answer}"

    # Удаляем клавиатуру с вариантами
    bot.send_message(chat_id, feedback) #reply_markup=ReplyKeyboardMarkup(remove_keyboard=True))

    # Отправляем следующий вопрос или завершаем викторину
    if current_state['total_questions'] < 10:  # Ограничим 10 вопросами
        send_next_question(chat_id)
    else:
        final_score = current_state['score']
        bot.send_message(chat_id,
                         f"Викторина завершена!\nВаш результат: {final_score}/10")
        del user_state[chat_id]

if __name__ == "main":
    print("Бот с викториной запущен...")

bot.polling(none_stop=True)
