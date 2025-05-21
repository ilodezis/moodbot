import asyncio
import random
import threading
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.types import FSInputFile

import datetime
import json
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.base import STATE_RUNNING
from apscheduler.triggers.cron import CronTrigger
import pytz
import requests
from bs4 import BeautifulSoup
import aiohttp

# --- Логирование ---
logging.basicConfig(
    filename='bot.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Константы ---
ADMIN_ID = 409183653  # <-- теперь только admin
TARGET_USER_ID = 791353019  # <-- ID получателя для send_* команд

API_TOKEN = '7818869168:AAGmcVSu7NliSSoNiBLoe2ARzVLCYgbpgRI'

WATER_REMINDER_INTERVAL = 1800  # 30 minutes
TABLETS_REMINDER_INTERVAL = 600  # 10 minutes
MOOD_SCALE_MIN = 1
MOOD_SCALE_MAX = 5
BUFFER_SIZE = 1  # Немедленная запись каждой записи в файл

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

STATE_FILE = 'mood_log.json'

if not os.path.exists(STATE_FILE):
    with open(STATE_FILE, 'w') as f:
        json.dump([], f)

mood_fields = [
    ('mood', 'Настроение'),
    ('anxiety', 'Тревожность'),
    ('energy', 'Энергия'),
    ('focus', 'Фокус'),
    ('reactivity', 'Эмоциональная чувствительность')
]

random_tips = [
    "💧 Не забудь пить воду. Мозг и сердце скажут спасибо.",
    "🥗 Съешь что-нибудь тёплое и нормальное. Полноценный приём пищи = самоподдержка.",
    "🍎 Перекус — это тоже забота. Не пропускай, если чувствуешь упадок.",
    "💦 Гидратация важнее, чем кажется. Просто выпей стакан воды.",
    "🧃 Фрукты, овощи, тёплая еда — всё это не банально. Это топливо для твоего тела.",
    "Ты не сломана — ты устала. И это не одно и то же.",
    "Пить магний — это не слабость, это грамотность.",
    "Сегодня достаточно просто прожить день, не выигрывать его.",
    "Мозгу сейчас не нужна победа. Мозгу нужно тепло и предсказуемость.",
    "Когда тревога — не требуй от себя продуктивности. Требуй мягкости.",
    "Если стало тяжело — не ускоряйся, а замедлись.",
    "Твоя ценность не уменьшается, когда ты устаёшь.",
    "Иногда лучший выбор — это не делать ничего.",
    "Не нужно быть продуктивной. Нужно быть живой.",
    "Грусть — это не ошибка. Это просто часть спектра.",
    "Ты не обязана быть стабильной, чтобы быть достойной любви.",
    "Когда всё раздражает — это не ты плохая. Это перегруз.",
    "Ты не обязана объяснять, почему тебе плохо.",
    "Тело — не враг. Оно просто просит внимания.",
    "Ты не обязана справляться одна.",
    "Раздражение — это тоже сигнал. Его можно уважать.",
    "Никакой ты не ленивая. Просто ресурса мало.",
    "Не весь день надо быть в порядке. Достаточно одного момента.",
    "Твоя медлительность — это способ себя спасти.",
    "Ты не обязана быть сильной круглосуточно.",
    "Каждое твоё состояние — валидно. Даже когда непонятно, почему оно такое.",
    "Ты — не диагноз. Ты — человек, который справляется.",
    "Усталость — это не лень, а симптом.",
    "Даже медленный прогресс — это прогресс.",
    "Если не можешь — значит, уже на пределе. Это тоже сигнал.",
    "Можно не хотеть. Можно ничего не хотеть. Это нормально.",
    "Никто не обязан понимать. Достаточно, что ты знаешь, как тебе.",
    "Ты не должна оправдываться за своё состояние.",
    "Иногда самое мужественное — признать, что ты устала.",
    "Ты не одна. И никогда не была.",
    "Если хочется плакать — плачь. Это очистка, не слабость.",
    "Никому не станет легче, если тебе станет хуже. Заботься о себе.",
    "Когда ты заботишься о себе — ты уже не в проигрыше.",
    "Стабильность — это не одно и то же, что безэмоциональность.",
    "Если ты встала с кровати — это уже победа.",
    "Не все дни яркие. Но все дни важные.",
    "Ты — не сумма своих продуктивных часов.",
    "Тревога говорит с тобой, но это не значит, что она права.",
    "Ты можешь доверять себе. Даже если кажется, что не можешь.",
    "Покой — не враг, а цель.",
    "Один день без слёз — уже достижение. Не обесценивай.",
    "Даже если мир шумит — ты можешь быть тихим островом.",
    "Ты — не проблема, которую нужно исправить.",
    "Иногда просто дыхание — уже акт силы.",
    "Ты имеешь право замедлиться. Мир подождёт.",
    "Никто не знает, как быть собой. Все учатся. Ты — тоже.",
    "Ты не обязана быть сильной ради кого-то. Только ради себя.",
    "Если не можешь думать — чувствуй. Если не можешь чувствовать — дыши.",
    "Нет плохих чувств. Есть неуслышанные.",
    "Ты — целая, даже в разбитом состоянии.",
    "Стабильность начинается с одного доброго жеста к себе.",
    "Никто не может быть идеальным. Даже ты.",
    "Позаботься о себе так, как заботилась бы о подруге.",
    "Иногда лучший план — никакого плана.",
    "Ты не потеряна. Ты — в процессе.",
    "Если не можешь справиться — попроси помощи. Это смело.",
    "Ты заслуживаешь быть в покое. Просто потому что ты есть.",
    "Всё, что ты чувствуешь — допустимо.",
    "Когда трудно — не решай, просто выживи.",
    "Ты — не цифры. Ты — опыт и тепло.",
    "Твоя история важна. Даже если она тихая.",
    "Будь к себе мягкой. Особенно когда тяжело.",
    "Ты заслуживаешь восстановления, а не только выживания.",
    "Иногда просто поесть и лечь — это форма заботы.",
    "День может быть разным. Ты не обязана быть одинаковой.",
    "Даже шаг назад — может быть шагом к себе.",
    "Если тревожно — заземлись: дыши, почувствуй тело.",
    "Ты имеешь право на тишину и одиночество.",
    "Даже злость — это способ твоего тела просить защиты.",
    "Ты уже многое пережила. Это о чём-то говорит.",
    "Каждый момент не в страдании — уже лечение.",
    "Ты не обязана быть удобной. Ты обязана быть собой.",
    "Твоя ценность не зависит от продуктивности.",
    "Нормально не быть ок. Особенно сейчас.",
    "Ты не невидимка. Твоя боль видна.",
    "Ты не должна быть объяснимой, чтобы быть принятой.",
    "Ты не сломана. Просто перегружена.",
    "Слезы — это тоже терапия.",
    "Ты имеешь право быть важной для себя.",
    "Если ничего не помогает — просто посиди. Ты всё равно существуешь.",
    "Даже молчание — это форма общения с собой.",
    "Если не справляешься — это не про слабость. Это про предел.",
    "Ты достойна заботы не потому, что полезна, а потому что есть.",
    "Никто не требует от тебя быть стальной. Даже ты.",
    "Ты можешь быть мягкой и сильной одновременно.",
    "Если всё рушится — укройся, а не строй заново.",
    "Ты важна. Даже если сейчас не чувствуешь этого.",
    "Можно перестать делать. И просто быть.",
    "Каждый раз, когда ты выбираешь не сдаться — это важно.",
    "Ты — не диагноз. Ты — живой человек.",
    "Если небо серое — это не значит, что солнце исчезло.",
    "Ты можешь ошибаться — и всё равно быть достойной.",
    "Ты достойна любви. Даже в самый сломанный день.",
    "Усталость — сигнал. Не игнорируй её.",
    "Ты можешь быть доброй к себе. Прямо сейчас.",
    "Если тебе тяжело — это не потому что ты слаба. А потому что груз тяжёлый.",
    "Ничего страшного, если ты не готова. Всё приходит поэтапно.",
    "Даже без мотивации — ты имеешь значение.",
    "Иногда лучшее, что ты можешь сделать — это не делать.",
    "Не винить себя — это уже шаг к себе.",
    "Ты — не проблема. Ты — процесс.",
    "🚶 Прогуляйся хотя бы 10 минут. Даже если не хочется — это сработает.",
    "🧘 Сделай 5 глубоких вдохов и выдохов. Это обнулит нервную систему.",
    "🛏️ Если чувствуешь перегруз — просто полежи с закрытыми глазами 10 минут.",
    "🎧 Включи музыку, которая тебя собирает. Даже одна песня может сменить состояние.",
    "📴 Убери телефон хотя бы на полчаса. Мозг отдохнёт от шума.",
    "💤 Не залипай — попробуй лечь спать чуть раньше сегодня.",
    "📓 Запиши всё, что тебя грузит. Мозг не любит таскать это внутри.",
    "🕯️ Устрой себе микроритуал: чай, тишина, одеяло, запах — что угодно, что даёт покой.",
    "💡 Поменяй обстановку хотя бы на 10 минут — другая комната, окно, балкон.",
    "🌞 Если есть солнце — постой на нём пару минут. Это реальный допинг.",
    "👕 Надень что-нибудь мягкое и комфортное. Это больше влияет, чем кажется.",
    "📦 Завалилась с делами? Начни с одного самого простого. Это уже движение.",
    "🧼 Убери хотя бы одну поверхность — порядок снаружи помогает внутри.",
    "📵 Не обязательно отвечать на всё сразу. Ты можешь не быть доступной.",
    "🛁 Вода расслабляет. Тёплый душ = кнопка перезагрузки.",
    "🥣 Горячая еда в одиночестве — это тоже забота, не стыд.",
    "🧍 Послушай тело: сядь удобно, проверь напряжение в плечах, челюсти, руках.",
    "🔌 Перестань себя пинать. Иногда честный отдых = шаг вперёд.",
    "🧠 Всё, что ты чувствуешь — это информация, а не приговор.",
    "🎈 Ты не обязана быть продуктивной, чтобы быть ценной.",
    "🧃 Если забыла поесть — сейчас хорошее время. Даже пара ложек — уже не пусто.",
    "💤 Если устала — полежи, даже 10 минут с закрытыми глазами меняют восприятие.",
    "📵 Отключи уведомления хотя бы на 1 час. Тишина — это забота.",
    "📦 Сделай одно маленькое дело. Даже мыть кружку — уже действие.",
    "🧺 Если раздражает бардак — убери 1 вещь. Только одну.",
    "🌿 Открой окно. Проветривание = сброс накопившегося.",
    "🧴 Помажь руки или лицо — прикосновение к себе = сигнал «я есть»",
    "🎵 Найди 1 трек, от которого легче — и просто включи.",
    "🧘‍♀️ Потянись, раскрути плечи, пошевели шеей. Телу тоже тяжело от всего.",
    "👖 Надень тёплые носки или кофту. Физический комфорт важен при тревоге.",
    "💌 Напиши себе сообщение, которое хотела бы получить. Прочти вслух.",
    "📅 Не надо планировать жизнь. Просто проживи сегодня.",
    "🔌 Разреши себе отложить. Не обязательно всё сейчас.",
    "🪞 Посмотри в зеркало и не оценивай. Просто зафиксируй: ты есть.",
    "🫖 Выпей что-то тёплое. Не для пользы, а для тепла.",
    "🪫 Ты можешь не быть «на связи». Даже с близкими. Это право.",
    "🚰 Пей воду, даже если не хочешь. Обезвоженность усиливает тревожность.",
    "📉 Не сравнивай — особенно себя с собой в «лучшей версии».",
    "🔁 Всё циклично. Сегодняшнее состояние — не приговор.",
    "🫂 Напомни себе: ты выжила уже не один тяжёлый день. Значит, и этот проживёшь."
]

user_data = {}

easter_eggs = [
    "🐣 Пасхалка: ты одноклеточный ишак, но всё равно любимый 💛",
    "🐣 Пасхалка: уанючий, да. Но с душой 😤",
    "🐣 Пасхалка: если бы ты был багом — я бы тебя не фиксил 🫂",
    "🐣 Пасхалка: твар, конечно, но тёплая твар 🐸",
    "🐣 Пасхалка: даже ебанный — всё ещё человек 🫠"
]

# --- Универсальная клавиатура для напоминаний ---
reminder_kb = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Выпила", callback_data="confirm_water")
        ]
    ]
)

