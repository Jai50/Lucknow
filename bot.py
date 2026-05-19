import os
import re
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import asyncio

flask_app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 1919682117))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")  # Render set karega

if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN environment variable not set!")

# Storage (same as original)
user_data = {}
bookings = {}
user_active_booking = {}

# Global bot application instance
application = None

# ============================================
# YAHAN APKE SAARE HANDLER FUNCTIONS PASTE KAREIN
# (show_main_menu, forward_to_admin, start, book_command, info_command, etc.)
# ============================================
# Main neeche code diya hai – aap sirf copy-paste karein
# ============================================

# ---------- SHOW MAIN MENU ----------
async def show_main_menu(message, user_id=None):
    has_booking = user_id and user_id in user_active_booking
    if has_booking:
        booking_id = user_active_booking[user_id].get("booking_id", "Unknown")
        keyboard = [
            [InlineKeyboardButton("📅 Book Now", callback_data="menu_book")],
            [InlineKeyboardButton("ℹ️ Service Info", callback_data="menu_info")],
            [InlineKeyboardButton("📞 Contact Us", callback_data="menu_contact")],
            [InlineKeyboardButton("❌ Cancel Booking", callback_data="menu_cancel_booking")]
        ]
        menu_text = f"""
🔥 *LUCKNOW GLEEDEN SERVICE* 🔥
👩 *Only for Female*

📋 *Active Booking ID:* `{booking_id}`

📌 Type "book" or "hi" for new booking
"""
    else:
        keyboard = [
            [InlineKeyboardButton("📅 Book Now", callback_data="menu_book")],
            [InlineKeyboardButton("ℹ️ Service Info", callback_data="menu_info")],
            [InlineKeyboardButton("📞 Contact Us", callback_data="menu_contact")],
            [InlineKeyboardButton("❌ Cancel Booking", callback_data="menu_cancel_booking")]
        ]
        menu_text = """
🔥 *LUCKNOW GLEEDEN SERVICE* 🔥
👩 *Only for Female*

✨ Type "book" or "hi" to start booking ✨
"""
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

# ---------- FORWARD TO ADMIN ----------
async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text):
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name
    username = f"@{user.username}" if user.username else "No username"
    admin_msg = f"""
📩 *NEW MESSAGE FROM USER*

👤 Name: {user_name}
🆔 User ID: `{user_id}`
📝 Username: {username}

━━━━━━━━━━━━━━━━
💬 *Message:* 
{message_text}
━━━━━━━━━━━━━━━━

💡 *To reply:* Reply to this message with your response
"""
    try:
        await context.bot.send_message(ADMIN_ID, admin_msg, parse_mode='Markdown')
        print(f"✅ Forwarded to admin from {user_name}")
    except Exception as e:
        print(f"❌ Forward failed: {e}")

# ---------- COMMAND HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await show_main_menu(update.message, user_id)
    user = update.effective_user
    await context.bot.send_message(ADMIN_ID, f"🟢 *NEW USER*\n👤 {user.first_name}\n🆔 `{user.id}`", parse_mode='Markdown')

