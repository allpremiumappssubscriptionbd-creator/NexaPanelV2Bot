import os
import time
import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Configuration (আপনার ইনফরমেশন বসানো আছে)
BOT_TOKEN = "8839358484:AAH-i3a_cklN0abMhlrrtcYomokTCrhJpIU"
ADMIN_IDS = [8731246566]

# Zenex Core API Configuration (V4.0)
ZENEX_API_URL = "https://api.zenexnetwork.com"
ZENEX_API_KEY = "ZNX_QWF4SO4CHD1QEESAJC5CPP6X"

PANEL_CONFIG = {
    "panel_name": "✨ Nexal Panel V2",
    "maintenance": False,
    "numbers_per_click": 1
}

DYNAMIC_SERVICES = {
    "Dashboard": {"ranges": ["4473845XXX", "4473846XXX"]},
    "Facebook": {"ranges": ["4473847XXX"]},
    "Instagram": {"ranges": ["4473899XXX"]}
}

CUSTOM_BUTTONS = {
    "get_number": {"text": "⚡ Get Service Number", "callback": "get_number_services"},
    "search_range": {"text": "🔍 Search Range Matrix", "callback": "search_range_prompt"},
    "live_console": {"text": "📊 Live Traffic Console", "callback": "live_console"},
    "check_balance": {"text": "💳 Account Balance", "callback": "check_balance"},
    "support": {"text": "🛠️ Help & Support", "callback": "help"}
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

class AdminStates(StatesGroup):
    waiting_for_panel_name = State()
    waiting_for_limit = State()
    waiting_for_service_name = State()
    waiting_for_range_input = State()

class UserStates(StatesGroup):
    waiting_for_search_range = State()

TEMP_DATA = {}

def main_menu(user_id):
    keyboard = []
    row = []
    for key, btn in CUSTOM_BUTTONS.items():
        row.append(InlineKeyboardButton(text=btn["text"], callback_data=btn["callback"]))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton(text="🔐 Admin Control Hub", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(Command("start"))
async def cmd_start(message: Message):
    if PANEL_CONFIG["maintenance"] and message.from_user.id not in ADMIN_IDS:
        await message.answer("⚠️ System is currently under maintenance. Please check back later.")
        return
    
    welcome_text = (
        f"👋 Welcome, **{message.from_user.first_name}**!\n\n"
        f"🌐 Connected to **{PANEL_CONFIG['panel_name']}**\n"
        f"💎 _Next-Gen OTP & Automated Number Matrix_\n\n"
        f"📌 Please choose an option from below:"
    )
    try:
        await message.answer(welcome_text, reply_markup=main_menu(message.from_user.id), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error in start command: {e}")

@router.callback_query(F.data == "back_home")
async def back_home(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            f"🌐 **{PANEL_CONFIG['panel_name']}**\n"
            f"💎 _Main Control Dashboard_\n\n"
            f"📌 Select an action below:",
            reply_markup=main_menu(callback.from_user.id),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.answer()

@router.callback_query(F.data == "get_number_services")
async def get_number_services(callback: CallbackQuery):
    keyboard = []
    for s_name, s_data in DYNAMIC_SERVICES.items():
        ranges_count = len(s_data["ranges"])
        keyboard.append([InlineKeyboardButton(text=f"📂 {s_name} ➔ [{ranges_count} Active Ranges]", callback_data=f"user_select_service_{s_name}")])
    
    keyboard.append([InlineKeyboardButton(text="🔍 Search Custom Range", callback_data="search_range_prompt")])
    keyboard.append([InlineKeyboardButton(text="🔙 Back to Home", callback_data="back_home")])
    
    try:
        await callback.message.edit_text(
            "⚡ **Service Provisioning Matrix**\n\n🎯 Select your desired service below to fetch numbers instantly:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.answer()

@router.callback_query(F.data.startswith("user_select_service_"))
async def user_select_service(callback: CallbackQuery):
    service_name = callback.data.replace("user_select_service_", "")
    s_data = DYNAMIC_SERVICES.get(service_name, {"ranges": []})
    ranges = s_data["ranges"]
    
    if not ranges:
        await callback.answer("⚠️ No active ranges found for this service.", show_alert=True)
        return
    
    target_range = ranges[0]
    try:
        await callback.message.edit_text(
            f"⏳ **Provisioning Number...**\n\n🔹 Service: `{service_name}`\n🔸 Range: `{target_range}`",
            parse_mode="Markdown"
        )
    except Exception:
        pass
    asyncio.create_task(execute_get_number(callback.message.chat.id, callback.message.message_id, target_range))

@router.callback_query(F.data == "search_range_prompt")
async def search_range_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_search_range)
    try:
        await callback.message.edit_text(
            "🔍 **Custom Range Search**\n\n💬 Send the range prefix (e.g., `447384XXX`) to fetch numbers:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Cancel", callback_data="get_number_services")]]),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.answer()

@router.message(UserStates.waiting_for_search_range)
async def process_searched_range(message: Message, state: FSMContext):
    search_query = message.text.strip()
    await state.clear()
    
    matched_service = "Universal Matrix"
    for s_name, s_data in DYNAMIC_SERVICES.items():
        for r in s_data["ranges"]:
            if search_query in r or r in search_query:
                matched_service = s_name
                break
    
    msg = await message.answer(
        f"🔍 **Range Matched!**\n\n📌 Query: `{search_query}`\n🏷️ Service: `{matched_service}`\n\n⏳ Provisioning number..."
    )
    asyncio.create_task(execute_get_number(message.chat.id, msg.message_id, search_query))

async def execute_get_number(chat_id: int, message_id: int, target_range: str):
    headers = {"mapikey": ZENEX_API_KEY}
    payload = {"range": target_range, "is_national": False, "remove_plus": False}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{ZENEX_API_URL}/v1/getnum", json=payload, headers=headers) as response:
                if response.status == 200:
                    res_data = await response.json()
                    number_data = res_data.get("data", {})
                    number = number_data.get("number", "+447384561029")
                    country = number_data.get("country", "United Kingdom")
                    operator = number_data.get("operator", "Vodafone")
                    
                    initial_text = (
                        f"✨ **Number Generated Successfully!**\n\n"
                        f"📱 Number: `{number}`\n"
                        f"🎯 Range: `{target_range}`\n"
                        f"🌍 Country: `{country}`\n"
                        f"📡 Operator: `{operator}`\n\n"
                        f"⏳ **Listening for incoming OTP (Auto-checking every 5s)...**"
                    )
                    
                    try:
                        await bot.edit_message_text(
                            chat_id=chat_id, message_id=message_id, text=initial_text,
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_home")]]),
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
                    asyncio.create_task(poll_otp_for_user(chat_id, number, message_id))
                else:
                    try:
                        await bot.edit_message_text(
                            chat_id=chat_id, message_id=message_id,
                            text="❌ Failed to fetch number from API endpoint.",
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="get_number_services")]])
                        )
                    except Exception:
                        pass
    except Exception as e:
        try:
            await bot.edit_message_text(
                chat_id=chat_id, message_id=message_id,
                text=f"❌ Connection Error: `{str(e)}`",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="get_number_services")]])
            )
        except Exception:
            pass

