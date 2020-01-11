#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import mysql.connector
import telebot
import threading
from telebot import types  , apihelper
import config
import constants
import dbworker
import logging
import datetime


token = '772417845:AAG-n9TZ916OZFnIGIhlNxQtM1HEYcri2iw' #'803726023:AAFwhuBSBLIukHyM1-x1DisN0QpoDAtfuZ4'   # '772417845:AAG-n9TZ916OZFnIGIhlNxQtM1HEYcri2iw'
apihelper.proxy = {'https': 'https://S8VSgZ2UoW:fLYGTLW50g@196.196.64.91:3128'}
conn = mysql.connector.connect(host=constants.DB_HOST,
                               user=constants.DB_USER,
                               passwd=constants.DB_PASS,
                               db=constants.DB_NAME)
cursor = conn.cursor()

GROUP_ID = -1001457202594 # -1001245378977  # -1001457202594

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(token)

def getWhiteListUsers():
    cursor.execute('SELECT * FROM whitelist')
    users = cursor.fetchall()
    print(users)
    return set([user[1] for user in users])

whitelist_users = getWhiteListUsers()

def updateWhiteList():
    global whitelist_users
    whitelist_users = getWhiteListUsers()

def isUserInWhitelist(user_id):
    global whitelist_users
    return user_id in whitelist_users

def deleteMessageThread(token, chat_id, message_id):
    time.sleep(60)
    api_tg = telebot.TeleBot(token=token, threaded=False) # threaded может там по-другому в параметрах указывается
    api_tg.delete_message(chat_id, message_id)


def start_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton(constants.deal_msg)
    itembtn2 = types.KeyboardButton(constants.tour_msg)
    itembtn3 = types.KeyboardButton(constants.balance)
    itembtn4 = types.KeyboardButton(constants.faq)
    itembtn5 = types.KeyboardButton(constants.subscribe_msg)
    itembtn6 = types.KeyboardButton(constants.in_chat)
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5, itembtn6)
    return markup


def reset_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=1)
    itembtn = types.KeyboardButton(constants.returned)
    markup.add(itembtn)
    return markup


def yes_no_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton(constants.btn_yes_post)
    itembtn2 = types.KeyboardButton(constants.btn_no_post)
    markup.add(itembtn1, itembtn2)
    return markup

def forward_whitelist_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton(constants.btn_yes_post)
    itembtn2 = types.KeyboardButton(constants.btn_no_post)
    markup.add(itembtn1, itembtn2)
    return markup


def subscribe_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    itembtn1 = types.KeyboardButton(constants.buy_subscribe)
    itembtn2 = types.KeyboardButton(constants.check_subscribe)
    itembtn3 = types.KeyboardButton(constants.returned)
    markup.add(itembtn1, itembtn2, itembtn3)
    return markup


def inline_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton(text=constants.post_btn, url="t.me/Life_Models_Bot")
    markup.add(btn1)
    return markup


def inline_private_markup():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(text=constants.returned, url="t.me/joinchat/O86x40o6-aEryRnRK3ShBQ")
    markup.add(btn1)
    return markup


mk = types.ReplyKeyboardRemove()


@bot.message_handler(commands=['getID'], func=lambda message: message.chat.type == 'supergroup')
def start_msg(message):
    print(message.chat.id)
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)


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


def saveMessageText(chat_id, message_text):
    cursor.execute('SELECT * FROM texts WHERE chat_id=%s', (chat_id,))
    entry = cursor.fetchone()
    if entry is None:
        cursor.execute("INSERT INTO texts (chat_id, message_txt) VALUES (%s, %s)", (chat_id, message_text))
        conn.commit()
    else:
        cursor.execute('UPDATE texts SET message_txt=%s WHERE chat_id=%s', (message_text, chat_id))
        conn.commit()

