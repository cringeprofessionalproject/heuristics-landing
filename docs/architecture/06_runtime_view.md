> 🤖 Документация сгенерирована автоматически с помощью скилла **arc42-documenter**.

# 6. Динамическое поведение (Runtime View)

## 6.1 Сценарий 1: Интерактивная анимация сопоставления объектов на `heuristics.ru`

При загрузке страницы `index.html` активируется Canvas-движок, визуализирующий осевой скоринг между сущностями выборки A и каталога B:

```mermaid
sequenceDiagram
    autonumber
    actor Visitor as Посетитель сайта
    participant Browser as Браузер (index.html)
    participant Engine as Canvas Visualizer Engine

    Visitor->>Browser: Открытие https://heuristics.ru
    Browser->>Engine: init() [Расчет координат точек A и B]
    loop Анимационный цикл (requestAnimationFrame)
        Engine->>Engine: draw() [Отрисовка сетки, узлов, связей]
        Engine->>Browser: Рендеринг лучей сопоставления и пульсирующих гэпов
    end
    Visitor->>Browser: Клик «Запросить доступ» / «Открыть SPLASH»
    Browser->>Visitor: Переход на https://splash.heuristics.ru
```

## 6.2 Сценарий 2: Обработка сметы и подбор аналогов в СПЛЭШ 2.0

Жизненный цикл обработки входящей PDF/Excel спецификации от конкурента:

```mermaid
sequenceDiagram
    autonumber
    actor Manager as Менеджер / Снабженец
    participant Nginx as Nginx (splash.heuristics.ru)
    participant Backend as Express Backend (:3006)
    participant Extractor as Axis Extractor
    participant DB as PostgreSQL 15 (:5434)
    participant LLM as DeepSeek / Ollama

    Manager->>Nginx: POST /api/v2/documents/analyze (файл сметы)
    Nginx->>Backend: proxy_pass 127.0.0.1:3006
    Backend->>Extractor: Извлечение текста и позиций SKU
    alt Стандартное правило классификации
        Extractor->>DB: Поиск по известным паттернам и осям
    else Нестандартное или зашумлённое наименование
        Backend->>LLM: Промпт нормализации и детекции осей
        LLM-->>Backend: JSON с осями (сечение, жилы, ГОСТ)
    end
    Backend->>DB: Выборка кандидатов SUPRLAN из каталога (15 469 SKU)
    Backend->>Backend: Расчет скоринга S(a, b) с учетом весов
    Backend-->>Nginx: 200 OK + JSON (Спецификация + Рекомендованные аналоги + Гэпы)
    Nginx-->>Manager: Отображение интерактивной таблицы подбора
```