async def poll_otp_for_user(chat_id: int, target_number: str, message_id: int):
    headers = {"mapikey": ZENEX_API_KEY}
    for _ in range(60):
        await asyncio.sleep(5)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{ZENEX_API_URL}/v1/numsuccess/info", headers=headers) as response:
                    if response.status == 200:
                        res_data = await response.json()
                        otps = res_data.get("data", {}).get("otps", [])
                        for item in otps:
                            if item.get("number") == target_number or target_number in item.get("number", ""):
                                success_text = (
                                    f"🎉 **OTP Received Successfully!**\n\n"
                                    f"📱 Number: `{target_number}`\n"
                                    f"💬 OTP Code: `{item.get('otp')}`\n"
                                    f"🕒 Timestamp: _{item.get('created_at')}_\n\n"
                                    f"✅ Delivery complete."
                                )
                                try:
                                    await bot.edit_message_text(
                                        chat_id=chat_id, message_id=message_id, text=success_text,
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_home")]]),
                                        parse_mode="Markdown"
                                    )
                                except Exception:
                                    pass
                                return
        except Exception:
            pass
    try:
        await bot.edit_message_text(
            chat_id=chat_id, message_id=message_id,
            text=f"⏰ **Timeout:** No OTP received for `{target_number}` within time limit.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_home")]])
        )
    except Exception:
        pass

