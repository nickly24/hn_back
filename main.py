from flask import Flask, request, jsonify, Response, stream_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import json
import re
import pymysql




app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://tekbot:77tanufe@147.45.138.77:3306/tekbot'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, 
     origins="*",
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
     allow_headers=["*"],
     supports_credentials=False,
     max_age=3600)



db = SQLAlchemy(app)



def get_kanban_db_connection():
    try:
        print("🔌 Попытка подключения к канбан-базе данных...")
        connection = pymysql.connect(
            host='147.45.138.77',
            port=3306,
            user='tekman',
            password='Moloko123!',
            database='TEKMAN',
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Подключение к канбан-базе успешно!")
        return connection
    except Exception as e:
        print(f"❌ Ошибка подключения к канбан-базе: {e}")
        print(f"🔍 Тип ошибки: {type(e).__name__}")
        return None

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
    model_id = db.Column(db.Integer, nullable=False)
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

@app.route('/')
def index():
    return jsonify({'message': 'Hello World', 'api': 'AI Chat API'})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'API работает'})



@app.route('/api/models', methods=['GET'])
def get_models():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        connection = pymysql.connect(
            host='147.45.138.77',
            port=3306,
            user='tekbot',
            password='77tanufe',
            database='tekbot',
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            if user.role == 'admin':
                cursor.execute("SELECT * FROM models ORDER BY id")
            else:
                cursor.execute("SELECT * FROM models WHERE admin_only = 0 ORDER BY id")
            
            models = cursor.fetchall()
            
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
        print(f"Ошибка получения моделей: {e}")
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
        try:
            connection = pymysql.connect(
                host='147.45.138.77',
                port=3306,
                user='tekbot',
                password='77tanufe',
                database='tekbot',
                charset='utf8',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT model_name FROM models WHERE id = %s", (chat.model_id,))
                model_info = cursor.fetchone()
                model_name = model_info['model_name'] if model_info else 'Неизвестная модель'
                
        except Exception as e:
            print(f"Ошибка получения названия модели: {e}")
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
    model_id = data.get('model_id')
    
    if not user_id or not model_id:
        return jsonify({'error': 'user_id and model_id required'}), 400
    
    try:
        connection = pymysql.connect(
            host='147.45.138.77',
            port=3306,
            user='tekbot',
            password='77tanufe',
            database='tekbot',
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
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
        print(f"Ошибка проверки модели: {e}")
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
    model_id = data.get('model_id')
    
    if not all([user_id, chat_id, message, model_id]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    user_message = Message(chat_id=chat_id, role='user', content=message)
    db.session.add(user_message)
    print(f"Сохранено сообщение пользователя: {len(message)} символов")
    
    chat = db.session.get(Chat, chat_id)
    if len(chat.messages) == 0:
        chat.title = message[:50] + "..." if len(message) > 50 else message
        db.session.add(chat)
        print(f"Обновлен заголовок чата: {chat.title}")
    
    db.session.commit()
    print(f"Сообщение пользователя сохранено в БД")
    
    try:
        connection = pymysql.connect(
            host='147.45.138.77',
            port=3306,
            user='tekbot',
            password='77tanufe',
            database='tekbot',
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM models WHERE id = %s", (model_id,))
            model_info = cursor.fetchone()
            
            if not model_info:
                return jsonify({'error': 'Model not found'}), 404
            
            print(f"Используем модель: {model_info['model_name']}")
            print(f"API URL: {model_info['model_api']}")
            
    except Exception as e:
        print(f"Ошибка получения информации о модели: {e}")
        return jsonify({'error': 'Database connection failed'}), 500
    finally:
        if 'connection' in locals():
            connection.close()
    
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at.asc()).all()
    
    api_messages = []
    for msg in messages:
        api_messages.append({"role": msg.role, "content": msg.content})
    
    url = model_info['model_api']
    
    print(f"Отправляем запрос к AI API модели {model_info['model_name']}")
    print(f"Количество сообщений в контексте: {len(api_messages)}")
    
    def generate():
        try:
            payload = {
                'chat_id': chat_id,
                'mess': message
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            ai_response = response.json()
            print(f"Получен ответ от API: {ai_response}")
            
            if isinstance(ai_response, list) and len(ai_response) > 0:
                ai_message = ai_response[0].get('mess', '')
                print(f"Извлечено сообщение из массива: {len(ai_message)} символов")
            else:
                ai_message = ai_response.get('mess', '')
                print(f"Извлечено сообщение из объекта: {len(ai_message)} символов")
            
            if not ai_message:
                print(f"Пустое сообщение от AI")
                yield f"data: {json.dumps({'error': 'Empty response from AI'})}\n\n"
                return
            
            print(f"Получен ответ от AI: {len(ai_message)} символов")
            print(f"Количество строк в ответе: {len(ai_message.split('\\n'))}")
            
            lines = ai_message.split('\n')
            chunk_size = 2
            
            for i in range(0, len(lines), chunk_size):
                chunk_lines = lines[i:i + chunk_size]
                chunk = '\n'.join(chunk_lines)
                
                if i + chunk_size < len(lines):
                    chunk += '\n'
                
                print(f"Отправляем чанк: {len(chunk)} символов, строк: {len(chunk_lines)}")
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                
                import time
                time.sleep(0.15)
            
            try:
                with app.app_context():
                    assistant_message = Message(
                        chat_id=chat_id, 
                        role='assistant', 
                        content=ai_message
                    )
                    db.session.add(assistant_message)
                    db.session.commit()
                    print(f"Сохранен ответ ассистента: {len(ai_message)} символов")
            except Exception as e:
                print(f"Ошибка сохранения в БД: {e}")
                print(f"Детали ошибки: {type(e).__name__}")
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
        try:
            connection = pymysql.connect(
                host='147.45.138.77',
                port=3306,
                user='tekbot',
                password='77tanufe',
                database='tekbot',
                charset='utf8',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with connection.cursor() as cursor:
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
            print(f"Ошибка проверки модели: {e}")
            return jsonify({'error': 'Database connection failed'}), 500
        finally:
            if 'connection' in locals():
                connection.close()
    
    db.session.commit()
    
    try:
        connection = pymysql.connect(
            host='147.45.138.77',
            port=3306,
            user='tekbot',
            password='77tanufe',
            database='tekbot',
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT model_name FROM models WHERE id = %s", (chat.model_id,))
            model_info = cursor.fetchone()
            model_name = model_info['model_name'] if model_info else 'Неизвестная модель'
            
    except Exception as e:
        print(f"Ошибка получения названия модели: {e}")
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
    print(f"Запрос на удаление чата ID: {chat_id}")
    try:
        chat = Chat.query.get_or_404(chat_id)
        print(f"Найден чат: '{chat.title}' с {len(chat.messages)} сообщениями")
        
        db.session.delete(chat)
        db.session.commit()
        
        print(f"Чат ID: {chat_id} успешно удален из БД")
        return jsonify({'success': True, 'message': f'Chat {chat_id} deleted successfully'})
    except Exception as e:
        print(f"Ошибка удаления чата ID: {chat_id}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# =============================================
# КАНБАН API РОУТЫ
# =============================================

# Роуты для web_canban
@app.route('/api/web_canban', methods=['GET'])
def get_web_canban():
    """Получить все задачи из web канбан-доски"""
    print("🔄 GET /api/web_canban - запрос на получение задач")
    connection = get_kanban_db_connection()
    if not connection:
        print("❌ Не удалось получить подключение к базе данных")
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            print("📋 Выполняем запрос: SELECT * FROM web_canban ORDER BY id DESC")
            cursor.execute("SELECT * FROM web_canban ORDER BY id DESC")
            tasks = cursor.fetchall()
            print(f"✅ Получено задач: {len(tasks)}")
            return jsonify(tasks)
    except Exception as e:
        print(f"❌ Ошибка выполнения запроса: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()
        print("🔌 Соединение с базой данных закрыто")

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
            cursor.execute("SELECT id FROM web_canban WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Task not found'}), 404
            
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
            cursor.execute("SELECT id FROM tsd_android_canban WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Task not found'}), 404
                
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
            cursor.execute("SELECT id FROM win_tsd_canban WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Task not found'}), 404
            
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
            cursor.execute("SELECT id FROM system_canban WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Task not found'}), 404
            
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
    app.run(debug=True, host='0.0.0.0', port=80)

# Для запуска через gunicorn: gunicorn main:app --timeout 60 --bind 0.0.0.0:$PORT
