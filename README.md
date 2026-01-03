# Stripe Payment

Проект представляет собой Django-приложение с интеграцией Stripe API для обработки платежей.

## Основные возможности
- Управление товарами (создание, редактирование и удаление товаров)
- Мультивалютность (поддержка USD и EUR)
- Два способа оплаты (Stripe Checkout и Stripe Elements)
- Система заказов
- Скидки и налоги
- Адаптивный интерфейс с современным дизайном
- Полная административная панель Django
- Docker поддержка для быстрого развертывания
---
## Автор
**Диана Шакирова**  
[![GitHub](https://img.shields.io/badge/GitHub-DianaShakirovaM-black)](https://github.com/DianaShakirovaM)  

## Установка

### Технологии
- Backend: Django 4.2, Django REST Framework
- Платежи: Stripe API
- Frontend: HTML, CSS, JavaScript, Stripe.js
- База данных: SQLite,
- Контейнеризация: Docker, Docker Compose

### Требования
- Python 3.11+
- Docker 20.10+ (опционально)
- Stripe аккаунт (тестовый или продакшен)

### Локальный запуск
1. Клонируйте репозиторий:
```bash
   git clone https://github.com/DianaShakirovaM/payments.git
   cd payments
```
2. Установите зависимости:
```bash
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
```
3.Примените миграции:
```bash
  python manage.py migrate
  python manage.py import_ingredients_json
  python manage.py import_tags_json
```
4. Запустите сервер:
```bash
  python manage.py runserver
```
---
## Доступы
 - [Админ-панель](https://dianapayments.pythonanywhere.com/admin/)
 - [Товар (Euro)](https://dianapayments.pythonanywhere.com/item/1/)
 - [Товар (USD)](https://dianapayments.pythonanywhere.com/item/2/)
 ---
## Примеры запросов
1. Получение списка товаров
```bash
GET http://localhost:8000/api/items/
```
2. Получение Stripe Payment Intent
```bash
GET http://localhost:8000/buy/1/
```
3. Создание заказа
```bash
POST http://localhost:8000/api/orders/ \
```
```json
  {
    "items": [
      {"item_id": 1, "quantity": 2},
      {"item_id": 2, "quantity": 1}
    ],
    "discount": 1,
    "tax": 1
  }'
```
