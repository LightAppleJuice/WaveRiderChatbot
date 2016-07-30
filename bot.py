# coding=UTF-8
"""
Created on 15.06.2016

@author: A. Plistik
"""

from threading import Thread
from settings import settings
from URLParser import URLParser
import telebot
import Commands

config = settings()
bot = telebot.TeleBot(config.bot_token)


def generate_markup():
    """Создание кнопок"""
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('pikabu+', 'mdk+', 'joyreactor+')
    markup.add('pikabu-', 'mdk-', 'joyreactor-')
    return markup


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    """Приветствие нового пользователя"""
    bot.send_message(chat_id=message.chat.id, text="Dear {0}, please, select Public".format(message.chat.first_name),
                     reply_markup=generate_markup())


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    if "+" in message.text:
        """Добавление чата в базу"""
        base.addRow(chatID=message.chat.id, userName=message.chat.first_name, source=message.text.strip('+'))
        logger.appAdd(userName=message.chat.first_name)
    elif "-" in message.text:
        """Удаление чата из базы"""
        base.removeRow(chatID=message.chat.id, source=message.text.strip('-'))
        logger.appDelete(userName=message.chat.first_name)


if __name__ == '__main__':
    logger = Commands.workWithLog(config.log)
    base = Commands.workWithData(config.database_name)
    parser = URLParser(markup=generate_markup())

    # init threads
    t1 = Thread(target=bot.polling,
                kwargs={'none_stop': True})
    t2 = Thread(target=parser.find_new_post,
                kwargs={'target_url': 'https://api.vk.com/method/wall.get?domain=pikabu&count=10&filter=owner',
                        'post_mask_url': 'https://new.vk.com/pikabu?w=wall-31480508_'})
    t3 = Thread(target=parser.find_new_post,
                kwargs={'target_url': 'https://api.vk.com/method/wall.get?domain=mudakoff&count=10&filter=owner',
                        'post_mask_url': 'https://new.vk.com/mudakoff?w=wall-57846937_'})
    t4 = Thread(target=parser.find_new_post,
                kwargs={'target_url': 'https://api.vk.com/method/wall.get?domain=joyreactor_ru&count=10&filter=owner',
                        'post_mask_url': 'https://new.vk.com/joyreactor_ru?w=wall-34113013_'})
    # start threads
    t1.start()
    t2.start()
    t3.start()
    t4.start()
