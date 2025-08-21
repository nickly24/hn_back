#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
from config import Config

def setup_kanban_tables():
    """Создание канбан-таблиц и добавление тестовых данных"""
    
    # Подключение к базе данных TEKMAN
    connection = pymysql.connect(
        host=Config.KANBAN_DB_HOST,
        port=Config.KANBAN_DB_PORT,
        user=Config.KANBAN_DB_USER,
        password=Config.KANBAN_DB_PASSWORD,
        database=Config.KANBAN_DB_NAME,
        charset='utf8'
    )
    
    try:
        with connection.cursor() as cursor:
            print("🔧 Создание канбан-таблиц...")
            
            # Создание таблицы win_tsd_canban
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `win_tsd_canban` (
                    `id` int NOT NULL AUTO_INCREMENT,
                    `task` varchar(255) NOT NULL,
                    `description` text,
                    `status` enum('set', 'process', 'done') DEFAULT 'set',
                    PRIMARY KEY (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8
            """)
            
            # Создание таблицы system_canban
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS `system_canban` (
                    `id` int NOT NULL AUTO_INCREMENT,
                    `task` varchar(255) NOT NULL,
                    `description` text,
                    `status` enum('set', 'process', 'done') DEFAULT 'set',
                    PRIMARY KEY (`id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8
            """)
            
            print("✅ Таблицы созданы")
            
            # Проверяем, есть ли уже данные
            cursor.execute("SELECT COUNT(*) FROM win_tsd_canban")
            win_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM system_canban")
            system_count = cursor.fetchone()[0]
            
            print("✅ Таблицы уже существуют, тестовые данные не добавляются")
            
            # Создание индексов
            print("🔍 Создание индексов...")
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_win_tsd_status ON win_tsd_canban (status)",
                "CREATE INDEX IF NOT EXISTS idx_win_tsd_priority ON win_tsd_canban (priority)",
                "CREATE INDEX IF NOT EXISTS idx_win_tsd_assigned_to ON win_tsd_canban (assigned_to)",
                "CREATE INDEX IF NOT EXISTS idx_win_tsd_due_date ON win_tsd_canban (due_date)",
                "CREATE INDEX IF NOT EXISTS idx_system_status ON system_canban (status)",
                "CREATE INDEX IF NOT EXISTS idx_system_priority ON system_canban (priority)",
                "CREATE INDEX IF NOT EXISTS idx_system_assigned_to ON system_canban (assigned_to)",
                "CREATE INDEX IF NOT EXISTS idx_system_due_date ON system_canban (due_date)"
            ]
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    print(f"⚠️ Индекс уже существует: {e}")
            
            # Подтверждение изменений
            connection.commit()
            
            print("🎉 Канбан-таблицы успешно настроены!")
            print("📋 Созданы таблицы:")
            print("   - win_tsd_canban")
            print("   - system_canban")
            print("📊 Добавлены тестовые данные")
            print("🔍 Созданы индексы для оптимизации")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    setup_kanban_tables()
