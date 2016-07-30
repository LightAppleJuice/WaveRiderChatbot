# coding=UTF-8
"""
Created on 20.06.2016

@author: A. Plistik
"""

from settings import settings

config = settings()


import Commands
import time
import eventlet
import requests
from telebot import TeleBot


class URLParser:
    # Каждый раз получаем по 10 последних записей со стены
    FILENAME_VK = 'last_known_id.txt'
    sourceDic = {'pikabu': 2, 'mdk': 3, 'joyreactor': 4}

    def __init__(self, markup):
        self.bot = TeleBot(config.bot_token)
        self.logger = Commands.workWithLog(config.log)
        self.base = Commands.workWithData(config.database_name)
        self.markup = markup

    def get_data(self, target_url=''):
        timeout = eventlet.Timeout(10)
        try:
            feed = requests.get(target_url)
            return feed.json()
        except eventlet.timeout.Timeout:
            self.logger.siteWarning()
            return None
        finally:
            timeout.cancel()

    def send_new_posts(self, items, last_id, post_mask_url='', source=''):
        for item in items:
            if item['id'] <= last_id:
                break
            link = '{!s}{!s}'.format(post_mask_url, item['id'])
            usersBase = self.base.readRows()
            for elem in usersBase:
                if 1 == elem[self.sourceDic[source]]:
                    self.bot.send_message(elem[0], "Dear {0}, new post is available: {1}".format(elem[1], link),
                                          reply_markup=self.markup)
            self.logger.appSend(count=len(usersBase))
            # Спим секунду, чтобы избежать разного рода ошибок и ограничений (на всякий случай!)
            time.sleep(1)
        return

    def check_new_posts_vk(self, target_url='', post_mask_url=''):
        # Пишем текущее время начала
        dictIDs = {}
        with open(self.FILENAME_VK, 'rt') as file:
            last_id = file.readlines()
            for elem in last_id:
                elem = elem.split(' ')
                dictIDs[elem[0]] = int(elem[1])
                source = ''
                if elem[0] in post_mask_url:
                    last_id = int(elem[1])
                    source = elem[0]
                    break
            if last_id is None:
                #не прочитать файл
                return
        try:
            feed = self.get_data(target_url=target_url)
            # Если ранее случился таймаут, пропускаем итерацию. Если всё нормально - парсим посты.
            if feed is not None:
                # 0 - это какое-то число, так что начинаем с 1
                entries = feed['response'][1:]
                try:
                    # Если пост был закреплен, пропускаем его
                    tmp = entries[0]['is_pinned']
                    self.send_new_posts(entries[1:], last_id=last_id, post_mask_url=post_mask_url, source=source)
                except KeyError:
                    self.send_new_posts(entries, last_id=last_id, post_mask_url=post_mask_url, source=source)
                # Записываем новую "верхушку" группы, чтобы не повторяться
                with open(self.FILENAME_VK, 'w') as file:
                    for elem in dictIDs.keys():
                        if elem in post_mask_url:
                            try:
                                tmp = entries[0]['is_pinned']
                                # Если первый пост - закрепленный, то сохраняем ID второго
                                dictIDs[elem] = (entries[1]['id'])
                                self.logger.siteInfo((entries[1]['id']))
                            except KeyError:
                                dictIDs[elem] = (entries[0]['id'])
                                self.logger.siteInfo((entries[0]['id']))
                        file.writelines('{0} {1}\n'.format(elem, dictIDs[elem]))
        except Exception as ex:
            self.logger.siteError(ex)
            pass
        return

    def find_new_post(self, target_url='', post_mask_url=''):
        while True:
            self.check_new_posts_vk(target_url=target_url, post_mask_url=post_mask_url)
            time.sleep(int(config.sleep_time))