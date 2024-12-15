-- Создание таблицы для хранения формул
CREATE TABLE formulas (
    name VARCHAR(255),                           -- Новая колонка для имени
    id SERIAL PRIMARY KEY,                       -- Уникальный идентификатор
    latex TEXT NOT NULL,                         -- Оригинальная строка формулы (LaTeX)
    structure JSONB NOT NULL,                    -- Структурированное представление формулы (JSON)
    formula_type VARCHAR(50) NOT NULL,           -- Тип формулы (математическая/физическая)
    category VARCHAR(50),                        -- Категория формулы (например, алгебра, механика)
    variables JSONB,                             -- Связанные переменные и их параметры (например, единицы измерения)
    formula_hash VARCHAR(64) UNIQUE,            -- Хэш формулы для проверки уникальности
    tags JSONB,                                  -- Теги
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Дата создания записи
);


-- Индекс для быстрого поиска по JSONB-структуре
CREATE INDEX idx_structure ON formulas USING gin (structure);

-- Индекс для текстового поиска по строкам LaTeX
CREATE INDEX idx_latex_search ON formulas USING gin (to_tsvector('english', latex));

-- Индекс для поиска по триграммам в строках LaTeX
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_latex_trgm ON formulas USING gin (latex gin_trgm_ops);