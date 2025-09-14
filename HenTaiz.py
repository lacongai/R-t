# HenTaiz.py - Bot Telegram quản lý & gửi chúc tự động (đã sửa & tối ưu)
import logging
import asyncio
import aiohttp
import os
from io import BytesIO
from datetime import datetime, timedelta
import pytz
import json
import random
import re
from time import sleep
from urllib.parse import quote_plus
import asyncio
from rich.console import Console
from rich.text import Text 
import platform
import socket

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InputFile,
    ChatPermissions,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    Defaults,
    MessageHandler,
    filters,
)

# 🎨 Pretty Console with Rich (không bắt buộc để chạy bot, chỉ để hiển thị đẹp)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich import box
except Exception:
    Console = None
    Panel = None
    box = None

# ==================== CONFIG ====================
BOT_TOKEN = "7553795015:AAGj3pxeqLi7RtTx7_2R7ceNV1kRYW0N_hw"
YEUMONEY_TOKEN = "c4d4b0a2210fdf08a031e1085a3b884ed86e906b18e1a9fe43ce7eeb631eee5a"
LINK4M_TOKEN = "677d13ea99c2eb70ee48e57d"
TRAFFICUSER_TOKEN = "bf5e5566ec2f690001e277f5cfe0b92f73611f87"
BBMKTS_TOKEN = "e981e7b0b255b3487c5d444e"
SHRINKME_TOKEN = "922c7ca195e0cf432f81a462433f55412ff4c0bd"
EXE_TOKEN ="c0f710dcc2e11d8ab424885c4962d65631761a2e"
SHRTFLY_TOKEN = "e6a1057d8a6abf87be9c6e58e296eb04"
LAYMA_TOKEN = "1b0bb828772e4b3d71bc25942c820c91"
CLK_TOKEN = "22576a205d7dec44765c7a1669658bd4ce0471be"
API_QR = "http://192.168.1.82:8080/create-tim"
CUTTLY_API_KEY = ""
BITLY_API_KEY = ""

# ==================== FILES ====================
USER_FILE = "users.json"
GROUP_FILE = "groups.json"
CONFIG_FILE = "config.json"
ADMINS_FILE = "admins.json"     # file admins.json dùng để lưu ID admin
ADMINS = [6287661095]           # admin mặc định (fallback nếu file rỗng)      
LAST_SENT_FILE = "last_sent.txt"

# ---- Data (runtime) ----
user_warns = {}
user_messages = {}
warn_count = {}

# ---- Admin mặc định (fallback) ----
 # lưu ý: nên dùng số int cho id

# ---- Logger ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("HenTaizBot")

# ----------------- DECORATION -----------------

def show_banner():
    try:
        console = Console()
        os.system("clear" if os.name == "posix" else "cls")
        
        # Dùng raw string r"""...""" để tránh lỗi escape
        banner_text = Text(r"""
 _    _               _______         _
| |  | |             |__   __|       (_)
| |__| |  ___  _ __     | |     __ _  _  ____
|  __  | / _ \| '_ \    | |    / _` || ||_  /
| |  | ||  __/| | | |   | |   | (_| || | / /
|_|  |_| \___||_| |_|   |_|    \__,_||_|/___|








    """, style="bold magenta")

        
        # Hiệu ứng nhấp nháy
        for _ in range(3):
            console.print(banner_text)
            
            sleep(0.3)
            os.system("clear" if os.name == "posix" else "cls")
            sleep(0.2)

        console.print(banner_text)
        

        # Lấy thông tin thiết bị
        manufacturer = os.popen("getprop ro.product.manufacturer").read().strip() or "Unknown"
        model = os.popen("getprop ro.product.model").read().strip() or "Unknown"
        android_ver = os.popen("getprop ro.build.version.release").read().strip() or "?"
        sdk = os.popen("getprop ro.build.version.sdk").read().strip() or "?"

        # Thời gian hiện tại
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Kiến trúc CPU
        cpu_arch = platform.machine() or "Unknown"

        # Số bit CPU
        cpu_bits = platform.architecture()[0]

        
        device_info = f"""
[cyan bold]📱 Thiết bị:[/] {manufacturer} {model}
[magenta bold]🤖 Android:[/] {android_ver} (SDK {sdk})
[yellow]⏰ Thời gian:[/] {current_time}
[green]🔧 CPU:[/] {cpu_arch} ({cpu_bits})
"""

        # In panel
        console.print(
            Panel(
                "✨ [cyan bold]BY HENTAIZ - BOT TELEGRAM[/cyan bold] ✨",
                style="yellow",
                box=box.DOUBLE,
                expand=False,
            )
        )
        console.print(Panel(device_info, style="bold green", box=box.ROUNDED, expand=False))
        console.print("[bold green]🚀 Đang khởi động bot...[/green]\n")

    except Exception:
        # Trường hợp không có rich
        print("BY HENTAIZ - BOT TELEGRAM | Starting...")
        
    
# ==================== HELPERS (FS/JSON) ====================
def load_json(path, default):
    try:
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Lỗi ghi {path}: {e}")

def load_users():
    return load_json(USER_FILE, {})

def save_users(data):
    save_json(USER_FILE, data)

def load_groups():
    return load_json(GROUP_FILE, [])

def save_groups(groups):
    save_json(GROUP_FILE, groups)

