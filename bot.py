import telebot
import requests
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8562526168:AAHjZHJgZ-9_Ykz7N6U347q1QbfVJhUqQMw"
ADMIN_ID = 5857668954

bot = telebot.TeleBot(TOKEN)

===== الإعدادات =====

P2P_DOLLAR = 49.7
USD_COMMISSION = 0.1
TON_COMMISSION = 0.5

users_data = {}

===== تحميل الأرباح =====

if os.path.exists("profit.json"):
with open("profit.json", "r") as f:
TOTAL_PROFIT = json.load(f)["total_profit"]
else:
TOTAL_PROFIT = 0

def save_profit():
with open("profit.json", "w") as f:
json.dump({"total_profit": TOTAL_PROFIT}, f)

===== جلب سعر TON =====

def get_ton_price():
url = "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd"
r = requests.get(url)
data = r.json()
return data["the-open-network"]["usd"]

===== أمر الشراء =====

@bot.message_handler(commands=['buy'])
def buy(message):
ton_usdt = get_ton_price()

final_usdt_price = P2P_DOLLAR + USD_COMMISSION
ton_price_egp = (ton_usdt * P2P_DOLLAR) + TON_COMMISSION

markup = InlineKeyboardMarkup()
markup.add(
InlineKeyboardButton("🟣 شراء TON", callback_data="ton"),
InlineKeyboardButton("💵 شراء USDT", callback_data="usdt")
)

bot.send_message(
message.chat.id,
f"📊 الأسعار الحالية:\n\n"
f"💵 USDT = {final_usdt_price:.2f} جنيه\n"
f"🟣 TON = {ton_price_egp:.2f} جنيه\n\n"
f"اختر العملة 👇",
reply_markup=markup
)

===== اختيار العملة =====

@bot.callback_query_handler(func=lambda c: c.data in ["ton", "usdt"])
def choose_currency(call):
users_data[call.message.chat.id] = {"currency": call.data}
bot.send_message(call.message.chat.id, "💰 اكتب المبلغ بالجنيه:")

===== إدخال المبلغ =====

@bot.message_handler(func=lambda m: m.chat.id in users_data and "amount" not in users_data[m.chat.id])
def get_amount(message):
user_id = message.chat.id

try:
amount = float(message.text)
except:
bot.send_message(user_id, "❌ اكتب رقم صحيح.")
return

currency = users_data[user_id]["currency"]
ton_usdt = get_ton_price()

if currency == "usdt":
price = P2P_DOLLAR + USD_COMMISSION
else:
price = (ton_usdt * P2P_DOLLAR) + TON_COMMISSION

amount_received = amount / price

users_data[user_id]["amount"] = amount
users_data[user_id]["amount_received"] = amount_received

bot.send_message(
user_id,
f"📦 ستحصل على: {amount_received:.4f} {currency.upper()}\n\n"
f"🏦 أرسل عنوان محفظتك:"
)

===== إدخال المحفظة =====

@bot.message_handler(func=lambda m: m.chat.id in users_data and "wallet" not in users_data[m.chat.id])
def wallet(message):
user_id = message.chat.id
wallet_address = message.text.strip()

if not wallet_address.startswith("UQ") or len(wallet_address) < 40:
bot.send_message(user_id, "❌ عنوان TON غير صحيح.")
return

users_data[user_id]["wallet"] = wallet_address

paid_markup = InlineKeyboardMarkup()
paid_markup.add(InlineKeyboardButton("✅ تم الدفع", callback_data="paid"))

bot.send_message(
user_id,
"💳 حول المبلغ إلى:\n📲 01020143354",
reply_markup=paid_markup
)

===== تم الدفع =====

@bot.callback_query_handler(func=lambda c: c.data=="paid")
def paid(call):
user_id = call.message.chat.id
data = users_data[user_id]

admin_markup = InlineKeyboardMarkup()
admin_markup.add(
InlineKeyboardButton("✅ قبول", callback_data=f"approve_{user_id}"),
InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")
)

bot.send_message(
ADMIN_ID,
f"🚨 طلب جديد\n"
f"👤 {user_id}\n"
f"💰 {data['amount']} جنيه\n"
f"📦 {data['amount_received']:.4f} {data['currency'].upper()}\n"
f"🏦 {data['wallet']}",
reply_markup=admin_markup
)

bot.send_message(user_id, "⏳ جاري مراجعة الدفع...")

===== قبول =====

@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_"))
def approve(call):
global TOTAL_PROFIT

user_id = int(call.data.split("_")[1])
data = users_data[user_id]

ton_usdt = get_ton_price()

if data["currency"] == "usdt":
cost = data["amount_received"] * P2P_DOLLAR
else:
cost = data["amount_received"] * (ton_usdt * P2P_DOLLAR)

profit = data["amount"] - cost
TOTAL_PROFIT += profit
save_profit()

bot.send_message(
user_id,
"✅ تم استلام عملاتك، يرجى التأكد من محفظتك.\n\nمع تحيات @D_4_5 💎"
)

bot.send_message(
ADMIN_ID,
f"📈 ربح العملية: {profit:.2f} جنيه\n"
f"💰 إجمالي أرباحك: {TOTAL_PROFIT:.2f} جنيه"
)

===== رفض =====

@bot.callback_query_handler(func=lambda c: c.data.startswith("reject_"))
def reject(call):
user_id = int(call.data.split("_")[1])
bot.send_message(user_id, "❌ تم رفض الطلب الخاص بك.")

===== عرض الأرباح =====

@bot.message_handler(commands=['profit'])
def show_profit(message):
if message.chat.id == ADMIN_ID:
bot.send_message(
message.chat.id,
f"💰 إجمالي أرباحك:\n{TOTAL_PROFIT:.2f} جنيه"
)

bot.polling()
