> 🤖 Документация сгенерирована автоматически с помощью скилла **arc42-documenter**.

# 3. Границы системы и контекст (System Scope and Context)

## 3.1 Бизнес- и технический контекст

Экосистема разделена на два ключевых контура:
1. **Edge / Презентационный контур (GitHub Pages + DNS):** Обслуживает статический фронтенд `heuristics.ru` через CDN GitHub с поддержкой HTTPS.
2. **Core / Вычислительный контур (VPS 92.38.95.125):** Обслуживает поддомены, Nginx reverse proxy, Node.js бэкенды (PM2), Docker-контейнеры и базы данных PostgreSQL.

```mermaid
flowchart TD
    subgraph Users ["Внешний мир / Клиенты"]
        Visitor["Посетитель / Партнёр"]
        B2BUser["Менеджер / Аналитик (СПЛЭШ)"]
        ChatUser["Пользователь Matrix"]
    end

    subgraph EdgeLayer ["Edge Layer (GitHub Pages CDN)"]
        Landing["heuristics.ru\n(Landing / Showcase / Docs)"]
    end

    subgraph VPS ["VPS Host (92.38.95.125 - Ubuntu)"]
        Nginx["Nginx Reverse Proxy\n(SSL Let's Encrypt)"]
        
        subgraph PM2Apps ["PM2 Runtime"]
            SplashBackend["SPLASH 2.0 Backend\n(port :3006)\nExpress.js"]
            Splash1Backend["SPLASH 1.0 Backend\n(port :3003)\nExpress.js"]
            ThesisVault["Thesis Vault\n(port :3005)"]
        end

        subgraph DockerLayer ["Docker Containers"]
            SplashPG["splash-postgres\n(port :5434 -> 5432)\nDB: splash2, splash_db"]
            CrawlerPG["postgres-crawler\n(port :5433 -> 5432)"]
            StirlingPDF["stirling-pdf\n(port :8080)"]
            MatrixSynapse["matrix-synapse\n(port :8008, :3478 coturn)"]
            KonzeptBureau["konzept-bureau\n(port :8085)"]
            TwentyCRM["twenty-crm\n(port :3000)"]
        end
    end

    subgraph ExternalLLM ["Внешние ИИ Провайдеры"]
        DeepSeek["DeepSeek API / Ollama Cloud"]
    end

    Visitor -->|HTTPS:443| Landing
    B2BUser -->|HTTPS:443 splash.heuristics.ru| Nginx
    Visitor -->|HTTPS:443 pdf.heuristics.ru| Nginx
    ChatUser -->|HTTPS:443 matrix.heuristics.ru| Nginx

    Nginx -->|proxy :3006| SplashBackend
    Nginx -->|proxy :3003| Splash1Backend
    Nginx -->|proxy :3005| ThesisVault
    Nginx -->|proxy :8080| StirlingPDF
    Nginx -->|proxy :8008| MatrixSynapse

    SplashBackend -->|TCP:5434| SplashPG
    SplashBackend -->|HTTPS REST| DeepSeek
```

## 3.2 Описание внешних и внутренних интерфейсов

| Узел | Протокол / Порт | Назначение |
|---|---|---|
| **heuristics.ru** | HTTPS:443 (GitHub Pages) | Статический представительский сайт, документация методов, API и публикаций. |
| **splash.heuristics.ru** | HTTPS:443 → `localhost:3006` | Прикладная SPA и REST API v2 для подбора аналогов кабельной продукции. |
| **pdf.heuristics.ru** | HTTPS:443 → `localhost:8080` | Автономный сервис инженерии и конвертации PDF документов (Stirling-PDF). |
| **matrix.heuristics.ru** | HTTPS:443 → `localhost:8008` | Защищённый Matrix homeserver + Coturn STUN/TURN сервер для аудио/видео. |
| **PostgreSQL 15 (`splash-postgres`)** | Внутренний порт `5434` | Хранилище номенклатуры (15 469 SKU), правил сопоставления, весов осей и сессий. |
| **LLM Provider** | HTTPS REST | Генерация товарных описаний и распознавание сложных сущностей в сметах. |
