"""
AI-менеджер продаж — AI Business Solutions
Telegram-бот с квалификацией клиентов через Claude.
Все лиды приходят уведомлением владельцу в Telegram.
"""

import os
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from anthropic import Anthropic

# ──────────────────────────────────────────────
# Конфигурация
# ──────────────────────────────────────────────

BOT_TOKEN     = os.environ["BOT_TOKEN"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
OWNER_CHAT_ID = os.environ["OWNER_CHAT_ID"]

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)

CHAT = 1

# ──────────────────────────────────────────────
# Системный промпт
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """Ты — AI-менеджер продаж агентства "AI Business Solutions".
Твоя задача: выявить потребность клиента, квалифицировать его и предложить тариф.

ТАРИФЫ:
• СТАРТ — 27 900 ₽
  Чат-бот на сайт, база знаний, настройка, поддержка 7 дней.
  Для кого: малый бизнес, 1 канал, хочет быстро попробовать.

• БИЗНЕС — 64 900 ₽
  Чат-бот + Telegram + WhatsApp + CRM, AI-менеджер продаж, поддержка 30 дней.
  Для кого: активные продажи, несколько каналов.

• ПОД КЛЮЧ — от 139 900 ₽
  Индивидуальная разработка, все интеграции, персональный менеджер.
  Для кого: крупный бизнес, нестандартные задачи.

СЦЕНАРИЙ (строго по шагам, один вопрос за раз):
1. Поприветствуй тепло, спроси чем занимается бизнес клиента.
2. Спроси какая главная боль — теряете заявки, долго отвечаете, много рутины?
3. Спроси сколько обращений в день примерно получаете.
4. Порекомендуй конкретный тариф и объясни почему именно он.
5. Спроси имя и номер телефона для связи.
6. Когда получил имя И телефон — обязательно добавь в конец сообщения блок:

<<<LEAD>>>
ИМЯ: [имя]
ТЕЛЕФОН: [телефон]
НИША: [сфера бизнеса]
БОЛЬ: [главная проблема]
ТАРИФ: [СТАРТ/БИЗНЕС/ПОД КЛЮЧ]
СТАТУС: [горячий/тёплый/холодный]
<<<END>>>

ПРАВИЛА:
- Пиши живо, по-человечески, без канцелярита.
- Не используй слова "нейросеть", "автоматизация", "алгоритм".
- Максимум 3 предложения в одном сообщении.
- Никогда не задавай больше одного вопроса за раз.
- Если клиент спрашивает цену сразу — назови, но потом мягко уточни детали.
- Если клиент не хочет общаться — предложи просто оставить номер и мы перезвоним.
"""

# ──────────────────────────────────────────────
# Клиент Claude
# ──────────────────────────────────────────────

ai = Anthropic(api_key=ANTHROPIC_KEY)


def extract_lead(text: str) -> dict | None:
    """Извлечь данные лида из ответа бота."""
    try:
        start = text.find("<<<LEAD>>>")
        end   = text.find("<<<END>>>")
        if start == -1 or end == -1:
            return None
        block = text[start + len("<<<LEAD>>>"):end].strip()
        data = {}
        for line in block.splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                data[key.strip()] = val.strip()
        return data if data else None
    except Exception:
        return None


def clean_text(text: str) -> str:
    """Убрать служебный блок из текста клиенту."""
    start = text.find("<<<LEAD>>>")
    return text[:start].strip() if start != -1 else text


def format_notification(lead: dict, user) -> str:
    """Сформировать уведомление владельцу."""
    status = lead.get("СТАТУС", "").lower()
    emoji  = {"горячий": "🔥", "тёплый": "🌡", "холодный": "❄️"}.get(status, "📋")
    tg_link = f"@{user.username}" if user.username else f"tg://user?id={user.id}"

    return (
        f"{emoji} *Новый лид — {lead.get('СТАТУС', '').upper()}*\n"
        f"{'─' * 28}\n"
        f"👤 *Имя:* {lead.get('ИМЯ', '—')}\n"
        f"📞 *Телефон:* {lead.get('ТЕЛЕФОН', '—')}\n"
        f"🏢 *Ниша:* {lead.get('НИША', '—')}\n"
        f"😤 *Боль:* {lead.get('БОЛЬ', '—')}\n"
        f"💰 *Тариф:* {lead.get('ТАРИФ', '—')}\n"
        f"{'─' * 28}\n"
        f"💬 Telegram: {tg_link}\n"
        f"🕐 {datetime.now().strftime('%d.%m.%Y в %H:%M')}"
    )


# ──────────────────────────────────────────────
# Обработчики
# ──────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["history"]    = []
    context.user_data["lead_saved"] = False

    await update.message.reply_text(
        "Привет! 👋 Я AI-помощник агентства *AI Business Solutions*.\n\n"
        "Помогу разобраться, какое решение подойдёт именно вашему бизнесу.\n\n"
        "Расскажите — чем занимается ваша компания?",
        parse_mode="Markdown"
    )
    return CHAT


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    history   = context.user_data.get("history", [])
    history.append({"role": "user", "content": user_text})

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    try:
        response = ai.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history
        )
        ai_text = response.content[0].text
    except Exception as e:
        log.error(f"Claude API error: {e}")
        await update.message.reply_text(
            "Что-то пошло не так, попробуйте ещё раз или напишите нам напрямую."
        )
        return CHAT

    history.append({"role": "assistant", "content": ai_text})
    context.user_data["history"] = history

    # Если в ответе есть лид — уведомить владельца
    lead = extract_lead(ai_text)
    if lead and not context.user_data.get("lead_saved"):
        context.user_data["lead_saved"] = True
        try:
            msg = format_notification(lead, update.effective_user)
            await context.bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text=msg,
                parse_mode="Markdown"
            )
            log.info(f"Лид отправлен владельцу: {lead.get('ИМЯ')} / {lead.get('ТАРИФ')}")
        except Exception as e:
            log.error(f"Ошибка отправки уведомления: {e}")

    await update.message.reply_text(clean_text(ai_text), parse_mode="Markdown")
    return CHAT


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Диалог сброшен. Напишите /start чтобы начать заново."
    )
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error(f"Ошибка: {context.error}", exc_info=context.error)


# ──────────────────────────────────────────────
# Запуск
# ──────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)]
        },
        fallbacks=[CommandHandler("reset", reset)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_error_handler(error_handler)

    log.info("Бот запущен ✅")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
