"""Telegram-бот портфолио Марины Сухаревой.

Запуск:
    export BOT_TOKEN=123456:ABC
    export ADMIN_ID=11111111
    python bot.py

Заявки пишутся в applications.db и приходят тебе в Телеграм.
"""

import asyncio
import logging
import os
import sqlite3
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import content as C

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("portfolio")

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
DB_PATH = Path(__file__).parent / "applications.db"
MEDIA_DIR = Path(__file__).parent

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)


# --- Хранилище --------------------------------------------------------------
def init_db() -> None:
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                name TEXT, contact TEXT, type TEXT, budget TEXT, comment TEXT,
                username TEXT, user_id INTEGER, status TEXT DEFAULT 'new')"""
        )


def save_application(data: dict) -> int:
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(
            """INSERT INTO applications (name, contact, type, budget, comment, username, user_id)
               VALUES (?,?,?,?,?,?,?)""",
            (
                data.get("name", ""),
                data.get("contact", ""),
                data.get("type", ""),
                data.get("budget", ""),
                data.get("comment", ""),
                data.get("username", ""),
                data.get("user_id", 0),
            ),
        )
        return cur.lastrowid


# --- Клавиатуры -------------------------------------------------------------
def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🖼 Портфолио", callback_data="portfolio")],
            [InlineKeyboardButton(text="💼 Услуги и цены", callback_data="services")],
            [InlineKeyboardButton(text="👋 Обо мне", callback_data="about")],
            [InlineKeyboardButton(text="✍️ Оставить заявку", callback_data="apply_start")],
            [InlineKeyboardButton(text="🔗 Контакты", callback_data="contacts")],
        ]
    )


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="← В меню", callback_data="menu")]]
    )


def cases_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{c['title']}", callback_data=f"case:{c['title']}")]
        for c in C.CASES
    ]
    rows.append([InlineKeyboardButton(text="← В меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def case_kb(index: int) -> InlineKeyboardMarkup:
    rows = []
    if index > 0:
        rows.append([InlineKeyboardButton(text="←", callback_data=f"case_nav:{index - 1}")])
    if index < len(C.CASES) - 1:
        rows.append([InlineKeyboardButton(text="→", callback_data=f"case_nav:{index + 1}")])
    rows.append(
        [
            InlineKeyboardButton(text="✍️ Хочу так же", callback_data="apply_start"),
            InlineKeyboardButton(text="← В меню", callback_data="menu"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def types_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=t, callback_data=f"type:{t}")] for t in C.TYPES]
    rows.append([InlineKeyboardButton(text="← В меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def budgets_kb() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=b, callback_data=f"budget:{b}")] for b in C.BUDGETS]
    rows.append([InlineKeyboardButton(text="← В меню", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cases_text() -> str:
    lines = ["🖼 <b>Портфолио</b>\n"]
    for i, c in enumerate(C.CASES, 1):
        lines.append(f"{i}. <b>{c['title']}</b> — {c['category']}, {c['year']}\n   {c['description']}\n")
    lines.append("Открой кейс кнопками ниже 👇")
    return "\n".join(lines)


def services_text() -> str:
    lines = ["💼 <b>Услуги и цены</b>\n"]
    for name, desc, price in C.SERVICES:
        lines.append(f"• <b>{name}</b> — {price}\n   {desc}\n")
    lines.append("Точная цена — после брифа. Оставь заявку ↓")
    return "\n".join(lines)


def contacts_text() -> str:
    lines = ["🔗 <b>Контакты</b>\n"]
    for k, v in C.CONTACTS.items():
        lines.append(f"{k.capitalize()}: {v}")
    lines.append("\nИли сразу оставь заявку в боте — отвечу быстрее.")
    return "\n".join(lines)


# --- FSM --------------------------------------------------------------------
class Apply(StatesGroup):
    name = State()
    contact = State()
    type = State()
    budget = State()
    comment = State()


# --- Хендлеры ---------------------------------------------------------------
@router.message(CommandStart())
@router.message(Command("menu"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        f"<b>{C.NAME}</b>\n{C.ROLE}\n\n{C.INTRO}",
        reply_markup=main_menu(),
    )


@router.message(Command("portfolio"))
async def cmd_portfolio(message: Message) -> None:
    await message.answer(cases_text(), reply_markup=cases_kb())


@router.message(Command("services"))
async def cmd_services(message: Message) -> None:
    await message.answer(services_text(), reply_markup=back_menu())


@router.message(Command("contacts"))
async def cmd_contacts(message: Message) -> None:
    await message.answer(contacts_text(), reply_markup=back_menu())


@router.message(Command("apply"))
async def cmd_apply(message: Message, state: FSMContext) -> None:
    await state.set_state(Apply.name)
    await message.answer("✍️ <b>Заявка</b>\n\n1/4 — как тебя зовут?", reply_markup=back_menu())


@router.message(Command("apps"))
async def cmd_apps(message: Message) -> None:
    """Список заявок. Доступно только ADMIN_ID."""
    if message.from_user.id != ADMIN_ID:
        return
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute(
            """SELECT id, created_at, name, contact, type, budget, comment, username
               FROM applications ORDER BY id DESC LIMIT 20"""
        ).fetchall()
    if not rows:
        await message.answer("Заявок пока нет 🦆")
        return
    chunks = ["📋 <b>Последние заявки</b>\n"]
    for r in rows:
        chunks.append(
            f"#{r[0]} <i>{r[1]}</i>\n"
            f"{r[2]} · {r[3]}\n"
            f"{r[4]} · {r[5]}\n"
            f"{r[6]}\n"
            f"@{r[7]}\n" + "─" * 20
        )
    await message.answer("\n".join(chunks))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Команды:\n/start — меню\n/portfolio — работы\n/services — услуги и цены\n"
        "/apply — заявка\n/contacts — контакты",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data == "menu")
async def cb_menu(call: CallbackQuery) -> None:
    await call.message.edit_text(
        f"<b>{C.NAME}</b>\n{C.ROLE}\n\n{C.INTRO}", reply_markup=main_menu()
    )
    await call.answer()


@router.callback_query(F.data == "portfolio")
async def cb_portfolio(call: CallbackQuery) -> None:
    await call.message.edit_text(cases_text(), reply_markup=cases_kb())
    await call.answer()


@router.callback_query(F.data.startswith("case:"))
async def cb_case(call: CallbackQuery) -> None:
    title = call.data.split(":", 1)[1]
    idx = next((i for i, c in enumerate(C.CASES) if c["title"] == title), 0)
    await send_case(call.message, idx)


@router.callback_query(F.data.startswith("case_nav:"))
async def cb_case_nav(call: CallbackQuery) -> None:
    idx = int(call.data.split(":", 1)[1])
    await send_case(call.message, idx)


async def send_case(message: Message, idx: int) -> None:
    c = C.CASES[idx]
    text = (
        f"<b>{c['title']}</b>\n<i>{c['category']} · {c['year']}</i>\n\n"
        f"{c['description']}\n\n"
        f"✨ {c['result']}\n\n"
        f"Теги: {' · '.join(c.get('tags', []))}"
    )
    kb = case_kb(idx)
    images = c.get("images") or []
    if images:
        path = MEDIA_DIR / images[0]
        if path.exists():
            await message.answer_photo(FSInputFile(path), caption=text, reply_markup=kb)
            return
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "services")
async def cb_services(call: CallbackQuery) -> None:
    await call.message.edit_text(services_text(), reply_markup=back_menu())
    await call.answer()


@router.callback_query(F.data == "about")
async def cb_about(call: CallbackQuery) -> None:
    await call.message.edit_text(
        f"<b>{C.NAME}</b>\n{C.ROLE}\n\n{C.ABOUT}\n\n{C.TAGLINE}",
        reply_markup=back_menu(),
    )
    await call.answer()


@router.callback_query(F.data == "contacts")
async def cb_contacts(call: CallbackQuery) -> None:
    await call.message.edit_text(contacts_text(), reply_markup=back_menu())
    await call.answer()


# --- Приём заявки -----------------------------------------------------------
@router.callback_query(F.data == "apply_start")
async def cb_apply_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Apply.name)
    await call.message.edit_text(
        "✍️ <b>Заявка</b>\n\n1/4 — как тебя зовут?", reply_markup=back_menu()
    )
    await call.answer()


@router.message(Apply.name)
async def apply_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(Apply.contact)
    await message.answer(
        "2/4 — куда писать? Telegram, почта или @телефон — как удобнее.",
        reply_markup=back_menu(),
    )


@router.message(Apply.contact)
async def apply_contact(message: Message, state: FSMContext) -> None:
    await state.update_data(contact=message.text.strip())
    await state.set_state(Apply.type)
    await message.answer("3/4 — что нужно сделать? Выбери тип проекта:", reply_markup=types_kb())


@router.callback_query(F.data.startswith("type:"))
async def cb_type(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(type=call.data.split(":", 1)[1])
    await state.set_state(Apply.budget)
    await call.message.edit_text("4/4 — примерный бюджет?", reply_markup=budgets_kb())
    await call.answer()


@router.callback_query(F.data.startswith("budget:"))
async def cb_budget(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(budget=call.data.split(":", 1)[1])
    await state.set_state(Apply.comment)
    await call.message.edit_text(
        "Почти готово — расскажи пару слов о задаче (что делаем, сроки, ссылки).",
        reply_markup=back_menu(),
    )
    await call.answer()


@router.message(Apply.comment)
async def apply_comment(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    data["comment"] = message.text.strip()
    data["username"] = message.from_user.username or ""
    data["user_id"] = message.from_user.id
    app_id = save_application(data)
    await state.clear()

    await message.answer(
        "✅ <b>Заявка принята!</b>\n"
        f"Номер: #{app_id}\n\nОтвечу в течение рабочего дня. "
        "Если срочно — напиши мне напрямую, ссылка ниже.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✉️ Написать в Telegram",
                        url=f"https://t.me/{C.CONTACTS['telegram'].lstrip('@')}",
                    )
                ],
                [InlineKeyboardButton(text="← В меню", callback_data="menu")],
            ]
        ),
    )

    if ADMIN_ID:
        notify = (
            f"🔔 <b>Новая заявка #{app_id}</b>\n\n"
            f"Имя: {data['name']}\n"
            f"Контакт: {data['contact']}\n"
            f"Тип: {data['type']}\n"
            f"Бюджет: {data['budget']}\n\n"
            f"Задача: {data['comment']}\n\n"
            f"TG: @{data['username']} (<code>{data['user_id']}</code>)"
        )
        try:
            await bot.send_message(ADMIN_ID, notify)
        except Exception:
            log.exception("Не удалось отправить заявку админу")


@router.callback_query(F.data == "cancel")
async def cb_cancel(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text("Заявка отменена. Начать заново?", reply_markup=main_menu())
    await call.answer()


async def main() -> None:
    init_db()
    await bot.set_my_commands(
        [
            BotCommand(command="portfolio", description="Работы"),
            BotCommand(command="services", description="Услуги и цены"),
            BotCommand(command="apply", description="Оставить заявку"),
            BotCommand(command="contacts", description="Контакты"),
            BotCommand(command="help", description="Помощь"),
        ]
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
