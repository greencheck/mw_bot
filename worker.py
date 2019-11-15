import mysql.connector
import telebot
from telebot import apihelper
import constants

token = '772417845:AAG-n9TZ916OZFnIGIhlNxQtM1HEYcri2iw'
apihelper.proxy = {'https': 'https://feonavinogradova:divopasy@82.146.34.38:8080'}
bot = telebot.TeleBot(token)
conn = mysql.connector.connect(host=constants.DB_HOST,
                               user=constants.DB_USER,
                               passwd=constants.DB_PASS,
                               db=constants.DB_NAME)
cursor = conn.cursor()



@bot.message_handler(func=lambda message: message.chat.type == 'private')
def send_msg(message):
    bot.send_message(message.chat.id, "Оставь меня в покое!")


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
    cursor.execute('UPDATE users SET count_inv=count_inv+1 WHERE id_telegram=%s', (id_telegram,))
    conn.commit()


def getCountInv(id_telegram):
    cursor.execute('SELECT count_inv FROM users WHERE id_telegram=%s', (id_telegram,))
    entry = cursor.fetchone()
    return entry[0]


@bot.message_handler(func=lambda message: message.chat.type == 'supergroup')
def check_message(message):
    admin_list = get_admin_ids(bot, message.chat.id)
    if admin_list.count(message.from_user.id):
        print("Admin send message!")
    else:
        if getCountInv(message.from_user.id) < constants.count_access_message:
            bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            bot.send_message(message.chat.id,
                             first_last_name_checker(message.from_user.first_name, message.from_user.last_name) +
                             constants.warning_message)


@bot.message_handler(content_types=['new_chat_members'])
def inviter(message):
    if message.new_chat_member.first_name == message.from_user.first_name:
        print("Человек вступил по ссылке.")
        if inUsers(message.from_user.id):
            print("in Group")
        else:
            addNewUser(message.from_user.id)
            bot.send_message(message.chat.id, 'Привет, ' +
                             first_last_name_checker(message.new_chat_member.first_name,
                                                     message.new_chat_member.last_name) +
                             constants.hello_message)
    else:
        print("Человек был приглашен другим человеком.")
        if inUsers(message.new_chat_member.id):
            print("(New) User in Group!")
        else:
            bot.send_message(message.chat.id, 'Привет, ' +
                             first_last_name_checker(message.new_chat_member.first_name,
                                                     message.new_chat_member.last_name) +
                             constants.hello_message)
            addNewUser(message.new_chat_member.id)
            addNewInviteListEntry(message.from_user.id, message.new_chat_member.id, message.chat.id)
            incrementSuccessInvited(message.from_user.id)


@bot.message_handler(content_types=['left_chat_member'])
def left(message):
    print("left")


bot.polling()
