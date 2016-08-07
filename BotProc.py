#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Main Bot Class

import json  #Представляет словарь в строку
import os  # Для проверки на существование файла
import requests  # Для осуществления запросов
import urllib  # Для загрузки картинки с сервера
from io import BytesIO  # Для отправки картинки к пользователю
import time  # Представляет время в читаемый формат
import vk
import numpy as np
from PIL import Image
#import caffe
import requests
import TextMatcher
from RequestSender import RequestSender
import urllib2
import random
from settings import settings
import telebot
from re import findall
import logging
from InfoToMusic import InfoToMusic
from poster import poster
from TextMatcher import TextModels
from TextMatcher import TextProcessing

class MusicBot:
    def __init__(self):
        # Bot initialization
        self.config = settings()
        self.bot = telebot.TeleBot(self.config.bot_token)
        self.users = self.read_users(self.config.users_name)

        #self.users_id = self.read_users(self.config.users_token)
        self.link = "https://oauth.vk.com/authorize?\
        client_id= %s&display=mobile&scope=wall,offline,audio,photos&response_type=token&v=5.45" % self.config.id_vkapi
        self.imgPath = 'C:\ChatBot\WaveRiderChatbot\photos\userPhoto'#'/home/andrew/Projects/WaveRiderChatbot/'
        self.mp3Path = '/home/andrew/Projects/WaveRiderChatbot/music/'
        self.infoProcessors = {}

        # Loading models
        # TODO
        self.textModels = TextModels(self.config.w2vec_model, self.config.w2vec_dict, self.config.eng_rus_dict)
        self.imageModels = []

        # Logger initialization
        self.logger = logging.getLogger('BotLogger')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(self.config.log)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        rs = RequestSender()
        self.allLyrics = rs.getAllLyricsByStyles(rs.getAllStyles())
        self.logger.info('Translating all lyrics...')
        for currSongId in self.allLyrics.keys():
            song_name_translated = self.textModels.preprocess_sentence(self.allLyrics[currSongId][0])
            song_text_translated = self.textModels.preprocess_sentence(self.allLyrics[currSongId][1])
            self.allLyrics[currSongId] = song_name_translated, song_text_translated

        self.logger.info('Transform all lyrics to vectors...')
        textProp = TextProcessing(self.textModels)
        textProp.text_dict_to_vec_dict(self.allLyrics)
        return




        # Bot messages
        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.bot.send_message(chat_id=message.chat.id,
                                  text='Привет, {0} {1}!\nТебе нужно что-то запостить?\nЯ подберу подходящую музыку {2} под пост и опубликую его для тебя в vk.\n'
                                       'Я могу работать как с текстом, так и с фотографиями. Просто отправь мне всё необходимое.\n\n'
                                  .format(message.from_user.first_name, '\xE2\x9C\x8B', '\xF0\x9F\x8E\xB6'))

        @self.bot.message_handler(commands=['help'])
        def help(message):
            self.bot.send_message(chat_id=message.chat.id,
                                  text='Я подберу для тебя музыку {0}, подходящую под загруженную фотографию или текст. '
                                       'Уточню результат, если потребуется. Загружу найденную песню, '
                                       'а также смогу опубликовать сгенерированный пост на твоей старнице в VK.'
                                  .format('\xF0\x9F\x8E\xA7'))

        @self.bot.message_handler(func=lambda message: True, content_types=['text'])
        def parse_message(message):
            users_id = self.read_users(self.config.users_token)
            strToFind = 'https:.+access_token=(.+)\&expires_in=.+'

            if u"Опубликовать в VK" == message.text:
                self.logger.info('From user: VK Publication request.')
                if not usersClass.findUser(chatId=message.chat.id):
                    keyboard = telebot.types.InlineKeyboardMarkup()
                    url_button = telebot.types.InlineKeyboardButton(text="Перейти в VK", url=self.link)
                    keyboard.add(url_button)
                    self.bot.send_message(chat_id=message.chat.id,
                                     text='Прости {0}, но я не смогу обновить твою стену, '
                                          'пока ты не пришлешь мне текст из адресной строки, '
                                          'после перехода по ссылке:'
                                     .format('\xF0\x9F\x98\x94'), reply_markup=keyboard)
                else:
                    usersClass.post(pathToMusic=self.music_name, pathToImage=self.photo_name, text=self.text)
                    self.bot.send_message(chat_id=message.chat.id,
                                          text='Отлично! Не будем останавливаться)\n'
                                               'Отправь мне фотографию или текст.', reply_markup=self.generate_markup())
            elif 'https' in message.text:
                self.logger.info('From user: VK Authorization request.')
                usersClass.addUser(message)
                if not usersClass.findUser(message.chat.id):
                    self.bot.send_message(chat_id=message.chat.id,
                                          text='Не могу найти токен.\n '
                                               'Проверь, пожалуйста, скопированную строку и пришли мне ее еще раз')
                else:
                    self.bot.send_message(chat_id=message.chat.id,
                                          text='Приветствую тебя, пользователь')
                    usersClass.post(pathToMusic=self.music_name, pathToImage=self.photo_name, text=self.text)
                    self.bot.send_message(chat_id=message.chat.id,
                                          text='Отлично! Не будем останавливаться)\n'
                                               'Отправь мне фотографию или текст.', reply_markup=self.generate_markup())
            elif u"Хочу еще" == message.text:
                self.logger.info('From user: One more request.')
            elif u"Отмена" == message.text:
                self.logger.info('From user: Cancel request.')
                self.bot.send_message(chat_id=message.chat.id,
                                      text='Прости, что не получилось. Может попробуем еще раз?\n'
                                           'Отправь мне фотографию или текст.',
                                      reply_markup=telebot.types.ReplyKeyboardHide())

                # TODO: delete saved images?
                self.infoProcessors[message.chat.id].clearAll()
                del self.infoProcessors[message.chat.id]
                self.logger.info('All data for id ' + str(message.chat.id) + ' were cleared.')

            else:
                self.logger.info('From user: Text description')
                text = message.text.encode("utf-8")

                # Create new InfoToMusic for new chat_id
                self.logger.info('Creating new InfoToMusic for new chat_id')
                if message.chat.id not in self.infoProcessors.keys():
                    self.infoProcessors[message.chat.id] = InfoToMusic(self.textProcModels, self.imageProcModels)

                self.infoProcessors[message.chat.id].userText = text
                self.infoProcessors[message.chat.id].process()




        @self.bot.message_handler(func=lambda message: True, content_types=['photo'])
        def get_image(message):
            self.logger.info('From user: Image')
            self.bot.send_chat_action(message.chat.id, "upload_photo")

            height_list = []
            for ph in message.photo:
                height_list.append(ph.height)
            photo_ind = np.argmax(height_list)

            file_info = self.bot.get_file(message.photo[photo_ind].file_id)
            file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(self.config.bot_token, file_info.file_path))

            # Create new InfoToMusic for new chat_id
            self.logger.info('Creating new InfoToMusic for new chat_id')
            if message.chat.id not in self.infoProcessors.keys():
                self.infoProcessors[message.chat.id] = InfoToMusic(self.textProcModels, self.imageProcModels)

            # Saving image
            newImgPath = os.path.join(self.imgPath, str(message.chat.id))
            photo_name = os.path.join(newImgPath, os.path.basename(file_info.file_path))
            if not os.path.isdir(self.imgPath):
                os.mkdir(self.imgPath)
            if not os.path.isdir(newImgPath):
                os.mkdir(newImgPath)
            f = open(photo_name, 'wb')
            f.write(file.content)
            f.close()
            self.logger.info('Image saved: ' + photo_name)

            # Filling fields in appropriate InfoToMusic
            img = np.array(Image.open(photo_name))
            self.infoProcessors[message.chat.id].userImage = img
            self.infoProcessors[message.chat.id].imgFilePath = photo_name
            self.infoProcessors[message.chat.id].process()


    def generate_markup(self):
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Опубликовать в VK')
        markup.add('Хочу еще')
        markup.add('Отмена')
        return markup

    def read_users(self, pathToBase=''):
        res = {}
        if os.path.isfile(pathToBase):
            with open(pathToBase, 'r') as base:
                res = json.loads(base.read())
        return res

    def process(self):
        self.bot.polling(none_stop=True)


if __name__ == '__main__':
    Bot = MusicBot()
    usersClass = poster()
    Bot.process()
