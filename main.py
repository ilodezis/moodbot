import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.types import FSInputFile

import datetime
import json
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- Новые константы ---
ADMIN_ID = 409183653  # <-- теперь только admin

API_TOKEN = '7818869168:AAGmcVSu7NliSSoNiBLoe2ARzVLCYgbpgRI'

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
    "Ты — не проблема. Ты — процесс."
    "🚶 Прогуляйся хотя бы 10 минут. Даже если не хочется — это сработает.",
    "🧘 Сделай 5 глубоких вдохов и выдохов. Это обнулит нервную систему.",
    "🛏️ Если чувствуешь перегруз — просто полежи с закрытыми глазами 10 минут.",
    "🎧 Включи музыку, которая тебя собирает. Даже одна песня может сменить состояние.",
    "📴 Убери телефон хотя бы на полчаса. Мозг отдохнёт от шума.",
    "💤 Не залипай — попробуй лечь спать чуть раньше сегодня.",
"   📓 Запиши всё, что тебя грузит. Мозг не любит таскать это внутри.",
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
    "🎈 Ты не обязана быть продуктивной, чтобы быть ценной."
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
            types.InlineKeyboardButton(text="✅ Выпила", callback_data="confirm_water"),
            types.InlineKeyboardButton(text="🧘 Осанка", callback_data="confirm_posture"),
            types.InlineKeyboardButton(text="⏰ Позже", callback_data="later")
        ]
    ]
)

# --- Обёртка для проверки ADMIN_ID ---
def admin_only(handler):
    async def wrapper(message, *args, **kwargs):
        # Проверяем только команды, начинающиеся с /
        if message.text and message.text.startswith('/'):
            if message.from_user.id != ADMIN_ID:
                print(f"[LOG] Access denied for {message.from_user.id} to admin command {message.text}")
                await message.answer("У тебя нет доступа к этой команде.")
                return
            print(f"[LOG] ADMIN {message.from_user.id} triggered {message.text}")
        return await handler(message, *args, **kwargs)
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

@dp.message(Command(commands=['start']))
async def start_handler(message: types.Message):
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

async def ask_next_field(message):
    user_id = message.chat.id
    print(f"[DEBUG] ask_next_field for user {user_id}, step {user_data[user_id]['step']}")
    step = user_data[user_id]['step']
    if step < len(mood_fields):
        _, field_name = mood_fields[step]
        await message.answer(f"{field_name} (1–10):")
    else:
        await message.answer("Хочешь что-то добавить? Напиши сюда. Если нет — просто отправь '-' или 'нет'.")

@dp.message(Command(commands=['_test_remind']))
@admin_only
async def test_reminders(message: types.Message):
    print(f"[DEBUG] test_reminders called by {message.chat.id}")
    await send_reminder()
    await periodic_tip()
    await message.answer("🔔 Тестовые напоминания и советы отправлены.")

@dp.message(Command(commands=['_test_water']))
@admin_only
async def test_water(message: types.Message):
    print(f"[DEBUG] test_water called by {message.chat.id}")
    await message.answer("💧 Напоминание: не забудь пить воду", reply_markup=reminder_kb)
    reminder_states[message.chat.id] = {'type': 'water', 'time': datetime.datetime.now()}
    asyncio.create_task(water_annoy_loop(message.chat.id))

@dp.message(Command(commands=['_test_tablets']))
@admin_only
async def test_tablets(message: types.Message):
    print(f"[DEBUG] test_tablets called by {message.chat.id}")
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Приняла", callback_data="confirm_tablets")]
        ]
    )
    await message.answer("💊 Напоминание: не забудь принять добавки / таблетки", reply_markup=keyboard)
    reminder_states[message.chat.id] = {'type': 'tablets', 'time': datetime.datetime.now()}
    asyncio.create_task(tablet_annoy_loop(message.chat.id))

@dp.message(Command(commands=['_test_mood']))
@admin_only
async def test_mood(message: types.Message):
    print(f"[DEBUG] test_mood called by {message.chat.id}")
    await message.answer("🧠 Пора оценить своё состояние. Напиши /start и просто отметь, как ты")
    print(f"[DEBUG] test_reminders called by {message.chat.id}")
    await send_reminder()
    await periodic_tip()
    await message.answer("🔔 Тестовые напоминания и советы отправлены.")

@dp.message(Command(commands=['_test_tip']))
@admin_only
async def test_random_tip(message: types.Message):
    print(f"[DEBUG] test_random_tip called by {message.chat.id}")
    await message.answer(f"Тестовый совет: {random.choice(random_tips)}")

@dp.message(Command(commands=['_clear_log']))
@admin_only
async def clear_log(message: types.Message):
    print(f"[DEBUG] clear_log called by {message.chat.id}")
    with open(STATE_FILE, 'w') as f:
        json.dump([], f)
    await message.answer("🧹 Лог очищен. Все записи удалены.")

@dp.message(Command(commands=['_test_log']))
@admin_only
async def test_log_entry(message: types.Message):
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

@dp.message(Command(commands=['export_log']))
@admin_only
async def export_log(message: types.Message):
    try:
        print(f"[LOG] export_log called by {message.chat.id}")
        await message.answer_document(
            types.FSInputFile("mood_log.json"),
            caption="📂 Вот лог со всеми состояниями"
        )
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при отправке: {e}")

