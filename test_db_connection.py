#!/usr/bin/env python3
import pymysql

def test_kanban_connection():
    """Тестируем подключение к базе данных канбан-досок"""
    try:
        print("🔌 Тестируем подключение к базе данных канбан-досок...")
        print("📡 Параметры подключения:")
        print("   Host: 147.45.138.77")
        print("   Port: 3306")
        print("   User: tekman")
        print("   Database: TEKMAN")
        
        connection = pymysql.connect(
            host='147.45.138.77',
            port=3306,
            user='tekman',
            password='Moloko123!',
            database='TEKMAN',
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print("✅ Подключение успешно!")
        
        # Проверяем, есть ли таблицы канбан-досок
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE '%canban%'")
            tables = cursor.fetchall()
            
            print(f"📋 Найдено таблиц канбан-досок: {len(tables)}")
            for table in tables:
                table_name = list(table.values())[0]
                print(f"   - {table_name}")
                
                # Проверяем количество записей в каждой таблице
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cursor.fetchone()
                print(f"     Записей: {count['count']}")
        
        connection.close()
        print("✅ Тест завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print(f"🔍 Тип ошибки: {type(e).__name__}")

def test_main_db_connection():
    """Тестируем подключение к основной базе данных"""
    try:
        print("\n🔌 Тестируем подключение к основной базе данных...")
        print("📡 Параметры подключения:")
        print("   Host: 147.45.138.77")
        print("   Port: 3306")
        print("   User: tekbot")
        print("   Database: tekbot")
        
        connection = pymysql.connect(
            host='147.45.138.77',
            port=3306,
            user='tekbot',
            password='77tanufe',
            database='tekbot',
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print("✅ Подключение успешно!")
        
        # Проверяем таблицы
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print(f"📋 Всего таблиц: {len(tables)}")
            for table in tables:
                table_name = list(table.values())[0]
                print(f"   - {table_name}")
        
        connection.close()
        print("✅ Тест завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print(f"🔍 Тип ошибки: {type(e).__name__}")

if __name__ == "__main__":
    print("🚀 Начинаем тестирование подключений к базам данных...\n")
    
    test_kanban_connection()
    test_main_db_connection()
    
    print("\n🏁 Тестирование завершено!")
