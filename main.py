import telebot
import sqlite3
from datetime import datetime
import csv
import io
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot('7184160223:AAHPqgTuX23kh7JJnkWasGQLSIi0oGYZnXk')
ADMIN_ID = 1671143755
name = None
#@bot.message_handler(commands=['myid'])
#def my_id(message):
#    bot.send_message(message.chat.id, f"Sizning Telegram ID: {message.from_user.id}")
def recreate_user_table():
    conn = sqlite3.connect('cherry.sql')
    cur = conn.cursor()

    cur.execute('DROP TABLE IF EXISTS user')
    cur.execute('''CREATE TABLE user (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, pass TEXT, telegram_id INTEGER, username TEXT,last_login TEXT )''')
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Таблица user успешно пересоздана.")


@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('cherry.sql')
    cur = conn.cursor()
    #cur.execute('DROP TABLE cherry.sql')
    cur.execute('CREATE TABLE IF NOT EXISTS user(id int auto_increment primary key, name varchar(50), pass varchar(50), telegram_id int, username varchar(50), last_login varchar(50))')
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, "Salom, Hozir sizni royxatdan o'tkazamiz! Ismingizni kiriting")
    bot.register_next_step_handler(message, user_name)


def user_name(message):
    global name
    name = message.text.strip()
    bot.send_message(message.chat.id, "Parol kiriting")
    bot.register_next_step_handler(message, user_pass)



def user_pass(message):
    password = message.text.strip()
    conn = sqlite3.connect('cherry.sql')
    cur = conn.cursor()

    last_login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"

    # Проверяем, есть ли уже пользователь
    cur.execute("SELECT * FROM user WHERE name = ?", (name,))
    existing_user = cur.fetchone()
    # Tugmalar (inline)
    menu = InlineKeyboardMarkup()
    menu.add(
        InlineKeyboardButton("🧸 O'yinchoqlar", url="https://t.me/+oD2drSIYhgJiNTc6"),
        InlineKeyboardButton("📚 Konstovar", url="https://t.me/+CPV5sTPqLNBjYjAy")
    )
    if existing_user:
        cur.execute("UPDATE user SET last_login = ? WHERE name = ?", (last_login_time, name))
        conn.commit()
        bot.send_message(message.chat.id, "❗ Siz allaqachon ro'yxatdan o'tgansiz.", reply_markup=menu)
    else:
        cur.execute("INSERT INTO user (name, pass, telegram_id, username, last_login) VALUES (?, ?, ?, ?, ?)",(name, password, user_id, username, last_login_time))
        conn.commit()

        # Получаем имя для обращения
        tg_name = message.from_user.first_name or message.from_user.username or "hurmatli foydalanuvchi"

        # Приветственное сообщение
        welcome_msg = (
            f"Assalomu aleykum {tg_name}, bizning onlayn marketimizni tanlaganingiz uchun rahmat!\n"
            f"Bizda hamma tovarlarimiz arzon va sifatli."
        )
        bot.send_message(message.chat.id, welcome_msg)

        bot.send_message(message.chat.id, "✅ Siz muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=menu)

    cur.close()
    conn.close()


    #markub = telebot.types.InlineKeyboardMarkup()
    #markub.add(telebot.types.InlineKeyboardButton("Foydalanuvchilar ro'yhati", callback_data='users'))
    #bot.send_message(message.chat.id, "Siz ro'yhatdan o'tingiz", reply_markup=markub)
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    conn = sqlite3.connect('cherry.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM user')
    users = cur.fetchall()
    info = ''
    for el in users:
        info += f'Ism: {el[1]}, Parol: {el[2]}\n'
    cur.close()
    conn.close()
    bot.send_message(call.message.chat.id, info)
@bot.message_handler(commands=['clear'])
def clear(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Sizda bu buyruqni bajarishga ruxsat yo'q.")
        return

    conn = sqlite3.connect('cherry.sql')
    cur = conn.cursor()
    cur.execute('DELETE FROM user')
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, "🧹 Baza tozalandi. Foydalanuvchilar o'chirildi.")

@bot.message_handler(commands=['users'])
def show_users_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Bu buyruq faqat admin uchun.")
        return

    conn = sqlite3.connect('cherry.sql')
    cur = conn.cursor()
    cur.execute('SELECT name, pass, telegram_id, username, last_login FROM user')
    users = cur.fetchall()
    info = '📄 Barcha foydalanuvchilar:\n\n'
    for name, password, telegram_id, username, last_login in users:
        user_ref = f"@{username}" if username != "NoUsername" else f"(ID: {telegram_id})"
        login_info = last_login if last_login else "Hech qachon"
        info += f'👤 Ism: {name}, 🔑 Parol: {password}, 📱 Telegram: {user_ref}, 🕒 Oxirgi kirish: {login_info}\n'
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, info)
@bot.message_handler(commands=['export'])
def export_users_to_excel(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Bu buyruq faqat admin uchun.")
        return

    conn = sqlite3.connect('cherry.sql')
    cur = conn.cursor()
    cur.execute('SELECT name, pass, telegram_id, username, last_login FROM user')
    users = cur.fetchall()
    cur.close()
    conn.close()

    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ism', 'Parol', 'Telegram ID', 'Username', 'Oxirgi kirish'])

    for user in users:
        writer.writerow(user)

    output.seek(0)
    csv_file = io.BytesIO()
    csv_file.write(output.getvalue().encode())
    csv_file.seek(0)
    output.close()

    bot.send_document(message.chat.id, csv_file, visible_file_name="foydalanuvchilar.csv")
@bot.message_handler(commands=['search'])
def search_user_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Bu buyruq faqat admin uchun.")
        return

    bot.send_message(message.chat.id, "🔍 Qidirish uchun ism yoki username kiriting:")
    bot.register_next_step_handler(message, process_search)


def process_search(message):
    keyword = message.text.strip().lower()
    conn = sqlite3.connect('cherry.sql')
    cur = conn.cursor()

    cur.execute("SELECT name, pass, telegram_id, username, last_login FROM user")
    users = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for name, password, telegram_id, username, last_login in users:
        if keyword in name.lower() or (username and keyword in username.lower()):
            user_ref = f"@{username}" if username != "NoUsername" else f"(ID: {telegram_id})"
            login_info = last_login if last_login else "Hech qachon"
            results.append(
                f'👤 Ism: {name}, 🔑 Parol: {password}, 📱 Telegram: {user_ref}, 🕒 Oxirgi kirish: {login_info}'
            )

    if results:
        response = "🔎 Qidiruv natijalari:\n\n" + "\n".join(results)
    else:
        response = "❌ Hech qanday mos foydalanuvchi topilmadi."

    bot.send_message(message.chat.id, response)


#sqlite jadvalga yengi narsa qo'shish kerak bo'lganda
#recreate_user_table()
bot.remove_webhook()
bot.polling(none_stop=True)
