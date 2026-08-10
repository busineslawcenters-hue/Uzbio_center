import asyncio
import logging
import os
import re

from dotenv import load_dotenv

load_dotenv()  # подхватывает переменные из файла .env, лежащего рядом с bot.py

import aiohttp
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

logging.basicConfig(level=logging.INFO)

# =========================================================
# НАСТРОЙКИ — поправьте под себя
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_TELEGRAM_BOT_TOKEN_HERE")

# Вебхук Bitrix24, например:
# https://your-company.bitrix24.ru/rest/1/xxxxxxxxxxxxxxxxx/
BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL", "PUT_YOUR_BITRIX_WEBHOOK_URL_HERE")

# ID канала/чата, куда будут падать заявки, например: -1001234567890
# Бот должен быть добавлен в этот канал/чат как администратор.
CHANNEL_ID = os.getenv("CHANNEL_ID", "PUT_YOUR_CHANNEL_ID_HERE")

# Продукты: у каждого — своё название (ru/uz) и фото.
# "photo" может быть:
#   - путём к локальному файлу, например "photos/product1.jpg"
#   - либо прямой ссылкой на картинку в интернете, например "https://.../image.jpg"
PRODUCTS = {
    "product_1": {
        "ru": "«KRISTALL»",
        "uz": "«KRISTALL» ",
        "photo": "product1.jpg",
    },
    "product_2": {
        "ru": "«A9 ANDROBÓSS»",
        "uz": "«A9 ANDROBÓSS»",
        "photo": "product2.jpg",
    },
    "product_3": {
        "ru": "«S9 SUSTAV PRO MAX»",
        "uz": "«S9 SUSTAV PRO MAX»",
        "photo": "product3.jpg",
    },
}

# Регионы Узбекистана (14 административных единиц)
REGIONS = {
    "ru": [
        "г. Ташкент", "Ташкентская область", "Андижанская область",
        "Ферганская область", "Наманганская область", "Сырдарьинская область",
        "Джизакская область", "Самаркандская область", "Бухарская область",
        "Навоийская область", "Кашкадарьинская область", "Сурхандарьинская область",
        "Хорезмская область", "Республика Каракалпакстан",
    ],
    "uz": [
        "Toshkent sh.", "Toshkent viloyati", "Andijon viloyati",
        "Farg'ona viloyati", "Namangan viloyati", "Sirdaryo viloyati",
        "Jizzax viloyati", "Samarqand viloyati", "Buxoro viloyati",
        "Navoiy viloyati", "Qashqadaryo viloyati", "Surxondaryo viloyati",
        "Xorazm viloyati", "Qoraqalpog'iston Respublikasi",
    ],
}

OTHER_CITY = {"ru": "✍️ Другой город (напишите сами)", "uz": "✍️ Boshqa shahar (o'zingiz yozing)"}

SELECT_BTN = {"ru": "✅ Выбрать", "uz": "✅ Tanlash"}

TEXTS = {
    "choose_lang": "Выберите язык / Tilni tanlang",
    "ru": {
        "welcome": "Здравствуйте! 👋\nЭто бот для оформления заявки.",
        "ask_phone": "Пожалуйста, отправьте ваш номер телефона, нажав на кнопку ниже.",
        "phone_btn": "📱 Отправить номер телефона",
        "ask_product": "Выберите продукт, который вас интересует:",
        "ask_name": "Введите вашу Фамилию и Имя:",
        "ask_age": "Укажите ваш возраст:",
        "ask_region": "Выберите ваш регион:",
        "done": (
            "✅ Спасибо! Ваша заявка принята.\n\n"
            "Телефон: {phone}\n"
            "Продукт: {product}\n"
            "ФИО: {name}\n"
            "Возраст: {age}\n"
            "Регион: {region}\n\n"
            "Наш менеджер свяжется с вами в ближайшее время."
        ),
        "need_contact": "Пожалуйста, воспользуйтесь кнопкой ниже, чтобы отправить номер, либо введите его вручную (например: +998901234567).",
        "need_age": "Пожалуйста, введите возраст цифрами, например: 35",
    },
    "uz": {
        "welcome": "Assalomu alaykum! 👋\nBu ariza topshirish uchun bot.",
        "ask_phone": "Iltimos, quyidagi tugma orqali telefon raqamingizni yuboring.",
        "phone_btn": "📱 Telefon raqamni yuborish",
        "ask_product": "Sizni qiziqtirgan mahsulotni tanlang:",
        "ask_name": "Familiya va ismingizni kiriting:",
        "ask_age": "Yoshingizni kiriting:",
        "ask_region": "Hududingizni tanlang:",
        "done": (
            "✅ Rahmat! Arizangiz qabul qilindi.\n\n"
            "Telefon: {phone}\n"
            "Mahsulot: {product}\n"
            "F.I.Sh: {name}\n"
            "Yosh: {age}\n"
            "Hudud: {region}\n\n"
            "Bizning menejerimiz siz bilan tez orada bog'lanadi."
        ),
        "need_contact": "Iltimos, pastdagi tugma orqali yoki qo'lda kiriting (masalan: +998901234567).",
        "need_age": "Iltimos, yoshingizni raqamlar bilan kiriting, masalan: 35",
    },
}