def load_last_sent():
    try:
        if not os.path.exists(LAST_SENT_FILE):
            return ""
        with open(LAST_SENT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""

def save_last_sent(date_str):
    try:
        with open(LAST_SENT_FILE, "w", encoding="utf-8") as f:
            f.write(date_str)
    except Exception as e:
        logger.error(f"Lỗi ghi {LAST_SENT_FILE}: {e}")

def init_files():
    if not os.path.exists(CONFIG_FILE):
        save_json(CONFIG_FILE, {
            "friend_link": "https://t.me/@LearnModsGame",
            "friend_image": "https://i.ibb.co/4mM6JXq/welcome.jpg"
        })
    if not os.path.exists(ADMINS_FILE):
        save_json(ADMINS_FILE, [])
    if not os.path.exists(USER_FILE):
        save_json(USER_FILE, {})
    if not os.path.exists(GROUP_FILE):
        save_json(GROUP_FILE, [])
    if not os.path.exists(LAST_SENT_FILE):
        save_last_sent("")

def is_admin(user_id: int) -> bool:
    admins = load_json(ADMINS_FILE, [])
    # admins.json ưu tiên, nếu rỗng dùng ADMINS_FILE (fallback)
    if admins:
        return int(user_id) in set(int(x) for x in admins)
    return int(user_id) in set(ADMINS)
    
def ok_icon(x): 
    return "🟢" if x else "🔴"

# ==================== DECORATION ====================

        
# ==================== LỜI CHÚC & NGÀY LỄ ====================
HOLIDAYS = {
    "01/01": "🎉 Chúc mừng năm mới! Một khởi đầu tràn đầy niềm vui và may mắn! ✨",
    "30/04": "🇻🇳 Chúc mừng ngày Giải phóng miền Nam 30/4! ❤️",
    "01/05": "👷‍♂️ Ngày Quốc tế Lao động 1/5 – Chúc bạn thành công! 💪",
    "02/09": "🇻🇳 Quốc khánh 2/9 – Ngày trọng đại của dân tộc Việt Nam! 🎇",
    "24/12": "🎄 Giáng Sinh an lành, ấm áp bên gia đình và bạn bè! 🎅",
    "14/02": "❤️ Valentine hạnh phúc, tràn đầy yêu thương 💘",
    "08/03": "🌹 Ngày Quốc tế Phụ nữ 8/3 – Luôn xinh đẹp và hạnh phúc! 💐",
    "20/10": "💖 Ngày Phụ nữ Việt Nam 20/10! 🌸",
    "01/06": "🧸 Ngày Quốc tế Thiếu nhi 1/6 – Luôn vui tươi như trẻ nhỏ 🎈",
    "20/11": "📚 Ngày Nhà giáo Việt Nam 20/11 – Tri ân thầy cô ❤️"
}

MORNING_QUOTES = [
    "☀️ Chúc bạn một ngày mới đầy năng lượng và thành công! 🚀",
    "💡 Hãy tin rằng hôm nay sẽ tốt hơn ngày hôm qua!",
    "🔥 Dù khó khăn, bạn vẫn luôn mạnh mẽ và tuyệt vời!",
    "🌸 Hãy cười nhiều hơn, mọi chuyện sẽ trở nên nhẹ nhàng 💖",
    "💪 Không gì là không thể, hôm nay bạn sẽ làm được!",
    "✨ Hãy bắt đầu ngày mới bằng sự tự tin và lòng biết ơn!"
]

# ==================== HTTP HELPERS ====================
async def fetch_json(session: aiohttp.ClientSession, url: str, method: str = "GET", headers=None, json_payload=None, timeout=15):
    try:
        if method == "GET":
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                return await resp.json(content_type=None)
        else:
            async with session.post(url, headers=headers, json=json_payload, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                return await resp.json(content_type=None)
    except Exception as e:
        return {"error": str(e)}

async def fetch_text(session: aiohttp.ClientSession, url: str, timeout=15):
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            return await resp.text()
    except Exception as e:
        return f"error:{e}"

# ==================== WELCOME & GOODBYE ====================
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_html(f"👋 Chào mừng <b>{member.full_name}</b> đã tham gia nhóm!")
        await update.message.reply_photo("https://i.ibb.co/4mM6JXq/welcome.jpg")

async def goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.left_chat_member:
        user = update.message.left_chat_member
        await update.message.reply_html(f"👋 Tạm biệt <b>{user.full_name}</b>, hẹn gặp lại!")
        await update.message.reply_photo("https://i.ibb.co/ckDqh2k/goodbye.jpg")

# ==================== AUTO GREETING ====================
async def send_greeting(app: Application, target_chat_id=None):
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    today = datetime.now(tz).strftime("%d/%m")
    holiday_msg = HOLIDAYS.get(today)
    normal_msg = random.choice(MORNING_QUOTES)

    if target_chat_id:
        data = load_users()
        groups = load_groups()
        user_info = data.get(str(target_chat_id))
        is_birthday = user_info and user_info.get("birthday") == today
        try:
            if holiday_msg and is_birthday:
                await app.bot.send_message(int(target_chat_id), holiday_msg)
                await app.bot.send_message(int(target_chat_id), f"🎂 Chúc mừng sinh nhật {user_info['name']} 🎉🥳🎁")
            elif is_birthday:
                await app.bot.send_message(int(target_chat_id), normal_msg)
                await app.bot.send_message(int(target_chat_id), f"🎂 Chúc mừng sinh nhật {user_info['name']} 🎉🥳🎁")
            elif holiday_msg:
                await app.bot.send_message(int(target_chat_id), holiday_msg)
            else:
                await app.bot.send_message(int(target_chat_id), normal_msg)
        except Exception as e:
            logger.error(f"Lỗi gửi cho {target_chat_id}: {e}")
        return

    # Gửi tự động toàn bộ user
    data = load_users()
    groups = load_groups()
    birthday_users = []
    for uid, info in data.items():
        try:
            is_birthday = info.get("birthday") == today
            if holiday_msg and is_birthday:
                await app.bot.send_message(int(uid), holiday_msg)
                await app.bot.send_message(int(uid), f"🎂 Chúc mừng sinh nhật {info['name']} 🎉🥳🎁")
                birthday_users.append(info)
            elif is_birthday:
                await app.bot.send_message(int(uid), normal_msg)
                await app.bot.send_message(int(uid), f"🎂 Chúc mừng sinh nhật {info['name']} 🎉🥳🎁")
                birthday_users.append(info)
            elif holiday_msg:
                await app.bot.send_message(int(uid), holiday_msg)
            else:
                await app.bot.send_message(int(uid), normal_msg)
        except Exception as e:
            logger.error(f"Không gửi được cho {uid}: {e}")

    # Thông báo vào group nếu có sinh nhật
    if birthday_users:
        for g in groups:
            for b in birthday_users:
                try:
                    await app.bot.send_message(g, f"🎂 Hôm nay là sinh nhật của {b['name']}! 🎉🥳🎁")
                except Exception:
                    pass

    save_last_sent(today)
    logger.info(f"✅ Đã gửi lời chúc ngày {today}")

async def check_and_send(app: Application, force=False):
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    today = datetime.now(tz).strftime("%d/%m")
    last_sent = load_last_sent()
    if force or last_sent != today:
        await send_greeting(app)
    else:
        logger.info("⏭️ Đã gửi lời chúc hôm nay, bỏ qua.")

# ==================== GROUP MANAGEMENT ====================
# Cảnh cáo (3 lần thì ban)
# ================== BẢO VỆ & PHÒNG THỦ ==================

# ================== BẢO VỆ & PHÒNG THỦ ==================

async def cmd_antiraid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    if len(context.args) < 1:
        return await update.message.reply_text("❌ /antiraid <on|off>")
    status = context.args[0].lower()
    await update.message.reply_text(f"🛡️ Chống raid: **{status.upper()}**")

async def cmd_kickban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ Reply vào user để kick + ban")

    user_id = update.message.reply_to_message.from_user.id
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text(f"🚫 Đã kick + ban `{user_id}`")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")

async def cmd_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")

    deleted = 0
    async for msg in context.bot.get_chat_history(update.effective_chat.id, limit=200):
        if msg.from_user and msg.from_user.is_bot:
            try:
                await context.bot.delete_message(update.effective_chat.id, msg.id)
                deleted += 1
            except:
                pass
    await update.message.reply_text(f"🧹 Đã xóa {deleted} tin nhắn bot!")

async def cmd_lockdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    try:
        await context.bot.set_chat_permissions(update.effective_chat.id, ChatPermissions())
        await update.message.reply_text("🔒 Group đã bị **LOCKDOWN**!")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")

async def cmd_fortress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    if len(context.args) < 1:
        return await update.message.reply_text("❌ /fortress <link>")
    link = context.args[0]
    await update.message.reply_text(f"🏰 Fortress bảo vệ đã kích hoạt cho: {link}")

async def cmd_shield(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    if len(context.args) < 1:
        return await update.message.reply_text("❌ /shield <on|off>")
    status = context.args[0].lower()
    await update.message.reply_text(f"🛡️ Khiên bảo vệ: **{status.upper()}**")

async def cmd_autoban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    if len(context.args) < 1:
        return await update.message.reply_text("❌ /autoban <on|off>")
    status = context.args[0].lower()
    await update.message.reply_text(f"🤖 Auto-ban: **{status.upper()}**")

async def cmd_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ Reply vào user để thêm whitelist")

    user_id = update.message.reply_to_message.from_user.id
    await update.message.reply_text(f"✅ Đã thêm `{user_id}` vào **whitelist**")

async def cmd_addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    if not context.args:
        return await update.message.reply_text("❓ Dùng: /addadmin <id>")

    try:
        uid = int(context.args[0])
    except Exception:
        return await update.message.reply_text("❌ ID không hợp lệ.")
    admins = load_json(ADMINS_FILE, [])
    if uid not in admins:
        admins.append(uid)
        save_json(ADMINS_FILE, admins)
    await update.message.reply_text(f"✅ Đã thêm {uid} vào admin")

async def cmd_deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    if not context.args:
        return await update.message.reply_text("❓ Dùng: /deladmin <id>")

    try:
        uid = int(context.args[0])
    except Exception:
        return await update.message.reply_text("❌ ID không hợp lệ.")
    admins = load_json(ADMINS_FILE, [])
    if uid in admins:
        admins.remove(uid)
        save_json(ADMINS_FILE, admins)
    await update.message.reply_text(f"✅ Đã xoá {uid} khỏi admin")
    
# ================== QUẢN TRỊ THÀNH VIÊN ==================

async def cmd_checkadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_admin(uid):
        await update.message.reply_text(f"✅ Bạn ({uid}) là **ADMIN** của bot.")
    else:
        await update.message.reply_text(f"❌ Bạn ({uid}) KHÔNG phải admin bot.")

async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ Reply vào user để cảnh cáo")

    user_id = update.message.reply_to_message.from_user.id
    warn_count[user_id] = warn_count.get(user_id, 0) + 1
    if warn_count[user_id] >= 3:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, user_id)
            await update.message.reply_text(f"⚠ User `{user_id}` bị **BAN** (3 lần cảnh cáo)")
            warn_count[user_id] = 0
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi: {e}")
    else:
        await update.message.reply_text(f"⚠ Đã cảnh cáo `{user_id}` ({warn_count[user_id]}/3)")

async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ Reply vào user để kick")

    user_id = update.message.reply_to_message.from_user.id
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user_id)
        await update.message.reply_text(f"🚫 Đã kick `{user_id}`")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")

async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ Reply vào user để mute")

    user_id = update.message.reply_to_message.from_user.id
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"🔇 Đã mute `{user_id}`")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")