# --- Клавиатуры для mood трекинга ---
def mood_inline_keyboard(step):
    # step: 0..4, шкала теперь от 1 до 5
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text=str(i), callback_data=f"mood_{step}_{i}")
                for i in range(1, 6)
            ]
        ]
    )

# --- Обёртка для проверки ADMIN_ID ---
def admin_only(handler):
    async def wrapper(message: types.Message, **kwargs):
        print(f"[ADMIN_ONLY] Called for user {getattr(message.from_user, 'id', None)} with text: {getattr(message, 'text', None)}")
        # Проверяем только команды, начинающиеся с /
        if message.text and message.text.startswith('/'):
            if message.from_user.id != ADMIN_ID:
                print(f"[LOG] Access denied for {message.from_user.id} to admin command {message.text}")
                await message.answer("У тебя нет доступа к этой команде.")
                return
            print(f"[LOG] ADMIN {message.from_user.id} triggered {message.text}")
        else:
            print(f"[ADMIN_ONLY] Not a command or no text: {getattr(message, 'text', None)}")
        return await handler(message, **kwargs)
    return wrapper

# --- Обёртка для callback_query (admin only, если потребуется) ---
def admin_only_callback(handler):
    async def wrapper(callback_query, *args, **kwargs):
        if callback_query.from_user.id != ADMIN_ID:
            print(f"[LOG] Access denied for {callback_query.from_user.id} to callback {callback_query.data}")
            await callback_query.answer("У тебя нет доступа к этой команде.", show_alert=True)
            return
        print(f"[LOG] ADMIN {callback_query.from_user.id} triggered callback {callback_query.data}")
        return await handler(callback_query, *args, **kwargs)
    return wrapper

