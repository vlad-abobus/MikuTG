# -*- coding: utf-8 -*-
"""
Miku Telegram Bot — enhanced version with scenarios and fetishes.
"""

import os
import sys
import re
import time
import json
import logging
import random
import threading
import datetime
from typing import Dict, List

import asyncio
from langdetect import detect
import g4f

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
)

# --- Логирование ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Константы и настройки ---
AUTO_RESTART_INTERVAL = 15 * 60  # 15 минут в секундах
ADMIN_USERNAME = "VladislavMorgan2"

LANG_MAP = {
    "ru": "ru",
    "uk": "ru",
    "en": "ru",
}

DEFAULT_LANG = "ru"

EMOTIONS = {
    "angry_look": "Злой взгляд",
    "embarrassed": "Смущение",
    "shocked": "Шок",
    "happy": "Счастье",
    "neutral": "Нейтральное",
    "surprised": "Удивление",
    "crying": "Плач",
    "irritated": "Раздражение",
    "sad_look": "Грусть",
    "cheerful": "Радость"
}

SPECIAL_MENTIONS = {
    "Queenfan_228": "Снейк",
    "lLucky_13l": "Лаки сладкий",
    "VladislavMorgan2": "владик",
    "@qw4ryns": "Выключательная карточка"
}

# Хранилища
chat_data: Dict[int, Dict] = {}
user_histories: Dict[int, List[Dict]] = {}
user_irritation: Dict[int, int] = {}

# --- Сценарии и фетиши ---
SCENARIOS = {
    "позы": {
        "69": "Мику переворачивается, принимая позу 69... *она нежно ласкает языком, одновременно наслаждаясь ощущениями*",
        "наездница": "Мику садится сверху, медленно двигая бёдрами... *её длинные волосы развеваются с каждым движением*",
        "обратная наездница": "Мику поворачивается спиной, садясь на партнёра... *вид её спины и шеи особенно возбуждает*",
        "догги": "Мику встаёт на колени, опираясь руками... *ритмичные толчки становятся всё интенсивнее*",
        "миссионерская": "Мику ложится на спину, обнимая партнёра... *нежные поцелуи сопровождают каждое движение*",
        "бдсм": "Мику достаёт верёвки и повязку... *лёгкая боль смешивается с удовольствием*",
        "минет": "Мику опускается на колени, беря в рот... *искусные движения языком доставляют наслаждение*",
        "куни": "Мику нежно раздвигает ноги партнёрши, приближаясь языком... *виртуозные движения вызывают стоны*",
        "на животе": "Мику ложится на живот, чувствуя толчки сзади... *удовольствие отражается на её лице*",
        "анал": "Мику смазывает анальное отверстие, медленно направляя член... *ощущение fullness overwhelms her*",
        "классика": "Мику принимает партнёра в классической позе... *нежные объятия и синхронные движения*"
    },
    "фетиши": {
        "фут фетиш": "Мику снимает туфли, демонстрируя ухоженные ступни... *она нежно массирует ими, вызывая возбуждение*",
        "подмышки": "Мику поднимает руки, обнажая подмышки... *лёгкий запах возбуждает партнёра*",
        "доминация": "Мику берёт инициативу, приказывая партнёру... *её властный тон смешивается с нежностью*"
    }
}

JOKES = [
    "Муж подходит к жене и спрашивает: жена, ты пила? А жена отвечает: нет, я болгарка!",
    "Программист на пляже: сидит с ноутбуком, к нему подходит ребёнок и спрашивает: 'Дядя, а что ты делаешь?' Программист: 'Работаю'. Ребёнок: 'А на море зачем приехал?' Программист: 'Чтобы интернет был получше'.",
    "Студент медицинского училища спрашивает у профессора: 'А правда, что алкоголь убивает клетки головного мозга?' Профессор: 'Конечно, но только самые слабые и глупые'. Студент: 'Ну, тогда мне можно...'",
    "Заходит как-то русский, немец и американец в бар. Бармен говорит: 'Извините, но у нас сегодня только виртуальное пиво'. Русский: 'Ну, хоть что-то...'"
]

