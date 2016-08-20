# coding=UTF-8
import sqlite3
from settings import settings
from os.path import split
from requests import post
from json import loads
from re import findall
import vk


class poster:

    def __init__(self):
        self.config = settings()
        pathToData = self.config.users_token
        self.connection = sqlite3.connect(pathToData, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.cursor.execute('''CREATE TABLE if not exists users (chatID COUNTER CONSTRAINT PrimaryKey PRIMARY KEY,
                                                                 token Text(100) NOT NULL)''')

    def findUser(self, chatId):
        with self.connection:
            result = self.cursor.execute('SELECT * FROM users WHERE chatID={0}'.format(chatId)).fetchall()
        if result:
            self.token = result[0][1]
        else:
            self.token = None
        return self.token

    def addUser(self, message):
        strToFind = 'https:.+access_token=(.+)\&expires_in=.+'
        try:
            self.token = findall(strToFind, message.text)[0]
            sqlStr = "INSERT INTO users VALUES ({0}, '{1}')".format(message.chat.id, self.token)
            with self.connection:
                try:
                    self.cursor.execute(sqlStr)
                except sqlite3.IntegrityError:
                    pass  # попытка повторной запист
        except:
            self.token = None

    def post(self, pathToMusic, **kwargs):
        pathToMusic = pathToMusic
        pathToImage = kwargs.get('pathToImage', None)
        text = kwargs.get('text', '')
        resultPost=[]

        session = vk.Session(access_token=self.token)
        api = vk.API(session)
        gid = self.config.id_vkapi

        audio = {'file': (split(pathToMusic)[1], open(pathToMusic, 'rb'))}

        # Получаем ссылку для загрузки изображений
        method_url = 'https://api.vk.com/method/audio.getUploadServer?'
        data = dict(access_token=self.token, gid=gid)
        response = post(method_url, data)
        result = loads(response.text)
        upload_url = result['response']['upload_url']

        # Загружаем изображение на url
        response = post(upload_url, files=audio)
        result = loads(response.text)

        # Сохраняем фото на сервере и получаем id
        method_url = 'https://api.vk.com/method/audio.save?'
        data = dict(access_token=self.token, gid=gid, audio=result['audio'], hash=result['hash'], server=result['server'])
        response = post(method_url, data)
        resultAid = loads(response.text)['response']['aid']
        result = loads(response.text)['response']['owner_id']
        resultPost.append('audio{0}_{1}'.format(result, resultAid))

        if pathToImage:
            img = {'photo': (split(pathToImage)[1], open(pathToImage, 'rb'))}

            # Получаем ссылку для загрузки изображений
            method_url = 'https://api.vk.com/method/photos.getWallUploadServer?'
            data = dict(access_token=self.token, gid=gid)
            response = post(method_url, data)
            result = loads(response.text)
            upload_url = result['response']['upload_url']

            # Загружаем изображение на url
            response = post(upload_url, files=img)
            result = loads(response.text)

            # Сохраняем фото на сервере и получаем id
            method_url = 'https://api.vk.com/method/photos.saveWallPhoto?'
            data = dict(access_token=self.token, gid=gid, photo=result['photo'], hash=result['hash'],
                        server=result['server'])
            response = post(method_url, data)
            resultPost.append(loads(response.text)['response'][0]['id'])

        api.wall.post(message='{0} #Muzis #WaveRiderChatbot'.format(text), attachments=','.join(resultPost))

    def __del__(self):
        self.cursor.close()
        self.connection.close()