reminder_states = {}
ping_blocked_until = {}
active_users = set()
file_lock = threading.Lock()
reminder_states_lock = asyncio.Lock()
buffer = []

# --- Объявление хэндлеров (все принимают **kwargs) ---

async def start_handler(message: types.Message, **kwargs):
    print(f"[DEBUG] /start from {message.chat.id}")
    user_data[message.chat.id] = {'step': 0, 'entry': {}}
    greeting = (
        "🐰 Привет, зайка. Это бот, который я сделал с любовью специально для тебя.\n\n"
        "Он поможет тебе отслеживать настроение, фокус, тревожность и всё, что может незаметно сбиваться.\n"
        "Ты просто отвечаешь на пару вопросов — и всё. Никаких выводов, только поддержка. 💛\n\n"
        "Что делает бот:\n"
        "— Утром и вечером просит тебя оценить своё состояние по шкале от 1 до 10 по пяти критериям.\n"
        "— Принимает любые комментарии.\n"
        "— Присылает добрые советы, чтобы стало хотя бы немного легче.\n"
        "— Сохраняет всё в файл, чтобы потом можно было проанализировать, когда и почему становилось тяжело.\n\n"
        "Чтобы начать: просто нажми /start или дождись напоминания.\n"
        "Если что-то не работает — напиши Тимуру.\n\n"
        "Погнали? Давай оценим твоё состояние. По шкале от 1 до 10:"
    )
    await message.answer(greeting)
    await ask_next_field(message)

async def ask_next_field(message: types.Message, **kwargs):
    print(f"[DEBUG] ask_next_field for user {message.chat.id}, step {user_data[message.chat.id]['step']}")
    step = user_data[message.chat.id]['step']
    if step < len(mood_fields):
        _, field_name = mood_fields[step]
        await message.answer(f"{field_name} (1–5):")
    else:
        await message.answer("Хочешь что-то добавить? Напиши сюда. Если нет — просто отправь '-' или 'нет'.")

async def ask_next_field_mood(chat_id):
    step = user_data[chat_id]['step']
    if step < len(mood_fields):
        _, field_name = mood_fields[step]
        await bot.send_message(
            chat_id,
            f"{field_name} (1–5):",
            reply_markup=mood_inline_keyboard(step)
        )
    else:
        await bot.send_message(
            chat_id,
            "Хочешь что-то добавить? Напиши сюда. Если нет — просто отправь '-' или 'нет'."
        )

# --- Тестовые команды (отправляют только админу) ---
async def test_water(message: types.Message, **kwargs):
    print(f"[DEBUG] test_water called by {message.chat.id}")
    await message.answer("💧 Тест: напоминание про воду (только админу)", reply_markup=reminder_kb)
    reminder_states[message.chat.id] = {'type': 'water', 'time': datetime.datetime.now()}
    asyncio.create_task(water_annoy_loop(message.chat.id))

async def test_tablets(message: types.Message, **kwargs):
    print(f"[DEBUG] test_tablets called by {message.chat.id}")
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Приняла", callback_data="confirm_tablets")]
        ]
    )
    await message.answer("💊 Тест: напоминание про таблетки (только админу)", reply_markup=keyboard)
    reminder_states[message.chat.id] = {'type': 'tablets', 'time': datetime.datetime.now()}
    asyncio.create_task(tablet_annoy_loop(message.chat.id))