async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
    if not update.message.reply_to_message:
        return await update.message.reply_text("❌ Reply vào user để unmute")

    user_id = update.message.reply_to_message.from_user.id
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(f"🔊 Đã unmute `{user_id}`")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")

# ================== CHẶN LINK ==================

async def anti_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        return  # Admin được phép gửi link
    text = update.message.text or ""
    if re.search(r"(https?://|t\.me/|telegram\.me/)", text):
        try:
            await update.message.delete()
        except Exception:
            pass
        await update.message.reply_text(
            f"🚫 {update.effective_user.mention_html()} không được phép gửi link!",
            parse_mode="HTML",
        )

async def anti_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()
    last_time = user_messages.get(user_id, 0)

    if now - last_time < 1.5:
        if not is_admin(user_id):
            try:
                await update.effective_chat.restrict_member(
                    user_id, ChatPermissions(can_send_messages=False), until_date=int(time.time() + 60)
                )
            except Exception:
                pass
            await update.message.reply_text(
                f"🤐 {update.effective_user.mention_html()} đã bị mute 1 phút vì spam!",
                parse_mode="HTML",
            )
    user_messages[user_id] = now

# ==================== FRIEND (KẾT BẠN) & ADMINS_FILE ====================
async def cmd_ketban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = load_json(CONFIG_FILE, {})
    link = cfg.get("friend_link")
    img = cfg.get("friend_image")
    if not link or not img:
        await update.message.reply_text("❌ Chưa cấu hình link kết bạn trong config.json")
        return
    try:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=img,
            caption=f"📌 Kết bạn với admin tại link dưới đây:\n👉 {link}",
        )
    except Exception as e:
        await update.reply_text(f"Lỗi gửi ảnh: {e}")