def getSaveMesage(chat_id):
    cursor.execute('SELECT message_txt FROM texts WHERE chat_id=%s', (chat_id,))
    entry = cursor.fetchone()
    return entry[0]


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.deal_msg)
def post_msg(message):
    state = dbworker.get_current_state(message.chat.id)
    balance = getBalance(message.from_user.id)
    sub_status = checkSubscriber(message.from_user.id)
    if sub_status:
        if state == config.States.S_YN_POST.value:
            bot.send_message(message.chat.id, constants.msg_enter_text, reply_markup=reset_markup())
        else:
            bot.send_message(message.chat.id, constants.msg_enter_text, reply_markup=reset_markup())
            dbworker.set_state(message.chat.id, config.States.S_YN_POST.value)
    else:
        if balance < 5:
            bot.send_message(message.chat.id, getStrFailDeal(message.from_user.id))
        else:
            if state == config.States.S_YN_POST.value:
                bot.send_message(message.chat.id, constants.msg_cost_3 +
                                 constants.msg_enter_text, reply_markup=reset_markup())
            else:
                bot.send_message(message.chat.id, constants.msg_cost_3 +
                                 constants.msg_enter_text, reply_markup=reset_markup())
                dbworker.set_state(message.chat.id, config.States.S_YN_POST.value)


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.btn_yes_post
                     and dbworker.get_current_state(message.chat.id) == config.States.S_YN_POST.value)
def yes_post(message):
    print("Yes Post!")
    bot.send_message(message.chat.id, "Сейчас будет отправлено сообщение!", reply_markup=reset_markup())
    try:
        msg_id = getSaveMesage(message.chat.id)
        # bot.send_message(GROUP_ID, message.text, reply_markup=mk)
        bot.forward_message(GROUP_ID, message.chat.id, int(msg_id))
        if not checkSubscriber(message.from_user.id):
            setBalance(message.from_user.id, (getBalance(message.from_user.id) - 5))
        dbworker.set_state(message.chat.id, config.States.S_START.value)
        bot.send_message(message.chat.id, constants.offer_success)
    except Exception as ex:
        print(ex)


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.btn_no_post
                     and dbworker.get_current_state(message.chat.id) == config.States.S_YN_POST.value)
def no_post(message):
    dbworker.set_state(message.chat.id, config.States.S_START.value)
    bot.send_message(message.chat.id, "Главное меню", reply_markup=start_markup())


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_YN_POST.value)
def yes_or_no_post(message):
     saveMessageText(message.chat.id, message.message_id)
     bot.send_message(message.chat.id, constants.accept_public, reply_markup=yes_no_markup())


def getStrFailTour(telegram_id):
    balance = getBalance(telegram_id)
    res = (constants.msg_cost_5 + constants.msg_on_balance + str(balance) +
           constants.msg_not_enough_for_post + constants.tour)
    return res


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.tour_msg)
def tour_msg(message):
    state = dbworker.get_current_state(message.chat.id)
    balance = getBalance(message.from_user.id)
    sub_status = checkSubscriber(message.from_user.id)
    if sub_status:
        if state == config.States.S_YN_POST.value:
            bot.send_message(message.chat.id, constants.msg_enter_text, reply_markup=reset_markup())
        else:
            bot.send_message(message.chat.id, constants.msg_enter_text, reply_markup=reset_markup())
            dbworker.set_state(message.chat.id, config.States.S_YN_POST.value)
    else:
        if balance < 5:
            bot.send_message(message.chat.id, getStrFailTour(message.from_user.id))
        else:
            if state == config.States.S_YN_TOUR.value:
                bot.send_message(message.chat.id, constants.msg_cost_5 +
                                 constants.msg_enter_text, reply_markup=reset_markup())
            else:
                bot.send_message(message.chat.id, constants.msg_cost_5 +
                                 constants.msg_enter_text, reply_markup=reset_markup())
                dbworker.set_state(message.chat.id, config.States.S_YN_TOUR.value)


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.btn_yes_tour
                     and dbworker.get_current_state(message.chat.id) == config.States.S_YN_TOUR.value)
