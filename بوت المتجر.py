import sqlite3
from datetime import datetime
import telebot
from telebot import types

TOKEN = "8792298957:AAEJwxlnyYEuQnE_bdzQeWQsfDaPVUldRmc"
ADMIN_ID =  8293515549

bot = telebot.TeleBot(TOKEN)

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'ar',
            points INTEGER DEFAULT 0,
            last_day TEXT DEFAULT ''
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price INTEGER,
            details TEXT,
            category TEXT,
            media_type TEXT DEFAULT 'text',
            media_id TEXT DEFAULT ''
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            code TEXT PRIMARY KEY,
            points INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            price INTEGER,
            date TEXT,
            status TEXT DEFAULT 'completed'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS force_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT UNIQUE,
            channel_url TEXT,
            title TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

def get_user(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, lang, points, last_day FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, lang, points, last_day) VALUES (?, 'ar', 0, '')", (user_id,))
        conn.commit()
        cursor.execute("SELECT user_id, lang, points, last_day FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    conn.close()
    return user

def add_points(user_id, points_to_add):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points_to_add, user_id))
    conn.commit()
    conn.close()

def check_subscription(user_id):
    if user_id == ADMIN_ID:
        return True, []
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id, channel_url, title FROM force_channels")
    channels = cursor.fetchall()
    conn.close()

    if not channels:
        return True, []

    unsubscribed = []
    for ch_id, ch_url, title in channels:
        try:
            member = bot.get_chat_member(ch_id, user_id)
            if member.status not in ['creator', 'administrator', 'member']:
                unsubscribed.append((ch_id, ch_url, title))
        except Exception:
            unsubscribed.append((ch_id, ch_url, title))

    if unsubscribed:
        return False, unsubscribed
    return True, []

def get_sub_keyboard(unsubscribed_channels):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch_id, ch_url, title in unsubscribed_channels:
        markup.add(types.InlineKeyboardButton(f"✨ 𝑱𝒐𝒊𝒏 ➲ {title}", url=ch_url))
    markup.add(types.InlineKeyboardButton("🔄 ⚡ 𝑻𝒆𝒔𝒕 𝑺𝒖𝒃𝒔𝒄𝒓𝒊𝒑𝒕𝒊𝒐𝒏 | تأكيد الاشتراك ⚡", callback_data="check_sub"))
    return markup

def main_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_categories = types.InlineKeyboardButton("🛍️ 𝑺𝒕𝒐𝒓𝒆 | المنتجات والأقسام", callback_data="view_categories")
    btn_profile = types.InlineKeyboardButton("👤 𝑷𝒓𝒐𝒇𝒊𝒍𝒆 | حسابي ورصيدي", callback_data="my_profile")
    btn_daily = types.InlineKeyboardButton("🎁 𝑫𝒂𝒊𝒍𝒚 𝑮𝒊𝒇𝒕 | الهدية اليومية", callback_data="daily_gift")
    btn_charge = types.InlineKeyboardButton("💳 𝑪𝒉𝒂𝒓𝒈𝒆 | شحن كود", callback_data="charge_account")
    btn_lang = types.InlineKeyboardButton("🌐 𝑳𝒂𝒏𝒈𝒖𝒂𝒈𝒆 | تغيير اللغة", callback_data="change_lang")

    markup.add(btn_categories, btn_profile)
    markup.add(btn_daily, btn_charge)
    markup.add(btn_lang)

    if user_id == ADMIN_ID:
        btn_admin = types.InlineKeyboardButton("⚙️ 𝑨𝒅𝒎𝒊𝒏 𝑷𝒂𝒏𝒆𝒍 | لوحة التحكم", callback_data="admin_panel")
        markup.add(btn_admin)

    return markup

def admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_add_prod = types.InlineKeyboardButton("➕ 𝑨𝒅𝒅 𝑷𝒓𝒐𝒅𝒖𝒄𝒕 | إضافة منتج", callback_data="adm_add_prod")
    btn_del_prod = types.InlineKeyboardButton("🗑️ 𝑫𝒆𝒍𝒆𝒕𝒆 𝑷𝒓𝒐𝒅𝒖𝒄𝒕 | حذف منتج", callback_data="adm_del_prod")
    btn_add_cat = types.InlineKeyboardButton("📂 𝑨𝒅𝒅 𝑪𝒂𝒕𝒆𝒈𝒐𝒓𝒚 | إضافة قسم", callback_data="adm_add_cat")
    btn_gen_card = types.InlineKeyboardButton("💳 𝑵𝒆𝒘 𝑪𝒂𝒓𝒅 | إنشاء كود", callback_data="adm_gen_card")
    btn_add_pts = types.InlineKeyboardButton("💰 𝑷𝒐𝒊𝒏𝒕𝒔 | تعديل النقاط", callback_data="adm_mod_pts")
    btn_fsub = types.InlineKeyboardButton("📢 𝑭𝒐𝒓𝒄𝒆 𝑺𝒖𝒃 | اشتراك إجباري", callback_data="adm_force_sub")
    btn_proof = types.InlineKeyboardButton("📜 𝑷𝒓𝒐𝒐𝒇 𝑪𝒉𝒂𝒏𝒏𝒆𝒍 | قناة الإثباتات", callback_data="adm_proof_chan")
    btn_stats = types.InlineKeyboardButton("📊 𝑺𝒕𝒂𝒕𝒊𝒔𝒕𝒊𝒄𝒔 | الإحصائيات", callback_data="adm_stats")
    btn_bc = types.InlineKeyboardButton("📢 𝑩𝒓𝒐𝒂𝒅𝒄𝒂𝒔𝒕 | إذاعة عامة", callback_data="adm_broadcast")
    btn_back = types.InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 | القائمة الرئيسية", callback_data="main_menu")

    markup.add(btn_add_prod, btn_del_prod)
    markup.add(btn_add_cat, btn_gen_card)
    markup.add(btn_add_pts, btn_stats)
    markup.add(btn_fsub, btn_proof)
    markup.add(btn_bc)
    markup.add(btn_back)
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    get_user(user_id)

    is_sub, unsub_channels = check_subscription(user_id)
    if not is_sub:
        welcome_sub = (
            f"❖ ─── ✦ 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆 ✦ ─── ❖\n"
            f"👑 **مرحباً بك في متجر ﻳـﻤـﺎﻧـﻲ ﻣـﺎﺭﻛـﺔ** 👑\n\n"
            f"⚠️ **عذراً عزيزي، يجب عليك الاشتراك في القنوات الرسمية لاستخدام البوت:**"
        )
        bot.send_message(
            message.chat.id,
            welcome_sub,
            reply_markup=get_sub_keyboard(unsub_channels),
            parse_mode="Markdown"
        )
        return

    welcome_text = (
        f"❖ ─── ✦ 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆 ✦ ─── ❖\n"
        f"👑 **أهلاً بك في بوت ﻳـﻤـﺎﻧـﻲ ﻣـﺎﺭﻛـﺔ الفاخر** 👑\n"
        f"✨ **𝑾𝒆𝒍𝒄𝒐𝒎𝒆 𝒕𝒐 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆 𝑶𝒇𝒇𝒊𝒄𝒊𝒂𝒍 𝑩𝒐𝒕** ✨\n"
        f"❖ ──────────────── ❖\n\n"
        f"⚡ **اختر من القائمة أدناه لتصفح المتجر:**"
    )

    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=main_keyboard(user_id),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if call.data == "check_sub":
        is_sub, unsub_channels = check_subscription(user_id)
        if is_sub:
            bot.answer_callback_query(call.id, "✅ شكراً لاشتراكك! تم فتح بوت ﻳـﻤـﺎﻧـﻲ ﻣـﺎﺭﻛـﺔ.", show_alert=True)
            welcome_text = (
                f"❖ ─── ✦ 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆 ✦ ─── ❖\n"
                f"👑 **أهلاً بك في بوت ﻳـﻤـﺎﻧـﻲ ﻣـﺎﺭﻛـﺔ الفاخر** 👑\n"
                f"✨ **𝑾𝒆𝒍𝒄𝒐𝒎𝒆 𝒕𝒐 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆 𝑶𝒇𝒇𝒊𝒄𝒊𝒂𝒍 𝑩𝒐𝒕** ✨\n"
                f"❖ ──────────────── ❖\n\n"
                f"⚡ **اختر من القائمة أدناه لتصفح المتجر:**"
            )
            bot.edit_message_text(
                welcome_text,
                chat_id=chat_id,
                message_id=msg_id,
                reply_markup=main_keyboard(user_id),
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "❌ لم تشترك في جميع القنوات بعد!", show_alert=True)
            try:
                bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=get_sub_keyboard(unsub_channels))
            except:
                pass
        return

    if user_id != ADMIN_ID:
        is_sub, unsub_channels = check_subscription(user_id)
        if not is_sub:
            bot.answer_callback_query(call.id, "⚠️ يجب عليك الاشتراك في القنوات أولاً!", show_alert=True)
            bot.send_message(chat_id, "⚠️ **يرجى الاشتراك في القنوات التالية لاستخدام البوت:**", reply_markup=get_sub_keyboard(unsub_channels), parse_mode="Markdown")
            return

    if call.data == "main_menu":
        welcome_text = (
            f"❖ ─── ✦ 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆 ✦ ─── ❖\n"
            f"👑 **القائمة الرئيسية - ﻳـﻤـﺎﻧـﻲ ﻣـﺎﺭﻛـﺔ** 👑\n"
            f"❖ ──────────────── ❖"
        )
        bot.edit_message_text(
            welcome_text,
            chat_id=chat_id,
            message_id=msg_id,
            reply_markup=main_keyboard(user_id),
            parse_mode="Markdown"
        )

    elif call.data == "my_profile":
        user = get_user(user_id)
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,))
        orders_count = cursor.fetchone()[0]
        conn.close()

        profile_text = (
            f"╔════════════════════╗\n"
            f"👤 **𝑼𝒔𝒆𝒓 𝑷𝒓𝒐𝒇𝒊𝒍𝒆 | ملف الحساب**\n"
            f"👑 **𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆 𝑺𝒚𝒔𝒕𝒆𝒎**\n"
            f"╚════════════════════╝\n\n"
            f"🆔 **آيدي الحساب:** `{user_id}`\n"
            f"💰 **رصيد النقاط:** ✨ `{user[2]}` **نقطة** ✨\n"
            f"📦 **إجمالي عمليات الشراء:** `{orders_count}` **طلب**\n"
            f"🌐 **اللغة المفضلة:** `{user[1]}`\n\n"
            f"❖ ─── ✦ 💎 ✦ ─── ❖"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 | العودة", callback_data="main_menu"))
        bot.edit_message_text(profile_text, chat_id=chat_id, message_id=msg_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "daily_gift":
        user = get_user(user_id)
        today = datetime.now().strftime("%Y-%m-%d")

        if user[3] == today:
            bot.answer_callback_query(call.id, "🎁 لقد استلمت هديتك اليومية بالفعل! عد غداً.", show_alert=True)
        else:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET points = points + 10, last_day = ? WHERE user_id = ?", (today, user_id))
            conn.commit()
            conn.close()
            bot.answer_callback_query(call.id, "🎉 مبروك! حصلت على +10 نقاط هدية من 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆.", show_alert=True)
            bot.edit_message_text("🎉 **🎁 تم استلام الهدية اليومية (+10 نقاط) بنجاح من 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆!**", chat_id=chat_id, message_id=msg_id, reply_markup=main_keyboard(user_id), parse_mode="Markdown")

    elif call.data == "change_lang":
        user = get_user(user_id)
        new_lang = "en" if user[1] == "ar" else "ar"
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (new_lang, user_id))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, f"تم تغيير اللغة إلى: {new_lang}", show_alert=True)
        bot.edit_message_text("✅ **تم تحديث إعدادات اللغة بنجاح.**", chat_id=chat_id, message_id=msg_id, reply_markup=main_keyboard(user_id), parse_mode="Markdown")

    elif call.data == "charge_account":
        msg = bot.send_message(chat_id, "💳 **يرجى إرسال كود الشحن الخاص بك الآن:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_card_recharge)

    elif call.data == "view_categories":
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories")
        categories = cursor.fetchall()
        conn.close()

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🌐 ✨ 𝑨𝒍𝒍 𝑷𝒓𝒐𝒅𝒖𝒄𝒕𝒔 | جميع المنتجات", callback_data="cat_all"))
        for cat in categories:
            markup.add(types.InlineKeyboardButton(f"📁 📂 {cat[0]}", callback_data=f"cat_{cat[0]}"))
        markup.add(types.InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 | العودة", callback_data="main_menu"))

        cat_text = (
            f"📂 ─── ✦ 𝒀𝒂𝒎𝒂𝒏𝒊 𝑪𝒂𝒕𝒆𝒈𝒐𝒓𝒊𝒆𝒔 ✦ ─── 📂\n"
            f"👑 **اختر القسم المطلوب من متجر ﻳـﻤـﺎﻧـﻲ ﻣـﺎﺭﻛـﺔ:**"
        )
        bot.edit_message_text(cat_text, chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("cat_"):
        cat_name = call.data.split("cat_")[1]
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        if cat_name == "all":
            cursor.execute("SELECT id, name, price FROM products")
        else:
            cursor.execute("SELECT id, name, price FROM products WHERE category = ?", (cat_name,))
        products = cursor.fetchall()
        conn.close()

        markup = types.InlineKeyboardMarkup()
        if not products:
            markup.add(types.InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 | العودة للأقسام", callback_data="view_categories"))
            bot.edit_message_text("عذراً، لا توجد منتجات في هذا القسم حالياً.", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        else:
            for p_id, name, price in products:
                btn_name = types.InlineKeyboardButton(f"📦 {name}", callback_data=f"prod_{p_id}")
                btn_price = types.InlineKeyboardButton(f"💎 {price} N", callback_data=f"prod_{p_id}")
                markup.add(btn_name, btn_price)

            markup.add(types.InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 | العودة للأقسام", callback_data="view_categories"))
            prod_list_text = (
                f"🛍️ ─── ✦ 𝒀𝒂𝒎𝒂𝒏𝒊 𝑷𝒓𝒐𝒅𝒖𝒄𝒕𝒔 ✦ ─── 🛍️\n"
                f"⚡ **قائمة المنتجات المتاحة للشراء:**"
            )
            bot.edit_message_text(prod_list_text, chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("prod_"):
        prod_id = int(call.data.split("prod_")[1])
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, details, category, media_type, media_id FROM products WHERE id = ?", (prod_id,))
        prod = cursor.fetchone()
        conn.close()

        if prod:
            p_id, name, price, details, category, media_type, media_id = prod
            caption = (
                f"╔════════════════════╗\n"
                f"📦 **𝑷𝒓𝒐𝒅𝒖𝒄𝒕:** {name}\n"
                f"👑 **𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆 𝑺𝒕𝒐𝒓𝒆**\n"
                f"╚════════════════════╝\n\n"
                f"📂 **القسم:** `{category}`\n"
                f"💎 **السعر:** `{price}` **نقطة**\n"
                f"📝 **التفاصيل والوصف:**\n{details}\n\n"
                f"❖ ─── ✦ ✨ ✦ ─── ❖"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(f"🛒 𝑩𝒖𝒚 𝑵𝒐𝒘 | شراء الآن ({price} نقطة)", callback_data=f"buy_{p_id}"))
            markup.add(types.InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 | العودة للمنتجات", callback_data="view_categories"))

            if media_type == "photo" and media_id:
                bot.send_photo(chat_id, media_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
            elif media_type == "video" and media_id:
                bot.send_video(chat_id, media_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
            elif media_type == "document" and media_id:
                bot.send_document(chat_id, media_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
            elif media_type == "audio" and media_id:
                bot.send_audio(chat_id, media_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
            elif media_type == "voice" and media_id:
                bot.send_voice(chat_id, media_id, reply_markup=markup)
                bot.send_message(chat_id, caption, parse_mode="Markdown")
            else:
                bot.edit_message_text(caption, chat_id=chat_id, message_id=msg_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data.startswith("buy_"):
        prod_id = int(call.data.split("buy_")[1])
        user = get_user(user_id)
        
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, details, media_type, media_id FROM products WHERE id = ?", (prod_id,))
        prod = cursor.fetchone()

        if not prod:
            bot.answer_callback_query(call.id, "عذراً، هذا المنتج غير متوفر.", show_alert=True)
            conn.close()
            return

        p_id, name, price, details, media_type, media_id = prod

        if user[2] < price:
            bot.answer_callback_query(call.id, f"❌ رصيدك غير كافٍ! تحتاج إلى {price} نقطة ولكن رصيدك {user[2]} نقطة.", show_alert=True)
            conn.close()
            return

        new_pts = user[2] - price
        cursor.execute("UPDATE users SET points = ? WHERE user_id = ?", (new_pts, user_id))
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO orders (user_id, product_id, product_name, price, date) VALUES (?, ?, ?, ?, ?)",
                       (user_id, p_id, name, price, now_str))

        cursor.execute("SELECT value FROM settings WHERE key = 'proof_channel'")
        proof_res = cursor.fetchone()
        
        conn.commit()
        conn.close()

        bot.answer_callback_query(call.id, "🎉 تم الشراء بنجاح من 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆!", show_alert=True)
        delivery_msg = (
            f"🎉 ─── ✦ 𝑺𝒖𝒄𝒄𝒆𝒔𝒔𝒇𝒖𝒍 𝑶𝒓𝒅𝒆𝒓 ✦ ─── 🎉\n"
            f"👑 **تمت عملية الشراء بنجاح من ﻳـﻤـﺎﻧـﻲ ﻣـﺎﺭﻛـﺔ!**\n\n"
            f"📦 **المنتج:** `{name}`\n"
            f"💰 **المبلغ المخصوم:** `{price}` **نقطة**\n\n"
            f"🔑 **محتوى السلعة / البيانات:**\n{details}\n\n"
            f"✨ **شكراً لثقتكم بمتجر 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆!** ✨"
        )
        
        if media_type == "photo" and media_id:
            bot.send_photo(chat_id, media_id, caption=delivery_msg, parse_mode="Markdown")
        elif media_type == "video" and media_id:
            bot.send_video(chat_id, media_id, caption=delivery_msg, parse_mode="Markdown")
        elif media_type == "document" and media_id:
            bot.send_document(chat_id, media_id, caption=delivery_msg, parse_mode="Markdown")
        elif media_type == "audio" and media_id:
            bot.send_audio(chat_id, media_id, caption=delivery_msg, parse_mode="Markdown")
        elif media_type == "voice" and media_id:
            bot.send_voice(chat_id, media_id)
            bot.send_message(chat_id, delivery_msg, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, delivery_msg, parse_mode="Markdown")

        if proof_res and proof_res[0]:
            proof_channel = proof_res[0]
            try:
                proof_text = (
                    f"🛍️ ─── ✦ 𝒀𝒂𝒎𝒂𝒏𝒊 𝑷𝒓𝒐𝒐𝒇𝒔 ✦ ─── 🛍️\n"
                    f"👑 **عملية شراء جديدة ناجحة!**\n\n"
                    f"👤 **المشتري:** [{user_id}](tg://user?id={user_id})\n"
                    f"📦 **المنتج:** {name}\n"
                    f"💰 **السعر:** {price} نقطة\n"
                    f"📅 **التاريخ:** `{now_str}`\n\n"
                    f"✨ **شكراً لثقتكم بـ 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆!**"
                )
                bot.send_message(proof_channel, proof_text, parse_mode="Markdown")
            except Exception:
                pass

        try:
            bot.send_message(ADMIN_ID, f"🔔 **عملية شراء جديدة في 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆:**\n👤 المستخدم: `{user_id}`\n📦 المنتج: {name}\n💰 السعر: {price} نقطة", parse_mode="Markdown")
        except:
            pass

    elif call.data == "admin_panel":
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "غير مصرح لك بدخول هذه اللوحة.", show_alert=True)
            return
        bot.edit_message_text("⚙️ **أهلاً بك في لوحة تحكم أدمن 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆:**", chat_id=chat_id, message_id=msg_id, reply_markup=admin_keyboard(), parse_mode="Markdown")

    elif call.data == "adm_stats":
        if user_id != ADMIN_ID: return
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        u_cnt = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM products")
        p_cnt = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*), SUM(price) FROM orders")
        o_res = cursor.fetchone()
        o_cnt = o_res[0] or 0
        o_sum = o_res[1] or 0
        conn.close()

        stats_msg = (
            f"📊 ─── ✦ 𝒀𝒂𝒎𝒂𝒏𝒊 𝑺𝒕𝒂𝒕𝒔 ✦ ─── 📊\n"
            f"👑 **إحصائيات متجر ﻳـﻤـﺎﻧـﻲ ﻣـﺎﺭﻛـﺔ:**\n\n"
            f"👥 **عدد المشتركين:** `{u_cnt}`\n"
            f"📦 **عدد المنتجات:** `{p_cnt}`\n"
            f"🛒 **عدد الطلبات الناجحة:** `{o_cnt}`\n"
            f"💰 **إجمالي النقاط المستهلكة:** `{o_sum}` **نقطة**"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 | الأدمن", callback_data="admin_panel"))
        bot.edit_message_text(stats_msg, chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "adm_force_sub":
        if user_id != ADMIN_ID: return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("➕ إضافة قناة", callback_data="adm_add_fsub"))
        markup.add(types.InlineKeyboardButton("🗑️ حذف قناة", callback_data="adm_del_fsub"))
        markup.add(types.InlineKeyboardButton("📋 عرض القنوات", callback_data="adm_list_fsub"))
        markup.add(types.InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 | الأدمن", callback_data="admin_panel"))
        bot.edit_message_text("📢 **إدارة قنوات الاشتراك الإجباري:**", chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "adm_add_fsub":
        if user_id != ADMIN_ID: return
        msg = bot.send_message(chat_id, "📢 **أرسل آيدي أو معرف القناة:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_add_fsub_id)

    elif call.data == "adm_del_fsub":
        if user_id != ADMIN_ID: return
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM force_channels")
        chans = cursor.fetchall()
        conn.close()

        markup = types.InlineKeyboardMarkup()
        for c_id, c_title in chans:
            markup.add(types.InlineKeyboardButton(f"❌ {c_title}", callback_data=f"delfchan_{c_id}"))
        markup.add(types.InlineKeyboardButton("🔙 العودة", callback_data="adm_force_sub"))
        bot.edit_message_text("🗑️ اختر القناة التي تريد حذفها من الاشتراك الإجباري:", chat_id=chat_id, message_id=msg_id, reply_markup=markup)

    elif call.data.startswith("delfchan_"):
        if user_id != ADMIN_ID: return
        c_db_id = int(call.data.split("delfchan_")[1])
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM force_channels WHERE id = ?", (c_db_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "تم حذف القناة بنجاح!", show_alert=True)
        bot.edit_message_text("✅ تم حذف قناة الاشتراك الإجباري بنجاح.", chat_id=chat_id, message_id=msg_id, reply_markup=admin_keyboard())

    elif call.data == "adm_list_fsub":
        if user_id != ADMIN_ID: return
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title, channel_id, channel_url FROM force_channels")
        chans = cursor.fetchall()
        conn.close()

        if not chans:
            txt = "لا توجد قنوات اشتراك إجباري مضافة حالياً."
        else:
            txt = "📢 **قنوات الاشتراك الإجباري المضافة:**\n\n"
            for t, cid, curl in chans:
                txt += f"🔹 **الاسم:** {t}\nالمعرف: `{cid}`\nالرابط: {curl}\n\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 | العودة", callback_data="adm_force_sub"))
        bot.edit_message_text(txt, chat_id=chat_id, message_id=msg_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "adm_proof_chan":
        if user_id != ADMIN_ID: return
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = 'proof_channel'")
        p_res = cursor.fetchone()
        conn.close()

        curr = p_res[0] if p_res else "غير معينة"

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("⚙️ تعيين / تغيير القناة", callback_data="adm_set_proof"))
        markup.add(types.InlineKeyboardButton("❌ إزالة القناة", callback_data="adm_rem_proof"))
        markup.add(types.InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 | الأدمن", callback_data="admin_panel"))

        bot.edit_message_text(f"📜 **إدارة قناة الإثباتات:**\n\nالقناة الحالية: `{curr}`", chat_id=chat_id, message_id=msg_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "adm_set_proof":
        if user_id != ADMIN_ID: return
        msg = bot.send_message(chat_id, "📜 أرسل آيدي أو معرف قناة الإثباتات:")
        bot.register_next_step_handler(msg, process_set_proof_channel)

    elif call.data == "adm_rem_proof":
        if user_id != ADMIN_ID: return
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM settings WHERE key = 'proof_channel'")
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "تم إزالة قناة الإثباتات بنجاح!", show_alert=True)
        bot.edit_message_text("✅ تم إزالة قناة الإثباتات.", chat_id=chat_id, message_id=msg_id, reply_markup=admin_keyboard())

    elif call.data == "adm_add_cat":
        if user_id != ADMIN_ID: return
        msg = bot.send_message(chat_id, "📁 أرسل اسم القسم الجديد الذي تريد إضافته:")
        bot.register_next_step_handler(msg, process_add_category)

    elif call.data == "adm_gen_card":
        if user_id != ADMIN_ID: return
        msg = bot.send_message(chat_id, "💳 أرسل الكود وعدد النقاط بالشكل التالي:\n`CODE123 100`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_gen_card)

    elif call.data == "adm_mod_pts":
        if user_id != ADMIN_ID: return
        msg = bot.send_message(chat_id, "💰 أرسل آيدي المستخدم وعدد النقاط بالشكل التالي:\n`123456789 50`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_mod_points)

    elif call.data == "adm_broadcast":
        if user_id != ADMIN_ID: return
        msg = bot.send_message(chat_id, "📢 أرسل نص الإذاعة التي تريد توجيهها لجميع المستخدمين:")
        bot.register_next_step_handler(msg, process_broadcast)

    elif call.data == "adm_add_prod":
        if user_id != ADMIN_ID: return
        msg = bot.send_message(chat_id, "➕ **أرسل اسم المنتج الجديد:**", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_add_prod_step1)

    elif call.data == "adm_del_prod":
        if user_id != ADMIN_ID: return
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM products")
        prods = cursor.fetchall()
        conn.close()

        markup = types.InlineKeyboardMarkup()
        for p_id, p_name in prods:
            markup.add(types.InlineKeyboardButton(f"❌ {p_name}", callback_data=f"delp_{p_id}"))
        markup.add(types.InlineKeyboardButton("🔙 𝑩𝒂𝒄𝒌 | الأدمن", callback_data="admin_panel"))
        bot.edit_message_text("🗑️ اختر المنتج الذي تريد حذفه:", chat_id=chat_id, message_id=msg_id, reply_markup=markup)

    elif call.data.startswith("delp_"):
        if user_id != ADMIN_ID: return
        p_id = int(call.data.split("delp_")[1])
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (p_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "تم حذف المنتج بنجاح!", show_alert=True)
        bot.edit_message_text("✅ تم حذف المنتج.", chat_id=chat_id, message_id=msg_id, reply_markup=admin_keyboard())

def process_add_fsub_id(message):
    if message.from_user.id != ADMIN_ID: return
    ch_id = message.text.strip()
    msg = bot.send_message(message.chat.id, "🔗 أرسل رابط القناة للمستخدمين:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_add_fsub_url, ch_id)

def process_add_fsub_url(message, ch_id):
    if message.from_user.id != ADMIN_ID: return
    ch_url = message.text.strip()
    msg = bot.send_message(message.chat.id, "📝 أرسل اسم القناة الرسمي:")
    bot.register_next_step_handler(msg, process_add_fsub_title, ch_id, ch_url)

def process_add_fsub_title(message, ch_id, ch_url):
    if message.from_user.id != ADMIN_ID: return
    ch_title = message.text.strip()
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO force_channels (channel_id, channel_url, title) VALUES (?, ?, ?)", (ch_id, ch_url, ch_title))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ **تم إضافة قناة الاشتراك الإجباري بنجاح!**\n\n📌 **الاسم الظاهر:** {ch_title}\n🆔 **المعرف/الآيدي:** `{ch_id}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أو القناة مضافة سابقاً: {e}")

def process_set_proof_channel(message):
    if message.from_user.id != ADMIN_ID: return
    ch_id = message.text.strip()
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('proof_channel', ?)", (ch_id,))
    conn.commit()
    conn.close()
    bot.reply_to(message, f"✅ **تم تعيين قناة الإثباتات بنجاح!**\n📜 القناة: `{ch_id}`", parse_mode="Markdown")

def process_card_recharge(message):
    code = message.text.strip()
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM cards WHERE code = ?", (code,))
    card = cursor.fetchone()

    if card:
        pts = card[0]
        cursor.execute("DELETE FROM cards WHERE code = ?", (code,))
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (pts, message.from_user.id))
        conn.commit()
        bot.reply_to(message, f"✅ **تم شحن حسابك بـ {pts} نقطة بنجاح من 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆!**", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ كود الشحن غير صحيح أو تم استخدامه سابقاً.")
    conn.close()

def process_add_category(message):
    if message.from_user.id != ADMIN_ID: return
    cat_name = message.text.strip()
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat_name,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ تم إضافة القسم `{cat_name}` بنجاح!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أو القسم موجود بالفعل: {e}")

def process_gen_card(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        code, pts = message.text.strip().split()
        pts = int(pts)
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO cards (code, points) VALUES (?, ?)", (code, pts))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ **تم إنشاء كود الشحن بنجاح:**\nالكود: `{code}`\nالنقاط: **{pts}**", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "❌ الصيغة خاطئة! أرسل الكود والنقاط بينهما مسافة.", parse_mode="Markdown")

def process_mod_points(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        target_id, pts = message.text.strip().split()
        target_id = int(target_id)
        pts = int(pts)
        add_points(target_id, pts)
        bot.reply_to(message, f"✅ تم تعديل نقاط المستخدم `{target_id}` بمقدار **{pts}** نقطة بنجاح!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "❌ الصيغة خاطئة! أرسل الآيدي ثم عدد النقاط.", parse_mode="Markdown")

def process_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    success = 0
    fail = 0
    for u in users:
        try:
            bot.send_message(u[0], f"📢 **إشعار هام من 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆:**\n\n{text}", parse_mode="Markdown")
            success += 1
        except:
            fail += 1

    bot.reply_to(message, f"📊 **اكتملت الإذاعة:**\n✅ تم الإرسال بنجاح إلى: **{success}**\n❌ فشل الإرسال إلى: **{fail}**", parse_mode="Markdown")

def process_add_prod_step1(message):
    if message.from_user.id != ADMIN_ID: return
    p_name = message.text.strip()
    msg = bot.send_message(message.chat.id, f"💰 أدخل سعر المنتج ({p_name}) بالنقاط:")
    bot.register_next_step_handler(msg, process_add_prod_step2, p_name)

def process_add_prod_step2(message, p_name):
    if message.from_user.id != ADMIN_ID: return
    try:
        p_price = int(message.text.strip())
        msg = bot.send_message(message.chat.id, "📝 أدخل تفاصيل ومحتوى المنتج:")
        bot.register_next_step_handler(msg, process_add_prod_step3, p_name, p_price)
    except:
        bot.reply_to(message, "❌ السعر يجب أن يكون رقماً صحيحاً.")

def process_add_prod_step3(message, p_name, p_price):
    if message.from_user.id != ADMIN_ID: return
    p_details = message.text
    msg = bot.send_message(message.chat.id, "📁 أدخل اسم القسم الخاص بالمنتج:")
    bot.register_next_step_handler(msg, process_add_prod_step4, p_name, p_price, p_details)

def process_add_prod_step4(message, p_name, p_price, p_details):
    if message.from_user.id != ADMIN_ID: return
    p_cat = message.text.strip()
    msg = bot.send_message(
        message.chat.id,
        "📎 **أرسل الآن المرفق الخاص بالسلعة (فيديو، ملف/مستند، صورة، صوت) أو أرسل كلمة 'لا' إذا كانت السلعة نصية فقط:**",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_add_prod_step5, p_name, p_price, p_details, p_cat)

def process_add_prod_step5(message, p_name, p_price, p_details, p_cat):
    if message.from_user.id != ADMIN_ID: return

    media_type = 'text'
    media_id = ''

    if message.photo:
        media_type = 'photo'
        media_id = message.photo[-1].file_id
    elif message.video:
        media_type = 'video'
        media_id = message.video.file_id
    elif message.document:
        media_type = 'document'
        media_id = message.document.file_id
    elif message.audio:
        media_type = 'audio'
        media_id = message.audio.file_id
    elif message.voice:
        media_type = 'voice'
        media_id = message.voice.file_id

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (p_cat,))
    cursor.execute(
        "INSERT INTO products (name, price, details, category, media_type, media_id) VALUES (?, ?, ?, ?, ?, ?)",
        (p_name, p_price, p_details, p_cat, media_type, media_id)
    )
    conn.commit()
    conn.close()

    bot.send_message(
        message.chat.id,
        f"✅ **تم إضافة المنتج بنجاح إلى 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆!**\n\n📦 **المنتج:** {p_name}\n💰 **السعر:** {p_price}\n📁 **القسم:** {p_cat}\n📎 **نوع المرفق:** {media_type}",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("🤖 بوت 𝒀𝒂𝒎𝒂𝒏𝒊 𝑴𝒂𝒓𝒌𝒆 يعمل الآن...")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)