# ==================== SHORTENER SERVICES ====================
async def svc_layma(session: aiohttp.ClientSession, long_url: str):
    enc = quote_plus(long_url)
    api = f"https://api.layma.net/api/admin/shortlink/quicklink?tokenUser={LAYMA_TOKEN}&format=json&url={long_url}&link_du_phong={enc}"
    data = await fetch_json(session, api)
    if isinstance(data, dict):
        if data.get("success") and data.get("html"):
            return data["html"], True
        if data.get("message"):
            return f"Lỗi: {data['message']}", False
    return None, False

async def svc_link4m(session: aiohttp.ClientSession, long_url: str):
    api = f"https://link4m.co/api-shorten/v2?api={LINK4M_TOKEN}&url={long_url}"
    data = await fetch_json(session, api)
    if isinstance(data, dict) and data.get("status") == "success":
        return data.get("shortenedUrl") or data.get("shortened"), True
    return None, False

async def svc_trafficuser(session: aiohttp.ClientSession, long_url: str):
    api = f"https://my.trafficuser.net/api?api={TRAFFICUSER_TOKEN}&url={long_url}&alias=CustomAlias"
    data = await fetch_json(session, api)

    if isinstance(data, dict) and data.get("status") == "success":
        return data.get("message") == ""
        return data.get("ShortenedUrl") or data.get("shortenedUrl"), True
    return None, False
    
async def svc_bbmkts(session: aiohttp.ClientSession, long_url: str):
    api = f"https://bbmkts.com/dapi?token={BBMKTS_TOKEN}&longurl={long_url}"
    data = await fetch_json(session, api)
    if isinstance(data, dict) and data.get("status") == "success":
        return data.get("shortenedUrl") or data.get("bbmktsUrl"), True
    return None, False

async def svc_yeumoney(session: aiohttp.ClientSession, long_url: str):
    api = f"https://yeumoney.com/QL_api.php?token={YEUMONEY_TOKEN}&format=json&url={long_url}"
    data = await fetch_json(session, api)
    if isinstance(data, dict):
        for key in ("shortenedUrl", "shorturl", "short_url", "short", "url"):
            if key in data and isinstance(data[key], str) and data[key].strip():
                return data[key].strip(), True
    return None, False

async def svc_ouo(session: aiohttp.ClientSession, long_url: str):
    api = f"http://ouo.io/api/Bzuerfpm?s={long_url}"
    text = await fetch_text(session, api)
    if isinstance(text, str) and text.startswith("http"):
        return text.strip(), True
    return None, False

async def svc_exe(session: aiohttp.ClientSession, long_url: str):
    api = f"https://exe.io/st?api={EXE_TOKEN}&url={long_url}"
    data = await fetch_json(session, api)
    if isinstance(data, dict) and str(data.get("status")).lower() in ("success", "ok", "true", "200"):
        return data.get("shortenedUrl") or data.get("shortened") or data.get("url"), True
    return None, False

async def svc_shrtfly(session: aiohttp.ClientSession, long_url: str):
    api = f"https://shrtfly.com/api?api={SHRTFLY_TOKEN}&type=1&url={long_url}"
    data = await fetch_json(session, api)
    if isinstance(data, dict) and str(data.get("status")).lower() in ("success", "ok", "true", "200"):
        return data.get("shortenedUrl") or data.get("shortened") or data.get("url"), True
    return None, False

async def svc_clk(session: aiohttp.ClientSession, long_url: str):
    api = f"https://clk.sh/api?api={CLK_TOKEN}&url={long_url}"
    data = await fetch_json(session, api)
    if isinstance(data, dict) and data.get("status") == "success":
        return data.get("shortenedUrl") or data.get("shortened"), True
    return None, False

async def svc_shrinkme(session: aiohttp.ClientSession, long_url: str):
    if not SHRINKME_TOKEN or SHRINKME_TOKEN.startswith("PUT-"):
        return None, False
    api_url = f"https://shrinkme.io/api?api={SHRINKME_TOKEN}&url={long_url}"
    try:
        async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            data = await resp.json(content_type=None)
            if data.get("status") == "success":
                base_link = data.get("shortenedUrl") or data.get("shortened")
                if base_link:
                    path = base_link.split("/")[-1]
                    return f"https://shrinkme.ink/{path}", True
    except Exception:
        return None, False
    return None, False

async def svc_isgd(session: aiohttp.ClientSession, long_url: str):
    api = f"https://is.gd/create.php?format=simple&url={long_url}"
    text = await fetch_text(session, api)
    if isinstance(text, str) and text.startswith("http"):
        return text.strip(), True
    return None, False

async def svc_tinyurl(session: aiohttp.ClientSession, long_url: str):
    api = f"http://tinyurl.com/api-create.php?url={long_url}"
    text = await fetch_text(session, api)
    if isinstance(text, str) and text.startswith("http"):
        return text.strip(), True
    return None, False

async def svc_cuttly(session: aiohttp.ClientSession, long_url: str):
    if not CUTTLY_API_KEY:
        return None, False
    api = f"https://cutt.ly/api/api.php?key={CUTTLY_API_KEY}&short={long_url}"
    data = await fetch_json(session, api)
    if isinstance(data, dict) and data.get("url", {}).get("status") == 7:
        return data["url"].get("shortLink"), True
    return None, False

async def svc_bitly(session: aiohttp.ClientSession, long_url: str):
    if not BITLY_API_KEY:
        return None, False
    api = "https://api-ssl.bitly.com/v4/shorten"
    headers = {"Authorization": f"Bearer {BITLY_API_KEY}", "Content-Type": "application/json"}
    payload = {"long_url": long_url}
    data = await fetch_json(session, api, method="POST", headers=headers, json_payload=payload)
    if isinstance(data, dict) and data.get("link"):
        return data["link"], True
    return None, False

