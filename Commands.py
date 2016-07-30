# coding=UTF-8
"""
Created on 15.06.2016

@author: A. Plistik
"""

import sqlite3
import logging


class workWithLog:

    def __init__(self, pathToLog):
        # Избавляемся от спама в логах от библиотеки requests
        logging.getLogger('requests').setLevel(logging.CRITICAL)
        logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(message)s',
                            level=logging.INFO,
                            filename=pathToLog,
                            datefmt='%d.%m.%Y %H:%M:%S')
        logging.info('[App] Script started')

    def siteWarning(self):
        """
        Создание файла лога в случае его отсутсвия
        """
        logging.warning('[Site] Got Timeout while retrieving data. Cancelling...')

    def siteError(self, exception):
        """
        Создание файла лога в случае его отсутсвия
        """
        logging.error('[Site] Exception of type {!s} in check_new_post(): {!s}'
                      .format(type(exception).__name__, str(exception)))

    def siteInfo(self, id):
        """
        Создание файла лога в случае его отсутсвия
        """
        logging.info('[Site] New post id is {!s}'.format(id))

    def appSend(self, count):
        """
        Создание файла лога в случае его отсутсвия
        """
        logging.warning('[App] Send {0} new posts'.format(count))

    def appAdd(self, userName):
        """
        Добавление пользователя в базу
        """
        logging.info('[App] {0} joined the mailing list'.format(userName))

    def appDelete(self, userName):
        """
        Удаление пользователя из базы
        """
        logging.info('[App] {0} left the mailing list'.format(userName))


class workWithData:

    def __init__(self, pathToData):
        self.connection = sqlite3.connect(pathToData, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.cursor.execute('''CREATE TABLE if not exists users (chatID COUNTER CONSTRAINT PrimaryKey PRIMARY KEY,
                                                                 FirstName Text(30) NOT NULL,
                                                                 pikabu INTEGER,
                                                                 mdk INTEGER,
                                                                 joyreactor INTEGER)''')

    def addRow(self, chatID, userName='Dear Users', source=""):
        """
        Добавление новой записи в таблицу
        :param chatID: идентификатор чата
        :param userName: имя пользователя
        """
        sqlStr = "INSERT INTO users VALUES ({0}, '{1}', 0, 0, 0)".format(chatID, userName)
        try:
            self.cursor.execute(sqlStr)
        except sqlite3.IntegrityError:
            pass # попытка повторной запист
        sqlStr = "UPDATE users SET {0}=1 where chatID={1}; ".format(source, chatID)
        self.cursor.execute(sqlStr)
        self.connection.commit()

    def readRows(self):
        """ Получаем все строки базы данных
        :return: список идентификаторов чатов и имен пользователей
        """
        with self.connection:
            return self.cursor.execute('SELECT * FROM users').fetchall()

    def removeRow(self, chatID, source=""):
        """
        Удаляем запись адреса
        :param chatID: идентификатор чата
        """
        sqlStr = "UPDATE users SET  {0}=0 where chatID={1}; ".format(source, chatID)
        self.cursor.execute(sqlStr)
        self.connection.commit()

    def __del__(self):
        self.cursor.close()
        self.connection.close()