async def test_mood(message: types.Message, **kwargs):
    print(f"[DEBUG] test_mood called by {message.chat.id}")
    await message.answer("🧠 Тест: напоминание про трекинг настроения (только админу)")

async def test_tip(message: types.Message, **kwargs):
    print(f"[DEBUG] test_tip called by {message.chat.id}")
    await message.answer(f"Тестовый совет (только админу): {random.choice(random_tips)}")

async def test_combo_reminder():
    try:
        # Вода
        await bot.send_message(
            TARGET_USER_ID,
            "💧 Напоминание: не забудь пить воду",
            reply_markup=reminder_kb
        )
        reminder_states[TARGET_USER_ID] = {'type': 'water', 'time': datetime.datetime.now()}
        asyncio.create_task(water_annoy_loop(TARGET_USER_ID))

        # Таблетки
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="✅ Приняла", callback_data="confirm_tablets")]
            ]
        )
        await bot.send_message(
            TARGET_USER_ID,
            "💊 Напоминание: не забудь принять добавки / таблетки",
            reply_markup=keyboard
        )
        reminder_states[TARGET_USER_ID] = {'type': 'tablets', 'time': datetime.datetime.now()}
        asyncio.create_task(tablet_annoy_loop(TARGET_USER_ID))

        # Опрос настроения (запуск через ask_next_field_mood)
        user_data[TARGET_USER_ID] = {'step': 0, 'entry': {}}
        await ask_next_field_mood(TARGET_USER_ID)

        print("[DEBUG] test_combo_reminder: все три напоминания отправлены")
    except Exception as e:
        print(f"[ERROR] test_combo_reminder: {e}")

# --- SEND-команды (отправляют ей) ---
async def send_water(message: types.Message, **kwargs):
    print(f"[DEBUG] send_water called by {message.chat.id}")
    target_id = TARGET_USER_ID
    print(f"[DEBUG] TARGET_USER_ID = {target_id} (type: {type(target_id)})")
    try:
        await bot.send_message(target_id, "Сообщение от мужа:\n💧 Напоминание: не забудь пить воду", reply_markup=reminder_kb)
        reminder_states[target_id] = {'type': 'water', 'time': datetime.datetime.now()}
        asyncio.create_task(water_annoy_loop(target_id))
        await message.answer("✅ Отправлено ей.")
    except Exception as e:
        print(f"[ERROR] send_water: {e}")
        await message.answer(f"❌ Ошибка отправки: {e}")

async def send_tablets(message: types.Message, **kwargs):
    print(f"[DEBUG] send_tablets called by {message.chat.id}")
    target_id = TARGET_USER_ID
    print(f"[DEBUG] TARGET_USER_ID = {target_id} (type: {type(target_id)})")
    try:
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="✅ Приняла", callback_data="confirm_tablets")]
            ]
        )
        await bot.send_message(target_id, "Сообщение от мужа:\n💊 Напоминание: не забудь принять добавки / таблетки", reply_markup=keyboard)
        reminder_states[target_id] = {'type': 'tablets', 'time': datetime.datetime.now()}
        asyncio.create_task(tablet_annoy_loop(target_id))
        await message.answer("✅ Отправлено ей.")
    except Exception as e:
        print(f"[ERROR] send_tablets: {e}")
        await message.answer(f"❌ Ошибка отправки: {e}")

async def send_mood(message: types.Message, **kwargs):
    print(f"[DEBUG] send_mood called by {message.chat.id}")
    target_id = TARGET_USER_ID
    print(f"[DEBUG] TARGET_USER_ID = {target_id} (type: {type(target_id)})")
    try:
        # Initialize the mood tracking process for the target user
        user_data[target_id] = {'step': 0, 'entry': {}}
        await bot.send_message(
            target_id,
            "Сообщение от мужа:\n🧠 Как ты сейчас? Давай оценим твоё состояние по шкале от 1 до 5:\n"
            "1. Настроение\n2. Тревожность\n3. Энергия\n4. Фокус\n5. Эмоциональная чувствительность\n\n"
            "Просто нажимай на кнопки, я всё запишу.",
        )
        await ask_next_field_mood(target_id)
        await message.answer("✅ Отправлено ей.")
    except Exception as e:
        print(f"[ERROR] send_mood: {e}")
        await message.answer(f"❌ Ошибка отправки: {e}")

async def send_tip(message: types.Message, **kwargs):
    print(f"[DEBUG] send_tip called by {message.chat.id}")
    target_id = TARGET_USER_ID
    print(f"[DEBUG] TARGET_USER_ID = {target_id} (type: {type(target_id)})")
    try:
        await bot.send_message(target_id, f"Сообщение от мужа:\n📌 Совет: {random.choice(random_tips)}")
        await message.answer("✅ Отправлено ей.")
    except Exception as e:
        print(f"[ERROR] send_tip: {e}")
        await message.answer(f"❌ Ошибка отправки: {e}")

async def send_message(message: types.Message, **kwargs):
    print(f"[DEBUG] send_message called by {message.chat.id}")
    target_id = TARGET_USER_ID
    print(f"[DEBUG] TARGET_USER_ID = {target_id} (type: {type(target_id)})")
    try:
        text = message.text.split(maxsplit=1)
        if len(text) < 2:
            await message.answer("❌ Укажите текст сообщения после команды. Пример: `/say Привет!`")
            return
        await bot.send_message(target_id, f"Сообщение от мужа:\n{text[1]}")
        await message.answer("✅ Сообщение отправлено.")
    except Exception as e:
        print(f"[ERROR] send_message: {e}")
        await message.answer(f"❌ Ошибка отправки: {e}")

async def test_reminders(message: types.Message, **kwargs):
    print(f"[DEBUG] test_reminders called by {message.chat.id}")
    await message.answer("🔔 Тестовая команда больше не отправляет все напоминания сразу. Используй отдельные команды:\n"
                         "/test_water — напоминание про воду\n"
                         "/test_tablets — напоминание про таблетки\n"
                         "/test_mood — напоминание про трекинг настроения\n"
                         "/test_tip — случайный совет")