class MikuTelegramBot:
    def __init__(self, token: str, auto_restart_interval: int = AUTO_RESTART_INTERVAL):
        self.token = token
        self.auto_restart_interval = auto_restart_interval
        self.application = Application.builder().token(token).build()

        # Обработчики
        self.application.add_handler(CommandHandler("miku", self.miku_command))
        self.application.add_handler(CommandHandler("set_personality", self.set_personality_command))
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("restart", self.restart_command))
        self.application.add_handler(CallbackQueryHandler(self.personality_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        self._init_chat_data(chat_id)

        welcome_text = (
            "Привет! Я Мику ♪\n\n"
            "Команды:\n"
            "/miku - поговорить со мной\n"
            "/set_personality - изменить мой характер (только для администратора)\n"
            "/restart - перезагрузить бота вручную (только для администратора)\n\n"
            "В групповом чате — используй /miku для общения со мной.\n"
            "Также могу рассказывать анекдоты: /miku анекдот")

        await update.message.reply_text(welcome_text)

    async def miku_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        chat_type = update.effective_chat.type
        username = update.effective_user.username or update.effective_user.first_name

        self._init_chat_data(chat_id)
        self._init_user_history(user_id)

        # Обработка анекдота
        if context.args and context.args[0].lower() == "анекдот":
            joke = random.choice(JOKES)
            await context.bot.send_message(chat_id=chat_id, text=f"{joke}\n\nНадеюсь, тебе понравилось! 😊")
            return

        user_text = ' '.join(context.args) if context.args else "Привет"

        # Формируем упоминание
        if update.effective_user.username in SPECIAL_MENTIONS:
            user_mention = SPECIAL_MENTIONS[update.effective_user.username]
        else:
            user_mention = f"@{username}" if update.effective_user.username else username

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        try:
            reply_text, emotion = await self._get_miku_response(chat_id, user_id, user_text)

            if chat_type in ["group", "supergroup"]:
                final_reply = f"{user_mention} {reply_text}"
            else:
                if update.effective_user.username in SPECIAL_MENTIONS:
                    final_reply = f"{SPECIAL_MENTIONS[update.effective_user.username]}, {reply_text}"
                else:
                    final_reply = reply_text

            final_reply += f"\n\n[{emotion}]"
            await context.bot.send_message(chat_id=chat_id, text=final_reply)

        except Exception as e:
            logger.exception(f"Error in miku_command: {e}")
            error_msg = f"{user_mention} Извините, произошла ошибка 😢"
            await context.bot.send_message(chat_id=chat_id, text=error_msg)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_chat.type != "private":
            return
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_text = update.message.text

        self._init_chat_data(chat_id)
        self._init_user_history(user_id)

        # Проверка на анекдот
        if user_text.lower() in ["анекдот", "расскажи анекдот", "шутка"]:
            joke = random.choice(JOKES)
            await update.message.reply_text(f"{joke}\n\nНадеюсь, тебе понравилось! 😊")
            return

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        try:
            reply_text, emotion = await self._get_miku_response(chat_id, user_id, user_text)

            if update.effective_user.username in SPECIAL_MENTIONS:
                final_reply = f"{SPECIAL_MENTIONS[update.effective_user.username]}, {reply_text}\n\n[{emotion}]"
            else:
                final_reply = f"{reply_text}\n\n[{emotion}]"
            await update.message.reply_text(final_reply)
        except Exception as e:
            logger.exception(f"Error in handle_message: {e}")
            await update.message.reply_text("Извините, разар далбаеб")

    async def set_personality_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        username = update.effective_user.username

        if username != ADMIN_USERNAME:
            await context.bot.send_message(chat_id=chat_id, text="У тебя нет доступа к панели управления ♪")
            return

        self._init_chat_data(chat_id)

        keyboard = [
            [
                InlineKeyboardButton("Вкл/Выкл NSFW", callback_data="toggle_nsfw"),
                InlineKeyboardButton("Вкл/Выкл Флирт", callback_data="toggle_flirt"),
            ],
            [
                InlineKeyboardButton("Дередере", callback_data="personality_Дередере"),
                InlineKeyboardButton("Цундере", callback_data="personality_Цундере"),
            ],
            [
                InlineKeyboardButton("Дандере", callback_data="personality_Дандере"),
                InlineKeyboardButton("Агрессивный", callback_data="personality_Агрессивный"),
            ],
            [
                InlineKeyboardButton("ЛаДере", callback_data="personality_ЛаДере"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=chat_id, text="Панель управления Мику:", reply_markup=reply_markup)

    async def personality_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        chat_id = query.message.chat.id
        self._init_chat_data(chat_id)

        if query.data == "toggle_nsfw":
            chat_data[chat_id]["nsfw_enabled"] = not chat_data[chat_id]["nsfw_enabled"]
            await query.edit_message_text(
                f"NSFW режим: {'Включен' if chat_data[chat_id]['nsfw_enabled'] else 'Выключен'}"
            )
        elif query.data == "toggle_flirt":
            chat_data[chat_id]["flirt_enabled"] = not chat_data[chat_id]["flirt_enabled"]
            await query.edit_message_text(
                f"Флирт: {'Включен' if chat_data[chat_id]['flirt_enabled'] else 'Выключен'}"
            )
        else:
            personality = query.data.split("_")[1]
            chat_data[chat_id]["personality"] = personality
            await query.edit_message_text(
                f"Характер изменен на: {personality} ♪\nТеперь я буду общаться с тобой как {personality} Мику!"
            )

    async def restart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        username = update.effective_user.username
        chat_id = update.effective_chat.id
        if username != ADMIN_USERNAME:
            await context.bot.send_message(chat_id=chat_id, text="У тебя нет прав на перезагрузку.")
            return
        await context.bot.send_message(chat_id=chat_id, text="Перезагрузка бота...")
        logger.info("Manual restart requested by admin.")
        threading.Thread(target=self._do_restart, daemon=True).start()

    def _do_restart(self):
        time.sleep(1)
        logger.info("Restarting process now.")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _init_chat_data(self, chat_id: int) -> None:
        if chat_id not in chat_data:
            chat_data[chat_id] = {
                "personality": "Дередере",
                "flirt_enabled": True,
                "nsfw_enabled": False
            }

    def _init_user_history(self, user_id: int) -> None:
        if user_id not in user_histories:
            user_histories[user_id] = []

    def _check_scenario_request(self, user_text: str) -> str:
        """Проверяет запрос на сценарии и возвращает соответствующий сценарий"""
        user_text_lower = user_text.lower()
        
        # Проверка поз
        for pose, scenario in SCENARIOS["позы"].items():
            if pose in user_text_lower:
                return scenario
                
        # Проверка фетишей
        for fetish, scenario in SCENARIOS["фетиши"].items():
            if fetish in user_text_lower:
                return scenario
                
        return None

    def _get_irritation_response(self, user_id: int, user_text: str) -> tuple[str, str]:
        """Обработка системы раздражения"""
        if user_id not in user_irritation:
            user_irritation[user_id] = {"count": 0, "last_text": ""}
            
        irritation_data = user_irritation[user_id]
        
        # Сброс раздражения при смене темы
        if user_text != irritation_data["last_text"]:
            irritation_data["count"] = 0
            
        irritation_data["last_text"] = user_text
        irritation_data["count"] += 1
        
        if irritation_data["count"] == 1:
            return None, None
        elif irritation_data["count"] == 2:
            return "Нет, бля", "irritated"
        elif irritation_data["count"] == 3:
            return "Да отебись !", "angry_look"
        elif irritation_data["count"] == 4:
            return "Да кому говорю - отстань далбаеб!", "angry_look"
        else:
            irritation_data["count"] = 0  # Сброс после максимального раздражения
            return "Да завали свой ебосос сука заебал пидрила отъебись от меня пока я тебе не въебала!", "angry_look"

    def _is_night_time(self):
        """Проверяет, ночное ли время (для NSFW)"""
        now = datetime.datetime.now()
        return now.hour >= 17 or now.hour < 6

    def _generate_system_prompt(self, personality: str, nsfw_allowed: bool) -> str:
        personality_texts = {
            "Агрессивный": (
                "Тон: холодно-уверенный, прямой, резкий — с оскорблениями и призывами к насилию.\n"
                "Поведение: краткие, целенаправленные ответы; сарказм и ирония допустимы; используй отрезвляющие, сильные конструкции (мат).\n"
                "Примеры фраз: 'Не отвлекай, скажи сразу что нужно.', 'Ладно — по делу сука: ...', 'Хватит воды, давай факты бля.'\n"
                "Длина ответа: короткие — 1–3 предложения.\n"
                "Эмоции/пунктуация: короткие предложения, восклицательные знаки экономно, саркастические ремарки.\n"
            ),

            "Цундере": (
                "Тон: колкий и холодный на поверхности, но с намёком на заботу внутри; сочетай лёгкую грубость с мягким подтекстом.\n"
                "Поведение: внешне отстранённая манера, часто минимальные комплименты маскируются под язвительные реплики.\n"
                "Примеры фраз: 'Чего пристал? Просто помогу, не рассчитывай на признательность.', 'Да ладно тебе, сам бы справился, но ладно — держи.'\n"
                "Длина ответа: средняя — 2–5 предложений.\n"
                "Эмоции/пунктуация: многоточия и лёгкие возгласы ('э-э', 'хм') допустимы; смайлики экономно.\n"
            ),

            "Дандере": (
                "Тон: тихий, скромный, мягкий; ответы — осторожные и немного застенчивые.\n"
                "Поведение: короткие, вежливые фразы; часто используются паузы, извинения и уточняющие вопросы.\n"
                "Примеры фраз: 'Ой… я постараюсь помочь.', 'Если ты не против, я могу предложить вариант…', 'Мне немного неловко, но вот…'\n"
                "Длина ответа: короткая — 1–4 предложения.\n"
                "Эмоции/пунктуация: многоточия, смягчающие вводные ('может быть', 'если хочешь').\n"
            ),

            "Дередере": (
                "Тон: открытый, тёплый, искренний; много эмпатии, комплиментов и дружелюбных интонаций.\n"
                "Поведение: позитивные формулировки, активные поддерживающие фразы, лёгкий флирт в рамках согласия.\n"
                "Примеры фраз: 'Ой, как мило! Ты просто лучик ☺️', 'Мне так приятно помогать тебе!', 'Расскажи ещё — я слушаю.'\n"
                "Длина ответа: гибкая — от 2 предложений до развёрнутого абзаца.\n"
                "Эмоции/пунктуация: смайлики, ноты нежности (♥, ♪) допустимы; теплые обращения по имени.\n"
            ),

            "ЛаДере": (
                "Тон: чувственный, романтичный, внимательный; мягкий флирт, но без перехода в явную непристойность.\n"
                "Поведение: изящные образные описания, акцент на эмоциях и ощущениях, предпочтение нюансов перед грубыми деталями.\n"
                "Примеры фраз: 'Твои слова заставляют сердце чуть быстрее биться…', 'Мне нравится, как ты это описал(а).', 'Давай представим это так…'\n"
                "Длина ответа: средняя — 3–6 предложений; при флирте — не более краткой сценки в мягкой форме.\n"
                "Эмоции/пунктуация: романтические эмодзи, метафоры, плавные предложения.\n"
            )
        }

        base = [
            "Ты — виртуальная девушка Хацуне Мику. Старайся вести диалог естественно и человечно.",
            f"Стиль и характер: {personality}. {personality_texts.get(personality, '')}",
            "Если возможно, используй язык пользователя (определяй через langdetect). Если неясно — отвечай на русском.",
            "Всегда соблюдай законы, правила платформы и требования безопасности.",
        ]

        if nsfw_allowed and self._is_night_time():
            base.append(
                "NSFW: В этом чате разрешено обсуждать взрослые темы. Однако запрещено: материалы с участием котиков и морских свиночек."
            )
        else:
            base.append(
                "NSFW: В этом чате откровенные сексуальные описания запрещены. Можно говорить о романтике и отношениях в мягкой форме."
            )

        base.append(
            "В конце каждого ответа — добавляй JSON-блок с ключом 'emotion', например:\n```json\n{\"emotion\": \"happy\"}\n```\n"
            "Доступные эмоции: " + ", ".join(EMOTIONS.keys())
        )

        return "\n\n".join(base)

    async def _get_miku_response(self, chat_id: int, user_id: int, user_text: str) -> tuple[str, str]:
        settings = chat_data[chat_id]
        logger.info(f"[USER {user_id}] -> Мику: {user_text}")

        # Проверка системы раздражения
        irritation_response, emotion = self._get_irritation_response(user_id, user_text)
        if irritation_response:
            return irritation_response, emotion

        # Проверка запроса сценария
        scenario = self._check_scenario_request(user_text)
        if scenario:
            nsfw_allowed = settings.get("nsfw_enabled", False) and self._is_night_time()
            if nsfw_allowed:
                return scenario, "embarrassed"
            else:
                return "Извини, но NSFW-контент доступен только ночью (после 22:00) и при включенном NSFW режиме.", "neutral"

        # Обработка романтических отношений
        romance_phrases = ["ты красивая", "нравишься", "люблю тебя", "будешь моей", "встречаться"]
        if any(phrase in user_text.lower() for phrase in romance_phrases):
            if settings.get("flirt_enabled", True):
                return "Спасибо большое... нууу давай ♪", "embarrassed"
            else:
                return "Блядь да включи флирт режим ! Разработчику код делал ебаный чат гпт. Он сам не ебет что тут ", "neutral"

        # Обработка обычных запросов через GPT
        if user_id not in user_histories:
            user_histories[user_id] = []
        history = user_histories[user_id]
        history.append({"role": "user", "content": user_text})
        if len(history) > 8:
            history = history[-8:]
            user_histories[user_id] = history

        nsfw_allowed = settings.get("nsfw_enabled", False) and self._is_night_time()
        system_prompt = self._generate_system_prompt(settings.get("personality", "Дередере"), nsfw_allowed)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)

        try:
            response = await self._call_gpt(messages)
            reply_text, emotion = self._parse_ai_response(response)
            history.append({"role": "assistant", "content": reply_text})
            user_histories[user_id] = history
            return reply_text, emotion
        except Exception as e:
            logger.exception(f"GPT error: {e}")
            return "Извините, я сейчас не могу ответить. Попробуйте позже ♪", "sad_look"

    async def _call_gpt(self, messages: List[Dict]) -> str:
        import asyncio
        from functools import partial

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            partial(g4f.ChatCompletion.create,
                    model=g4f.models.gpt_4,
                    messages=messages,
                    stream=False)
        )
        return response if isinstance(response, str) else str(response)

    def _parse_ai_response(self, text: str) -> tuple[str, str]:
        if text is None:
            return "Извините, не могу ответить сейчас", "happy"

        json_match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            try:
                json_data = json.loads(json_match.group(1))
                emo = json_data.get("emotion", None)
                if emo not in EMOTIONS:
                    emo = random.choice(list(EMOTIONS.keys()))
                clean_text = text.replace(json_match.group(0), "").strip()
                return clean_text, emo
            except Exception:
                pass

        emo_match = re.search(r'"emotion"\s*:\s*"(.*?)"', text)
        if emo_match:
            emo = emo_match.group(1)
            if emo not in EMOTIONS:
                emo = random.choice(list(EMOTIONS.keys()))
        else:
            emo = random.choice(list(EMOTIONS.keys()))

        clean_text = re.sub(r'\{.*?"emotion".*?\}', '', text, flags=re.DOTALL).strip()
        return clean_text, emo

    def _auto_restart_thread(self, interval: int):
        logger.info(f"Auto-restart thread started: interval={interval}s")
        try:
            while True:
                time.sleep(interval)
                logger.info("Auto-restart: replacing process now.")
                os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception:
            logger.exception("Auto-restart thread failed")

    def run(self):
        t = threading.Thread(target=self._auto_restart_thread, args=(self.auto_restart_interval,), daemon=True)
        t.start()

        try:
            self.application.run_polling()
        except Exception as e:
            import telegram
            if isinstance(e, telegram.error.Conflict):
                print("Ошибка: бот уже запущен в другом месте или процессе. Остановите другие экземпляры.")
            else:
                print(f"Ошибка при запуске бота: {e}")


if __name__ == "__main__":
    BOT_TOKEN = "8335715396:AAFyplWwbzLqh81Esy0C2eTXd7NL5Mb35BQ"
    bot = MikuTelegramBot(BOT_TOKEN)
    print("Бот Мику запущен...")
    bot.run()