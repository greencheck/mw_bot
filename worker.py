#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import flask
import mysql.connector
import telebot
from telebot import apihelper, types

import config
import constants
import dbworker
import logging


# Наш вебхук-сервер
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            # Эта функция обеспечивает проверку входящего сообщения
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)


token = '772417845:AAG-n9TZ916OZFnIGIhlNxQtM1HEYcri2iw'
# apihelper.proxy = {'https': 'https://korben7dallas:dokepasy@154.127.61.72:8080'}
bot = telebot.TeleBot(token)
conn = mysql.connector.connect(host=constants.DB_HOST,
                               user=constants.DB_USER,
                               passwd=constants.DB_PASS,
                               db=constants.DB_NAME)
cursor = conn.cursor()

GROUP_ID = -1001457202594

WEBHOOK_HOST = '<ip/host where the bot is running>'
WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (token)

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(token)

app = flask.Flask(__name__)


# Empty webserver index, return nothing, just http 200
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


def start_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton(constants.deal_msg)
    itembtn2 = types.KeyboardButton(constants.tour_msg)
    itembtn3 = types.KeyboardButton(constants.balance)
    itembtn4 = types.KeyboardButton(constants.faq)
    itembtn5 = types.KeyboardButton(constants.in_chat)
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5)
    return markup

def reset_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=1)
    itembtn = types.KeyboardButton(constants.returned)
    markup.add(itembtn)
    return markup

def inline_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton(text=constants.post_btn, url="t.me/modelways_bot")
    markup.add(btn1)
    return markup

def inline_private_markup():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text=constants.returned, url="t.me/joinchat/OPvP81bbJaK1zwRvlDLg-g")
    markup.add(btn1)
    return markup


mk = types.ReplyKeyboardRemove()


@bot.message_handler(commands=["getID"])
def start_msg(message):
    bot.send_message(message.chat.id, str(bot.get_me()))


@bot.message_handler(commands=["start"], func=lambda message: message.chat.type == 'private')
def start_msg(message):
    if not inUsers(message.from_user.id):
        addNewUser(message.from_user.id)

    bot.send_message(message.chat.id, constants.hello_message, reply_markup=start_markup())


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.returned)
def reset_msg(message):
    dbworker.set_state(message.chat.id, config.States.S_START.value)
    bot.send_message(message.chat.id, "Главное меню", reply_markup=start_markup())


def getStrFailDeal(telegram_id):
    balance = getBalance(telegram_id)
    res = (constants.msg_cost_3 + constants.msg_on_balance + str(balance) +
           constants.msg_not_enough_for_post + constants.offer)
    return res


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.deal_msg)
def post_msg(message):
    state = dbworker.get_current_state(message.chat.id)
    balance = getBalance(message.from_user.id)
    if balance < 3:
        bot.send_message(message.chat.id, getStrFailDeal(message.from_user.id))
    else:
        if state == config.States.S_ENTER_POST.value:
            bot.send_message(message.chat.id, constants.msg_cost_3 +
                             constants.msg_enter_text, reply_markup=reset_markup())
        else:
            bot.send_message(message.chat.id, constants.msg_cost_3 +
                             constants.msg_enter_text, reply_markup=reset_markup())
            dbworker.set_state(message.chat.id, config.States.S_ENTER_POST.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ENTER_POST.value)
def user_entering_post_text(message):
    try:
        bot.send_message(GROUP_ID, message.text, reply_markup=mk)
        setBalance(message.from_user.id, (getBalance(message.from_user.id) - 3))
        dbworker.set_state(message.chat.id, config.States.S_START.value)
        bot.send_message(message.chat.id, constants.offer_success)
    except Exception as ex:
        print(ex)