class Form(StatesGroup):
    lang = State()
    phone = State()
    product = State()
    name = State()
    age = State()
    region = State()


router = Router()


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
        ]
    ])


def phone_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=TEXTS[lang]["phone_btn"], request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def send_products(message: Message, lang: str, state: FSMContext):
    """Отправляет каждый продукт отдельным сообщением: фото + подпись + кнопка выбора под ним."""
    sent_messages = []
    for key, data in PRODUCTS.items():
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=SELECT_BTN[lang], callback_data=key)]
        ])
        caption = data[lang]
        photo = data.get("photo")

        sent = None
        if photo:
            try:
                photo_input = photo if photo.startswith("http") else FSInputFile(photo)
                sent = await message.answer_photo(photo=photo_input, caption=caption, reply_markup=kb)
            except Exception as e:
                logging.exception("Не удалось отправить фото продукта %s: %s", key, e)

        if sent is None:
            # если фото не задано или не удалось отправить — отправляем просто текст с кнопкой
            sent = await message.answer(caption, reply_markup=kb)

        sent_messages.append({"chat_id": sent.chat.id, "message_id": sent.message_id})

    await state.update_data(product_messages=sent_messages)


def region_keyboard(lang: str) -> ReplyKeyboardMarkup:
    regions = REGIONS[lang]
    rows = [regions[i:i + 2] for i in range(0, len(regions), 2)]
    keyboard = [[KeyboardButton(text=r) for r in row] for row in rows]
    keyboard.append([KeyboardButton(text=OTHER_CITY[lang])])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(TEXTS["choose_lang"], reply_markup=lang_keyboard())
    await state.set_state(Form.lang)


@router.callback_query(F.data.in_(["lang_ru", "lang_uz"]))
async def process_lang(callback: CallbackQuery, state: FSMContext):
    lang = "ru" if callback.data == "lang_ru" else "uz"
    await state.update_data(lang=lang)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(TEXTS[lang]["welcome"])
    await callback.message.answer(TEXTS[lang]["ask_phone"], reply_markup=phone_keyboard(lang))
    await state.set_state(Form.phone)
    await callback.answer()


PHONE_RE = re.compile(r"^\+?\d[\d\s\-\(\)]{6,17}\d$")


async def _accept_phone(message: Message, state: FSMContext, phone: str):
    data = await state.get_data()
    lang = data["lang"]
    await state.update_data(phone=phone)
    await message.answer("👍", reply_markup=ReplyKeyboardRemove())
    await message.answer(TEXTS[lang]["ask_product"])
    await send_products(message, lang, state)
    await state.set_state(Form.product)