async def clear_log(message: types.Message, **kwargs):
    print(f"[DEBUG] clear_log called by {message.chat.id}")
    with open(STATE_FILE, 'w') as f:
        json.dump([], f)
    await message.answer("🧹 Лог очищен. Все записи удалены.")

async def test_log_entry(message: types.Message, **kwargs):
    print(f"[DEBUG] test_log_entry called by {message.chat.id}")
    dummy_entry = {
        "mood": 5,
        "anxiety": 4,
        "energy": 3,
        "focus": 6,
        "reactivity": 5,
        "comment": "тестовая запись",
        "timestamp": datetime.datetime.now().isoformat()
    }
    save_entry(dummy_entry)
    await message.answer("📁 Тестовая запись сохранена в лог.")

async def export_log(message: types.Message, **kwargs):
    print(f"[DEBUG] export_log called by {message.chat.id}")
    try:
        print(f"[LOG] export_log called by {message.chat.id}")
        await message.answer_document(
            types.FSInputFile("mood_log.json"),
            caption="📂 Вот лог со всеми состояними"
        )
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при отправке: {e}")

async def disable_pings(message: types.Message, **kwargs):
    print(f"[DEBUG] disable_pings called by {message.chat.id}")
    chat_id = message.chat.id
    ping_blocked_until[chat_id] = datetime.datetime.now() + datetime.timedelta(hours=1)
    print(f"[LOG] USER {chat_id} отключил напоминания до {ping_blocked_until[chat_id]}")
    
    # Удаляем все активные напоминания
    async with reminder_states_lock:
        if chat_id in reminder_states:
            reminder_states.pop(chat_id, None)
    
    # Удаляем из активных пользователей трекинга
    active_users.discard(chat_id)
    
    await message.answer("🫠 Окей, отключаю все напоминания на 1 час. Но потом я вернусь!")

async def update_reminder_state(chat_id, state):
    async with reminder_states_lock:
        reminder_states[chat_id] = state

def flush_buffer():
    global buffer
    if not buffer:
        return
    with file_lock:
        try:
            with open(STATE_FILE, 'r+') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
                data.extend(buffer)
                f.seek(0)
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.truncate()
            buffer = []
        except IOError as e:
            logger.error(f"Failed to flush buffer: {e}")

def save_entry(entry):
    logger.debug(f"save_entry: {entry}")
    buffer.append(entry)
    if len(buffer) >= BUFFER_SIZE:
        flush_buffer()

async def process_input(message: types.Message, **kwargs):
    try:
        logger.debug(f"process_input called by {message.from_user.id} with text: {message.text}")
        if message.from_user.id == ADMIN_ID:
            if message.text and message.text.startswith('/'):
                return
            await message.answer("Этот бот не предназначен для ввода данных админом.")
            return

        if message.chat.id in active_users:
            await message.answer("Сейчас идёт трекинг настроения. Заверши его, чтобы продолжить.")
            return

        if message.text.lower().strip() in ['/export_log', '/start', '/отъебись']:
            return
        print(f"[DEBUG] process_input: {message.text} from {message.chat.id}")
        text = message.text.lower().strip()
        if any(word in text for word in ['ишак', 'одноклеточный', 'твар', 'уанючий', 'ебучий', 'ебанный']):
            await message.answer(random.choice(easter_eggs))
            return
        user_id = message.chat.id
        if user_id not in user_data:
            await message.answer("Напиши /start, чтобы начать трекинг.")
            return

        step = user_data[user_id]['step']

        if step < len(mood_fields):
            try:
                val = int(message.text.strip())
                if not (1 <= val <= 5):
                    raise ValueError
                field_key, _ = mood_fields[step]
                user_data[user_id]['entry'][field_key] = val
                user_data[user_id]['step'] += 1
                # --- Уведомление админу о каждом ответе ---
                await bot.send_message(ADMIN_ID, f"Ответ на опрос ({field_key}): {val}")
                await ask_next_field(message)
            except ValueError:
                await message.answer("Пожалуйста, введи число от 1 до 5.")
        else:
            comment = message.text.strip()
            if comment.lower() in ['-', 'нет']:
                comment = ''
            entry = user_data[user_id]['entry']
            entry['comment'] = comment
            entry['timestamp'] = datetime.datetime.now().isoformat()
            save_entry(entry)
            await message.answer("Спасибо. Всё записал. ✍️")
            await message.answer(f"Совет дня: {random.choice(random_tips)}")
            # --- Уведомление админу о завершении опроса ---
            await bot.send_message(ADMIN_ID, f"Опрос завершён. Ответы: {json.dumps(entry, ensure_ascii=False)}")
            user_data.pop(user_id, None)
    except Exception as e:
        logger.error(f"Error in process_input: {e}")
        await message.answer("Произошла ошибка. Попробуйте еще раз.")

async def reminder_callback_handler(callback_query: types.CallbackQuery):
    print(f"[LOG] Callback {callback_query.data} от {callback_query.from_user.id}")
    # --- Уведомление админу о подтверждении ---
    if callback_query.from_user.id == TARGET_USER_ID:
        if callback_query.data.startswith('confirm_'):
            if callback_query.data == 'confirm_water':
                await bot.send_message(ADMIN_ID, "Вода: подтверждено!")
            else:
                await bot.send_message(ADMIN_ID, f"Она нажала: {callback_query.data.replace('confirm_', '').capitalize()}")
    # --- Очищаем reminder_states для confirm_water и confirm_tablets ---
    if callback_query.data == 'confirm_water':
        reminder_states.pop(callback_query.from_user.id, None)
        await callback_query.message.edit_text("Принято! 🥳")
    elif callback_query.data == 'confirm_tablets':
        reminder_states.pop(callback_query.from_user.id, None)
        await callback_query.message.edit_text("Принято! 🥳")