@router.callback_query(F.data == "live_console")
async def live_console(callback: CallbackQuery):
    headers = {"mapikey": ZENEX_API_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ZENEX_API_URL}/v1/active-ranges", headers=headers) as r1, \
                       session.get(f"{ZENEX_API_URL}/v1/numsuccess/info", headers=headers) as r2:
                
                traffic_text = "📊 **Live Traffic & Active Routes Matrix**\n\n"
                if r1.status == 200:
                    r1_data = await r1.json()
                    ranges = r1_data.get("data", {}).get("active_ranges", [])
                    traffic_text += "🌐 **Active Routes:**\n"
                    for route in ranges[:5]:
                        traffic_text += f"• `{route.get('service')}` ({route.get('range')}) ➔ **{route.get('hits')} Hits**\n"
                
                traffic_text += "\n💬 **Recent Live SMS Stream:**\n"
                if r2.status == 200:
                    r2_data = await r2.json()
                    otps = r2_data.get("data", {}).get("otps", [])
                    for item in otps[:3]:
                        traffic_text += f"• `{item.get('number')}` ➔ `{item.get('otp')}`\n"
                
                await callback.message.edit_text(
                    traffic_text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🔄 Refresh Console", callback_data="live_console")],
                        [InlineKeyboardButton(text="🔙 Back to Home", callback_data="back_home")]
                    ]),
                    parse_mode="Markdown"
                )
    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)

@router.callback_query(F.data == "check_balance")
async def check_balance(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "💳 **Account Status**\n\n🟢 API Connection: `Online & Active`\n🔗 Core Provider: `Zenex API V4.0`",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Home", callback_data="back_home")]]),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.answer()

@router.callback_query(F.data == "help")
async def help_menu(callback: CallbackQuery):
    try:
        await callback.message.edit_text(
            "🛠️ **Help & Support Desk**\n\n✨ Use inline buttons to provision numbers and view live SMS streams automatically.\n🔐 Admins can manage services and range lists from the Control Hub.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Home", callback_data="back_home")]]),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.answer()

@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("⛔ Access Denied!", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(text="➕ Add New Service", callback_data="admin_add_service")],
        [InlineKeyboardButton(text="✏️ Manage Services & Ranges", callback_data="admin_manage_services")],
        [InlineKeyboardButton(text="🔢 Set Number Limit", callback_data="set_limit"), InlineKeyboardButton(text="🏷️ Change Panel Name", callback_data="change_name")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="back_home")]
    ]
    try:
        await callback.message.edit_text(
            f"🔐 **Admin Control Hub**\n\n📂 Total Services: `{len(DYNAMIC_SERVICES)}`\n🌐 Current Panel: `{PANEL_CONFIG['panel_name']}`\n\n📌 Choose an administrative option:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.answer()

@router.callback_query(F.data == "admin_add_service")
async def admin_add_service(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS: return
    await state.set_state(AdminStates.waiting_for_service_name)
    try:
        await callback.message.edit_text(
            "➕ **Add New Service**\n\n💬 Send the name of the new service (e.g., `Dashboard`):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Cancel", callback_data="admin_panel")]]),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.answer()

@router.message(AdminStates.waiting_for_service_name)
async def save_new_service_name(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    service_name = message.text.strip()
    DYNAMIC_SERVICES[service_name] = {"ranges": []}
    await state.clear()
    await message.answer(
        f"✅ Service **{service_name}** added successfully!\n\n📌 Go to 'Manage Services' to add ranges.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔐 Admin Hub", callback_data="admin_panel")]])
    )

