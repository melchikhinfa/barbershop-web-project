import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory, Response
from dotenv import load_dotenv
import json

app = Flask(__name__)

DATABASE = 'barber.db'
load_dotenv(".env")


# -----------------------------------------------------------------------------
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# -----------------------------------------------------------------------------
def init_db():
    username = os.getenv("FLASK_USER", "default_user")
    password = os.getenv("FLASK_PASS", "default_pass")
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""  
            CREATE TABLE IF NOT EXISTS users (  
                id INTEGER PRIMARY KEY AUTOINCREMENT,  
                username TEXT UNIQUE NOT NULL,  
                password TEXT NOT NULL  
            )  
        """)  

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                specialist TEXT NOT NULL,
                service TEXT NOT NULL,
                strizhkaType TEXT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL
            )
        ''')

        cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", (username, password))  
        conn.commit()

# -----------------------------------------------------------------------------
# УТИЛИТНАЯ ФУНКЦИЯ ДЛЯ ПРОВЕРКИ АВТОРИЗАЦИИ
# -----------------------------------------------------------------------------
def check_auth(username, password):
    """
    Проверка логина и пароля в БД
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    
    user = cursor.fetchone()
    conn.close()
    return user is not None

# -----------------------------------------------------------------------------
# УТИЛИТНАЯ ФУНКЦИЯ ДЛЯ ГЕНЕРАЦИИ СЛОТОВ
# -----------------------------------------------------------------------------
def generate_time_slots(start_time_str, end_time_str, interval_minutes=60):
    """
    Генерирует тайм-слоты между start_time_str и end_time_str
    с шагом в interval_minutes.
    
    :param start_time_str: начало рабочего дня (например, "09:00")
    :param end_time_str: конец рабочего дня (например, "18:00")
    :param interval_minutes: шаг между слотами (в минутах)
    :return: список строк вида ["09:00", "10:00", ...]
    """
    time_format = "%H:%M"
    start = datetime.strptime(start_time_str, time_format)
    end = datetime.strptime(end_time_str, time_format)

    slots = []
    current = start
    while current < end:
        slots.append(current.strftime(time_format))
        current += timedelta(minutes=interval_minutes)
    return slots

# -----------------------------------------------------------------------------
# МАРШРУТЫ ДЛЯ FRONTEND (HTML, CSS, JS, КАРТИНКИ)
# -----------------------------------------------------------------------------
@app.route('/')
def serve_index():
    """
    Отдаёт главную страницу (index.html).
    """
    return send_from_directory('./public', 'index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    """
    Обслуживает любые статические файлы (CSS, JS, картинки).
    Например, /styles.css, /script.js, /background.jpg, /logo.png
    """
    return send_from_directory('./public', filename)

# -----------------------------------------------------------------------------
# МАРШРУТ ДЛЯ ПОЛУЧЕНИЯ СПИСКА ДОСТУПНЫХ СЛОТОВ
# -----------------------------------------------------------------------------
@app.route('/available-slots', methods=['GET'])
def get_available_slots():
    """
    Возвращает список доступных временных слотов на заданную дату.
    Параметр запроса: ?date=YYYY-MM-DD
    """
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'Дата не указана'}), 400

    # Подключаемся к базе
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Находим занятые слоты для конкретной даты
    cursor.execute("SELECT time FROM appointments WHERE date = ?", (date,))
    occupied_slots = [row[0] for row in cursor.fetchall()]

    conn.close()

    # Генерируем все возможные слоты за день (например, с 09:00 до 18:00, шаг 1 час)
    all_slots = generate_time_slots("09:00", "22:00", 60)

    # Исключаем те, которые уже заняты
    available_slots = [slot for slot in all_slots if slot not in occupied_slots]

    return jsonify({'slots': available_slots})

# -----------------------------------------------------------------------------
# МАРШРУТ ДЛЯ СОЗДАНИЯ ЗАПИСИ (POST)
# -----------------------------------------------------------------------------
@app.route('/appointment', methods=['POST'])
def create_appointment():
    """
    Создаёт новую запись по данным из тела запроса (JSON).
    Пример тела:
    {
      "date": "2025-01-15",
      "time": "09:00",
      "specialist": "Иван",
      "service": "Стрижка",
      "strizhkaType": "Классика",
      "name": "Петр Петров",
      "phone": "+7 000 000-00-00"
    }
    """
    data = request.get_json()

    date = data.get('date')
    time = data.get('time')
    specialist = data.get('specialist')
    service = data.get('service')
    strizhka_type = data.get('strizhkaType', '')
    name = data.get('name')
    phone = data.get('phone')

    if not all([date, time, specialist, service, name, phone]):
        return jsonify({'error': 'Не все поля заполнены'}), 400

    # Подключаемся к базе
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Проверим, что слот не занят
    cursor.execute("SELECT * FROM appointments WHERE date = ? AND time = ?", (date, time))
    row = cursor.fetchone()
    if row:  # если уже есть запись
        conn.close()
        return jsonify({'error': 'Данное время уже занято!'}), 400

    # Сохраняем новую запись
    cursor.execute('''
        INSERT INTO appointments (date, time, specialist, service, strizhkaType, name, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date, time, specialist, service, strizhka_type, name, phone))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Запись создана успешно!'})

# -----------------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЙ МАРШРУТ ДЛЯ ПРОВЕРКИ ВСЕХ ЗАПИСЕЙ (ДЛЯ ОТЛАДКИ)
# -----------------------------------------------------------------------------
@app.route('/appointments', methods=['GET'])
def get_appointments():
    """
    Возвращает список всех записей (appointments) только после базовой авторизации.
    Если авторизация не пройдена, возвращаем 401 c заголовком WWW-Authenticate,
    чтобы браузер отобразил окно для ввода логина/пароля.
    """
    # Получаем данные аутентификации из заголовка Authorization
    auth = request.authorization
    # Если не переданы учетные данные или они неверны
    if not auth or not check_auth(auth.username, auth.password):
        return Response(
            'Вы не авторизованы.\n'
            'Введите корректные логин и пароль.',
            401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM appointments")
    rows = cursor.fetchall()
    conn.close()

    appointments_list = []
    for row in rows:
        appointments_list.append({
            'id': row[0],
            'date': row[1],
            'time': row[2],
            'specialist': row[3],
            'service': row[4],
            'strizhkaType': row[5],
            'name': row[6],
            'phone': row[7],
        })
    response_json = json.dumps(appointments_list, ensure_ascii=False, indent=2)  
    return Response(  
        response=response_json,  
        status=200,  
        mimetype="application/json; charset=utf-8"  
    )  

# -----------------------------------------------------------------------------
# ТОЧКА ВХОДА
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    # Создаём таблицу (если ещё нет)
    init_db()

    # Запускаем сервер
    app.run(debug=True)