async def confirm_tablets_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    reminder_states.pop(chat_id, None)
    print(f"[LOG] confirm_tablets от {chat_id}")
    await callback_query.message.edit_text("💊 Принято. Умница.")
    # --- Уведомление админу о подтверждении ---
    if chat_id == TARGET_USER_ID:
        await bot.send_message(ADMIN_ID, "Таблетки: подтверждено!")

async def confirm_water_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    reminder_states.pop(chat_id, None)
    print(f"[LOG] confirm_water от {chat_id}")
    await callback_query.message.edit_text("💧 Хорош! Вода внутри — сила снаружи.")
    # --- Уведомление админу о подтверждении ---
    if chat_id == TARGET_USER_ID:
        await bot.send_message(ADMIN_ID, "Вода: подтверждено!")

async def periodic_tip():
    print("[DEBUG] periodic_tip called at", datetime.datetime.now())
    try:
        message = f"📌 Совет: {random.choice(random_tips)}"
        await bot.send_message(TARGET_USER_ID, message)
        print(f"[LOG] periodic_tip отправлено пользователю {TARGET_USER_ID}")
        # Уведомление админу
        await bot.send_message(ADMIN_ID, f"(отправлено {message})")
    except Exception as e:
        print(f"[LOG] periodic_tip error for TARGET_USER_ID: {e}")

async def send_water_reminder(chat_id):
    try:
        async with reminder_states_lock:
            # Проверяем, нет ли уже активного напоминания
            if chat_id in reminder_states and reminder_states[chat_id].get('type') == 'water':
                logger.debug(f"Water reminder already active for {chat_id}")
                return

        message = "💧 Напоминание: не забудь пить воду"
        await bot.send_message(chat_id, message, reply_markup=reminder_kb)
        await update_reminder_state(chat_id, {'type': 'water', 'time': datetime.datetime.now()})
        asyncio.create_task(water_annoy_loop(chat_id))
        
        if chat_id == TARGET_USER_ID:
            await bot.send_message(ADMIN_ID, f"(отправлено {message})")
    except Exception as e:
        logger.error(f"Error in send_water_reminder: {e}")

async def send_tablets_reminder(chat_id):
    try:
        async with reminder_states_lock:
            # Проверяем, нет ли уже активного напоминания
            if chat_id in reminder_states and reminder_states[chat_id].get('type') == 'tablets':
                logger.debug(f"Tablets reminder already active for {chat_id}")
                return

        message = "💊 Напоминание: не забудь принять добавки / таблетки"
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="✅ Приняла", callback_data="confirm_tablets")]
            ]
        )
        await bot.send_message(chat_id, message, reply_markup=keyboard)
        await update_reminder_state(chat_id, {'type': 'tablets', 'time': datetime.datetime.now()})
        asyncio.create_task(tablet_annoy_loop(chat_id))
        
        if chat_id == TARGET_USER_ID:
            await bot.send_message(ADMIN_ID, f"(отправлено {message})")
    except Exception as e:
        logger.error(f"Error in send_tablets_reminder: {e}")

async def send_mood_reminder(chat_id):
    try:
        # Проверяем, не идет ли уже опрос
        if chat_id in active_users:
            logger.debug(f"Mood tracking already active for {chat_id}")
            return
            
        message = (
            "🧠 Как ты сейчас? Давай оценим твоё состояние по шкале от 1 до 5:\n"
            "1. Настроение\n2. Тревожность\n3. Энергия\n4. Фокус\n5. Эмоциональная чувствительность\n\n"
            "Просто нажимай на кнопки, я всё запишу."
        )
        
        active_users.add(chat_id)  # Отмечаем, что начался опрос
        user_data[chat_id] = {'step': 0, 'entry': {}}
        
        await bot.send_message(chat_id, message)
        await ask_next_field_mood(chat_id)
        
        if chat_id == TARGET_USER_ID:
            await bot.send_message(ADMIN_ID, f"(отправлено {message})")
    except Exception as e:
        logger.error(f"Error in send_mood_reminder: {e}")
        active_users.discard(chat_id)  # Убираем из активных в случае ошибки

async def water_annoy_loop(chat_id):
    await asyncio.sleep(WATER_REMINDER_INTERVAL)  # 30 minutes
    
    # Проверяем, существует ли еще напоминание
    async with reminder_states_lock:
        if chat_id not in reminder_states or reminder_states[chat_id].get('type') != 'water':
            return
            
    if chat_id in ping_blocked_until and datetime.datetime.now() < ping_blocked_until[chat_id]:
        return
        
    if chat_id == TARGET_USER_ID:
        await bot.send_message(ADMIN_ID, "ВНИМАНИЕ: Она не нажала 'Выпила' в течение 30 минут после напоминания о воде!")
    
    water_annoy_texts = [
        "🚨 Ты воду вообще пьёшь, нет?",
        "💦 Алё, организм сушится",
        "🌊 Напоминаю: H2O — это важно, а не просто химия!",
        "🥤 Пить воду — это не опция, а необходимость!",
        "🫗 Даже один глоток — уже вклад в здоровье.",
        "💧 Вода нужна не только цветам, но и тебе!",
        "👀 Я всё вижу. Где твой стакан воды?",
        "🫙 Пора наполнить кружку и сделать глоток!",
        "🧊 Может, добавить лёд? Главное — выпей воды!",
        "🚰 Не забывай: вода — твой внутренний супергерой."
    ]
    while True:
        async with reminder_states_lock:
            if chat_id not in reminder_states or reminder_states[chat_id].get('type') != 'water':
                break
                
        if chat_id in ping_blocked_until and datetime.datetime.now() < ping_blocked_until[chat_id]:
            await asyncio.sleep(60)
            continue
            
        try:
            message = random.choice(water_annoy_texts)
            await bot.send_message(chat_id, message, reply_markup=reminder_kb)
            if chat_id == TARGET_USER_ID:
                await bot.send_message(ADMIN_ID, f"(отправлено повторное напоминание о воде)")
            await asyncio.sleep(600)  # 10 minutes
        except Exception as e:
            logger.error(f"Error in water_annoy_loop: {e}")
            break