@router.callback_query(F.data == "admin_manage_services")
async def admin_manage_services(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return
    keyboard = []
    for s_name in DYNAMIC_SERVICES.keys():
        keyboard.append([InlineKeyboardButton(text=f"📂 Edit Service: {s_name}", callback_data=f"admin_edit_service_{s_name}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Admin Hub", callback_data="admin_panel")])
    
    try:
        await callback.message.edit_text(
            "✏️ **Manage Services & Ranges**\n\n🎯 Select a service below to configure its ranges or delete it:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.answer()

@router.callback_query(F.data.startswith("admin_edit_service_"))
async def admin_edit_service(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return
    s_name = callback.data.replace("admin_edit_service_", "")
    s_data = DYNAMIC_SERVICES.get(s_name, {"ranges": []})
    ranges = s_data["ranges"]
    
    text = f"📂 Service: **{s_name}**\n\n🎯 **Configured Ranges:**\n"
    if ranges:
        for i, r in enumerate(ranges):
            text += f"• Range V{i+1}: `{r}`\n"
    else:
        text += "• _No ranges added yet._\n"
    
    keyboard = [
        [InlineKeyboardButton(text="➕ Add Range", callback_data=f"admin_add_range_{s_name}")],
        [InlineKeyboardButton(text="🗑️ Delete Service", callback_data=f"admin_del_service_{s_name}")],
        [InlineKeyboardButton(text="🔙 Back to Services", callback_data="admin_manage_services")]
    ]
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")
    except Exception:
        await callback.answer()

@router.callback_query(F.data.startswith("admin_add_range_"))
async def admin_add_range_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS: return
    s_name = callback.data.replace("admin_add_range_", "")
    TEMP_DATA[callback.from_user.id] = s_name
    await state.set_state(AdminStates.waiting_for_range_input)
    try:
        await callback.message.edit_text(
            f"➕ **Add Range for {s_name}**\n\n💬 Send the range prefix (e.g., `4473845XXX`):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Cancel", callback_data=f"admin_edit_service_{s_name}")]]),
            parse_mode="Markdown"
        )
    except Exception:
        await callback.answer()

@router.message(AdminStates.waiting_for_range_input)
async def save_service_range(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    s_name = TEMP_DATA.get(message.from_user.id)
    range_val = message.text.strip()
    
    if s_name in DYNAMIC_SERVICES:
        DYNAMIC_SERVICES[s_name]["ranges"].append(range_val)
            
    await state.clear()
    await message.answer(
        f"✅ Range added successfully to **{s_name}**!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔐 Admin Hub", callback_data="admin_panel")]])
    )

@router.callback_query(F.data.startswith("admin_del_service_"))
async def admin_del_service(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS: return
    s_name = callback.data.replace("admin_del_service_", "")
    if s_name in DYNAMIC_SERVICES:
        del DYNAMIC_SERVICES[s_name]
    try:
        await callback.message.edit_text(
            f"🗑️ Service **{s_name}** deleted successfully!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back to Services", callback_data="admin_manage_services")]])
        )
    except Exception:
        await callback.answer()

@router.callback_query(F.data == "set_limit")
async def set_limit_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS: return
    await state.set_state(AdminStates.waiting_for_limit)
    try:
        await callback.message.answer("🔢 Send numbers per click limit value:")
    except Exception:
        await callback.answer()

@router.message(AdminStates.waiting_for_limit)
async def save_limit(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    try:
        limit = int(message.text.strip())
        PANEL_CONFIG["numbers_per_click"] = limit
        await state.clear()
        await message.answer(
            f"✅ Limit updated to: **{limit}**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔐 Admin Hub", callback_data="admin_panel")]])
        )
    except ValueError:
        await message.answer("⚠️ Please enter a valid integer number.")

@router.callback_query(F.data == "change_name")
async def change_name_prompt(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS: return
    await state.set_state(AdminStates.waiting_for_panel_name)
    try:
        await callback.message.answer("🏷️ Send new display name for the panel:")
    except Exception:
        await callback.answer()

@router.message(AdminStates.waiting_for_panel_name)
async def save_panel_name(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    PANEL_CONFIG["panel_name"] = message.text.strip()
    await state.clear()
    await message.answer(
        "✅ Panel name updated successfully!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔐 Admin Hub", callback_data="admin_panel")]])
    )

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # অটো-রিকানেক্টিং পোলিং লুপ (কয়েব বা যেকোনো সার্ভারে আজীবন সচল রাখার জন্য)
    while True:
        try:
            logging.info("🤖 Bot is starting polling & running 24/7...")
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Polling crashed: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
