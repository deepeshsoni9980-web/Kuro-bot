import telebot
from telebot import types
import json
import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8967781131
UPI_ID = "9782253547-2@ybl"

bot = telebot.TeleBot(TOKEN)

# --- PRODUCT -> PLANS ---
PRODUCTS = {
    "Kuro": {
        "kuro 7days": 300,
        "kuro 1 Month": 999,
    },
    "YouTube Premium": {
        "YouTube 1 Month": 499,
        "YouTube 3 Month": 1299,
    },
    "Netflix": {
        "Netflix 1 Month": 199,
        "Netflix 3 Month": 499,
    },
}

# --- KEYS STOCK ---
KEYS = {}
if os.path.exists("keys.json"):
    with open("keys.json") as f:
        KEYS = json.load(f)
for prod in PRODUCTS:
    for plan in PRODUCTS[prod]:
        if plan not in KEYS:
            KEYS[plan] = []

balances = {}
if os.path.exists("bal.json"):
    with open("bal.json") as f:
        balances = json.load(f)

waiting_support = set()
waiting_funds = set()

def save_all():
    with open("keys.json", "w") as f:
        json.dump(KEYS, f)
    with open("bal.json", "w") as f:
        json.dump(balances, f)

def get_bal(uid):
    return balances.get(str(uid), 0)

def get_price(plan_name):
    for prod in PRODUCTS:
        if plan_name in PRODUCTS[prod]:
            return PRODUCTS[prod][plan_name]
    return 0

def main_menu():
    m = types.InlineKeyboardMarkup()
    m.add(types.InlineKeyboardButton("Buy Now", callback_data="buy"))
    m.add(types.InlineKeyboardButton("Add Funds", callback_data="addfunds"))
    m.add(types.InlineKeyboardButton("Price List", callback_data="pricelist"))
    m.add(types.InlineKeyboardButton("Check Balance", callback_data="balance"))
    m.add(types.InlineKeyboardButton("Support", callback_data="support"))
    return m

@bot.message_handler(commands=['start'])
def start(message):
    txt = "Hello! Welcome to Kuro Official\n"
    txt += "Balance: Rs." + str(get_bal(message.from_user.id))
    bot.send_message(message.chat.id, txt, reply_markup=main_menu())