def getStrFailTour(telegram_id):
    balance = getBalance(telegram_id)
    res = (constants.msg_cost_5 + constants.msg_on_balance + str(balance) +
           constants.msg_not_enough_for_post + constants.tour)
    return res


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.tour_msg)
def tour_msg(message):
    state = dbworker.get_current_state(message.chat.id)
    balance = getBalance(message.from_user.id)
    if balance < 5:
        bot.send_message(message.chat.id, getStrFailTour(message.from_user.id))
    else:
        if state == config.States.S_ENTER_TOUR.value:
            bot.send_message(message.chat.id, constants.msg_cost_5 +
                             constants.msg_enter_text, reply_markup=reset_markup())
        else:
            bot.send_message(message.chat.id, constants.msg_cost_5 +
                             constants.msg_enter_text, reply_markup=reset_markup())
            dbworker.set_state(message.chat.id, config.States.S_ENTER_TOUR.value)


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_ENTER_TOUR.value)
def user_entering_tour_text(message):
    try:
        bot.send_message(GROUP_ID, message.text, reply_markup=mk)
        setBalance(message.from_user.id, (getBalance(message.from_user.id) - 5))
        dbworker.set_state(message.chat.id, config.States.S_START.value)
        bot.send_message(message.chat.id, constants.tour_success)
    except Exception as ex:
        print(ex)


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.balance)
def balance_msg(message):
    print("Balance Button")
    balance = getBalance(message.from_user.id)
    bot.send_message(message.chat.id, constants.msg_get_balance + str(balance) + constants.msg_invited)


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.faq)
def faq_msg(message):
    print("FAQ Button")
    bot.send_message(message.chat.id, "/start - В начало.")

@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.in_chat)
def in_chat_msg(message):
    bot.send_message(message.chat.id, constants.back_to_chat_btn, reply_markup=inline_private_markup())



def get_admin_ids(bot, chat_id):
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]


def first_last_name_checker(first_name, last_name):
    if last_name is None:
        return str(first_name)
    else:
        return str(first_name + " " + last_name)


def inUsers(id_telegram):
    cursor.execute('SELECT * FROM users WHERE id_telegram=%s', (id_telegram,))
    entry = cursor.fetchone()
    if entry is None:
        return False
    else:
        return True


def inInviteList(from_id, new_id, group_id):
    cursor.execute('SELECT * FROM invite_list WHERE '
                   'from_user_id=%s and new_chat_member_id=%s and group_id=%s',
                   (from_id, new_id, group_id))
    entry = cursor.fetchone()
    if entry is None:
        return False
    else:
        return True


def addNewUser(id_telegram):
    cursor.execute("INSERT INTO users (id_telegram) VALUES (%s)", (id_telegram,))
    conn.commit()

def addNewInviteListEntry(from_id, new_id, group_id):
    cursor.execute("INSERT INTO invite_list (from_user_id, new_chat_member_id, group_id)"
                   " VALUES (%s, %s, %s)",
                   (from_id, new_id, group_id))
    conn.commit()


def incrementSuccessInvited(id_telegram):
    cursor.execute('UPDATE users SET count_inv=count_inv+1, balance=balance+1 WHERE id_telegram=%s', (id_telegram,))
    conn.commit()


def getCountInv(id_telegram):
    cursor.execute('SELECT count_inv FROM users WHERE id_telegram=%s', (id_telegram,))
    entry = cursor.fetchone()
    return entry[0]


def getBalance(id_telegram):
    cursor.execute('SELECT balance FROM users WHERE id_telegram=%s', (id_telegram,))
    entry = cursor.fetchone()
    return entry[0]


def setBalance(id_telegram, new_balance):
    cursor.execute('UPDATE users SET balance=%s WHERE id_telegram=%s', (new_balance, id_telegram))
    conn.commit()


@bot.message_handler(func=lambda message: message.chat.type == 'supergroup')
def check_message(message):
    admin_list = get_admin_ids(bot, message.chat.id)
    if admin_list.count(message.from_user.id):
        print("Admin send message!")
    else:
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        msg = bot.send_message(message.chat.id, constants.post_warning, reply_markup=inline_markup())
        time.sleep(180)
        bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)


@bot.message_handler(content_types=['new_chat_members'])
def inviter(message):
    if message.new_chat_member.first_name == message.from_user.first_name:
        print("Человек вступил по ссылке.")
        if inUsers(message.from_user.id):
            print("in Group")
        else:
            addNewUser(message.from_user.id)
    else:
        print("Человек был приглашен другим человеком.")
        if inUsers(message.new_chat_member.id):
            print("(New) User in Group!")
        else:
            addNewUser(message.new_chat_member.id)
            addNewInviteListEntry(message.from_user.id, message.new_chat_member.id, message.chat.id)
            incrementSuccessInvited(message.from_user.id)

# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

time.sleep(0.1)

# Set webhook
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Start flask server
app.run(host=WEBHOOK_LISTEN,
        port=WEBHOOK_PORT,
        ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
        debug=True)


# bot.polling()


