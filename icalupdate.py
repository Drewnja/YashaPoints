import os
import requests
import schedule
import time
from datetime import datetime, timedelta

# Папка для хранения файлов
folder = 'coefficients'
if not os.path.exists(folder):
    os.makedirs(folder)

def get_week_dates():
    """Вычисляем понедельник и воскресенье в зависимости от текущего дня"""
    today = datetime.now()
    
    # Если сегодня воскресенье
    if today.weekday() == 6:
        monday = today + timedelta(days=1)  # Следующий понедельник
        sunday = monday + timedelta(days=6)  # Воскресенье той же недели
    else:
        monday = today - timedelta(days=today.weekday())  # Понедельник текущей недели
        sunday = monday + timedelta(days=6)  # Воскресенье текущей недели

    start_date = monday.strftime('%Y.%m.%d')
    finish_date = sunday.strftime('%Y.%m.%d')
    return start_date, finish_date

def download_ical():
    # Удаляем старый файл
    for file in os.listdir(folder):
        if file.endswith('.ics'):
            os.remove(os.path.join(folder, file))
    
    # Получаем даты понедельника и воскресенья
    start_date, finish_date = get_week_dates()

    # Обновленный URL с новыми датами
    url = f'https://ruz.fa.ru/api/schedule/person/7004dcb2-88e5-11e8-b636-005056bf5929.ics?start={start_date}&finish={finish_date}&lng=1'
    
    # Скачиваем файл
    response = requests.get(url)
    if response.status_code == 200:
        file_name = f'schedule.ics'
        with open(os.path.join(folder, file_name), 'wb') as file:
            file.write(response.content)
        print(f'Новый файл {file_name} успешно скачан и сохранен.')
    else:
        print(f'Не удалось скачать файл: статус {response.status_code}')

# Планируем выполнение каждое воскресенье в 23:00
schedule.every().sunday.at("23:00").do(download_ical)

# Бесконечный цикл для выполнения запланированных задач
while True:
    schedule.run_pending()
    time.sleep(60)