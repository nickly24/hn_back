#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
from config import Config

def create_admin_user():
    """Создание тестового админа"""
    
    # Подключение к базе данных tekbot
    connection = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8'
    )
    
    try:
        with connection.cursor() as cursor:
            print("🔧 Создание тестового админа...")
            
            # Проверяем, есть ли уже админ
            cursor.execute("SELECT id FROM users WHERE role = 'admin'")
            admin_exists = cursor.fetchone()
            
            if admin_exists:
                print("✅ Админ уже существует")
                cursor.execute("SELECT login, full_name FROM users WHERE role = 'admin'")
                admin = cursor.fetchone()
                print(f"📋 Логин: {admin[0]}")
                print(f"👤 Имя: {admin[1]}")
                return
            
            # Создаем админа
            cursor.execute("""
                INSERT INTO users (plant_id, login, password, full_name, role)
                VALUES (%s, %s, %s, %s, %s)
            """, (1, 'admin', 'admin123', 'Администратор', 'admin'))
            
            connection.commit()
            
            print("🎉 Тестовый админ создан!")
            print("📋 Данные для входа:")
            print("   Логин: admin")
            print("   Пароль: admin123")
            print("   Роль: admin")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    create_admin_user()
