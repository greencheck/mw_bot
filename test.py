import mysql.connector
import constants




conn = mysql.connector.connect(host=constants.DB_HOST,
                               user=constants.DB_USER,
                               passwd=constants.DB_PASS,
                               db=constants.DB_NAME)
cursor = conn.cursor()


def getCountInv(id_telegram):
    cursor.execute('SELECT count_inv FROM users WHERE id_telegram=%s', (id_telegram,))
    entry = cursor.fetchone()
    return entry[0]

p = getCountInv(185198284)

print(p)