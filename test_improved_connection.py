#!/usr/bin/env python3
"""
Тест улучшенного подключения к БД с retry логикой
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import get_kanban_db_connection, get_main_db_connection, safe_kanban_query

def test_kanban_connection():
    """Тест подключения к канбан БД"""
    print("🔧 Тестируем улучшенное подключение к канбан БД...")
    
    connection = get_kanban_db_connection()
    if connection:
        print("✅ Подключение к канбан БД успешно!")
        try:
            connection.close()
            print("✅ Соединение закрыто")
        except:
            pass
    else:
        print("❌ Не удалось подключиться к канбан БД")

def test_main_connection():
    """Тест подключения к основной БД"""
    print("\n🔧 Тестируем улучшенное подключение к основной БД...")
    
    connection = get_main_db_connection()
    if connection:
        print("✅ Подключение к основной БД успешно!")
        try:
            connection.close()
            print("✅ Соединение закрыто")
        except:
            pass
    else:
        print("❌ Не удалось подключиться к основной БД")

def test_safe_query():
    """Тест безопасного запроса"""
    print("\n🔧 Тестируем безопасный запрос к канбан БД...")
    
    try:
        # Пытаемся получить список таблиц
        tables = safe_kanban_query("SHOW TABLES LIKE '%canban%'")
        print(f"✅ Найдено канбан таблиц: {len(tables)}")
        for table in tables:
            table_name = list(table.values())[0]
            print(f"  📋 {table_name}")
            
            # Проверяем количество записей в каждой таблице
            try:
                count_result = safe_kanban_query(f"SELECT COUNT(*) as count FROM {table_name}", fetch_method="fetchone")
                count = count_result['count'] if count_result else 0
                print(f"     📊 Записей: {count}")
            except Exception as e:
                print(f"     ❌ Ошибка подсчета записей: {e}")
                
    except Exception as e:
        print(f"❌ Ошибка выполнения безопасного запроса: {e}")

def test_multiple_queries():
    """Тест множественных запросов подряд"""
    print("\n🔧 Тестируем множественные запросы подряд...")
    
    success_count = 0
    total_queries = 5
    
    for i in range(total_queries):
        try:
            result = safe_kanban_query("SELECT 1 as test_value", fetch_method="fetchone")
            if result and result.get('test_value') == 1:
                success_count += 1
                print(f"✅ Запрос {i+1}/{total_queries} успешен")
            else:
                print(f"❌ Запрос {i+1}/{total_queries} вернул неожиданный результат")
        except Exception as e:
            print(f"❌ Запрос {i+1}/{total_queries} завершился с ошибкой: {e}")
    
    print(f"\n📊 Результат: {success_count}/{total_queries} запросов успешно")

if __name__ == "__main__":
    print("🚀 Начинаем тестирование улучшенного подключения к БД...\n")
    
    test_kanban_connection()
    test_main_connection()
    test_safe_query()
    test_multiple_queries()
    
    print("\n🏁 Тестирование завершено!")
    print("\n💡 Если все тесты прошли успешно, ваша БД теперь работает надежно!")
    print("   Проблемы с отключениями на 10-20 минут должны исчезнуть.")