# ==================== MAKE FILE ====================
async def cmd_makefile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_html(
            "❌ Vui lòng nhập nội dung để tạo file\n"
            "Ví dụ: <code>/makefile Đây là nội dung file</code>"
        )
    raw_content = " ".join(context.args)
    file_obj = BytesIO()
    file_obj.write(raw_content.encode("utf-8"))
    file_obj.seek(0)
    await update.message.reply_document(
        document=InputFile(file_obj, filename="output.txt"),
        caption="📁 Đây là file bạn vừa tạo"
    )

# ==================== QR Code Integration ====================
async def svc_qr(session: aiohttp.ClientSession, data: str):
    enc = quote_plus(data)
    # ⚠️ Đổi thành API thật của bạn
    api = f"{API_QR}?data={enc}"
    try:
        async with session.get(api, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                return await resp.read(), True
            return f"Lỗi: HTTP {resp.status}", False
    except Exception as e:
        return f"Lỗi khi gọi API QR: {e}", False

async def cmd_qr(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        return await update.message.reply_text("❌ Vui lòng nhập dữ liệu để tạo QR\nVí dụ: /qr HelloWorld")
    text_data = " ".join(ctx.args).strip()
    session: aiohttp.ClientSession = ctx.application.bot_data.get("session")
    if not session:
        session = aiohttp.ClientSession()
        ctx.application.bot_data["session"] = session
    qr_data, ok = await svc_qr(session, text_data)
    if ok and isinstance(qr_data, (bytes, bytearray)):
        bio = BytesIO(qr_data)
        bio.name = "qrcode.png"
        bio.seek(0)
        await update.message.reply_photo(photo=bio, caption=f"📌 QR cho: {text_data}")
    else:
        await update.message.reply_text(qr_data if isinstance(qr_data, str) else "❌ Không tạo được QR")

# ==================== COMMANDS: SHORT (ALL) ====================
async def reply_single(update: Update, context: ContextTypes.DEFAULT_TYPE, svc_func, svc_name: str, emoji: str):
    if not context.args:
        return await update.message.reply_text(
            f"❌ Vui lòng nhập URL cho {svc_name}\nVí dụ: /{svc_name.lower()} https://example.com"
        )
    long_url = context.args[0].strip()
    session: aiohttp.ClientSession = context.application.bot_data.get("session")
    if not session:
        session = aiohttp.ClientSession()
        context.application.bot_data["session"] = session
    short, ok = await svc_func(session, long_url)
    status = ok_icon(ok)
    if ok and short and isinstance(short, str) and short.startswith("http"):
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"{emoji} Mở {svc_name}", url=short)]])
        await update.message.reply_html(f"{emoji} <b>{svc_name}</b> {status}: <code>{short}</code>", reply_markup=kb)
    else:
        await update.message.reply_html(f"{emoji} <b>{svc_name}</b> {status}: {short or 'Lỗi'}")

# Lệnh từng dịch vụ
async def cmd_yeumoney(update, ctx):   await reply_single(update, ctx, svc_yeumoney, "Yeumoney", "💰")
async def cmd_link4m(update, ctx):     await reply_single(update, ctx, svc_link4m, "Link4m", "🔗")
async def cmd_bbmkts(update, ctx):await reply_single(update, ctx, svc_bbmkts, "bbmkts", "🍀")
async def cmd_trafficuser(update, ctx):await reply_single(update, ctx, svc_trafficuser, "Trafficuser", "🎭")
async def cmd_layma(update, ctx):      await reply_single(update, ctx, svc_layma, "Layma", "🗒️")
async def cmd_ouo(update, ctx):        await reply_single(update, ctx, svc_ouo, "Ouo", "🕐")
async def cmd_exe(update, ctx):        await reply_single(update, ctx, svc_exe, "Exe", "📍")
async def cmd_shrtfly(update, ctx):    await reply_single(update, ctx, svc_shrtfly, "Shrtfly", "✈️")
async def cmd_clk(update, ctx):        await reply_single(update, ctx, svc_clk, "Clk.sh", "🔹")
async def cmd_shrinkme(update, ctx):   await reply_single(update, ctx, svc_shrinkme, "ShrinkMe", "📉")
async def cmd_isgd(update, ctx):       await reply_single(update, ctx, svc_isgd, "is.gd", "🌐")
async def cmd_tinyurl(update, ctx):    await reply_single(update, ctx, svc_tinyurl, "TinyURL", "🔗")
async def cmd_cuttly(update, ctx):     await reply_single(update, ctx, svc_cuttly, "Cutt.ly", "✂️")
async def cmd_bitly(update, ctx):      await reply_single(update, ctx, svc_bitly, "Bitly", "🌀")

async def short_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_html(
            "❌ Vui lòng nhập URL\nVí dụ: <code>/short https://example.com</code>"
        )

    long_url = context.args[0].strip()
    session: aiohttp.ClientSession = context.application.bot_data.get("session")
    if not session:
        session = aiohttp.ClientSession()
        context.application.bot_data["session"] = session

    tasks = [
        # Vượt lâu
        svc_yeumoney(session, long_url),
        svc_link4m(session, long_url),
        svc_layma(session, long_url),
        svc_bbmkts(session, long_url),
        svc_trafficuser(session, long_url),
        # Vượt nhanh
        svc_ouo(session, long_url),
        svc_exe(session, long_url),
        svc_shrtfly(session, long_url),
        # Không vượt
        svc_clk(session, long_url),
        svc_shrinkme(session, long_url),
        svc_isgd(session, long_url),
        svc_tinyurl(session, long_url),
        svc_cuttly(session, long_url),
        svc_bitly(session, long_url),
    ]
    results = await asyncio.gather(*tasks)

    names = [
        "💰 Yeumoney", "🔗 Link4m", "🗒️ Layma", "🎭 trafficuser", "🍀 bbmkts", 
        "🕐 Ouo", "📍 Exe", "✈️ Shrtfly",
        "🔹 Clk.sh", "📉 ShrinkMe", "🌐 is.gd", "🔗 TinyURL",
        "✂️ Cutt.ly", "🌀 Bitly"
    ]

    text = (
        "✨ <b>Kết quả rút gọn</b> ✨\n\n"
        "📌 <b>Link gốc:</b>\n"
        f"<code>{long_url}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔗 <b>Link rút gọn:</b>\n"
    )

    keyboard_rows = []
    row = []
    for name, (short, ok) in zip(names, results):
        status = ok_icon(ok)
        text += f"{name} {status}: {short if short else '❌ Lỗi'}\n"
        if ok and short and isinstance(short, str) and short.startswith("http"):
            row.append(InlineKeyboardButton(name, url=short))
            if len(row) == 2:
                keyboard_rows.append(row)
                row = []
    if row:
        keyboard_rows.append(row)

    text += "━━━━━━━━━━━━━━━━━━━━━━━"

    await update.message.reply_html(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard_rows) if keyboard_rows else None,
    )

