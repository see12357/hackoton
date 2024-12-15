# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта, включая модель
COPY . .

# Указываем переменные окружения для Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=127.0.0.1
ENV FLASK_ENV=development

# Указываем порт, на котором будет работать приложение
EXPOSE 5000

# Запускаем приложение
CMD ["flask", "run"]
