# Backend API

Простой Flask API сервер для AI чат-приложения.

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

```bash
python app.py
```

Сервер запустится на порту 80.

## Структура

- `app.py` - основной файл сервера с API эндпоинтами
- `config.py` - конфигурация базы данных и API
- `requirements.txt` - зависимости Python

## API эндпоинты

- `GET /api/models` - получение списка моделей
- `GET /api/chats` - получение списка чатов пользователя
- `POST /api/chats` - создание нового чата
- `POST /api/chat` - отправка сообщения в чат
- `PUT /api/chats/<id>` - обновление чата
- `DELETE /api/chats/<id>` - удаление чата
- Канбан API для различных проектов
