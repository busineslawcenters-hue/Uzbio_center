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
        "desc": {
            "uz": (
                "KRISTALL nima?\n\n"
                "KRISTALL — ko'z salomatligi va ko'rish organlarining normal fiziologik faoliyatini "
                "qo'llab-quvvatlashga mo'ljallangan vitaminlar, aminokislotalar va biologik faol "
                "moddalardan tashkil topgan kompleks.\n\n"
                "Ayniqsa telefon, kompyuter va boshqa ekranlar qarshisida ko'p vaqt o'tkazadigan "
                "insonlar uchun mos.\n\n"
                "Asosiy tarkibi:\n"
                "• Chernika ekstrakti — 200 mg\n"
                "• Lutein — 10 mg\n"
                "• Taurin — 100 mg\n"
                "• A vitamini\n"
                "• E vitamini — 10 mg\n\n"
                "Qanday foyda beradi?\n"
                "• Lutein — ko'z to'r pardasi tarkibida uchraydigan muhim pigmentlardan biri bo'lib, "
                "ko'rish tizimining normal faoliyatida ishtirok etadi.\n"
                "• Chernika tarkibidagi biologik faol moddalar ko'z salomatligini qo'llab-quvvatlash "
                "uchun qo'llanadi.\n"
                "• Taurin ko'z to'qimalaridagi metabolik va energetik jarayonlarda ishtirok etuvchi "
                "aminokislotadir.\n"
                "• A va E vitaminlari esa antioksidant himoya hamda ko'rish tizimining normal "
                "faoliyatini qo'llab-quvvatlashda muhim ahamiyatga ega.\n\n"
                "KRISTALL:\n"
                "• ko'zlarning tez charchashida;\n"
                "• telefon va kompyuterda uzoq ishlaganda;\n"
                "• uzoq vaqt kitob o'qiganda;\n"
                "• yuqori vizual yuklama vaqtida;\n"
                "• ko'rish organlarining normal faoliyatini saqlashda;\n"
                "• ko'z to'qimalarini antioksidant himoya bilan ta'minlashda qo'shimcha yordam "
                "berishi mumkin.\n\n"
                "Kimlar uchun?\n"
                "• kompyuterda ko'p ishlaydiganlar;\n"
                "• telefondan muntazam foydalanadiganlar;\n"
                "• uzoq vaqt o'qiydigan talabalar va o'quvchilar;\n"
                "• ko'zlari tez charchaydigan insonlar;\n"
                "• ko'z salomatligini vitamin va mikroelementlar bilan qo'llab-quvvatlashni "
                "istaganlar.\n\n"
                "Qo'llash usuli:\n"
                "• Kattalar: ovqatdan 30 daqiqa keyin 1 kapsuladan kuniga 2 mahal.\n"
                "• 6 yoshdan katta bolalar: 1 kapsuladan kuniga 1 mahal.\n"
                "• Tavsiya etilgan kurs: 30 kun."
            ),
            "ru": (
                "Что такое KRISTALL?\n\n"
                "KRISTALL — комплекс витаминов, аминокислот и биологически активных веществ, "
                "предназначенный для поддержки здоровья глаз и нормальной физиологической функции "
                "органов зрения.\n\n"
                "Особенно подходит людям, которые проводят много времени перед телефоном, "
                "компьютером и другими экранами.\n\n"
                "Основной состав:\n"
                "• Экстракт черники — 200 мг\n"
                "• Лютеин — 10 мг\n"
                "• Таурин — 100 мг\n"
                "• Витамин A\n"
                "• Витамин E — 10 мг\n\n"
                "Какую пользу приносит?\n"
                "• Лютеин — один из важных пигментов, содержащихся в сетчатке глаза, участвует в "
                "нормальном функционировании зрительной системы.\n"
                "• Биологически активные вещества, содержащиеся в чернике, применяются для "
                "поддержки здоровья глаз.\n"
                "• Таурин — аминокислота, участвующая в метаболических и энергетических процессах "
                "в тканях глаза.\n"
                "• Витамины A и E играют важную роль в антиоксидантной защите и поддержании "
                "нормального функционирования зрительной системы.\n\n"
                "KRISTALL может оказать дополнительную поддержку:\n"
                "• при быстрой утомляемости глаз;\n"
                "• при длительной работе за телефоном и компьютером;\n"
                "• при длительном чтении книг;\n"
                "• при высокой зрительной нагрузке;\n"
                "• для поддержания нормального функционирования органов зрения;\n"
                "• для обеспечения антиоксидантной защиты тканей глаза.\n\n"
                "Для кого?\n"
                "• для людей, много работающих за компьютером;\n"
                "• для тех, кто регулярно пользуется телефоном;\n"
                "• для студентов и школьников, много читающих;\n"
                "• для людей с быстрой утомляемостью глаз;\n"
                "• для тех, кто хочет поддержать здоровье глаз витаминами и микроэлементами.\n\n"
                "Способ применения:\n"
                "• Взрослым: по 1 капсуле 2 раза в день через 30 минут после еды.\n"
                "• Детям старше 6 лет: по 1 капсуле 1 раз в день.\n"
                "• Рекомендуемый курс: 30 дней."
            ),
        },
    },
    "product_2": {
        "ru": "«A9 ANDROBÓSS»",
        "uz": "«A9 ANDROBÓSS»",
        "photo": "product2.jpg",
        "desc": {
            "uz": (
                "A9 ANDROBOSS nima?\n\n"
                "A9 ANDROBOSS — erkaklar organizmi va jinsiy faoliyatini qo'llab-quvvatlashga "
                "mo'ljallangan biologik faol qo'shimcha.\n\n"
                "Mahsulot tarkibidagi jenshen, evrikoma, tribulus, rux, selen hamda vitaminlar "
                "organizmning umumiy tonusi, jismoniy faollik va erkaklar reproduktiv tizimini "
                "qo'llab-quvvatlashga yordam beradi.\n\n"
                "Asosiy tarkibi:\n"
                "• Jenshen ekstrakti — 50 mg\n"
                "• Evrikoma ildizi — 200 mg\n"
                "• Tribulus ildizi — 500 mg\n"
                "• C vitamini — 25 mg\n"
                "• Rux oksidi — 20 mg\n"
                "• Natriy selenit — 50 mkg\n"
                "• E vitamini — 50 mg\n\n"
                "Qanday foyda beradi?\n"
                "• jismoniy va ruhiy charchoq paytida organizmni qo'llab-quvvatlashga;\n"
                "• erkaklarning jinsiy faolligi va umumiy tonusini saqlashga;\n"
                "• normal testosteron almashinuvini qo'llab-quvvatlashga;\n"
                "• spermatogenez va spermatozoidlarning normal harakatchanligini "
                "qo'llab-quvvatlashga;\n"
                "• erkaklar reproduktiv tizimining normal faoliyatini saqlashga yordam berishi "
                "mumkin.\n\n"
                "Tarkibidagi rux erkaklar reproduktiv salomatligi va immun tizimi uchun muhim "
                "mikroelementlardan biri hisoblanadi.\n\n"
                "Mahsulot erkaklarda:\n"
                "• jinsiy faollik pasayganda;\n"
                "• jismoniy va ruhiy charchoq kuchayganda;\n"
                "• reproduktiv tizim faoliyatini qo'llab-quvvatlash zarur bo'lganda;\n"
                "• spermatozoidlar soni yoki harakatchanligi bilan bog'liq holatlarda qo'shimcha "
                "vosita sifatida tavsiya etilishi mumkin.\n\n"
                "Qo'llash usuli:\n"
                "1 tabletkadan kuniga 1–2 mahal, ovqatdan keyin qabul qilinadi."
            ),
            "ru": (
                "Что такое A9 ANDROBOSS?\n\n"
                "A9 ANDROBOSS — биологически активная добавка, предназначенная для поддержки "
                "мужского организма и половой функции.\n\n"
                "Входящие в состав женьшень, элеутерококк, трибулус, цинк, селен и витамины "
                "способствуют поддержанию общего тонуса организма, физической активности и "
                "мужской репродуктивной системы.\n\n"
                "Основной состав:\n"
                "• Экстракт женьшеня — 50 мг\n"
                "• Корень элеутерококка — 200 мг\n"
                "• Корень трибулуса — 500 мг\n"
                "• Витамин C — 25 мг\n"
                "• Оксид цинка — 20 мг\n"
                "• Селенит натрия — 50 мкг\n"
                "• Витамин E — 50 мг\n\n"
                "Какую пользу приносит?\n"
                "Может способствовать:\n"
                "• поддержке организма при физической и психической усталости;\n"
                "• поддержанию половой активности и общего тонуса у мужчин;\n"
                "• поддержке нормального обмена тестостерона;\n"
                "• поддержке сперматогенеза и нормальной подвижности сперматозоидов;\n"
                "• поддержанию нормального функционирования мужской репродуктивной системы.\n\n"
                "Входящий в состав цинк является одним из важных микроэлементов для мужского "
                "репродуктивного здоровья и иммунной системы.\n\n"
                "Продукт может быть рекомендован мужчинам в качестве дополнительного средства:\n"
                "• при снижении половой активности;\n"
                "• при повышенной физической и психической усталости;\n"
                "• при необходимости поддержки репродуктивной системы;\n"
                "• при состояниях, связанных с количеством или подвижностью сперматозоидов.\n\n"
                "Способ применения:\n"
                "По 1 таблетке 1–2 раза в день, после еды."
            ),
        },
    },
    "product_3": {
        "ru": "«S9 SUSTAV PRO MAX»",
        "uz": "«S9 SUSTAV PRO MAX»",
        "photo": "product3.jpg",
        "desc": {
            "uz": (
                "S9 SUSTAV PRO MAX nima?\n\n"
                "S9 SUSTAV PRO MAX — bo'g'im, tog'ay, pay va suyak tizimini qo'llab-quvvatlashga "
                "mo'ljallangan biologik faol qo'shimcha.\n\n"
                "Mahsulot tarkibida tog'ay to'qimalarining muhim komponentlari hisoblangan "
                "glyukozamin, xondroitin va kollagen, shuningdek kaltsiy va vitaminlar mavjud.\n\n"
                "Asosiy tarkibi:\n"
                "• Kollagen — 20 mg\n"
                "• Glyukozamin gidroxloridi — 400 mg\n"
                "• Xondroitin sulfat — 400 mg\n"
                "• Kaltsiy glitserofosfat — 100 mg\n"
                "• D3 vitamini — 5 mkg\n"
                "• Kaltsiy karbonat — 200 mg\n"
                "• Askorbin kislota — 30 mg\n\n"
                "Qanday foyda beradi?\n\n"
                "S9 tarkibidagi:\n"
                "• Glyukozamin — tog'ay to'qimasining tarkibiy qismlaridan biri bo'lib, "
                "bo'g'imlarning harakatchanligini qo'llab-quvvatlaydi.\n"
                "• Xondroitin — tog'ay va biriktiruvchi to'qimalarning tabiiy komponentlaridan "
                "biri.\n"
                "• Kollagen — biriktiruvchi to'qimalarning muhim oqsili bo'lib, tog'ay, pay va "
                "boshqa to'qimalar tarkibida mavjud.\n\n"
                "Kaltsiy va D3 vitamini esa suyak tizimining normal holatini saqlashda muhim rol "
                "o'ynaydi.\n\n"
                "Kompleks:\n"
                "• bo'g'imlarning normal harakatchanligini saqlashga;\n"
                "• tog'ay va biriktiruvchi to'qimalarni qo'llab-quvvatlashga;\n"
                "• jismoniy yuklama vaqtida bo'g'imlarga tushadigan zo'riqishni yengillashtirishga;\n"
                "• suyaklar, paylar va bo'g'imlarning normal holatini saqlashga yordam beradi.\n\n"
                "Kimlar uchun?\n"
                "• faol hayot tarzini olib boradigan insonlar;\n"
                "• sportchilar, ayniqsa kuch va dinamik sport turlari bilan shug'ullanuvchilar;\n"
                "• bo'g'imlariga muntazam jismoniy yuklama tushadiganlar;\n"
                "• katta yoshdagi insonlar;\n"
                "• suyak, pay, tog'ay va bo'g'imlarni qo'llab-quvvatlashni istaganlar.\n\n"
                "Qo'llash usuli:\n"
                "Kattalar uchun — 1 tabletkadan kuniga 2 mahal, ovqat vaqtida.\n\n"
                "Tavsiya etilgan kurs: 1 oy.\n"
                "Shifokor tavsiyasiga ko'ra kursni takrorlash mumkin."
            ),
            "ru": (
                "Что такое S9 SUSTAV PRO MAX?\n\n"
                "S9 SUSTAV PRO MAX — биологически активная добавка, предназначенная для "
                "поддержки суставов, хрящевой ткани, связок и костной системы.\n\n"
                "В состав продукта входят глюкозамин, хондроитин и коллаген — важные компоненты "
                "хрящевой ткани, а также кальций и витамины.\n\n"
                "Основной состав:\n"
                "• Коллаген — 20 мг\n"
                "• Глюкозамина гидрохлорид — 400 мг\n"
                "• Хондроитина сульфат — 400 мг\n"
                "• Кальция глицерофосфат — 100 мг\n"
                "• Витамин D3 — 5 мкг\n"
                "• Карбонат кальция — 200 мг\n"
                "• Аскорбиновая кислота — 30 мг\n\n"
                "Какую пользу приносит?\n\n"
                "В составе S9:\n"
                "• Глюкозамин — один из структурных компонентов хрящевой ткани, поддерживает "
                "подвижность суставов.\n"
                "• Хондроитин — один из естественных компонентов хрящевой и соединительной "
                "ткани.\n"
                "• Коллаген — важный белок соединительной ткани, входящий в состав хрящей, связок "
                "и других тканей.\n\n"
                "Кальций и витамин D3 играют важную роль в поддержании нормального состояния "
                "костной системы.\n\n"
                "Комплекс способствует:\n"
                "• поддержанию нормальной подвижности суставов;\n"
                "• поддержке хрящевой и соединительной ткани;\n"
                "• снижению нагрузки на суставы при физических нагрузках;\n"
                "• поддержанию нормального состояния костей, связок и суставов.\n\n"
                "Для кого?\n"
                "• для людей, ведущих активный образ жизни;\n"
                "• для спортсменов, особенно занимающихся силовыми и динамичными видами спорта;\n"
                "• для тех, чьи суставы регулярно подвергаются физическим нагрузкам;\n"
                "• для людей старшего возраста;\n"
                "• для тех, кто хочет поддержать кости, связки, хрящи и суставы.\n\n"
                "Способ применения:\n"
                "Взрослым — по 1 таблетке 2 раза в день, во время еды.\n\n"
                "Рекомендуемый курс: 1 месяц.\n"
                "Курс можно повторить по рекомендации врача."
            ),
        },
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
        "welcome": "Здравствуйте! 👋\nЭто официальный бот Uzbio Center для оформления заявки.",
        "ask_phone": "Пожалуйста, напишите ваш номер телефона текстом (например: +998901234567).\nВаш номер используется только для связи с вами.",
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
        "need_contact": "Пожалуйста, введите номер телефона текстом, например: +998901234567",
        "need_age": "Пожалуйста, введите возраст цифрами, например: 35",
    },
    "uz": {
        "welcome": "Assalomu alaykum! 👋\nBu — Uzbio Center'ning rasmiy ariza topshirish boti.",
        "ask_phone": "Iltimos, telefon raqamingizni matn ko'rinishida yozing (masalan: +998901234567).\nRaqamingiz faqat siz bilan bog'lanish uchun ishlatiladi.",
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
        "need_contact": "Iltimos, telefon raqamingizni matn ko'rinishida kiriting, masalan: +998901234567",
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

        # отправляем подробное описание продукта отдельным сообщением под карточкой
        desc = data.get("desc", {}).get(lang)
        if desc:
            await message.answer(desc)

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
    await callback.message.answer(TEXTS[lang]["ask_phone"], reply_markup=ReplyKeyboardRemove())
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


@router.message(Form.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if PHONE_RE.match(text):
        await _accept_phone(message, state, text)
        return

    data = await state.get_data()
    lang = data.get("lang", "ru")
    await message.answer(TEXTS[lang]["need_contact"])


@router.message(Form.phone)
async def process_phone_invalid(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await message.answer(TEXTS[lang]["need_contact"])


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