async def tablet_annoy_loop(chat_id):
    await asyncio.sleep(TABLETS_REMINDER_INTERVAL)  # 10 minutes
    
    # Проверяем, существует ли еще напоминание
    async with reminder_states_lock:
        if chat_id not in reminder_states or reminder_states[chat_id].get('type') != 'tablets':
            return
            
    if chat_id in ping_blocked_until and datetime.datetime.now() < ping_blocked_until[chat_id]:
        return
        
    if chat_id == TARGET_USER_ID:
        await bot.send_message(ADMIN_ID, "ВНИМАНИЕ: Она не нажала 'Приняла' в течение 10 минут после напоминания о таблетках!")
    
    tablets_annoy_texts = [
        "💊 Напоминаю: таблетки сами себя не примут!",
        "⏰ Время принять добавки. Не забывай!",
        "🧠 Организм ждёт добавки. Пора принять!",
        "📦 Таблетки ждут тебя. Не откладывай!",
        "🫙 Пора заботиться о себе — добавки ждут!",
        "🕑 Не тяни, просто прими таблетку!",
        "🧴 Это не сложно — просто сделай это сейчас.",
        "🦸‍♀️ Таблетки — твоя суперсила сегодня.",
        "🫶 Забота о себе начинается с маленьких шагов.",
        "💡 Не забудь: регулярность — залог эффекта!"
    ]
    while True:
        async with reminder_states_lock:
            if chat_id not in reminder_states or reminder_states[chat_id].get('type') != 'tablets':
                break
                
        if chat_id in ping_blocked_until and datetime.datetime.now() < ping_blocked_until[chat_id]:
            await asyncio.sleep(60)
            continue
            
        try:
            message = random.choice(tablets_annoy_texts)
            keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="✅ Приняла", callback_data="confirm_tablets")]
                ]
            )
            await bot.send_message(chat_id, message, reply_markup=keyboard)
            if chat_id == TARGET_USER_ID:
                await bot.send_message(ADMIN_ID, f"(отправлено повторное напоминание о таблетках)")
            await asyncio.sleep(420)  # 7 minutes
        except Exception as e:
            logger.error(f"Error in tablet_annoy_loop: {e}")
            break

# Remove duplicate weather functions and add the correct ones
async def get_lyubertsy_weather_text():
    """Получить погоду в Люберцах через wttr.in"""
    url = "https://wttr.in/Lyubertsy?format=%l:+%c+%t&lang=ru"
    headers = {"User-Agent": "curl/7.64.1", "Accept-Language": "ru"}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            try:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        logger.error(f"wttr.in returned status: {resp.status}")
                        return "⚠️ Сервис погоды временно недоступен"
                    weather_text = await resp.text()
            except asyncio.TimeoutError:
                logger.error("wttr.in request timed out")
                return "⚠️ Сервис погоды не отвечает (таймаут)"
            except aiohttp.ClientError as e:
                logger.error(f"AIOHTTP error: {e}")
                return "⚠️ Ошибка при подключении к сервису погоды"
        result = (
            f"🌤️ {weather_text.strip()}\n"
            "Данные предоставлены wttr.in"
        )
        return result
    except Exception as e:
        logger.error(f"Ошибка получения погоды: {e}")
        return "⚠️ Не удалось получить погоду в Люберцах"

async def send_weather_to_user(message: types.Message, **kwargs):
    """Отправить погоду пользователю"""
    msg = await message.answer("⏳ Получаю погоду...")
    try:
        weather = await asyncio.wait_for(get_lyubertsy_weather_text(), timeout=7)
        await bot.send_message(TARGET_USER_ID, f"Сообщение от мужа:\n{weather}")
        await msg.edit_text("✅ Погода отправлена")
    except asyncio.TimeoutError:
        await msg.edit_text("❌ Не удалось получить погоду за 7 секунд (таймаут)")
    except Exception as e:
        logger.error(f"Ошибка отправки погоды: {e}")
        await msg.edit_text("❌ Не удалось отправить погоду (ошибка)")

async def scheduled_weather():
    """Scheduled weather update for automatic sending"""
    try:
        weather = await get_lyubertsy_weather_text()
        await bot.send_message(TARGET_USER_ID, f"🌞 Утренняя погода:\n{weather}")
    except Exception as e:
        logger.error(f"Ошибка отправки запланированной погоды: {e}")

# --- Обработчики команд и сообщений ---
async def admin_help(message: types.Message, **kwargs):
    help_text = (
        "🛠️ Админские команды:\n"
        "/test_water — тестовое напоминание про воду\n"
        "/test_tablets — тестовое напоминание про таблетки\n"
        "/test_mood — тестовое напоминание про трекинг настроения\n"
        "/test_tip — тестовый случайный совет\n"
        "/send_water — отправить напоминание про воду ей\n"
        "/send_tablets — отправить напоминание про таблетки ей\n"
        "/send_mood — отправить напоминание про трекинг настроения ей\n"
        "/send_tip — отправить совет ей\n"
        "/send_weather — отправить погоду ей\n"  # Добавлено
        "/say <текст> — отправить произвольное сообщение ей\n"
        "/clear_log — очистить лог состояний\n"
        "/test_log — добавить тестовую запись в лог\n"
        "/export_log — выгрузить лог\n"
        "/admin_help — этот список команд"
    )
    await message.answer(help_text)