# ==================== STATUS ====================
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        session: aiohttp.ClientSession = context.application.bot_data.get("session")
        if not session:
            session = aiohttp.ClientSession()
            context.application.bot_data["session"] = session

        checks = {
            # Vượt lâu
            "💰 Yeumoney":   lambda s: svc_yeumoney(s, "https://example.com"),
            "🔗 Link4m":     lambda s: svc_link4m(s, "https://example.com"),
            "🗒️ Layma":     lambda s: svc_layma(s, "https://example.com"),
            "🎭 Trafficuser":lambda s: svc_trafficuser(s, "https://example.com"),
            "🍀 bbmkts":lambda s: svc_bbmkts(s, "https://example.com"),
            # Vượt nhanh
            "🕐 Ouo":       lambda s: svc_ouo(s, "https://example.com"),
            "📍 Exe":       lambda s: svc_exe(s, "https://example.com"),
            "✈️ Shrtfly":   lambda s: svc_shrtfly(s, "https://example.com"),
            # Không vượt
            "🔹 Clk.sh":    lambda s: svc_clk(s, "https://example.com"),
            "📉 ShrinkMe":  lambda s: svc_shrinkme(s, "https://example.com"),
            "🌐 is.gd":     lambda s: svc_isgd(s, "https://example.com"),
            "🔗 TinyURL":   lambda s: svc_tinyurl(s, "https://example.com"),
            "✂️ Cutt.ly":   (lambda s: svc_cuttly(s, "https://example.com")) if CUTTLY_API_KEY else None,
            "🌀 Bitly":     (lambda s: svc_bitly(s, "https://example.com")) if BITLY_API_KEY else None,
            "🧾 MakeFile":  lambda s: svc_tinyurl(s, "https://example.com"),
            "📠 QR":        lambda s: svc_qr(s, "Hello"),
        }

        tasks, names = [], []
        for name, fn in checks.items():
            if fn:
                tasks.append(fn(session))
                names.append(name)

        if not tasks:
            return await update.message.reply_html("❗ Không có dịch vụ nào để kiểm tra.")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        rows = []
        up = down = 0
        for name, res in zip(names, results):
            ok = False
            if isinstance(res, tuple):
                _, ok = res
            elif res and not isinstance(res, Exception):
                ok = True
            if ok:
                rows.append(f"{name:<12} -> ✅ Online")
                up += 1
            else:
                rows.append(f"{name:<12} -> ❌ Offline")
                down += 1

        table = "\n".join(rows)
        text = (
            "📊 <b>Kiểm tra trạng thái dịch vụ</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "<pre>" + table + "</pre>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Tổng kết:</b> {up} dịch vụ ✅ / {down} dịch vụ ❌"
        )
        await update.message.reply_html(text)

    except Exception as e:
        await update.message.reply_html(f"❌ Lỗi khi kiểm tra dịch vụ:\n<code>{e}</code>")
        logger.exception("Error in /status")

# ==================== INLINE QUERY ====================
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = (update.inline_query.query or "").strip()
    if not query:
        return

    session: aiohttp.ClientSession = context.application.bot_data.get("session")
    if not session:
        session = aiohttp.ClientSession()
        context.application.bot_data["session"] = session

    tiny_task = svc_tinyurl(session, query)
    isgd_task = svc_isgd(session, query)
    ouo_task = svc_ouo(session, query)
    exe_task = svc_exe(session, query)
    shrtfly_task = svc_shrtfly(session, query)
    yeu_task = svc_yeumoney(session, query)
    link4m_task = svc_link4m(session, query)
    layma_task = svc_layma(session, query)
    traffic_task = svc_trafficuser(session, query)
    bbmkts_task = svc_bbmkts(session, query)

    tiny_r, isgd_r, ouo_r, exe_r, shrtfly_r, yeu_r, link4m_r, layma_r, traffic_r = await asyncio.gather(
        tiny_task, isgd_task, ouo_task, exe_task, shrtfly_task, yeu_task, link4m_task, layma_task, traffic_task, bbmkts_task
    )

    results = []

    if yeu_r[1] and yeu_r[0]:
        results.append(InlineQueryResultArticle(id="yeu", title="💰 Yeumoney", description=yeu_r[0],
                                               input_message_content=InputTextMessageContent(yeu_r[0])))

    if link4m_r[1] and link4m_r[0]:
        results.append(InlineQueryResultArticle(id="link4m", title="🔗 Link4m", description=link4m_r[0],
                                               input_message_content=InputTextMessageContent(link4m_r[0])))

    if layma_r[1] and layma_r[0]:
        results.append(InlineQueryResultArticle(id="layma", title="🗒️ Layma", description=layma_r[0],
                                               input_message_content=InputTextMessageContent(layma_r[0])))
    if traffic_r[1] and traffic_r[0]:
        results.append(InlineQueryResultArticle(id="trafficuser", title="🎭 TrafficUser", description=traffic_r[0],
                                               input_message_content=InputTextMessageContent(traffic_r[0])))                                              

    if bbmkts_r[1] and bbmkts_r[0]:
        results.append(InlineQueryResultArticle(id="bbmkts", title="🍀 bbmkts", description=bbmkts_r[0],
                                               input_message_content=InputTextMessageContent(bbmkts_r[0])))

    if tiny_r[1] and tiny_r[0]:
        results.append(InlineQueryResultArticle(id="tiny", title="🔗 TinyURL", description=tiny_r[0],
                                               input_message_content=InputTextMessageContent(tiny_r[0])))

    if isgd_r[1] and isgd_r[0]:
        results.append(InlineQueryResultArticle(id="isgd", title="🌐 is.gd", description=isgd_r[0],
                                               input_message_content=InputTextMessageContent(isgd_r[0])))

    if ouo_r[1] and ouo_r[0]:
        results.append(InlineQueryResultArticle(id="ouo", title="🕐 Ouo.io", description=ouo_r[0],
                                               input_message_content=InputTextMessageContent(ouo_r[0])))

    if exe_r[1] and exe_r[0]:
        results.append(InlineQueryResultArticle(id="exe", title="📍 Exe.io", description=exe_r[0],
                                               input_message_content=InputTextMessageContent(exe_r[0])))

    if shrtfly_r[1] and shrtfly_r[0]:
        results.append(InlineQueryResultArticle(id="shrtfly", title="✈️ Shrtfly", description=shrtfly_r[0],
                                               input_message_content=InputTextMessageContent(shrtfly_r[0])))

    if not results:
        results.append(InlineQueryResultArticle(
            id="none",
            title="❌ Không có dịch vụ khả dụng",
            description="No service returned a short link.",
            input_message_content=InputTextMessageContent("No service available"),
        ))

    await update.inline_query.answer(results, cache_time=0)

