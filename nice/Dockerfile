FROM python:3.11

# Отключаем создание .pyc файлов и буферизацию вывода
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем весь проект в контейнер
COPY . /app/

# Если у вас уже есть подготовленная база данных
COPY db.sqlite3 /app/db.sqlite3

# Если статика нужна
RUN python manage.py collectstatic --noinput

RUN mkdir -p /app/media

# создаем пользователя и меняем владельца
RUN useradd -m dp && chown -R dp:dp /app
USER dp

# Открываем порт, на котором будет работать сервер
EXPOSE 8000

# Запускаем сервер 
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

