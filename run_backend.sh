#!/bin/bash

echo "🚀 Запуск бэкенда на порту 80..."

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем, что порт 80 свободен
if lsof -Pi :80 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Порт 80 занят. Остановите процесс на порту 80 или используйте sudo"
    echo "💡 Попробуйте: sudo lsof -i :80"
    exit 1
fi

# Запускаем Flask приложение
echo "✅ Запуск Flask приложения на http://localhost:80"
echo "🔧 API доступен по адресу: http://localhost:80/api"
echo ""
echo "Для остановки нажмите Ctrl+C"

python app.py
