#!/bin/bash

echo "Настройка канбан-таблиц..."

# Выполнение SQL скрипта для создания канбан-таблиц
mysql -u tekbot -p'77tanufe' -h 147.45.138.77 -P 3306 -D tekman < kanban_setup.sql

if [ $? -eq 0 ]; then
    echo "✅ Канбан-таблицы успешно созданы!"
    echo "📋 Созданы таблицы:"
    echo "   - win_tsd_canban"
    echo "   - system_canban"
    echo "📊 Добавлены тестовые данные"
else
    echo "❌ Ошибка при создании канбан-таблиц"
    exit 1
fi