def yes_tour(message):
    bot.send_message(message.chat.id, "Сейчас будет отправлено сообщение!", reply_markup=reset_markup())
    try:
        print("Yes Tour!")
        msg_id = getSaveMesage(message.chat.id)
        # bot.send_message(GROUP_ID, message.text, reply_markup=mk)
        bot.forward_message(GROUP_ID, message.chat.id, int(msg_id))
        if not checkSubscriber(message.from_user.id):
            setBalance(message.from_user.id, (getBalance(message.from_user.id) - 5))
        dbworker.set_state(message.chat.id, config.States.S_START.value)
        bot.send_message(message.chat.id, constants.tour_success)
    except Exception as ex:
        print(ex)


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.btn_no_tour
                     and dbworker.get_current_state(message.chat.id) == config.States.S_YN_TOUR.value)
def no_tour(message):
    dbworker.set_state(message.chat.id, config.States.S_START.value)
    bot.send_message(message.chat.id, "Главное меню", reply_markup=start_markup())


@bot.message_handler(func=lambda message: dbworker.get_current_state(message.chat.id) == config.States.S_YN_TOUR.value
                     or dbworker.get_current_state(message.chat.id) == config.States.S_YN_POST.value)
def yes_or_no(message):
    saveMessageText(message.chat.id, message.message_id)
    bot.send_message(message.chat.id, constants.accept_public, reply_markup=yes_no_markup())


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.balance)
def balance_msg(message):
    print("Balance Button")
    balance = getBalance(message.from_user.id)
    bot.send_message(message.chat.id, constants.msg_get_balance + str(balance) + constants.msg_invited)


@bot.message_handler(func=lambda message: message.chat.type == u'private' and message.text == constants.faq)
def faq_msg(message):
    print("FAQ Button")
    bot.send_message(message.chat.id, "/start - В начало.\nПоддержка @LifeModelsSupportBot")


def checkSubscriber(id_telegram):
    cursor.execute('SELECT date FROM subscribers_list WHERE subs_id = %s', (id_telegram,))
    entry = cursor.fetchall()
    if not entry:
        return False
    else:
        subscribe_day = entry[len(entry) - 1][0]
        now_day = datetime.datetime.now()
        delta = now_day - subscribe_day
        if delta.days < 30:
            return True
        else:
            return False


def getDaysSubscriber(id_telegram):
    cursor.execute('SELECT date FROM subscribers_list WHERE subs_id = %s', (id_telegram,))
    entry = cursor.fetchall()
    subscribe_day = entry[len(entry) - 1][0]
    now_day = datetime.datetime.now()
    delta = now_day - subscribe_day
    print(subscribe_day, now_day)
    return delta.days


def setSubscriber(id_telegram):
    cursor.execute("INSERT INTO subscribers_list (subs_id) VALUES (%s)", (id_telegram,))
    conn.commit()


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.subscribe_msg)
def subscribe_msg(message):
    subscribe_status = checkSubscriber(message.from_user.id)
    balance = getBalance(message.from_user.id)
    bot.send_message(message.chat.id, "С помощью подписки Вы сможете в течение 30 дней публиковать предложения и туры "
                                      "без траты приглашенных. Стоимость подписки - 30 приглашенных. ")
    if subscribe_status:
        count_subs_day = getDaysSubscriber(message.from_user.id)
        bot.send_message(message.chat.id, "У вас есть подписка. Количество дней: %s" % str(30 - count_subs_day))
    else:
        if balance < 30:
            bot.send_message(message.chat.id, "Недостаточно средств для подписки! "
                                              "На вашем счету %s приглашенных." % str(balance))
        else:
            bot.send_message(message.chat.id, constants.get_subscribe_question, reply_markup=yes_no_markup())
            dbworker.set_state(message.chat.id, config.States.S_BUY_SUBSCRIBE.value)


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.btn_yes_tour
                     and dbworker.get_current_state(message.chat.id) == config.States.S_BUY_SUBSCRIBE.value)
