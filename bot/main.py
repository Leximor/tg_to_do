import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Row, Select, Column
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput
import requests
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs
from datetime import datetime

API_URL = os.getenv("API_URL", "http://backend:8000/api/")
BOT_TOKEN = os.getenv("BOT_TOKEN", "test")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

from aiogram.fsm.state import State, StatesGroup

class MainSG(StatesGroup):
    main = State()
    add_title = State()
    add_desc = State()
    add_due = State()
    add_category = State()

def get_or_create_profile(telegram_id, telegram_username, first_name, last_name):
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramBot/1.0'
        }
        resp = requests.post(f"{API_URL}profiles/", json={
            "telegram_id": telegram_id,
            "telegram_username": telegram_username,
            "first_name": first_name,
            "last_name": last_name,
        }, headers=headers, timeout=10)
        if resp.status_code in (200, 201):
            return resp.json()["id"]
        else:
            print(f"Failed to create profile: status {resp.status_code}")
    except Exception as e:
        print(f"Error creating profile: {e}")
    return None

def get_tasks(telegram_id):
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramBot/1.0'
        }
        resp = requests.get(f"{API_URL}tasks/?telegram_id={telegram_id}", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and 'results' in data:
                return data['results']
            elif isinstance(data, list):
                return data
            else:
                print(f"Unexpected API response format: {type(data)}")
                return []
        else:
            print(f"Failed to get tasks: status {resp.status_code}")
    except Exception as e:
        print(f"Error getting tasks: {e}")
    return []

def check_api_health():
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramBot/1.0'
        }
        resp = requests.get(f"{API_URL}categories/", headers=headers, timeout=5)
        print(f"API health check: status={resp.status_code}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"API health check: received {len(data)} categories")
                return True
            except:
                print("API health check: invalid JSON response")
                return False
        else:
            print(f"API health check: status {resp.status_code}")
            return False
    except Exception as e:
        print(f"API health check failed: {e}")
        return False

async def on_start(m: Message, dialog_manager: DialogManager):
    if not check_api_health():
        await m.answer("⚠️ Внимание: API недоступен. Некоторые функции могут не работать.")
    await dialog_manager.start(MainSG.main, mode=StartMode.RESET_STACK)

async def show_tasks(dialog_manager: DialogManager, **kwargs):
    telegram_id = dialog_manager.event.from_user.id
    tasks = get_tasks(telegram_id)
    if not tasks:
        return {"tasks": "Нет задач"}
    lines = []
    for t in tasks:
        if not isinstance(t, dict):
            print(f"Task is not a dict: {type(t)}, value: {t}")
            continue
        created_at = t.get('created_at', '')
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                created_str = created_at[:16]
        else:
            created_str = 'Дата не указана'
        due_date = t.get('due_date', '')
        if due_date:
            try:
                dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                due_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                due_str = due_date[:16]
        else:
            due_str = 'Дедлайн не указан'
        cats = t.get("categories", [])
        if cats:
            if isinstance(cats[0], dict):
                cats_str = ", ".join(c.get("name", str(c)) for c in cats if c.get("name"))
            else:
                cats_str = ", ".join(str(c) for c in cats)
        else:
            cats_str = "Не указана"
        desc = t.get("description", "")
        if not desc:
            desc = "Описание отсутствует"
        lines.append(f"Создана: {created_str}\n{t['title']}\nОписание: {desc}\nКатегории: {cats_str}\nДедлайн: {due_str}")
    return {"tasks": "\n\n".join(lines)}

async def on_title_message(message: Message, widget, manager: DialogManager):
    manager.dialog_data["title"] = message.text
    await manager.switch_to(MainSG.add_desc)

async def on_add_clicked(callback, button, manager: DialogManager):
    await manager.switch_to(MainSG.add_title)

async def on_desc_message(message: Message, widget, manager: DialogManager):
    manager.dialog_data["description"] = message.text
    await manager.switch_to(MainSG.add_category)

async def on_category_chosen(callback: types.CallbackQuery, widget, manager: DialogManager, item_id):
    manager.dialog_data["category_id"] = item_id
    await manager.switch_to(MainSG.add_due)

async def on_due_message(message: Message, widget, manager: DialogManager):
    manager.dialog_data["due_date"] = message.text
    telegram_id = message.from_user.id
    telegram_username = message.from_user.username
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    profile_id = get_or_create_profile(telegram_id, telegram_username, first_name, last_name)
    if not profile_id:
        await message.answer("Ошибка: не удалось создать профиль пользователя.")
        await manager.switch_to(MainSG.main)
        return

    category_id = manager.dialog_data.get("category_id")
    categories_list = [category_id] if category_id else []

    due_date = manager.dialog_data.get("due_date")
    data = {
        "title": manager.dialog_data["title"],
        "description": manager.dialog_data["description"],
        "user": profile_id,
        "categories": categories_list,
        "due_date": due_date,
    }

    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramBot/1.0'
        }
        resp = requests.post(f"{API_URL}tasks/", json=data, headers=headers, timeout=10)
        if resp.status_code in (200, 201):
            await message.answer("Задача добавлена!")
        else:
            await message.answer(f"Ошибка при добавлении задачи: {resp.text}")
    except Exception as e:
        await message.answer(f"Ошибка при добавлении задачи: {e}")

    await manager.switch_to(MainSG.main)

