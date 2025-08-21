-- Создание таблицы для чатов
CREATE TABLE IF NOT EXISTS `chats` (
    `id` int NOT NULL AUTO_INCREMENT,
    `user_id` int NOT NULL,
    `title` varchar(255) DEFAULT 'Новый чат',
    `model` varchar(50) DEFAULT 'TEKMAN-1',
    `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
    `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `user_id` (`user_id`),
    CONSTRAINT `chats_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8;

-- Создание таблицы для сообщений
CREATE TABLE IF NOT EXISTS `messages` (
    `id` int NOT NULL AUTO_INCREMENT,
    `chat_id` int NOT NULL,
    `role` enum('user', 'assistant') NOT NULL,
    `content` text NOT NULL,
    `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `chat_id` (`chat_id`),
    CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`chat_id`) REFERENCES `chats` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8;

-- Добавление индексов для оптимизации
CREATE INDEX idx_chats_user_id ON chats (user_id);

CREATE INDEX idx_messages_chat_id ON messages (chat_id);

CREATE INDEX idx_messages_created_at ON messages (created_at);