def buy_subscribe_msg(message):
    setBalance(message.from_user.id, (getBalance(message.from_user.id) - 30))
    setSubscriber(message.from_user.id)
    bot.send_message(message.chat.id, constants.success_subscribe, reply_markup=start_markup())


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.text == constants.in_chat)
def in_chat_msg(message):
    bot.send_message(message.chat.id, constants.back_to_chat_btn, reply_markup=inline_private_markup())


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.forward_from != None)
def forwarded_msg(message):
    print('eee')
    admin_list = get_admin_ids(bot, GROUP_ID)
    if admin_list.count(message.from_user.id):
       print('User is admin. Add to white list')
       bot.send_message(message.chat.id, 'Dobavit v whitelist?', reply_markup=forward_whitelist_markup())
       # сохраняем id пользователя
       saveForwardedUser(message.from_user.id, message.forward_from.id)
       # меняем стейт
       dbworker.set_state(message.chat.id, config.States.S_ADMIN_FORWARDED_MESSAGE.value)



@bot.message_handler(func=lambda message: message.chat.type == 'private' and dbworker.get_current_state(message.chat.id) == config.States.S_ADMIN_FORWARDED_MESSAGE.value)
def add_to_whitelist(message):
    user_id = getForwardedUserForAdmin(message.chat.id)
    if user_id is None:
        print('Not found user')
        bot.send_message(message.chat.id, 'not found user', reply_markup=reset_markup())
        dbworker.set_state(message.chat.id, config.States.S_START.value)
    else:
        if message.text == constants.btn_yes_post:
            addToWhiteList(user_id)
            global whitelist_users
            whitelist_users.add(user_id)
            bot.send_message(message.chat.id, 'dobavlen v whitelist', reply_markup=reset_markup())
            print('User added to whitelist')
            dbworker.set_state(message.chat.id, config.States.S_START.value)
        else:
            bot.send_message(message.chat.id, 'Отмена добавления в WhiteList', reply_markup=reset_markup())
            
        
        

def get_admin_ids(bot, chat_id):
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]

def first_last_name_checker(first_name, last_name):
    if last_name is None:
        return str(first_name)
    else:
        return str(first_name + " " + last_name)

def saveForwardedUser(admin_id, user_id):
    cursor.execute('SELECT * FROM selected_users_admins WHERE admin_id=%s', (admin_id,))
    entry = cursor.fetchone()
    if entry is None:
        cursor.execute("INSERT INTO selected_users_admins (admin_id, user_id) VALUES (%s, %s)", (admin_id, user_id))
        conn.commit()
    else:
        cursor.execute("UPDATE selected_users_admins SET user_id=%s WHERE admin_id=%s", (user_id, admin_id))
        conn.commit()

def addToWhiteList(user_id):
    cursor.execute('SELECT * FROM whitelist WHERE user_id=%s', (user_id,))
    entry = cursor.fetchone()
    if entry is None:
        cursor.execute("INSERT INTO whitelist (user_id) VALUES (%s)", (user_id,))
        conn.commit()


def getForwardedUserForAdmin(admin_id):
    cursor.execute('SELECT * FROM selected_users_admins WHERE admin_id=%s', (admin_id,))
    entry = cursor.fetchone()
    if entry is None:
        return None
    return entry[2]

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
    print(admin_list)
    if isUserInWhitelist(message.from_user.id) or admin_list.count(message.from_user.id):
        print("Admin send message!")
    else:
        bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        msg = bot.send_message(message.chat.id, constants.post_warning, reply_markup=inline_markup())
        # time.sleep(180)
        my_thread = threading.Thread(target=deleteMessageThread, args=(token, message.chat.id, msg.message_id))
        my_thread.start()
        #bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)


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


@bot.message_handler(func=lambda message: message.chat.type == 'private')
def any_msg(message):
    if not inUsers(message.from_user.id):
        addNewUser(message.from_user.id)

    bot.send_message(message.chat.id, constants.hello_message, reply_markup=start_markup())

bot.remove_webhook()

bot.polling()