@router.message(Form.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    await _accept_phone(message, state, message.contact.phone_number)


@router.message(Form.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    # Принимаем номер, введённый вручную текстом — важно для случаев,
    # когда кнопка "поделиться контактом" недоступна (например, у аккаунтов
    # без привязанного номера, у модерации Telegram Ads при автоматической
    # проверке бота, или если пользователь просто набрал номер сам).
    text = message.text.strip()
    if PHONE_RE.match(text):
        await _accept_phone(message, state, text)
        return

    data = await state.get_data()
    lang = data.get("lang", "ru")
    await message.answer(TEXTS[lang]["need_contact"], reply_markup=phone_keyboard(lang))


@router.message(Form.phone)
async def process_phone_invalid(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await message.answer(TEXTS[lang]["need_contact"], reply_markup=phone_keyboard(lang))


@router.callback_query(Form.product, F.data.in_(list(PRODUCTS.keys())))
async def process_product(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data["lang"]
    product_key = callback.data
    await state.update_data(product=product_key)

    # убираем кнопки со всех карточек продуктов, не только с выбранной
    for msg_ref in data.get("product_messages", []):
        try:
            await bot.edit_message_reply_markup(
                chat_id=msg_ref["chat_id"], message_id=msg_ref["message_id"], reply_markup=None
            )
        except Exception:
            pass

    await callback.message.answer(TEXTS[lang]["ask_name"])
    await state.set_state(Form.name)
    await callback.answer()


@router.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    await state.update_data(name=message.text.strip())
    await message.answer(TEXTS[lang]["ask_age"])
    await state.set_state(Form.age)


@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    age_text = message.text.strip()

    if not age_text.isdigit() or not (1 <= int(age_text) <= 120):
        await message.answer(TEXTS[lang]["need_age"])
        return

    await state.update_data(age=age_text)
    await message.answer(TEXTS[lang]["ask_region"], reply_markup=region_keyboard(lang))
    await state.set_state(Form.region)


@router.message(Form.region)
async def process_region(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    text = message.text.strip()

    # Если уже ждём произвольное название города — просто сохраняем его
    if data.get("awaiting_custom_region"):
        await state.update_data(region=text, awaiting_custom_region=False)
        await finish_form(message, state)
        return

    if text == OTHER_CITY[lang]:
        prompt = "Напишите название вашего города:" if lang == "ru" else "Shahringiz nomini yozing:"
        await message.answer(prompt, reply_markup=ReplyKeyboardRemove())
        await state.update_data(awaiting_custom_region=True)
        return

    await state.update_data(region=text)
    await finish_form(message, state)


async def finish_form(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    phone = data.get("phone", "")
    product_key = data.get("product")
    product_name = PRODUCTS[product_key][lang] if product_key else ""
    name = data.get("name", "")
    age = data.get("age", "")
    region = data.get("region", "")
    telegram_username = message.from_user.username or ""
    telegram_id = message.from_user.id

    await message.answer(
        TEXTS[lang]["done"].format(phone=phone, product=product_name, name=name, age=age, region=region),
        reply_markup=ReplyKeyboardRemove(),
    )

    await send_to_bitrix(
        lang=lang,
        phone=phone,
        product_name=product_name,
        full_name=name,
        age=age,
        region=region,
        telegram_username=telegram_username,
        telegram_id=telegram_id,
    )

    await send_to_channel(
        bot=message.bot,
        phone=phone,
        product_name=product_name,
        full_name=name,
        age=age,
        region=region,
        telegram_username=telegram_username,
        telegram_id=telegram_id,
    )

    await state.clear()


async def send_to_bitrix(lang, phone, product_name, full_name, age, region, telegram_username, telegram_id):
    if not BITRIX_WEBHOOK_URL or "PUT_YOUR" in BITRIX_WEBHOOK_URL:
        logging.warning("BITRIX_WEBHOOK_URL не настроен — заявка не отправлена в CRM")
        return

    url = BITRIX_WEBHOOK_URL.rstrip("/") + "/crm.lead.add.json"

    name_parts = full_name.split(maxsplit=1)
    last_name = name_parts[0] if name_parts else full_name
    first_name = name_parts[1] if len(name_parts) > 1 else ""

    comments = (
        f"Язык/Til: {lang}\n"
        f"Продукт/Mahsulot: {product_name}\n"
        f"Возраст/Yosh: {age}\n"
        f"Регион/Hudud: {region}\n"
        f"Telegram: @{telegram_username} (id {telegram_id})"
    )

    payload = {
        "fields": {
            "TITLE": f"Заявка из Telegram-бота — {product_name}",
            "NAME": first_name,
            "LAST_NAME": last_name,
            "PHONE": [{"VALUE": phone, "VALUE_TYPE": "WORK"}],
            "COMMENTS": comments,
            "SOURCE_ID": "WEB",
        },
        "params": {"REGISTER_SONET_EVENT": "Y"},
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=15) as resp:
                result = await resp.json()
                if resp.status != 200 or "result" not in result:
                    logging.error("Ошибка Bitrix24: %s", result)
                else:
                    logging.info("Лид создан в Bitrix24, id=%s", result["result"])
    except Exception as e:
        logging.exception("Не удалось отправить лид в Bitrix24: %s", e)


async def send_to_channel(bot: Bot, phone, product_name, full_name, age, region, telegram_username, telegram_id):
    """Отправляет карточку заявки в Telegram-канал/чат, указанный в CHANNEL_ID."""
    if not CHANNEL_ID or "PUT_YOUR" in str(CHANNEL_ID):
        logging.warning("CHANNEL_ID не настроен — заявка не отправлена в канал")
        return

    text = (
        "🆕 <b>Новая заявка</b>\n\n"
        f"📞 Телефон: {phone}\n"
        f"📦 Продукт: {product_name}\n"
        f"👤 ФИО: {full_name}\n"
        f"🎂 Возраст: {age}\n"
        f"📍 Регион: {region}\n"
        f"💬 Telegram: @{telegram_username or '—'} (id {telegram_id})"
    )

    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logging.exception("Не удалось отправить заявку в канал: %s", e)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
