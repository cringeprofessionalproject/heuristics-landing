> 🤖 Документация сгенерирована автоматически с помощью скилла **arc42-documenter**.

# 9. Данные и алгоритмы (Data and Algorithms)

## 9.1 Математическая модель осевого скоринга $S(a, b)$

Алгоритм подбора аналогов основан на взвешенном сравнении векторных представлений физических осей товара $a$ (запрос / конкурент) и товара $b$ (кандидат из каталога):

$$S(a, b) = \frac{\sum_{i=1}^{n} w_i \cdot \text{score}(\text{axis}_i(a), \text{axis}_i(b))}{\sum_{i=1}^{n} w_i}$$

Где:
* $\text{axis}_i$: физический параметр (сечение, количество жил, материал проводника, броня, экранирование, класс гибкости, огнестойкость нг(А)-FRLS / HF, ГОСТ).
* $w_i \in \{w_{\text{critical}}, w_{\text{high}}, w_{\text{medium}}, w_{\text{low}}\}$: вес критичности оси.
* $\text{score}(\dots) \in [0, 1]$: функция частичного совпадения (равенство, допустимая замена в сторону улучшения качества, штраф за несовместимость).

### Иерархия весов осей:
1. **Critical ($w = 100$):** Мета-категория, сечение и число жил (несовпадение дает $S=0$).
2. **High ($w = 50$):** Материал проводника (медь/алюминий), исполнение по пожарной безопасности (FRLS, HF, LTx).
3. **Medium ($w = 20$):** Наличие экрана, тип брони, класс гибкости (1 vs 5 класс).
4. **Low ($w = 5$):** Цвет оболочки, фасовка (бухта/барабан), длина.

## 9.2 Структура ключевых таблиц базы данных `splash2`

```sql
-- Мета-категории и оси
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(64) UNIQUE NOT NULL,
    description TEXT
);

-- Каталог номенклатуры (15 469 SKU)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    category_id INT REFERENCES categories(id),
    brand VARCHAR(128) NOT NULL,
    sku VARCHAR(255) NOT NULL,
    name TEXT NOT NULL,
    axes_json JSONB NOT NULL DEFAULT '{}',
    is_suprlan BOOLEAN DEFAULT FALSE,
    in_stock NUMERIC DEFAULT 0,
    price_base NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс по осям для ускоренного поиска кандидатов
CREATE INDEX idx_products_axes ON products USING GIN (axes_json);
CREATE INDEX idx_products_category ON products(category_id);
```
