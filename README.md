# CRM System - Project Management & Developer Tracking

Полноценная CRM-система для управления проектами и разработчиками с ролевым доступом и React фронтендом.

## Технологии

### Backend
- Django 5.2.8
- Django REST Framework 3.15.2
- Django CORS Headers
- Django Filter
- drf-spectacular (API documentation)
- python-decouple (environment variables)

### Frontend
- React 18.3
- React Router v6
- TanStack Query (React Query)
- Axios
- Vite

## Функциональность

### Ролевая система доступа

1. **Admin (Генеральный/Технический директор)**
   - Полный доступ ко всем данным
   - Видит всё: проекты, разработчиков, финансы, документы
   - Может создавать, редактировать и удалять любые записи

2. **PM (Project Manager)**
   - Видит только свои проекты
   - Видит всех разработчиков (кроме паспортных данных и зарплат)
   - Может создавать и редактировать проекты

3. **DEV (Developer)**
   - Видит только проекты, к которым назначен
   - Не видит: суммы проектов, заказчиков, документы
   - Видит только свой профиль разработчика

### Основные возможности

- ✅ Управление проектами с этапами (stages в JSON формате)
- ✅ Управление разработчиками
- ✅ Валидация данных (completion_percent 0-100, salary > 0 и т.д.)
- ✅ Обработка ошибок с логированием
- ✅ API документация (Swagger UI)
- ✅ Фильтрация, поиск и сортировка
- ✅ Пагинация
- ✅ Token-based authentication

## Установка

### Требования

- Python 3.10+
- Node.js 18+
- npm или yarn

### 1. Backend Setup

```bash
# Перейти в директорию проекта
cd CrmTestTask

# Создать виртуальное окружение
python -m venv venv

# Активировать виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Создать миграции
python manage.py makemigrations

# Применить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser

# Создать папку для логов
mkdir logs

# Запустить сервер разработки
python manage.py runserver
```

Backend будет доступен на http://127.0.0.1:8000

### 2. Frontend Setup

```bash
# Перейти в директорию frontend
cd frontend

# Установить зависимости
npm install

# Запустить dev сервер
npm run dev
```

Frontend будет доступен на http://localhost:3000

## Использование

### Доступ к приложению

1. **Админ панель Django**: http://127.0.0.1:8000/admin/
2. **API документация**: http://127.0.0.1:8000/api/docs/
3. **React приложение**: http://localhost:3000

### Создание тестовых пользователей

```python
python manage.py shell

from users.models import User
from crm.models import Developer

# Admin
admin = User.objects.create_user(
    username='admin',
    password='admin123',
    role='ADMIN',
    first_name='Admin',
    email='admin@crm.com'
)

# Project Manager
pm = User.objects.create_user(
    username='pm',
    password='pm123',
    role='PM',
    first_name='Project Manager',
    email='pm@crm.com'
)

# Developer
dev_user = User.objects.create_user(
    username='dev',
    password='dev123',
    role='DEV',
    first_name='Developer',
    email='dev@crm.com'
)

# Создать профиль разработчика
Developer.objects.create(
    user=dev_user,
    full_name='John Developer',
    position='Senior Python Developer',
    cooperation_format='FULL_TIME',
    contacts='john@email.com, +1234567890',
    salary=5000,
    workload='Full-time',
    competencies='Python, Django, React',
    strengths='Fast learner, good communication',
    weaknesses='Needs more experience with DevOps'
)
```

### API Endpoints

#### Authentication
```
POST   /api/auth/login/    - Login (получить token)
POST   /api/auth/logout/   - Logout (удалить token)
GET    /api/auth/me/       - Получить текущего пользователя
```

#### Projects
```
GET    /api/projects/           - Список проектов
POST   /api/projects/           - Создать проект (Admin/PM)
GET    /api/projects/{id}/      - Детали проекта
PUT    /api/projects/{id}/      - Обновить проект (Admin/PM)
PATCH  /api/projects/{id}/      - Частично обновить (Admin/PM)
DELETE /api/projects/{id}/      - Удалить проект (Admin/PM)
GET    /api/projects/{id}/developers/ - Разработчики проекта
```

