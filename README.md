# AI-менеджер продаж — Telegram-бот

Бот квалифицирует клиентов через диалог с Claude
и мгновенно присылает лид тебе в Telegram.

---

## Запуск за 10 минут

### Шаг 1 — Токен бота
1. Открой @BotFather в Telegram
2. Напиши `/newbot`
3. Введи название: `AI Business Solutions`
4. Введи username: `AIBusinessBot` (или любой свободный)
5. Скопируй токен → это BOT_TOKEN

### Шаг 2 — Узнай свой chat_id
1. Напиши @userinfobot в Telegram
2. Скопируй число после `Id:` → это OWNER_CHAT_ID

### Шаг 3 — Ключ Claude
1. Зайди на console.anthropic.com
2. API Keys → Create Key
3. Скопируй ключ → это ANTHROPIC_API_KEY

### Шаг 4 — Деплой на Railway
1. Зайди на railway.app → New Project → Deploy from GitHub
2. Загрузи эту папку в GitHub
3. В Railway: Variables → добавь три переменные:
   - BOT_TOKEN
   - ANTHROPIC_API_KEY
   - OWNER_CHAT_ID
4. Deploy → готово!

---

## Как работает

Клиент пишет /start → бот задаёт 4 вопроса → рекомендует тариф
→ просит имя и телефон → тебе приходит уведомление:

🔥 Новый лид — ГОРЯЧИЙ
────────────────────────────
👤 Имя: Александр
📞 Телефон: +7 999 123 45 67
🏢 Ниша: Стоматология
😤 Боль: Теряем заявки ночью
💰 Тариф: БИЗНЕС
────────────────────────────
💬 Telegram: @username
🕐 17.06.2026 в 21:55

---

## Команды бота

/start — начать диалог
/reset — сбросить историю

---

## Переменные окружения

| Переменная        | Описание                    |
|-------------------|-----------------------------|
| BOT_TOKEN         | Токен от @BotFather         |
| ANTHROPIC_API_KEY | Ключ с console.anthropic.com|
| OWNER_CHAT_ID     | Твой Telegram chat_id       |
