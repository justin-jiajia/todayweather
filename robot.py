import logging
from json import loads
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, Updater, \
    CallbackContext, CommandHandler, CallbackQueryHandler
from requests import get
from os import path, environ

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if path.exists("config.json"):
    with open("config.json") as f:
        config = loads(f.read())
else:
    config = environ

USEAGE = "使用说明\n/setcity修改城市\n/nowweather 查看当前天气\n更多功能，敬请期待！"
waiting = {}
city = {}


def get_w_str(update: Update):
    if not city.get(update.effective_chat.id):
        return "你还没有设置城市，请先用 /setcity 设置城市~"
    jj = get("https://devapi.qweather.com/v7/weather/now",
             params={'key': config["qw_token"], "location": city.get(update.effective_chat.id)}).json()
    if jj['code'] != "200":
        return "出错了，请稍后再试！"
    now = jj["now"]
    return f"""
==========================
                           {now["text"]}
数据观测时间 | {now["obsTime"].replace("T", " ").replace("+08:00", "")}
温度                 | {now["temp"]}
体感温度         | {now["feelsLike"]}
风向                 | {now["windDir"]}
风速                 | {now["windSpeed"]}公里/时
相对湿度         | {now["humidity"]}%
本小时降雨量 | {now["precip"]}毫米
大气压强         | {now["pressure"]}百帕
能见度             | {now["vis"]}公里
==========================
    """


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="欢迎使用嘉嘉的天气机器人~\n" + USEAGE)


async def setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting[update.effective_chat.id] = True
    await context.bot.send_message(chat_id=update.effective_chat.id, text="请输入城市名：")


async def choose_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not waiting.get(update.effective_chat.id, False):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="不支持的命令\n" + USEAGE)
        return
    city_nq = update.message.text
    jj = get('https://geoapi.qweather.com/v2/city/lookup',
             params={'key': config["qw_token"], "location": city_nq}).json()
    if jj['code'] != "200":
        await context.bot.send_message(chat_id=update.effective_chat.id, text="城市不正确，请再试一次~")
        return
    waiting[update.effective_chat.id] = False
    keyboard = []
    for i in jj["location"]:
        keyboard.append([InlineKeyboardButton(i["adm1"] + i["name"], callback_data=i["id"])])
    keyboard.append([InlineKeyboardButton("返回", callback_data=0)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("哪个城市？", reply_markup=reply_markup)


async def nowweather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=get_w_str(update))


async def city_choose_keyboard_callback(update: Update, context: CallbackContext):  # 4
    query = update.callback_query
    await query.answer()
    city[update.effective_chat.id] = query.data
    await query.edit_message_text(text="您的选择已经保存！")


if __name__ == '__main__':
    application = ApplicationBuilder().token(config["tg_token"]).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    nw_handler = CommandHandler('nowweather', nowweather)
    application.add_handler(nw_handler)

    sc_handler = CommandHandler('setcity', setcity)
    application.add_handler(sc_handler)

    city_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), choose_city)
    application.add_handler(city_handler)

    application.add_handler(CallbackQueryHandler(city_choose_keyboard_callback))

    application.run_polling()