async def book_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    user_data[user_id] = {"step": "service"}
    keyboard = [
        [InlineKeyboardButton("💆‍♂️ Massage", callback_data="book_massage")],
        [InlineKeyboardButton("🤝 Casual Meet Up", callback_data="book_casual")],
        [InlineKeyboardButton("☀️ Day Service", callback_data="book_day")],
        [InlineKeyboardButton("🌙 Night Package", callback_data="book_night")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.edit_text("📅 *NEW BOOKING*\n\nSelect service:", reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text("📅 *NEW BOOKING*\n\nSelect service:", reply_markup=reply_markup, parse_mode='Markdown')

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ *SERVICE INFO*\n\n💆‍♂️ Massage - Day/Night\n🤝 Casual Meet Up - Day/Night\n☀️ Day Service - 1,2,4 Hours\n🌙 Night Package - 1,2,4 Hours, Full Night\n\n✅ 24x7 | Only for Female", parse_mode='Markdown')

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot.send_message(ADMIN_ID, f"📞 CONTACT REQUEST\nFrom: {user.first_name} (@{user.username or 'N/A'})\nID: {user.id}")
    await update.message.reply_text("✅ Request sent to admin! We'll contact you shortly.", parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 *Commands*\n/book - New booking\n/info - Service info\n/contact - Contact admin\n/cancel - Cancel booking\n/send [ID] [msg] - Admin only", parse_mode='Markdown')

async def send_to_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Usage: /send [user_id] [message]")
        return
    try:
        target_id = int(args[0])
        msg = " ".join(args[1:])
        await context.bot.send_message(chat_id=target_id, text=f"👑 *Admin:* {msg}", parse_mode='Markdown')
        await update.message.reply_text(f"✅ Sent to `{target_id}`", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def admin_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not update.message.reply_to_message:
        return
    replied = update.message.reply_to_message
    reply_text = update.message.text
    target_id = None
    # Extract user ID from forwarded message
    match = re.search(r"🆔 User ID: `(\d+)`", replied.text or "")
    if not match:
        match = re.search(r"User ID: (\d+)", replied.text or "")
    if not match:
        match = re.search(r"ID: (\d+)", replied.text or "")
    if match:
        target_id = int(match.group(1))
    if target_id:
        try:
            await context.bot.send_message(target_id, f"👑 *Admin:* {reply_text}", parse_mode='Markdown')
            await update.message.reply_text(f"✅ Reply sent to `{target_id}`", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ Failed: {e}")
    else:
        await update.message.reply_text("❌ No user ID found. Use /send instead.")

async def cancel_booking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_active_booking:
        booking_id = user_active_booking[user_id].get("booking_id", "Unknown")
        keyboard = [
            [InlineKeyboardButton("✅ Yes, Cancel", callback_data=f"confirm_yes_{booking_id}")],
            [InlineKeyboardButton("❌ No, Keep", callback_data="confirm_no")]
        ]
        await update.message.reply_text(f"⚠️ Cancel `{booking_id}`?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ No active booking", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📅 Book Now", callback_data="menu_book")]]))

async def easy_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message
    text = message.text.lower().strip()
    if user_id != ADMIN_ID:
        await forward_to_admin(update, context, message.text)
    if user_id in user_data:
        if text in ["cancel", "रद्द", "exit"]:
            if user_id in user_data:
                del user_data[user_id]
            await cancel_booking_command(update, context)
            return
        await handle_booking_flow(update, context)
        return
    if text in ["book", "booking", "बुक", "hi", "hello", "hey", "hii"]:
        await book_command(update, context)
    elif text in ["info", "information", "जानकारी"]:
        await info_command(update, context)
    elif text in ["contact", "support", "संपर्क"]:
        await contact_command(update, context)
    elif text in ["cancel", "रद्द"]:
        await cancel_booking_command(update, context)
    elif text in ["start", "menu"]:
        await show_main_menu(message, user_id)
    else:
        await message.reply_text("📝 Type 'book' or 'hi' to start booking")

async def handle_booking_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message
    text = message.text.strip()
    if user_id not in user_data:
        return
    step = user_data[user_id].get("step")
    if step == "age":
        user_data[user_id]["age"] = text
        user_data[user_id]["step"] = "location"
        await message.reply_text(f"✅ Age: *{text}*\n\n📍 *Share your LOCATION (Area Name)*", parse_mode='Markdown')
    elif step == "location":
        user_data[user_id]["location"] = text
        user_data[user_id]["step"] = "contact_details"
        keyboard = [[InlineKeyboardButton("⏭️ Skip", callback_data="skip_contact")]]
        await message.reply_text(f"✅ Location: *{text}*\n\n📞 *Share CONTACT (Optional)*\nOr click SKIP", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif step == "contact_details":
        await complete_booking(update, context, user_id, message, text)

async def skip_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in user_data or user_data[user_id].get("step") != "contact_details":
        await query.edit_message_text("Type 'book' to start")
        return
    await complete_booking(update, context, user_id, query.message, "Not provided")

async def complete_booking(update, context, user_id, message, contact_details):
    print(f"\n📝 COMPLETING BOOKING FOR USER: {user_id}")
    try:
        effective_user = update.effective_user
        user_first_name = effective_user.first_name
        user_username = effective_user.username
        service = user_data[user_id].get("service", "Unknown")
        duration = user_data[user_id].get("duration", "Unknown")
        place = user_data[user_id].get("place", "Unknown")
        status = user_data[user_id].get("status", "Unknown")
        age = user_data[user_id].get("age", "Unknown")
        location = user_data[user_id].get("location", "Unknown")
        service_type = user_data[user_id].get("type", "")
        contact = contact_details
        booking_id = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        booking_data = {
            "user_id": user_id, "user_name": user_first_name, "username": user_username,
            "service": service, "service_type": service_type, "duration": duration,
            "place": place, "status": status, "age": age, "location": location,
            "contact": contact, "booking_id": booking_id, "time": datetime.now().isoformat()
        }
        bookings[booking_id] = booking_data
        user_active_booking[user_id] = booking_data
        keyboard = [[InlineKeyboardButton("📅 New Booking", callback_data="menu_book")], [InlineKeyboardButton("❌ Cancel Booking", callback_data="menu_cancel_booking")], [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]]
        await message.reply_text(f"✅ *BOOKING CONFIRMED!*\n\n📋 ID: `{booking_id}`\n💼 {service} {service_type}\n⏱️ {duration}\n📍 {place}\n👥 {status}\n🎂 {age}\n🏠 {location}\n📞 {contact}\n\n*Our associate will contact you shortly!*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        username_display = f"@{user_username}" if user_username else "N/A"
        admin_msg = f"🔔 <b>NEW BOOKING</b>\n\n<b>CUSTOMER:</b>\n👤 {user_first_name}\n📝 {username_display}\n🆔 <code>{user_id}</code>\n🎂 {age}\n👥 {status}\n📞 {contact}\n\n<b>BOOKING:</b>\n💼 {service} {service_type}\n⏱️ {duration}\n📍 {place}\n🏠 {location}\n📋 <code>{booking_id}</code>"
        await context.bot.send_message(ADMIN_ID, admin_msg, parse_mode='HTML')
        if user_id in user_data:
            del user_data[user_id]
    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text(f"❌ Error: {e}")

# ---------- CALLBACK HANDLER (only essential parts – same as original) ----------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    if data == "main_menu":
        await show_main_menu(query.message, user_id)
    elif data == "menu_book":
        await book_command(update, context)
    elif data == "menu_info":
        await query.edit_message_text("ℹ️ Service info...", parse_mode='Markdown')
    elif data == "menu_contact":
        user = query.from_user
        await context.bot.send_message(ADMIN_ID, f"📞 Contact from {user.first_name} (@{user.username or 'N/A'})\nID: {user.id}")
        await query.edit_message_text("✅ Request sent to admin!", parse_mode='Markdown')
    elif data == "menu_cancel_booking":
        if user_id in user_active_booking:
            booking_id = user_active_booking[user_id].get("booking_id", "Unknown")
            keyboard = [[InlineKeyboardButton("✅ Yes", callback_data=f"confirm_yes_{booking_id}")], [InlineKeyboardButton("❌ No", callback_data="confirm_no")]]
            await query.edit_message_text(f"⚠️ Cancel `{booking_id}`?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ No active booking!")
    elif data.startswith("confirm_yes_"):
        booking_id = data.replace("confirm_yes_", "")
        if user_id in user_active_booking:
            booking_data = user_active_booking[user_id]
            customer_name = booking_data.get('user_name', 'Unknown')
            cancel_msg = f"🔔 <b>BOOKING CANCELLED</b>\n👤 {customer_name}\n🆔 {user_id}\n📋 {booking_id}"
            await context.bot.send_message(ADMIN_ID, cancel_msg, parse_mode='HTML')
            del user_active_booking[user_id]
            await query.edit_message_text(f"✅ Booking `{booking_id}` cancelled!", parse_mode='Markdown')
    elif data == "confirm_no":
        await query.edit_message_text("✅ Booking kept active!")
    elif data == "book_massage":
        user_data[user_id] = {"service": "Massage", "step": "day_night"}
        keyboard = [[InlineKeyboardButton("☀️ Day", callback_data="massage_day")], [InlineKeyboardButton("🌙 Night", callback_data="massage_night")], [InlineKeyboardButton("🔙 Back", callback_data="menu_book")]]
        await query.edit_message_text("✅ *Massage*\nSelect Day or Night:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif data == "massage_day":
        user_data[user_id]["type"] = "Day"
        user_data[user_id]["step"] = "duration"
        keyboard = [[InlineKeyboardButton("⏰ 1 Hour", callback_data="dur_1")], [InlineKeyboardButton("⏰ 2 Hours", callback_data="dur_2")], [InlineKeyboardButton("⏰ 4 Hours", callback_data="dur_4")], [InlineKeyboardButton("🔙 Back", callback_data="book_massage")]]
        await query.edit_message_text("Select duration:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif data == "massage_night":
        user_data[user_id]["type"] = "Night"
        user_data[user_id]["step"] = "duration"
        keyboard = [[InlineKeyboardButton("⏰ 1 Hour", callback_data="dur_1")], [InlineKeyboardButton("⏰ 2 Hours", callback_data="dur_2")], [InlineKeyboardButton("⏰ 4 Hours", callback_data="dur_4")], [InlineKeyboardButton("🌙 Full Night", callback_data="dur_night")], [InlineKeyboardButton("🔙 Back", callback_data="book_massage")]]
        await query.edit_message_text("Select duration:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif data in ["dur_1", "dur_2", "dur_4", "dur_night"]:
        dur_map = {"dur_1":"1 Hour","dur_2":"2 Hours","dur_4":"4 Hours","dur_night":"Full Night"}
        user_data[user_id]["duration"] = dur_map[data]
        user_data[user_id]["step"] = "place"
        keyboard = [[InlineKeyboardButton("🏢 Public Place", callback_data="place_public")], [InlineKeyboardButton("🏨 Hotel", callback_data="place_hotel")], [InlineKeyboardButton("🏠 Your Home", callback_data="place_home")], [InlineKeyboardButton("🔙 Back", callback_data="menu_book")]]
        await query.edit_message_text("📍 Where?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif data in ["place_public","place_hotel","place_home"]:
        place_map = {"place_public":"Public Place","place_hotel":"Hotel","place_home":"Your Home"}
        user_data[user_id]["place"] = place_map[data]
        user_data[user_id]["step"] = "status"
        keyboard = [[InlineKeyboardButton("👤 Single", callback_data="status_single")], [InlineKeyboardButton("👥 Couple", callback_data="status_couple")], [InlineKeyboardButton("🔙 Back", callback_data="menu_book")]]
        await query.edit_message_text("👥 Single or Couple?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif data in ["status_single","status_couple"]:
        status_map = {"status_single":"Single","status_couple":"Couple"}
        user_data[user_id]["status"] = status_map[data]
        user_data[user_id]["step"] = "age"
        await query.edit_message_text("🎂 Enter your age:", parse_mode='Markdown')
    elif data == "skip_contact":
        await skip_contact(update, context)

# ============================================
# FLASK WEBHOOK ROUTES
# ============================================
@flask_app.route('/webhook', methods=['POST'])
async def webhook():
    if not application:
        return jsonify({"error": "Bot not ready"}), 500
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return jsonify({"ok": True})
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"ok": False}), 500

@flask_app.route('/')
def health():
    return "Bot is running with webhook", 200

@flask_app.route('/health')
def health_check():
    return "OK", 200

# ============================================
# SET WEBHOOK ON STARTUP
# ============================================
def set_webhook():
    if not RENDER_URL:
        print("⚠️ RENDER_EXTERNAL_URL not set. Webhook not configured.")
        return False
    webhook_url = f"{RENDER_URL}/webhook"
    import requests
    resp = requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", json={"url": webhook_url})
    if resp.ok and resp.json().get("ok"):
        print(f"✅ Webhook set to {webhook_url}")
        return True
    else:
        print(f"❌ Webhook failed: {resp.text}")
        return False

# ============================================
# MAIN - WEBHOOK MODE (No Polling)
# ============================================
if __name__ == "__main__":
    print("🚀 Starting bot in webhook mode...")
    # Build application
    application = Application.builder().token(TOKEN).build()
    # Add all handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("book", book_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("contact", contact_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_booking_command))
    application.add_handler(CommandHandler("send", send_to_user))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_ID), admin_reply_handler))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, easy_type_handler))
    
    # Initialize bot
    application.initialize()
    # Set webhook (only once on Render)
    set_webhook()
    
    # Start Flask (which will handle incoming webhook requests)
    port = int(os.environ.get("PORT", 8080))
    print(f"✅ Bot ready. Listening on port {port}")
    flask_app.run(host='0.0.0.0', port=port)
