-- Создание таблицы win_tsd_canban
CREATE TABLE IF NOT EXISTS `win_tsd_canban` (
    `id` int NOT NULL AUTO_INCREMENT,
    `task` varchar(255) NOT NULL,
    `description` text,
    `status` enum('set', 'process', 'done') DEFAULT 'set',
    PRIMARY KEY (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8;

-- Создание таблицы system_canban
CREATE TABLE IF NOT EXISTS `system_canban` (
    `id` int NOT NULL AUTO_INCREMENT,
    `task` varchar(255) NOT NULL,
    `description` text,
    `status` enum('set', 'process', 'done') DEFAULT 'set',
    PRIMARY KEY (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8;

-- Добавление тестовых данных в win_tsd_canban
INSERT INTO
    `win_tsd_canban` (
        `task`,
        `description`,
        `status`
    )
VALUES (
        'Исправить баг с авторизацией',
        'Пользователи не могут войти в систему после обновления',
        'process'
    ),
    (
        'Добавить новый модуль отчетов',
        'Создать модуль для генерации PDF отчетов',
        'set'
    ),
    (
        'Оптимизировать базу данных',
        'Улучшить производительность запросов',
        'set'
    ),
    (
        'Обновить интерфейс',
        'Переделать дизайн главной страницы',
        'done'
    ),
    (
        'Исправить ошибки валидации',
        'Проблемы с проверкой форм',
        'process'
    ),
    (
        'Добавить уведомления',
        'Система push-уведомлений',
        'set'
    ),
    (
        'Тестирование API',
        'Провести полное тестирование всех эндпоинтов',
        'set'
    ),
    (
        'Документация',
        'Обновить техническую документацию',
        'process'
    );

-- Добавление тестовых данных в system_canban
INSERT INTO
    `system_canban` (
        `task`,
        `description`,
        `status`
    )
VALUES (
        'Обновление серверов',
        'Плановое обновление серверного оборудования',
        'process'
    ),
    (
        'Резервное копирование',
        'Настройка автоматического резервного копирования',
        'done'
    ),
    (
        'Мониторинг системы',
        'Внедрение системы мониторинга',
        'set'
    ),
    (
        'Безопасность',
        'Проверка уязвимостей системы',
        'set'
    ),
    (
        'Обновление ПО',
        'Обновление системного программного обеспечения',
        'process'
    ),
    (
        'Логирование',
        'Улучшение системы логирования',
        'set'
    ),
    (
        'Автоматизация',
        'Автоматизация рутинных задач',
        'set'
    ),
    (
        'Восстановление данных',
        'Процедуры восстановления после сбоев',
        'done'
    );