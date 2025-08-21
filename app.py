from flask import Flask, request, jsonify, Response, stream_template, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import json
import re
import pymysql
import os
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.config['JSON_AS_ASCII'] = False  # Поддержка UTF-8 в JSON
# Настройка CORS - разрешаем все хосты, методы и заголовки
CORS(app, 
     origins="*",  # Разрешаем все хосты
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Все HTTP методы
     allow_headers=["*"],  # Все заголовки
     supports_credentials=False,  # Отключаем credentials для безопасности
     max_age=3600)  # Кэшируем preflight запросы на 1 час

# Дополнительные заголовки CORS для максимальной совместимости
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Origin')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS,PATCH')
    response.headers.add('Access-Control-Allow-Credentials', 'false')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

db = SQLAlchemy(app)

# Функция подключения к канбан-базе данных
def get_kanban_db_connection():
    """Создает подключение к канбан-базе данных"""
    try:
        print(f"🔌 Попытка подключения к канбан-базе:")
        print(f"   Host: {Config.KANBAN_DB_HOST}")
        print(f"   Port: {Config.KANBAN_DB_PORT}")
        print(f"   User: {Config.KANBAN_DB_USER}")
        print(f"   Database: {Config.KANBAN_DB_NAME}")
        
        connection = pymysql.connect(
            host=Config.KANBAN_DB_HOST,
            port=Config.KANBAN_DB_PORT,
            user=Config.KANBAN_DB_USER,
            password=Config.KANBAN_DB_PASSWORD,
            database=Config.KANBAN_DB_NAME,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Подключение к канбан-базе успешно!")
        return connection
    except Exception as e:
        print(f"❌ Ошибка подключения к канбан-базе: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        return None

# Модели базы данных
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, nullable=False)
    login = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(30), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    chats = db.relationship('Chat', backref='user', lazy=True, cascade='all, delete-orphan')

class Chat(db.Model):
    __tablename__ = 'chats'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), default='Новый чат')
    model_id = db.Column(db.Integer, nullable=False)  # Теперь храним ID модели
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    role = db.Column(db.Enum('user', 'assistant'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Обработчик OPTIONS запросов для CORS preflight
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    response = Response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Origin')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS,PATCH')
    response.headers.add('Access-Control-Allow-Credentials', 'false')
    response.headers.add('Access-Control-Max-Age', '3600')
    return response

# Статические файлы frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join('static', path)):
        return send_from_directory('static', path)
    else:
        return send_from_directory('static', 'index.html')

# API эндпоинты
@app.route('/api/models', methods=['GET'])
def get_models():
    """Получить список доступных моделей ИИ"""
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    
    # Получаем пользователя для проверки роли
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        # Подключаемся к БД tekbot для получения моделей
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            if user.role == 'admin':
                # Админы видят все модели
                cursor.execute("SELECT * FROM models ORDER BY id")
            else:
                # Обычные пользователи видят только модели с admin_only = 0
                cursor.execute("SELECT * FROM models WHERE admin_only = 0 ORDER BY id")
            
            models = cursor.fetchall()
            
            # Форматируем ответ
            models_list = []
            for model in models:
                models_list.append({
                    'id': model['id'],
                    'model_name': model['model_name'],
                    'model_api': model['model_api'],
                    'admin_only': bool(model['admin_only'])
                })
            
            return jsonify({'models': models_list})
            
    except Exception as e:
        print(f"❌ Ошибка получения моделей: {e}")
        return jsonify({'error': 'Database connection failed'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@app.route('/api/auth', methods=['POST'])
def authenticate():
    data = request.get_json()
    login = data.get('login')
    password = data.get('password')
    
    user = User.query.filter_by(login=login, password=password).first()
    
    if user:
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'login': user.login,
                'full_name': user.full_name,
                'role': user.role
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Неверные учетные данные'}), 401

@app.route('/api/chats', methods=['GET'])
def get_chats():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    
    chats = Chat.query.filter_by(user_id=user_id).order_by(Chat.updated_at.desc()).all()
    
    chat_list = []
    for chat in chats:
        # Получаем информацию о модели
        try:
            connection = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                charset='utf8',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT model_name FROM models WHERE id = %s", (chat.model_id,))
                model_info = cursor.fetchone()
                model_name = model_info['model_name'] if model_info else 'Неизвестная модель'
                
        except Exception as e:
            print(f"❌ Ошибка получения названия модели: {e}")
            model_name = 'Неизвестная модель'
        finally:
            if 'connection' in locals():
                connection.close()
        
        chat_data = {
            'id': chat.id,
            'title': chat.title,
            'model_id': chat.model_id,
            'model_name': model_name,
            'created_at': chat.created_at.isoformat(),
            'updated_at': chat.updated_at.isoformat(),
            'message_count': len(chat.messages)
        }
        chat_list.append(chat_data)
    
    return jsonify({'chats': chat_list})

@app.route('/api/chats', methods=['POST'])
def create_chat():
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title', 'Новый чат')
    model_id = data.get('model_id')  # Теперь получаем ID модели
    
    if not user_id or not model_id:
        return jsonify({'error': 'user_id and model_id required'}), 400
    
    # Проверяем, что модель существует и доступна пользователю
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # Получаем пользователя для проверки роли
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if user.role == 'admin':
                cursor.execute("SELECT * FROM models WHERE id = %s", (model_id,))
            else:
                cursor.execute("SELECT * FROM models WHERE id = %s AND admin_only = 0", (model_id,))
            
            model_info = cursor.fetchone()
            if not model_info:
                return jsonify({'error': 'Model not found or not accessible'}), 404
            
    except Exception as e:
        print(f"❌ Ошибка проверки модели: {e}")
        return jsonify({'error': 'Database connection failed'}), 500
    finally:
        if 'connection' in locals():
            connection.close()
    
    chat = Chat(user_id=user_id, title=title, model_id=model_id)
    db.session.add(chat)
    db.session.commit()
    
    return jsonify({
        'id': chat.id,
        'title': chat.title,
        'model_id': chat.model_id,
        'created_at': chat.created_at.isoformat()
    })

@app.route('/api/chats/<int:chat_id>/messages', methods=['GET'])
def get_messages(chat_id):
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at.asc()).all()
    
    message_list = []
    for message in messages:
        message_data = {
            'id': message.id,
            'role': message.role,
            'content': message.content,
            'created_at': message.created_at.isoformat()
        }
        message_list.append(message_data)
    
    return jsonify({'messages': message_list})

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    data = request.get_json()
    user_id = data.get('user_id')
    chat_id = data.get('chat_id')
    message = data.get('message')
    model_id = data.get('model_id')  # Теперь получаем ID модели
    
    if not all([user_id, chat_id, message, model_id]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Сохраняем сообщение пользователя
    user_message = Message(chat_id=chat_id, role='user', content=message)
    db.session.add(user_message)
    print(f"✅ Сохранено сообщение пользователя: {len(message)} символов")
    
    # Обновляем заголовок чата если это первое сообщение
    chat = db.session.get(Chat, chat_id)
    if len(chat.messages) == 0:
        chat.title = message[:50] + "..." if len(message) > 50 else message
        db.session.add(chat)
        print(f"✅ Обновлен заголовок чата: {chat.title}")
    
    db.session.commit()
    print(f"✅ Сообщение пользователя сохранено в БД")
    
    # Получаем информацию о модели из БД tekbot
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM models WHERE id = %s", (model_id,))
            model_info = cursor.fetchone()
            
            if not model_info:
                return jsonify({'error': 'Model not found'}), 404
            
            print(f"🤖 Используем модель: {model_info['model_name']}")
            print(f"🔗 API URL: {model_info['model_api']}")
            
    except Exception as e:
        print(f"❌ Ошибка получения информации о модели: {e}")
        return jsonify({'error': 'Database connection failed'}), 500
    finally:
        if 'connection' in locals():
            connection.close()
    
    # Получаем историю сообщений для контекста
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at.asc()).all()
    
    # Формируем сообщения для API
    api_messages = []
    for msg in messages:
        api_messages.append({"role": msg.role, "content": msg.content})
    
    # Вызываем AI API используя URL из БД
    url = model_info['model_api']
    
    print(f"🚀 Отправляем запрос к AI API модели {model_info['model_name']}")
    print(f"📝 Количество сообщений в контексте: {len(api_messages)}")
    
    def generate():
        try:
            # Формируем запрос к API
            payload = {
                'chat_id': chat_id,
                'mess': message  # Отправляем только текущее сообщение
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            ai_response = response.json()
            print(f"🔍 Получен ответ от API: {ai_response}")
            
            # API возвращает массив, берем первый элемент
            if isinstance(ai_response, list) and len(ai_response) > 0:
                ai_message = ai_response[0].get('mess', '')
                print(f"📝 Извлечено сообщение из массива: {len(ai_message)} символов")
            else:
                ai_message = ai_response.get('mess', '')
                print(f"📝 Извлечено сообщение из объекта: {len(ai_message)} символов")
            
            if not ai_message:
                print(f"❌ Пустое сообщение от AI")
                yield f"data: {json.dumps({'error': 'Empty response from AI'})}\n\n"
                return
            
            print(f"✅ Получен ответ от AI: {len(ai_message)} символов")
            print(f"📊 Количество строк в ответе: {len(ai_message.split('\\n'))}")
            
            # Симулируем стриминг, разбивая ответ на части
            # Разбиваем по строкам, чтобы сохранить форматирование
            lines = ai_message.split('\n')
            chunk_size = 2  # Количество строк в одном чанке
            
            for i in range(0, len(lines), chunk_size):
                chunk_lines = lines[i:i + chunk_size]
                chunk = '\n'.join(chunk_lines)
                
                # Добавляем перенос строки, если это не последний чанк
                if i + chunk_size < len(lines):
                    chunk += '\n'
                
                print(f"📤 Отправляем чанк: {len(chunk)} символов, строк: {len(chunk_lines)}")
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                
                # Небольшая задержка для эффекта печати
                import time
                time.sleep(0.15)
            
            # Сохраняем полный ответ ассистента
            print(f"💾 Пытаемся сохранить в БД: {len(ai_message)} символов")
            try:
                with app.app_context():
                    assistant_message = Message(
                        chat_id=chat_id, 
                        role='assistant', 
                        content=ai_message
                    )
                    db.session.add(assistant_message)
                    db.session.commit()
                    print(f"✅ Сохранен ответ ассистента: {len(ai_message)} символов")
            except Exception as e:
                print(f"❌ Ошибка сохранения в БД: {e}")
                print(f"🔍 Детали ошибки: {type(e).__name__}")
                import traceback
                traceback.print_exc()
            
            yield f"data: [DONE]\n\n"
                            
        except Exception as e:
            print(f"Error in AI API call: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream', headers={
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    })

@app.route('/api/chats/<int:chat_id>', methods=['PATCH'])
def update_chat(chat_id):
    data = request.get_json()
    chat = Chat.query.get_or_404(chat_id)
    
    if 'title' in data:
        chat.title = data['title']
    
    if 'model_id' in data:
        # Проверяем, что модель существует и доступна пользователю
        try:
            connection = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                charset='utf8',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with connection.cursor() as cursor:
                # Получаем пользователя для проверки роли
                user = User.query.get(chat.user_id)
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                if user.role == 'admin':
                    cursor.execute("SELECT * FROM models WHERE id = %s", (data['model_id'],))
                else:
                    cursor.execute("SELECT * FROM models WHERE id = %s AND admin_only = 0", (data['model_id'],))
                
                model_info = cursor.fetchone()
                if not model_info:
                    return jsonify({'error': 'Model not found or not accessible'}), 404
                
                chat.model_id = data['model_id']
                
        except Exception as e:
            print(f"❌ Ошибка проверки модели: {e}")
            return jsonify({'error': 'Database connection failed'}), 500
        finally:
            if 'connection' in locals():
                connection.close()
    
    db.session.commit()
    
    # Получаем название модели для ответа
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT model_name FROM models WHERE id = %s", (chat.model_id,))
            model_info = cursor.fetchone()
            model_name = model_info['model_name'] if model_info else 'Неизвестная модель'
            
    except Exception as e:
        print(f"❌ Ошибка получения названия модели: {e}")
        model_name = 'Неизвестная модель'
    finally:
        if 'connection' in locals():
            connection.close()
    
    return jsonify({
        'id': chat.id,
        'title': chat.title,
        'model_id': chat.model_id,
        'model_name': model_name,
        'updated_at': chat.updated_at.isoformat()
    })

@app.route('/api/chats/<int:chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    print(f"🗑️ Запрос на удаление чата ID: {chat_id}")
    try:
        chat = Chat.query.get_or_404(chat_id)
        print(f"📝 Найден чат: '{chat.title}' с {len(chat.messages)} сообщениями")
        
        # Удаляем чат (связанные сообщения удалятся автоматически из-за cascade)
        db.session.delete(chat)
        db.session.commit()
        
        print(f"✅ Чат ID: {chat_id} успешно удален из БД")
        return jsonify({'success': True, 'message': f'Chat {chat_id} deleted successfully'})
    except Exception as e:
        print(f"❌ Ошибка удаления чата ID: {chat_id}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# =============================================
# КАНБАН API РОУТЫ
# =============================================

# Роуты для web_canban
@app.route('/api/web_canban', methods=['GET'])
def get_web_canban():
    """Получить все задачи из web канбан-доски"""
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM web_canban ORDER BY id DESC")
            tasks = cursor.fetchall()
            return jsonify(tasks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/web_canban', methods=['POST'])
def add_web_canban_task():
    """Добавить новую задачу в web канбан-доску"""
    data = request.get_json()
    if not data or 'task' not in data:
        return jsonify({'error': 'Missing required field: task'}), 400
    
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            query = """
            INSERT INTO web_canban (task, description, status)
            VALUES (%s, %s, %s)
            """
            cursor.execute(query, (
                data['task'],
                data.get('description', ''),
                data.get('status', 'set')
            ))
            connection.commit()
            
            task_id = cursor.lastrowid
            return jsonify({'message': 'Task added successfully', 'id': task_id}), 201
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/web_canban/<int:task_id>', methods=['PUT'])
def update_web_canban_task(task_id):
    """Обновить задачу в web канбан-доске"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            # Проверяем существование задачи
            cursor.execute("SELECT id FROM web_canban WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Task not found'}), 404
            
            # Формируем запрос для обновления
            set_parts = []
            params = []
            
            for field in ['task', 'description', 'status']:
                if field in data:
                    set_parts.append(f"{field} = %s")
                    params.append(data[field])
            
            if not set_parts:
                return jsonify({'error': 'No fields to update'}), 400
            
            params.append(task_id)
            query = f"UPDATE web_canban SET {', '.join(set_parts)} WHERE id = %s"
            cursor.execute(query, tuple(params))
            connection.commit()
            
            return jsonify({'message': 'Task updated successfully'})
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/web_canban/<int:task_id>', methods=['DELETE'])
def delete_web_canban_task(task_id):
    """Удалить задачу из web канбан-доски"""
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM web_canban WHERE id = %s", (task_id,))
            connection.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Task not found'}), 404
                
            return jsonify({'message': 'Task deleted successfully'})
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

# Роуты для tsd_android_canban
@app.route('/api/tsd_android_canban', methods=['GET'])
def get_tsd_android_canban():
    """Получить все задачи из tsd_android канбан-доски"""
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM tsd_android_canban ORDER BY id DESC")
            tasks = cursor.fetchall()
            return jsonify(tasks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/tsd_android_canban', methods=['POST'])
def add_tsd_android_canban_task():
    """Добавить новую задачу в tsd_android канбан-доску"""
    data = request.get_json()
    if not data or 'task' not in data:
        return jsonify({'error': 'Missing required field: task'}), 400
    
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            query = """
            INSERT INTO tsd_android_canban (task, description, status)
            VALUES (%s, %s, %s)
            """
            cursor.execute(query, (
                data['task'],
                data.get('description', ''),
                data.get('status', 'set')
            ))
            connection.commit()
            
            task_id = cursor.lastrowid
            return jsonify({'message': 'Task added successfully', 'id': task_id}), 201
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/tsd_android_canban/<int:task_id>', methods=['PUT'])
def update_tsd_android_canban_task(task_id):
    """Обновить задачу в tsd_android канбан-доске"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            # Проверяем существование задачи
            cursor.execute("SELECT id FROM tsd_android_canban WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Task not found'}), 404
                
            # Формируем запрос для обновления
            set_parts = []
            params = []
            
            for field in ['task', 'description', 'status']:
                if field in data:
                    set_parts.append(f"{field} = %s")
                    params.append(data[field])
            
            if not set_parts:
                return jsonify({'error': 'No fields to update'}), 400
            
            params.append(task_id)
            query = f"UPDATE tsd_android_canban SET {', '.join(set_parts)} WHERE id = %s"
            cursor.execute(query, tuple(params))
            connection.commit()
            
            return jsonify({'message': 'Task updated successfully'})
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/tsd_android_canban/<int:task_id>', methods=['DELETE'])
def delete_tsd_android_canban_task(task_id):
    """Удалить задачу из tsd_android канбан-доски"""
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM tsd_android_canban WHERE id = %s", (task_id,))
            connection.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Task not found'}), 404
                
            return jsonify({'message': 'Task deleted successfully'})
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

# Роуты для win_tsd_canban
@app.route('/api/win_tsd_canban', methods=['GET'])
def get_win_tsd_canban():
    """Получить все задачи из win_tsd канбан-доски"""
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM win_tsd_canban ORDER BY id DESC")
            tasks = cursor.fetchall()
            return jsonify(tasks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/win_tsd_canban', methods=['POST'])
def add_win_tsd_canban_task():
    """Добавить новую задачу в win_tsd канбан-доску"""
    data = request.get_json()
    if not data or 'task' not in data:
        return jsonify({'error': 'Missing required field: task'}), 400
    
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            query = """
            INSERT INTO win_tsd_canban (task, description, status)
            VALUES (%s, %s, %s)
            """
            cursor.execute(query, (
                data['task'],
                data.get('description', ''),
                data.get('status', 'set')
            ))
            connection.commit()
            
            task_id = cursor.lastrowid
            return jsonify({'message': 'Task added successfully', 'id': task_id}), 201
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/win_tsd_canban/<int:task_id>', methods=['PUT'])
def update_win_tsd_canban_task(task_id):
    """Обновить задачу в win_tsd канбан-доске"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            # Проверяем существование задачи
            cursor.execute("SELECT id FROM win_tsd_canban WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Task not found'}), 404
            
            # Формируем запрос для обновления
            set_parts = []
            params = []
            
            for field in ['task', 'description', 'status']:
                if field in data:
                    set_parts.append(f"{field} = %s")
                    params.append(data[field])
            
            if not set_parts:
                return jsonify({'error': 'No fields to update'}), 400
            
            params.append(task_id)
            query = f"UPDATE win_tsd_canban SET {', '.join(set_parts)} WHERE id = %s"
            cursor.execute(query, tuple(params))
            connection.commit()
            
            return jsonify({'message': 'Task updated successfully'})
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/win_tsd_canban/<int:task_id>', methods=['DELETE'])
def delete_win_tsd_canban_task(task_id):
    """Удалить задачу из win_tsd канбан-доски"""
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM win_tsd_canban WHERE id = %s", (task_id,))
            connection.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Task not found'}), 404
                
            return jsonify({'message': 'Task deleted successfully'})
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

# Роуты для system_canban
@app.route('/api/system_canban', methods=['GET'])
def get_system_canban():
    """Получить все задачи из system канбан-доски"""
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM system_canban ORDER BY id DESC")
            tasks = cursor.fetchall()
            return jsonify(tasks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/system_canban', methods=['POST'])
def add_system_canban_task():
    """Добавить новую задачу в system канбан-доску"""
    data = request.get_json()
    if not data or 'task' not in data:
        return jsonify({'error': 'Missing required field: task'}), 400
    
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            query = """
            INSERT INTO system_canban (task, description, status)
            VALUES (%s, %s, %s)
            """
            cursor.execute(query, (
                data['task'],
                data.get('description', ''),
                data.get('status', 'set')
            ))
            connection.commit()
            
            task_id = cursor.lastrowid
            return jsonify({'message': 'Task added successfully', 'id': task_id}), 201
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/system_canban/<int:task_id>', methods=['PUT'])
def update_system_canban_task(task_id):
    """Обновить задачу в system канбан-доске"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            # Проверяем существование задачи
            cursor.execute("SELECT id FROM system_canban WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Task not found'}), 404
            
            # Формируем запрос для обновления
            set_parts = []
            params = []
            
            for field in ['task', 'description', 'status']:
                if field in data:
                    set_parts.append(f"{field} = %s")
                    params.append(data[field])
            
            if not set_parts:
                return jsonify({'error': 'No fields to update'}), 400
            
            params.append(task_id)
            query = f"UPDATE system_canban SET {', '.join(set_parts)} WHERE id = %s"
            cursor.execute(query, tuple(params))
            connection.commit()
            
            return jsonify({'message': 'Task updated successfully'})
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

@app.route('/api/system_canban/<int:task_id>', methods=['DELETE'])
def delete_system_canban_task(task_id):
    """Удалить задачу из system канбан-доски"""
    connection = get_kanban_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM system_canban WHERE id = %s", (task_id,))
            connection.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Task not found'}), 404
                
            return jsonify({'message': 'Task deleted successfully'})
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=80)