#### Developers
```
GET    /api/developers/         - Список разработчиков
POST   /api/developers/         - Создать разработчика (Admin)
GET    /api/developers/{id}/    - Детали разработчика
PUT    /api/developers/{id}/    - Обновить (Admin)
PATCH  /api/developers/{id}/    - Частично обновить (Admin)
DELETE /api/developers/{id}/    - Удалить (Admin)
GET    /api/developers/{id}/projects/ - Проекты разработчика
```

### Пример запроса

```bash
# Login
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Получить проекты
curl http://127.0.0.1:8000/api/projects/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

## Структура проекта

```
CrmProject/
├── crm/                    # Основное приложение CRM
│   ├── models.py          # Модели Project и Developer
│   ├── serializers.py     # DRF сериализаторы с ролевым доступом
│   ├── views.py           # ViewSets с обработкой ошибок
│   ├── permissions.py     # Кастомные права доступа
│   ├── admin.py           # Django Admin с ролевым доступом
│   └── urls.py            # API routes
├── users/                  # Приложение пользователей
│   ├── models.py          # Кастомная модель User с ролями
│   ├── views.py           # Auth endpoints
│   └── urls.py            # Auth routes
├── crm_system/            # Настройки проекта
│   ├── settings.py        # Конфигурация (DRF, CORS, logging)
│   └── urls.py            # Главный URL config
├── frontend/              # React приложение
│   ├── src/
│   │   ├── components/    # React компоненты
│   │   ├── pages/         # Страницы приложения
│   │   ├── contexts/      # Context API (Auth)
│   │   ├── services/      # API клиент (axios)
│   │   └── main.jsx       # Entry point
│   ├── package.json
│   └── vite.config.js
├── .env                   # Environment variables (НЕ в git!)
├── .env.example          # Пример env файла
├── .gitignore
├── requirements.txt
└── README.md
```

## Исправленные проблемы

### Backend
✅ **stages → JSONField** - этапы проекта теперь в структурированном формате
✅ **Валидация completion_percent** - добавлены validators (0-100)
✅ **Убраны Django Groups** - используется только поле role
✅ **Обработка ошибок** - try-except блоки во всех views
✅ **SECRET_KEY в .env** - больше не в коде
✅ **Logging** - настроено логирование ошибок
✅ **Индексы БД** - добавлены db_index для часто запрашиваемых полей
✅ **N+1 запросы** - используется select_related и prefetch_related
✅ **Валидация файлов** - FileExtensionValidator для documents

### API
✅ **REST API** - полноценный API с DRF
✅ **Token authentication** - безопасная аутентификация
✅ **CORS** - настроен для React
✅ **API документация** - Swagger UI
✅ **Сериализаторы по ролям** - разные уровни доступа
✅ **Permissions** - кастомные права доступа

### Frontend
✅ **React приложение** - современный SPA
✅ **Роутинг** - React Router с защищенными маршрутами
✅ **State management** - Context API + TanStack Query
✅ **Auth система** - login/logout с токенами
✅ **Ролевой UI** - интерфейс адаптируется под роль
✅ **Responsive design** - адаптивная вёрстка

## Рекомендации для продакшена

### Критические
- [ ] Сменить SECRET_KEY в .env
- [ ] Установить DEBUG=False
- [ ] Настроить ALLOWED_HOSTS
- [ ] Переключиться на PostgreSQL
- [ ] Настроить HTTPS
- [ ] Зашифровать passport_data

### Важные
- [ ] Настроить мониторинг (Sentry)
- [ ] Настроить backup БД
- [ ] Добавить rate limiting
- [ ] Настроить CDN для статики
- [ ] Добавить тесты (pytest для backend, Jest для frontend)

## Поддержка

При возникновении проблем:
1. Проверьте логи в папке `logs/django.log`
2. Проверьте консоль браузера для frontend ошибок
3. Убедитесь что backend и frontend запущены одновременно
4. Проверьте что все зависимости установлены

## Лицензия

Proprietary - внутренний проект компании