async def get_categories(dialog_manager: DialogManager, **kwargs):
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'TelegramBot/1.0'
        }
        url = f"{API_URL}categories/"
        print(f"Requesting categories from: {url}")

        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Response status: {resp.status_code}")
        print(f"Response headers: {dict(resp.headers)}")
        print(f"Response content (first 200 chars): {resp.text[:200]}")

        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"Parsed categories: {data}")

                if isinstance(data, dict) and 'results' in data:
                    cats = data['results']
                elif isinstance(data, list):
                    cats = data
                else:
                    print(f"Unexpected categories response format: {type(data)}")
                    cats = []

                if isinstance(cats, list) and len(cats) > 0:
                    result = [(c["id"], c["name"]) for c in cats if "id" in c and "name" in c]
                    print(f"Formatted categories: {result}")
                    return {"categories": result}
                else:
                    print("Categories list is empty")
            except Exception as json_error:
                print(f"JSON parsing error: {json_error}")
                print(f"Response text: {resp.text}")
        else:
            print(f"API returned status {resp.status_code}")

    except Exception as e:
        print(f"Request error: {e}")

    print("Using fallback categories")
    return {"categories": [("test_id", "Test Category")]}

add_title_window = Window(
    Const("Введите заголовок задачи:"),
    MessageInput(on_title_message),
    state=MainSG.add_title,
)

add_desc_window = Window(
    Const("Введите описание задачи:"),
    MessageInput(on_desc_message),
    state=MainSG.add_desc,
)

add_category_window = Window(
    Const("Выберите категорию задачи:"),
    Column(
        Select(
            Format("{item[1]}"),
            id="category_select",
            item_id_getter=lambda x: x[0],
            items="categories",
            on_click=on_category_chosen,
        ),
    ),
    state=MainSG.add_category,
    getter=get_categories,
)

add_due_window = Window(
    Const("Введите дату дедлайна задачи (YYYY-MM-DD HH:MM):"),
    MessageInput(on_due_message),
    state=MainSG.add_due,
)

main_window = Window(
    Const("Ваши задачи:"),
    Format("{tasks}"),
    Row(
        Button(Const("Добавить задачу"), id="add", on_click=on_add_clicked),
    ),
    state=MainSG.main,
    getter=show_tasks,
)

dialog = Dialog(main_window, add_title_window, add_desc_window, add_category_window, add_due_window)

def register_handlers(dp: Dispatcher):
    @dp.message(Command("start"))
    async def cmd_start(m: Message, dialog_manager: DialogManager):
        await on_start(m, dialog_manager)

    @dp.callback_query(lambda c: c.data and c.data.startswith('disable_notifications:'))
    async def handle_disable_notifications(callback_query: types.CallbackQuery):
        await handle_callback_query(callback_query)

async def handle_callback_query(callback_query: types.CallbackQuery):
    try:
        if callback_query.data.startswith('disable_notifications:'):
            task_id = callback_query.data.split(':')[1]

            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'TelegramBot/1.0'
            }
            data = {'notifications_disabled': True}

            resp = requests.patch(f"{API_URL}tasks/{task_id}/", json=data, headers=headers, timeout=10)

            if resp.status_code == 200:
                await callback_query.answer("🔕 Уведомления для этой задачи отключены!")
                await callback_query.message.edit_reply_markup(reply_markup=None)
            else:
                await callback_query.answer("❌ Ошибка при отключении уведомлений")

    except Exception as e:
        print(f"Error handling callback query: {e}")
        await callback_query.answer("❌ Произошла ошибка")

async def main():
    register_handlers(dp)
    setup_dialogs(dp)
    dp.include_routers(dialog)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