async def main():
    try:
        print("[INFO] Bot starting...")
        logger.info("Starting bot...")
        
        # --- Регистрация хэндлеров ---
        print("[DEBUG] Registering handlers...")
        dp.message.register(start_handler, Command("start"))
        dp.message.register(admin_only(test_water), Command("test_water"))
        dp.message.register(admin_only(test_tablets), Command("test_tablets"))
        dp.message.register(admin_only(test_mood), Command("test_mood"))
        dp.message.register(admin_only(test_tip), Command("test_tip"))
        dp.message.register(admin_only(send_water), Command("send_water"))
        dp.message.register(admin_only(send_weather_to_user), Command("send_weather"))  # Добавлено
        dp.message.register(admin_only(send_tablets), Command("send_tablets"))
        dp.message.register(admin_only(send_mood), Command("send_mood"))
        dp.message.register(admin_only(send_tip), Command("send_tip"))
        dp.message.register(admin_only(send_message), Command("say"))
        dp.message.register(admin_only(test_reminders), Command("test_remind"))
        dp.message.register(admin_only(clear_log), Command("clear_log"))
        dp.message.register(admin_only(test_log_entry), Command("test_log"))
        dp.message.register(admin_only(export_log), Command("export_log"))
        dp.message.register(admin_only(admin_help), Command("admin_help"))
        dp.message.register(disable_pings, Command(commands=["отъебись", "off", "disable"]))  # Добавлены альтернативные команды
        dp.message.register(process_input)  # fallback

        dp.callback_query.register(reminder_callback_handler, lambda c: c.data in ['confirm_water', 'confirm_posture'])
        dp.callback_query.register(confirm_tablets_callback, lambda c: c.data == 'confirm_tablets')
        dp.callback_query.register(confirm_water_callback, lambda c: c.data == 'confirm_water')
        dp.callback_query.register(mood_callback_handler, lambda c: c.data.startswith("mood_"))

        print("[DEBUG] Starting scheduler...")
        # --- Используем pytz для таймзоны Москвы ---
        moscow_tz = pytz.timezone("Europe/Moscow")

        # Schedule jobs
        print("[DEBUG] Scheduling jobs...")
        
        # Регулярные напоминания
        # Вода: каждые 2 часа с 7:00 до 23:00
        scheduler.add_job(send_water_reminder, 'cron', hour='7-23/2', args=[TARGET_USER_ID], timezone=moscow_tz)
        # Таблетки: только дневные (пример: 9:30, 14:00, 23:00)
        scheduler.add_job(send_tablets_reminder, 'cron', hour=9, minute=30, args=[TARGET_USER_ID], timezone=moscow_tz)
        scheduler.add_job(send_tablets_reminder, 'cron', hour=14, minute=0, args=[TARGET_USER_ID], timezone=moscow_tz)
        scheduler.add_job(send_tablets_reminder, 'cron', hour=23, minute=0, args=[TARGET_USER_ID], timezone=moscow_tz)
        # Трекинг настроения: только после 7:00 и до полуночи (пример: 9:35 и 21:05)
        scheduler.add_job(send_mood_reminder, 'cron', hour=9, minute=35, args=[TARGET_USER_ID], timezone=moscow_tz)
        scheduler.add_job(send_mood_reminder, 'cron', hour=21, minute=5, args=[TARGET_USER_ID], timezone=moscow_tz)
        # Советы: каждые 4 часа с 7:00 до 23:00
        scheduler.add_job(periodic_tip, 'cron', hour='7-23/4', timezone=moscow_tz)
        # Погода в Люберцах каждый день в 7:30
        scheduler.add_job(scheduled_weather, 'cron', hour=7, minute=30, timezone=moscow_tz)

        # Start scheduler
        scheduler.start()
        print("[INFO] Scheduler started successfully")
        
        # Log scheduled jobs
        print("[INFO] Scheduled jobs:")
        for job in scheduler.get_jobs():
            print(f"  {job.id}: next run at {job.next_run_time}")

        # Start polling
        print("[INFO] Starting polling...")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
        
    except Exception as e:
        print(f"[CRITICAL] Fatal error in main(): {e}")
        logger.critical(f"Fatal error in main(): {e}", exc_info=True)
        raise
    finally:
        await shutdown(dp)

# --- Handler functions ---
async def mood_callback_handler(callback_query: types.CallbackQuery):
    try:
        # Parse callback data
        _, step, value = callback_query.data.split('_')
        step = int(step)
        value = int(value)
        chat_id = callback_query.message.chat.id

        # Initialize user data if needed
        if chat_id not in user_data:
            user_data[chat_id] = {'step': 0, 'entry': {}}

        # Save the value
        field_key, _ = mood_fields[step]
        user_data[chat_id]['entry'][field_key] = value
        user_data[chat_id]['step'] = step + 1

        # Notify admin about the response
        if chat_id == TARGET_USER_ID:
            await bot.send_message(ADMIN_ID, f"Ответ на опрос ({field_key}): {value}")

        # Update message to show the selected value
        await callback_query.message.edit_text(f"{mood_fields[step][1]}: {value}")

        # If not last step, ask next question
        if step + 1 < len(mood_fields):
            await ask_next_field_mood(chat_id)
        else:
            # НЕ сохраняем здесь, только запрашиваем комментарий
            await bot.send_message(
                chat_id,
                "Хочешь что-то добавить? Напиши сюда. Если нет — просто отправь '-' или 'нет'."
            )
            active_users.discard(chat_id)  # Remove from active users when done with questions

    except Exception as e:
        logger.error(f"Error in mood_callback_handler: {e}")
        await callback_query.answer("Произошла ошибка. Попробуйте еще раз.")
    finally:
        await callback_query.answer()

if __name__ == '__main__':
    try:
        print("[INFO] Starting bot...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[INFO] Bot stopped by user")
        logger.info("Bot stopped by user")
    except Exception as e:
        print(f"[CRITICAL] Unexpected error: {e}")
        logger.critical(f"Unexpected error: {e}", exc_info=True)
    finally:
        print("[INFO] Bot shutdown complete")
        logger.info("Bot shutdown complete")
