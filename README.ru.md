![Header](header.png)

<div align="center">

# tgauth

**Система OTP-аутентификации на основе Telegram**

[![License](https://img.shields.io/badge/license-MIT-2C2C2C?style=for-the-badge&labelColor=1E1E1E)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.x-2C2C2C?style=for-the-badge&logo=python&labelColor=1E1E1E)]()
[![FastAPI](https://img.shields.io/badge/fastapi-verify%20api-2C2C2C?style=for-the-badge&logo=fastapi&labelColor=1E1E1E)]()
[![Telegram](https://img.shields.io/badge/telegram-bot-2C2C2C?style=for-the-badge&logo=telegram&labelColor=1E1E1E)]()

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

## ■ Repository Structure

```
backend/
  main.py     FastAPI app — POST /verify, in-memory code store
  bot.py      Telegram bot (telebot) — approval, code generation, resources
  server.py   Flask routes — /auth form and per-resource redirects
frontend/     placeholder package
```

## ■ Скриншоты

<div align="center">

![Screenshot](screenshots/main.png)

*Главная страница аутентификации*

</div>

## ■ Запуск

```bash
# Verify API (FastAPI — module exposes `app`, run with uvicorn)
cd backend && uvicorn main:app

# Telegram bot configuration (read from env in bot.py):
#   TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID,
#   WEB_SERVER_HOST, WEB_SERVER_PORT, CODE_EXPIRATION_TIME
```

## ■ License

MIT © [pluttan](https://github.com/pluttan)
