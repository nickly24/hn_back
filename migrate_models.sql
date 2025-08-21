-- Миграция для поддержки моделей ИИ
-- Выполнять пошагово!

-- 1. Создаем таблицу models в БД tekbot (если её нет)
-- Выполнить в БД tekbot:
/*
CREATE TABLE IF NOT EXISTS models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_api VARCHAR(500) NOT NULL,
    admin_only TINYINT(1) DEFAULT 0
);

-- Вставляем первую модель
INSERT INTO models (model_name, model_api, admin_only) VALUES 
('TEKBOT-1', 'https://juenaferbabdar.beget.app/webhook/tekbot2', 1);
*/

-- 2. Обновляем структуру таблицы chats в БД tekbot
-- Выполнить в БД tekbot:

-- Сначала добавляем новую колонку
ALTER TABLE chats ADD COLUMN model_id INT AFTER title;

-- Обновляем существующие записи (ставим ID первой модели)
UPDATE chats SET model_id = 1 WHERE model_id IS NULL;

-- Делаем колонку NOT NULL
ALTER TABLE chats MODIFY COLUMN model_id INT NOT NULL;

-- Удаляем старую колонку model
ALTER TABLE chats DROP COLUMN model;

-- Добавляем индекс для оптимизации
CREATE INDEX idx_chats_model_id ON chats(model_id);

-- 3. Проверяем результат
-- SELECT * FROM chats;
-- SELECT * FROM models;
