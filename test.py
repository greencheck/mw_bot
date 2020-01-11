print("Hello, World!")
import time
import mysql.connector
import time
import constants
conn = mysql.connector.connect(host=constants.DB_HOST,
                               user=constants.DB_USER,
                               passwd=constants.DB_PASS,
                               db=constants.DB_NAME)

cursor = conn.cursor()

def getSaveMesage():
    cursor.execute('SELECT date FROM subscribers_list WHERE id = 2')
    entry = cursor.fetchall()
    return entry[len(entry) - 1][0]


# x = time.strftime('%Y-%m-%d %H:%M:%S')
# a = int(time.mktime(time.strptime(str(x), '%Y-%m-%d %H:%M:%S')))
# b = int(time.mktime(time.strptime(str(getSaveMesage()), '%Y-%m-%d %H:%M:%S')))
# print(b)
# print(getSaveMesage())
# conn.close()

import datetime # import datetime, timedelta

a = datetime.datetime.now()
print(a)
b = getSaveMesage()
print(b)

delta = b - a
print(delta.days )






one_month = 2592000