@dp.message(Command(commands=['отъебись']))
async def disable_pings(message: types.Message):
    ping_blocked_until[message.chat.id] = datetime.datetime.now() + datetime.timedelta(hours=1)
    print(f"[LOG] USER {message.chat.id} отключил напоминания до {ping_blocked_until[message.chat.id]}")
    await message.answer("🫠 Окей, отключаю напоминания на 1 час. Но потом я вернусь!")

@dp.message()
async def process_input(message: types.Message):
    # --- Исправлено: убрана опечатка и лишний символ, исправлен отступ ---
    if message.from_user.id == ADMIN_ID:
        # Можно просто return, либо явно:
        await message.answer("Этот бот не предназначен для ввода данных админом.")
        return

    if message.text.lower().strip() in ['/export_log', '/start', '/отъебись']:
        return  # эти команды обрабатываются отдельно
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
            if not (1 <= val <= 10):
                raise ValueError
            field_key, _ = mood_fields[step]
            user_data[user_id]['entry'][field_key] = val
            user_data[user_id]['step'] += 1
            await ask_next_field(message)
        except ValueError:
            await message.answer("Пожалуйста, введи число от 1 до 10.")
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
        user_data.pop(user_id, None)

# --- CallbackQuery хэндлеры оставляем без проверки user_only_callback ---
@dp.callback_query(lambda c: c.data in ['confirm_water', 'confirm_posture', 'later'])
async def reminder_callback_handler(callback_query: types.CallbackQuery):
    print(f"[LOG] Callback {callback_query.data} от {callback_query.from_user.id}")
    if callback_query.data.startswith('confirm_'):
        await callback_query.message.edit_text("Принято! 🥳")
    elif callback_query.data == 'later':
        await callback_query.message.edit_text("Ок, напомню позже.")

@dp.callback_query(lambda c: c.data == 'confirm_tablets')
async def confirm_tablets_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    reminder_states.pop(chat_id, None)
    print(f"[LOG] confirm_tablets от {chat_id}")
    await callback_query.message.edit_text("💊 Принято. Умница.")

@dp.callback_query(lambda c: c.data == 'confirm_water')
async def confirm_water_callback(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    reminder_states.pop(chat_id, None)
    print(f"[LOG] confirm_water от {chat_id}")
    await callback_query.message.edit_text("💧 Хорош! Вода внутри — сила снаружи.")

async def water_annoy_loop(chat_id):
    await asyncio.sleep(1800)  # 30 минут
    while chat_id in reminder_states and reminder_states[chat_id]['type'] == 'water':
        if chat_id in ping_blocked_until and datetime.datetime.now() < ping_blocked_until[chat_id]:
            await asyncio.sleep(60)
            continue
        try:
            await bot.send_message(chat_id, random.choice([
                "🚨 Ты воду вообще пьёшь, нет?",
                "💦 Алё, организм сушится",
                "🌊 Напоминаю: H2O — это важно, а не просто химия!"
            ]), reply_markup=reminder_kb)
            print(f"[LOG] water_annoy_loop: отправлено напоминание пользователю {chat_id}")
            await asyncio.sleep(300)
        except Exception as e:
            print(f"[LOG] water_annoy_loop error: {e}")
            continue

async def tablet_annoy_loop(chat_id):
    await asyncio.sleep(1800)  # 30 минут
    while chat_id in reminder_states and reminder_states[chat_id]['type'] == 'tablets':
        if chat_id in ping_blocked_until and datetime.datetime.now() < ping_blocked_until[chat_id]:
            await asyncio.sleep(60)
            continue
        try:
            keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="✅ Приняла", callback_data="confirm_tablets")]
                ]
            )
            await bot.send_message(chat_id, random.choice([
                "💊 Таблетки сами себя не примут!",
                "🧠 А добавочки где?",
                "⏰ Если не приняла — я буду пиликать!"
            ]), reply_markup=keyboard)
            print(f"[LOG] tablet_annoy_loop: отправлено напоминание пользователю {chat_id}")
            await asyncio.sleep(300)
        except Exception as e:
            print(f"[LOG] tablet_annoy_loop error: {e}")
            continue

def save_entry(entry):
    print(f"[DEBUG] save_entry: {entry}")
    with open(STATE_FILE, 'r+') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.truncate()

async def send_reminder():
    print("[DEBUG] send_reminder called")
    for chat_id in list(user_data.keys()):
        try:
            await bot.send_message(chat_id, "👋 Напоминание: не забудь оценить состояние и принять добавки. Напиши /start", reply_markup=reminder_kb)
            print(f"[LOG] send_reminder отправлено пользователю {chat_id}")
        except Exception as e:
            print(f"[LOG] send_reminder error: {e}")
            continue

async def periodic_tip():
    print("[DEBUG] periodic_tip called")
    for chat_id in list(user_data.keys()):
        try:
            await bot.send_message(chat_id, f"📌 Совет: {random.choice(random_tips)}")
            print(f"[LOG] periodic_tip отправлено пользователю {chat_id}")
        except Exception as e:
            print(f"[LOG] periodic_tip error: {e}")
            continue

async def main():
    print("[DEBUG] main() started")
    scheduler.add_job(send_reminder, 'cron', hour=9)
    scheduler.add_job(send_reminder, 'cron', hour=21)
    for h in [0, 3, 6, 9, 12, 15, 18, 21]:
        scheduler.add_job(periodic_tip, 'cron', hour=h)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    print("[DEBUG] __main__ entry")
    asyncio.run(main())
