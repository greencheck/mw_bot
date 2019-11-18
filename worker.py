#!/usr/bin/python
# -*- coding: utf-8 -*-
import mysql.connector
import telebot
from telebot import apihelper, types

import config
import constants
import dbworker

token = '772417845:AAG-n9TZ916OZFnIGIhlNxQtM1HEYcri2iw'
apihelper.proxy = {'https': 'https://feonavinogradova:divopasy@165.22.254.99:3128'}
bot = telebot.TeleBot(token)
conn = mysql.connector.connect(host=constants.DB_HOST,
                               user=constants.DB_USER,
                               passwd=constants.DB_PASS,
                               db=constants.DB_NAME)
cursor = conn.cursor()

GROUP_ID = -1001457202594


def start_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton(constants.deal_msg)
    itembtn2 = types.KeyboardButton(constants.tour_msg)
    itembtn3 = types.KeyboardButton(constants.balance)
    itembtn4 = types.KeyboardButton(constants.faq)
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    return markup

def reset_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=1)
    itembtn = types.KeyboardButton(constants.returned)
    markup.add(itembtn)
    return markup


mk = types.ReplyKeyboardRemove()


@bot.message_handler(commands=["getID"])
def start_msg(message):
    bot.send_message(message.chat.id, str(message.chat.id))


@bot.message_handler(commands=["start"], func=lambda message: message.chat.type == 'private')
def start_msg(message):
    if not inUsers(message.from_user.id):
        addNewUser(message.from_user.id)

    bot.send_message(message.chat.id, constants.hello_message, reply_markup=start_markup())


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.returned)
def reset_msg(message):
    dbworker.set_state(message.chat.id, config.States.S_START.value)
    bot.send_message(message.chat.id, "Основное окно", reply_markup=start_markup())


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
    bot.send_message(GROUP_ID, message.text, reply_markup=mk)
    setBalance(message.from_user.id, (getBalance(message.from_user.id) - 3))
    dbworker.set_state(message.chat.id, config.States.S_START.value)


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
    bot.send_message(GROUP_ID, message.text, reply_markup=mk)
    setBalance(message.from_user.id, (getBalance(message.from_user.id) - 5))
    dbworker.set_state(message.chat.id, config.States.S_START.value)


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.balance)
def balance_msg(message):
    print("Balance Button")
    balance = getBalance(message.from_user.id)
    bot.send_message(message.chat.id, constants.msg_get_balance + str(balance) + constants.msg_invited)


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.faq)
def faq_msg(message):
    print("FAQ Button")
    bot.send_message(message.chat.id, "/start - Начало")


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

bot.polling()