# --- ADMIN COMMANDS (sabse upar taaki ye pehle chale) ---
@bot.message_handler(commands=['addkey', 'addbal', 'stock', 'reply'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Tu Admin nahi hai!")
        return
    try:
        if message.text.startswith("/addkey"):
            parts = message.text.split()
            key = parts[-1]
            plan = " ".join(parts[1:-1])
            if plan not in KEYS:
                KEYS[plan] = []
            KEYS[plan].append(key)
            save_all()
            bot.reply_to(message, f"Key add ho gayi!\n{plan} me ab {len(KEYS[plan])} keys hai.")

        elif message.text.startswith("/addbal"):
            parts = message.text.split()
            tid = parts[1]
            amt = int(parts[2])
            balances[tid] = balances.get(tid, 0) + amt
            save_all()
            bot.reply_to(message, f"Rs.{amt} add ho gaya.")
            bot.send_message(int(tid), f"Admin ne Rs.{amt} add kiya! Balance: Rs.{balances[tid]}")

        elif message.text.startswith("/stock"):
            txt = "Stock:\n\n"
            for plan in KEYS:
                txt += f"{plan} : {len(KEYS[plan])} keys\n"
            bot.reply_to(message, txt)

        elif message.text.startswith("/reply"):
            parts = message.text.split(" ", 2)
            tid = parts[1]
            msg = parts[2]
            bot.send_message(int(tid), "Admin ka Jawab:\n" + msg)
            bot.reply_to(message, "Jawab bhej diya!")
    except:
        bot.reply_to(message, "Galat format! Example:\n/addkey kuro 7days KEY123\n/addbal 123456 500\n/reply 123456 hello")

# --- BUTTONS ---
@bot.callback_query_handler(func=lambda c: True)
def handle(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    bal = get_bal(uid)
    data = call.data

    # STEP 1 - SIRF PRODUCT
    if data == "buy":
        m = types.InlineKeyboardMarkup()
        for prod in PRODUCTS:
            m.add(types.InlineKeyboardButton(prod, callback_data="prod_" + prod))
        m.add(types.InlineKeyboardButton("Back", callback_data="back"))
        bot.send_message(cid, "Product chuno:", reply_markup=m)

    # STEP 2 - PRODUCT PE CLICK -> PLANS
    elif data.startswith("prod_"):
        prod = data.replace("prod_", "")
        m = types.InlineKeyboardMarkup()
        for plan, price in PRODUCTS[prod].items():
            stock = len(KEYS.get(plan, []))
            txt = f"{plan} - Rs.{price} | Stock: {stock}"
            m.add(types.InlineKeyboardButton(txt, callback_data="plan_" + plan))
        m.add(types.InlineKeyboardButton("Back", callback_data="buy"))
        bot.send_message(cid, f"{prod} ke Plans:", reply_markup=m)

    # STEP 3 - PLAN PE CLICK -> CONFIRM
    elif data.startswith("plan_"):
        plan = data.replace("plan_", "")
        price = get_price(plan)
        stock = len(KEYS.get(plan, []))
        if stock <= 0:
            bot.send_message(cid, "Out of Stock hai!")
            return
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("CONFIRM - Buy Karo", callback_data="confirm_" + plan))
        m.add(types.InlineKeyboardButton("Back", callback_data="buy"))
        txt = f"Plan: {plan}\nPrice: Rs.{price}\nTera Balance: Rs.{bal}\nStock: {stock}"
        bot.send_message(cid, txt, reply_markup=m)

    # STEP 4 - CONFIRM -> BALANCE KATE + KEY
    elif data.startswith("confirm_"):
        plan = data.replace("confirm_", "")
        price = get_price(plan)
        if len(KEYS.get(plan, [])) <= 0:
            bot.send_message(cid, "Stock khatam ho gaya!")
            return
        if bal < price:
            bot.send_message(cid, f"Balance kam hai! Bal: Rs.{bal} Chahiye: Rs.{price}")
            return
        balances[str(uid)] = bal - price
        key = KEYS[plan].pop(0)
        save_all()
        txt = "Order Done!\n\n"
        txt += "Plan: " + plan + "\n"
        txt += "Teri Key: " + key + "\n"
        txt += "Bacha Balance: Rs." + str(balances[str(uid)])
        bot.send_message(cid, txt)
        bot.send_message(ADMIN_ID, f"NEW ORDER\nUser: {uid}\nPlan: {plan}\nKey: {key}")

    # --- ADD FUNDS -> AMOUNT PUCHEGA ---
    elif data == "addfunds":
        waiting_funds.add(uid)
        bot.send_message(cid, "Kitna Add karna hai? Amount likh ke bhejo.\n\nExample: 500")

    elif data == "pricelist":
        txt = "Price List:\n\n"
        for prod in PRODUCTS:
            txt += prod + ":\n"
            for plan, price in PRODUCTS[prod].items():
                txt += f"  {plan} - Rs.{price} | Stock: {len(KEYS.get(plan,[]))}\n"
        bot.send_message(cid, txt)

    elif data == "balance":
        bot.send_message(cid, "Balance: Rs." + str(bal))

    elif data == "support":
        waiting_support.add(uid)
        bot.send_message(cid, "Support: Apni problem yaha likh ke bhejo.\nAdmin jawab dega.")

    elif data == "back":
        bot.send_message(cid, "Welcome Back!", reply_markup=main_menu())

# --- TEXT / PHOTO (QR + SUPPORT) ---
@bot.message_handler(func=lambda m: m.text is None or not m.text.startswith('/'), content_types=['text', 'photo'])
def all_msg(message):
    uid = message.from_user.id

    # 1. QR WALA - HAR BAAR NAYA QR
    if uid in waiting_funds:
        if message.text and message.text.isdigit():
            waiting_funds.remove(uid)
            amt = message.text
            upi_link = f"upi://pay?pa={UPI_ID}&pn=Kuro%20Official&am={amt}&cu=INR"
            qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=" + upi_link
            txt = f"Add Funds - Rs.{amt}\n\n"
            txt += f"1. Is QR pe Rs.{amt} payment karo\n"
            txt += f"UPI: {UPI_ID}\n"
            txt += "2. Screenshot Support pe bhejo\n"
            bot.send_photo(message.chat.id, qr_url, caption=txt)
        else:
            bot.send_message(uid, "Sirf number likho, jaise: 500")
        return

    # 2. SUPPORT WALA
    if uid in waiting_support and uid != ADMIN_ID:
        waiting_support.remove(uid)
        txt = f"NEW SUPPORT MSG\nUser: {message.from_user.first_name} ({uid})\n\n"
        if message.text:
            txt += message.text
            bot.send_message(ADMIN_ID, txt)
        else:
            bot.send_message(ADMIN_ID, txt)
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.send_message(uid, "Tera msg Admin ko bhej diya!")
        return

print("Bot chal raha hai...")
bot.polling()