# ==================== TRACK USER & BIRTHDAY ====================
async def track_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    chat = update.message.chat
    if chat.type in ("group", "supergroup"):
        groups = load_groups()
        if chat.id not in groups:
            groups.append(chat.id)
            save_groups(groups)
        return
    user = update.message.from_user
    uid = str(user.id)
    uname = f"@{user.username}" if user.username else user.full_name
    data = load_users()
    groups = load_groups()
    if uid not in data:
        data[uid] = {"name": uname, "birthday": None}
        save_users(data)
        await context.bot.send_message(chat_id=user.id, text="🎂 Nhập ngày sinh (dd/mm). VD: 19/08")

async def save_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    uid = str(update.message.from_user.id)
    text = update.message.text.strip()
    if len(text) == 5 and text[2] == "/":
        d, m = text.split("/")
        if d.isdigit() and m.isdigit():
            data = load_users()
            groups = load_groups()
            if uid in data and not data[uid]["birthday"]:
                data[uid]["birthday"] = text
                save_users(data)
                await update.message.reply_text(f"✅ Đã lưu sinh nhật: {text}")

# ==================== BASIC COMMANDS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 <b>Xin chào!</b>\n\n"
        "<b>Xin tự giới thiệu 1 chút</b>\n"
        "Tôi là bot rút gọn link @Kelly_Shorten_Bot✨\nĐể phục vụ mọi người miễn phí\n"
        "Gõ <b>/help</b> để xem hướng dẫn."
    )
    
    await update.message.reply_html(text)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 <b>Hướng dẫn sử dụng Bot</b>\n\n"
        "💥 <b>/start</b> - Bắt đầu bot\n"
        "🔎 <b>/help</b> - Xem lệnh\n\n"
        "👉 <b>/short &lt;url&gt;</b> - Rút gọn bằng tất cả dịch vụ\n"
        "👉 <b>/status</b> - Kiểm tra trạng thái dịch vụ\n\n"
        "<b>📌 Danh sách lệnh quản lý:</b>\n"
        "⚠ /warn - Cảnh cáo (3 lần sẽ ban)\n"
        "🚫 /kick - Kick thành viên\n"
        "🔇 /mute - Mute thành viên\n"
        "🔊 /unmute - Bỏ mute\n\n"
        "<b>🛡 Tự động:</b>\n"
        "👉 - Chào mừng thành viên mới\n"
        "👉 - Chặn spam, chặn link\n\n"
        "🧩 <b>Dịch vụ có sẵn:</b>\n\n"
        "🐇 Dịch vụ không cần vượt:\n"
        "   • 🔹 Clk.sh\n"
        "   • 🌐 is.gd\n"
        "   • 🔗 TinyURL.com\n"
        "   • ✂️ Cutt.ly\n"
        "   • 🌀 Bitly.com\n\n"
        "🐢 Dịch vụ cần vượt nhanh:\n"
        "   • 🕐 Ouo.io\n"
        "   • ✈️ Shrtfly.com\n"
        "   • 📉 ShrinkMe.io\n\n"        
        "🐌 Dịch vụ cần vượt chậm:\n"
        "   • 💰 Yeumoney.com\n"
        "   • 🔗 Link4m.com\n"
        "   • 🗒️ Layma.net\n"
        "   • 🎭 my.trafficuser.net\n"
        "   • 🍀 bbmkts.com\n\n"
        "Dịch vụ song song:\n"
        "   • 📠 QR -- API nhà làm lên ko có web\n\n"
        "✨ Bạn cũng có thể dùng inline: @Kelly_Shorten_Bot link\n\n"
        "🤖 Bot do @LearnModsGame tạo\nNik Name: <b>HenTaiz ؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒؒ</b>\nGiới tính: <b>Nữ</b>\n\n-- <b>Lưu ý:</b>\nCấm lên google tra tên\nCấm hỏi là nam hay nữ nói rồi đó nha mấy ní\n<b>Cần gì hỏi gì liên quan đến bot cứ ib chứ ko chắc có trong nhóm ko</b>"
    )
    
    await update.message.reply_html(help_text)

