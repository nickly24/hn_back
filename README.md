# H&N Backend

Бэкенд приложения H&N - Flask API сервер с интеграцией ИИ и канбан-системой.

## Технологии

- Python 3.8+
- Flask - веб-фреймворк
- Flask-SQLAlchemy - ORM для базы данных
- Flask-CORS - поддержка CORS
- PyMySQL - драйвер MySQL
- SQLite - локальная база данных

## Функциональность

- 🔐 API аутентификации пользователей
- 💬 Чат с ИИ моделями
- 📋 Канбан-доски (4 доски)
- 🗄️ Управление базой данных
- 🌐 CORS поддержка для всех хостов

## Установка и запуск

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python app.py
```

## Структура проекта

```
backend/
├── app.py              # Основной Flask приложение
├── config.py           # Конфигурация
├── requirements.txt    # Python зависимости
├── models/             # Модели базы данных
└── api/                # API эндпоинты
```

## API эндпоинты

### Аутентификация
- `POST /api/auth` - Вход в систему

### Модели ИИ
- `GET /api/models` - Список доступных моделей

### Чаты
- `GET /api/chats` - Список чатов пользователя
- `POST /api/chats` - Создание нового чата
- `GET /api/chats/<id>/messages` - Сообщения чата
- `POST /api/chat` - Отправка сообщения в чат
- `PATCH /api/chats/<id>` - Обновление чата
- `DELETE /api/chats/<id>` - Удаление чата

### Канбан-доски
- `GET /api/web_canban` - Задачи Web канбана
- `POST /api/web_canban` - Создание задачи
- `PUT /api/web_canban/<id>` - Обновление задачи
- `DELETE /api/web_canban/<id>` - Удаление задачи

Аналогично для других досок:
- `tsd_android_canban`
- `win_tsd_canban`
- `system_canban`

## Конфигурация

Создайте `config.py` с настройками:

```python
class Config:
    SECRET_KEY = 'your-secret-key'
    DB_HOST = 'localhost'
    DB_PORT = 3306
    DB_USER = 'username'
    DB_PASSWORD = 'password'
    DB_NAME = 'database_name'
```

## CORS настройки

Сервер настроен для работы с любыми хостами:
- Разрешены все origins (`*`)
- Поддерживаются все HTTP методы
- Разрешены все заголовки
- Preflight запросы кэшируются на 1 час

## База данных

- **Основная БД**: MySQL для пользователей и чатов
- **Канбан БД**: MySQL для задач и досок
- **SQLite**: Локальная БД для разработки
