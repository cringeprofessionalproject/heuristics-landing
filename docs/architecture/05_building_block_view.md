> 🤖 Документация сгенерирована автоматически с помощью скилла **arc42-documenter**.

# 5. Структура компонентов (Building Block View)

## 5.1 Уровень 1: Компоненты лендинга и фронтенд-модулей

Репозиторий `heuristics-landing` организован как модульный набор статических страниц и визуализаций:

```mermaid
graph TD
    subgraph HeuristicsLanding ["heuristics-landing Repository"]
        Index["index.html\n(Главный лендинг + Canvas Matching)"]
        Instruments["instruments.html\n(Каталог продуктов: SPLASH, ColumnMapper)"]
        Publications["publications.html\n(Технические отчёты и статьи)"]
        ApiDocs["api.html\n(Интерактивная документация REST API)"]
        Showcase["_showcase.html\n(Дизайн-витрина стилей)"]
        
        subgraph Styles ["Стили и темы оформления"]
            InstCSS["institution.css (Основной академический)"]
            SplashCSS["splash-style.css"]
            SwissCSS["swiss.css"]
            PrecisionCSS["precision.css"]
        end
        
        CanvasEngine["Canvas Match Visualizer\n(main.js / inline)"]
    end

    Index --> InstCSS
    Index --> CanvasEngine
    Instruments --> InstCSS
    Publications --> InstCSS
    ApiDocs --> InstCSS
```

## 5.2 Уровень 2: Компоненты бэкенда СПЛЭШ 2.0 (`splash2`)

Бэкенд СПЛЭШ 2.0 представляет собой модульный Express.js монолит:

```mermaid
graph TD
    subgraph SplashBackend ["SPLASH 2.0 Backend (Node.js)"]
        Server["server.js\n(HTTP Server, Middleware, Router setup)"]
        
        subgraph Routes ["REST API Routes (/api/v2)"]
            AuthRoute["auth.js (JWT login, roles)"]
            MatchingRoute["matching.js (Осевой скоринг, поиск аналогов)"]
            ProcessRoute["process.js (Парсинг спецификаций, классификация)"]
            DataRoute["data.js (Номенклатура, остатки, ABC)"]
            CatalogRoute["catalog.js (BOM250 карточки)"]
            AdminRoute["admin.js (Управление пользователями, файлы)"]
        end

        subgraph CoreServices ["Core Services"]
            ScoringEngine["scoring-engine.js (Алгоритм сравнения осей)"]
            Extractor["axis-extractor.js (Извлечение параметров из SKU)"]
            LLMClient["llm-client.js (Интеграция с Ollama / DeepSeek)"]
            DBPool["db.js (PostgreSQL Connection Pool)"]
        end
    end

    Server --> Routes
    MatchingRoute --> ScoringEngine
    ProcessRoute --> Extractor
    ProcessRoute --> LLMClient
    Routes --> DBPool
```

## 5.3 Ответственность модулей

| Модуль | Расположение | Ответственность |
|---|---|---|
| **Canvas Matcher** | `index.html` (JS Engine) | Рендеринг интерактивного графа сопоставления объектов А и В в реальном времени на HTML5 Canvas. |
| **API Showcase** | `api.html` | Документирование REST API v2 для интеграции со сторонними ERP и CRM системами. |
| **Scoring Engine** | `splash2/backend/` | Взвешенный расчет метрики сходства $S(a, b)$ между артикулами по 11 категориям. |
| **LLM Client** | `splash2/backend/llm-client.js` | Асинхронное взаимодействие с нейросетевыми провайдерами для генерации структурированных метаданных. |
| **PostgreSQL Pool** | `splash2/backend/db.js` | Высокопроизводительный пул подключений к БД `splash2` на порту 5434. |
