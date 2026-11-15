# 🤫 Шёпот (Whisper) — Telegram-бот анонимных сообщений

**Вирусный бот для пассивного заработка через Telegram Stars**

## 🎯 Концепция

Пользователь получает уникальную ссылку → делится ей в соцсетях → друзья и подписчики отправляют ему анонимные сообщения → **каждый пользователь становится промоутером бота**.

### Почему это работает?
- 🧠 Основано на психологии: любопытство + валидация
- 📈 Самопродвигающийся: каждый пользователь делится ссылкой
- 💰 Монетизация через Telegram Stars (встроенная платёжная система)
- 🔄 Сетевой эффект: чем больше людей — тем больше сообщений
- 🖥 Минимальные затраты: SQLite + любой VPS за $3-5/мес

## 🚀 Быстрый старт

### 1. Создай бота
1. Открой [@BotFather](https://t.me/BotFather) в Telegram
2. Отправь `/newbot` и следуй инструкциям
3. Скопируй токен бота
4. **Важно**: отправь `/setinline` и включи inline mode
5. Отправь `/setpayments` и включи Telegram Stars

### 2. Настрой проект
```bash
# Клонируй/скопируй файлы проекта
cd whisper-bot

# Установи зависимости
pip install -r requirements.txt

# Создай .env файл
cp .env.example .env
```

### 3. Заполни .env
```env
BOT_TOKEN=7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_IDS=123456789
BOT_USERNAME=WhisperAnonBot
```

- `BOT_TOKEN` — токен от BotFather
- `ADMIN_IDS` — твой Telegram ID (узнать: [@userinfobot](https://t.me/userinfobot))
- `BOT_USERNAME` — username бота без @

### 4. Запусти
```bash
python bot.py
```

## 💰 Монетизация

### Telegram Stars ⭐
Бот использует **Telegram Stars** — встроенную платёжную систему Telegram. Пользователи покупают Stars в приложении Telegram, а ты выводишь заработок через [Fragment](https://fragment.com).

| Услуга | Цена |
|--------|------|
| 🔓 Раскрыть отправителя | 49 ⭐ |
| ⭐ Premium неделя | 149 ⭐ |
| ⭐ Premium месяц | 449 ⭐ |

### Premium возможности
- 🔓 Раскрытие отправителей
- 🔤 Подсказки: первая буква имени, длина
- 📨 200 сообщений/день (vs 15 бесплатных)
- ✏️ Персональное приветствие для анонимной страницы

### Реферальная система (вирусный рост)
| Рефералов | Награда |
|-----------|---------|
| 3 | 1 бесплатное раскрытие |
| 10 | Premium на неделю |
| 25 | Premium на месяц |

## 📁 Структура проекта

```
whisper-bot/
├── bot.py              # Точка входа, запуск бота
├── config.py           # Настройки и константы
├── database.py         # SQLite база данных
├── utils.py            # Утилиты
├── keyboards.py        # Inline-клавиатуры
├── middlewares.py       # Middleware (антиспам, БД)
├── handlers/
│   ├── __init__.py
│   ├── start.py        # /start, регистрация, deep links
│   ├── messages.py     # Анонимные сообщения, ответы, раскрытие
│   ├── profile.py      # Профиль, настройки
│   ├── premium.py      # Premium, оплата Stars
│   ├── referral.py     # Реферальная система
│   └── admin.py        # Админ-панель, рассылка
├── requirements.txt    # Зависимости
├── .env.example        # Шаблон конфигурации
└── README.md           # Документация
```

## 🛡 Админ-команды

| Команда | Описание |
|---------|----------|
| `/admin` или `/stats` | Статистика бота |
| `/broadcast текст` | Рассылка всем пользователям |
| `/ban user_id` | Заблокировать пользователя |
| `/unban user_id` | Разблокировать |

## 🌐 Деплой на сервер

### Вариант 1: VPS (рекомендуется)

```bash
# На Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip python3-venv

# Создаём venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Запуск через systemd (создай /etc/systemd/system/whisper.service)
```

**Файл systemd:**
```ini
[Unit]
Description=Whisper Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/whisper-bot
Environment=PATH=/home/ubuntu/whisper-bot/venv/bin
ExecStart=/home/ubuntu/whisper-bot/venv/bin/python bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable whisper
sudo systemctl start whisper
sudo systemctl status whisper
```

### Вариант 2: Бесплатный хостинг

- **[Railway.app](https://railway.app)** — бесплатный тариф, легко деплоить
- **[Render.com](https://render.com)** — бесплатный тариф
- **[fly.io](https://fly.io)** — бесплатный тариф с 3 VM

### Вариант 3: Oracle Cloud Free Tier

Навсегда бесплатный VPS (1 CPU, 1 GB RAM) — идеально для бота:
1. Зарегистрируйся на [cloud.oracle.com](https://cloud.oracle.com)
2. Создай «Always Free» VM (Ubuntu)
3. Разверни бота по инструкции для VPS

## 📈 Стратегия продвижения

### День 1-7: Запуск
1. Отправь ссылку 20-30 друзьям
2. Попроси их поделиться в Stories
3. Размести в 5-10 Telegram чатах

### День 7-30: Рост
1. Создай TikTok/Reels контент: «Мне пишут анонимно... 😱»
2. Скриншоты смешных/интересных сообщений (с разрешения)
3. Telegram канал бота с лучшими анонимками

### Месяц 2+: Масштабирование
1. Коллаборации с блогерами
2. Конкурсы: «Кто получит больше сообщений»
3. Новые фичи по запросам пользователей

## 📊 Прогноз заработка

| Пользователей | ~Premium конверсия (2%) | Доход/мес ⭐ | ~USD/мес* |
|---------------|------------------------|-------------|-----------|
| 1 000 | 20 | 8 980 | ~$90 |
| 5 000 | 100 | 44 900 | ~$450 |
| 10 000 | 200 | 89 800 | ~$900 |
| 50 000 | 1 000 | 449 000 | ~$4 500 |

*Примерная конвертация Stars → USD через Fragment.com

## ⚙️ Кастомизация

### Изменить цены
Отредактируй `config.py`:
```python
PRICE_UNMASK = 49            # Раскрытие отправителя
PRICE_PREMIUM_WEEK = 149     # Premium неделя
PRICE_PREMIUM_MONTH = 449    # Premium месяц
```

### Изменить лимиты
```python
FREE_MESSAGES_PER_DAY = 15   # Бесплатных сообщений
MESSAGE_COOLDOWN_SECONDS = 20 # Пауза между сообщениями
```

### Добавить стоп-слова
```python
BANNED_WORDS = ["мат1", "мат2", "оскорбление"]
```

## 📄 Лицензия

MIT — используй, модифицируй, зарабатывай. Удачи! 🚀