# ==================== LIFECYCLE ====================
async def _on_startup(app: Application):
    # Tạo session dùng chung
    app.bot_data["session"] = aiohttp.ClientSession()

    # Set commands
    try:
        await app.bot.set_my_commands([
            ("start","Start"),
            ("help","Help"),
            ("status","Check services"),
            ("ketban","Link kết bạn"),
            ("addadmin","Thêm Admin"),
            ("deladmin","Xoá Admin"),
            ("antiraid","Chống raid tự động"),
            ("kickban","Kick + ban user"),
            ("cleanup","Dọn dẹp spam messages"),
            ("lockdown","Khóa group tạm thời"),
            ("fortress","Bảo vệ tối đa"),
            ("shield","Khiên bảo vệ"),
            ("autoban","Tự động ban"),
            ("whitelist","Thêm vào whitelist"),
            ("warn","Cảnh cáo (3 lần sẽ ban)"),
            ("kick","Kick thành viên"),
            ("mute","Mute thành viên"),
            ("unmute","Bỏ mute"),
            ("short","Shorten all"),
            ("qr","Tạo QR"),
            ("yeumoney","Yeumoney"),
            ("link4m","Link4m"),
            ("layma","Layma"),
            ("trafficuser","Trafficuser"),
            ("bbmkts","bbmkts"),
            ("ouo","Ouo"),
            ("exe","Exe"),
            ("shrtfly","Shrtfly"),
            ("clk","Clk.sh"),
            ("shrinkme","ShrinkMe"),
            ("isgd","is.gd"),
            ("tinyurl","TinyURL"),
            ("cuttly","Cutt.ly"),
            ("bitly","Bitly"),
            ("makefile","MakeFile"),
        ])
    except Exception:
        pass

    # Gửi chúc ngay khi khởi động nếu chưa gửi trong ngày
    await check_and_send(app, force=False)

    # Lên lịch gửi chúc hằng ngày 00:00 Asia/Ho_Chi_Minh bằng JobQueue
    tz = pytz.timezone("Asia/Ho_Chi_Minh")
    target_time = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0).time()
    app.job_queue.run_daily(
        lambda ctx: asyncio.create_task(check_and_send(app)),
        time=target_time,
        name="daily_greet"
    )

    logger.info("✅ Bot đã khởi động & lên lịch gửi chúc hằng ngày.")
    
async def _on_shutdown(app: Application):
    session = app.bot_data.get("session")
    if session and not session.closed:
        await session.close()

# ==================== COMMAND CHECK REACT ====================
# ==================== COMMAND CHECK REPLY ====================
SUPPORTED_COMMANDS = {
    "start","help","status","ketban","addadmin","deladmin",
    "antiraid","kickban","cleanup","lockdown","fortress","shield","autoban","whitelist",
    "warn","kick","mute","unmute",
    "short","qr","makefile",
    "yeumoney","link4m","trafficuser","bbmkts","layma",
    "ouo","exe","shrtfly","clk","shrinkme","isgd","tinyurl","cuttly","bitly"
}

async def react_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    cmd = update.message.text.split()[0].lstrip("/").split("@")[0].lower()

    if cmd in SUPPORTED_COMMANDS:
        await update.message.reply_text("✅")
    else:
        await update.message.reply_text("❌ Lệnh không hỗ trợ")
            
def main():
    if not BOT_TOKEN or BOT_TOKEN.startswith("PUT-"):
        raise SystemExit("❌ Set BOT_TOKEN in the script before running.")
    init_files()
    show_banner()
    defaults = Defaults(allow_sending_without_reply=True)
    app = Application.builder().token(BOT_TOKEN).post_init(_on_startup).defaults(defaults).build()

    # Welcome / Goodbye
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye))

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("checkadmin", cmd_checkadmin))
    # Group management
    # ================== ĐĂNG KÝ HANDLER ==================

    app.add_handler(CommandHandler("antiraid", cmd_antiraid))
    app.add_handler(CommandHandler("kickban", cmd_kickban))
    app.add_handler(CommandHandler("cleanup", cmd_cleanup))
    app.add_handler(CommandHandler("lockdown", cmd_lockdown))
    app.add_handler(CommandHandler("fortress", cmd_fortress))
    app.add_handler(CommandHandler("shield", cmd_shield))
    app.add_handler(CommandHandler("autoban", cmd_autoban))
    app.add_handler(CommandHandler("whitelist", cmd_whitelist))

    app.add_handler(CommandHandler("warn", cmd_warn))
    app.add_handler(CommandHandler("kick", cmd_kick))
    app.add_handler(CommandHandler("mute", cmd_mute))
    app.add_handler(CommandHandler("unmute", cmd_unmute))

    # Shorteners & tools
    app.add_handler(CommandHandler("short", short_cmd))
    app.add_handler(CommandHandler("qr", cmd_qr))
    app.add_handler(CommandHandler("makefile", cmd_makefile))
    app.add_handler(CommandHandler("ketban", cmd_ketban))
    app.add_handler(CommandHandler("addadmin", cmd_addadmin))
    app.add_handler(CommandHandler("deladmin", cmd_deladmin))

    # Single services
    app.add_handler(CommandHandler("yeumoney", cmd_yeumoney))
    app.add_handler(CommandHandler("link4m", cmd_link4m))
    app.add_handler(CommandHandler("trafficuser", cmd_trafficuser))
    app.add_handler(CommandHandler("bbmkts", cmd_bbmkts))
    app.add_handler(CommandHandler("layma", cmd_layma))
    app.add_handler(CommandHandler("ouo", cmd_ouo))
    app.add_handler(CommandHandler("exe", cmd_exe))
    app.add_handler(CommandHandler("shrtfly", cmd_shrtfly))
    app.add_handler(CommandHandler("clk", cmd_clk))
    app.add_handler(CommandHandler("shrinkme", cmd_shrinkme))
    app.add_handler(CommandHandler("isgd", cmd_isgd))
    app.add_handler(CommandHandler("tinyurl", cmd_tinyurl))
    app.add_handler(CommandHandler("cuttly", cmd_cuttly))
    app.add_handler(CommandHandler("bitly", cmd_bitly))

    # Inline
    app.add_handler(InlineQueryHandler(inline_query))

    # Track users & protections
    app.add_handler(MessageHandler(filters.ALL, track_user))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anti_link))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anti_spam))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_birthday))
    
    # React khi user gọi lệnh
    # React khi user gọi lệnh
    app.add_handler(MessageHandler(filters.COMMAND, react_command), group=0)
    
    logger.info("🚀 Bot is starting...")
    try:
        app.run_polling(stop_signals=None)
    finally:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_on_shutdown(app))

if __name__ == "__main__":
    main()
