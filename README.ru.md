<div align="center">

# tgauth

**Система OTP-аутентификации на основе Telegram**

</div>

Сервис аутентификации, использующий Telegram в качестве канала доставки OTP. Одобренный пользователь запрашивает одноразовый код у Telegram-бота, затем вводит его на веб-странице для подтверждения личности. Бот управляет одобрением новых пользователей администратором и назначением ресурсов каждому пользователю; отдельный сервис FastAPI предоставляет эндпоинт `POST /verify`, который проверяет код и возвращает токен сессии.

## ■ Возможности

- ❖ **Telegram OTP** — одноразовые коды, генерируемые ботом (`secrets.token_hex`) и доставляемые через Telegram
- ❖ **Проверка кода** — коды с ограниченным временем жизни, одноразовые (по умолчанию 5 мин в verify API, 10 мин в боте)
- ❖ **Одобрение администратором** — первый пользователь становится администратором; новые пользователи одобряются или отклоняются через inline-кнопки
- ❖ **Контроль доступа к ресурсам** — администратор выдаёт/отзывает ресурсы пользователям через `/manage`; пользователи просматривают свои ресурсы через `/resources`
- ❖ **Эндпоинт FastAPI для проверки** — `POST /verify` проверяет код и возвращает токен сессии
- ❖ **Маршрутизация аутентификации Flask** — маршрут формы `/auth` и маршруты перенаправления для каждого ресурса

## ■ Стек

<div align="center">

| Компонент | Технология |
|-----------|------------|
| Бот | Python (pyTelegramBotAPI) |
| Verify API | FastAPI + Pydantic |
| Маршрутизация аутентификации | Flask |

</div>

## ■ Как это работает

```
1. Пользователь отправляет команду Telegram-боту для получения одноразового кода.
2. Бот генерирует код через secrets.token_hex и доставляет его пользователю через Telegram.
3. Пользователь вводит код в веб-форму /auth, обслуживаемую Flask.
4. Код проверяется эндпоинтом FastAPI POST /verify.
5. Verify API сверяет код с хранилищем в памяти (ограниченное время жизни, одноразовый) и при успехе возвращает токен сессии.
6. Администратор управляет одобрением пользователей и доступом к ресурсам через inline-кнопки и команды /manage в боте.
```

## ■ Скриншоты

<div align="center">

![Screenshot](screenshots/main.png)

*Главная страница аутентификации*

</div>

## ■ Использование

```bash
# Verify API (FastAPI — module exposes `app`, run with uvicorn)
cd backend && uvicorn main:app

# Telegram bot configuration (read from env in bot.py):
#   TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID,
#   WEB_SERVER_HOST, WEB_SERVER_PORT, CODE_EXPIRATION_TIME
```

## ■ Структура репозитория

```
backend/
  main.py     FastAPI app — POST /verify, in-memory code store
  bot.py      Telegram bot (telebot) — approval, code generation, resources
  server.py   Flask routes — /auth form and per-resource redirects
frontend/     placeholder package
```

## ■ Лицензия

MIT © [pluttan](https://github.com/pluttan)
