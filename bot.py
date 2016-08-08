# coding=UTF-8
import json  # Представляет словарь в строку
import os  # Для проверки на существование файла
import requests  # Для осуществления запросов
import urllib  # Для загрузки картинки с сервера
from io import BytesIO  # Для отправки картинки к пользователю
import time  # Представляет время в читаемый формат
import vk
import numpy as np
from PIL import Image
import caffe
import requests
import TextMatcher
import RequestSender
import urllib2


class FeaturesNet(caffe.Net):
    def __init__(self, model_file, pretrained_file, mean_file=None, channel_swap=[2, 1, 0]):
        caffe.Net.__init__(self, model_file, pretrained_file, caffe.TEST)

        # configure pre-processing
        in_ = self.inputs[0]
        self.transformer = caffe.io.Transformer({in_: self.blobs[in_].data.shape})
        self.transformer.set_transpose(in_, (2, 0, 1))
        if mean_file is not None:
            blob = caffe.proto.caffe_pb2.BlobProto()
            data = open(mean_file, 'rb').read()
            blob.ParseFromString(data)
            arr = np.array(caffe.io.blobproto_to_array(blob))
            out = arr[0]
            self.transformer.set_mean('data', out)
        if channel_swap is not None:
            self.transformer.set_channel_swap(in_, channel_swap)

    def predict(self, image_list):
        in_ = self.inputs[0]
        caffe_in = np.zeros((len(image_list), image_list[0].shape[2]) + self.blobs[in_].data.shape[2:],
                            dtype=np.float32)
        for i, image in enumerate(image_list):
            caffe_in[i] = self.transformer.preprocess(in_, image)
        out = self.forward_all(**{in_: caffe_in})
        predictions = out[self.outputs[0]]

        return predictions


model_file = 'image_proc_model/deploy.prototxt'
pretrained = '../model/model.caffemodel'
mean_file = 'image_proc_model/imagenet_mean.binaryproto'
net = FeaturesNet(model_file, pretrained, mean_file=mean_file)

path_to_w2v_model = "/home/andrew/Projects/model/cbow_ns300_fullrostelLK4.npy"
path_to_w2v_dict = "/home/andrew/Projects/model/cbow_ns300_fullrostelLK4.dic"
text_matcher = TextMatcher.TextMatcher(path_to_w2v_model, path_to_w2v_dict)

request_sender = RequestSender.RequestSender()

big_lyrics = {}
styles =[32325,32486,4362,25357,20259,32501,32491,32454,32490,32487,32500,32494,
        32346,32370,32506,32510,20256,31662,32328, 25739]
for style in styles:
    lyrics = request_sender.sendRequest(style, 20)
    if lyrics:
        big_lyrics[style] = lyrics

from settings import settings
import telebot
from re import findall


config = settings()
bot = telebot.TeleBot(config.bot_token)
mp3Path=''

link = "https://oauth.vk.com/authorize?\
client_id=%s&display=mobile&scope=wall,offline,audio,photos&response_type=token&v=5.45" % config.id_vkapi


def read_users(pathToBase=''):
    res = {}
    if os.path.isfile(pathToBase):
        with open(pathToBase, 'r') as base:
            res = json.loads(base.read())
    return res


def make_post(token='', imgPath='', mp3Path=''):
    if (not imgPath) or (not mp3Path):
        return 0
    session = vk.Session(access_token=token)
    api = vk.API(session)

    gid = config.id_vkapi
    print imgPath
    print mp3Path


    # путь к вашему изображению
    img = {'photo': (os.path.split(imgPath)[1], open(imgPath, 'rb'))}

    # Получаем ссылку для загрузки изображений
    method_url = 'https://api.vk.com/method/photos.getWallUploadServer?'
    data = dict(access_token=token, gid=gid)
    response = requests.post(method_url, data)
    result = json.loads(response.text)
    print result
    upload_url = result['response']['upload_url']

    # Загружаем изображение на url
    response = requests.post(upload_url, files=img)
    result = json.loads(response.text)

    # Сохраняем фото на сервере и получаем id
    method_url = 'https://api.vk.com/method/photos.saveWallPhoto?'
    data = dict(access_token=token, gid=gid, photo=result['photo'], hash=result['hash'], server=result['server'])
    response = requests.post(method_url, data)
    resultPhoto = json.loads(response.text)['response'][0]['id']



    audio = {'file': (os.path.split(mp3Path)[1], open(mp3Path, 'rb'))}
    # Получаем ссылку для загрузки изображений
    method_url = 'https://api.vk.com/method/audio.getUploadServer?'
    data = dict(access_token=token, gid=gid)
    response = requests.post(method_url, data)
    result = json.loads(response.text)
    upload_url = result['response']['upload_url']

    # Загружаем изображение на url
    response = requests.post(upload_url, files=audio)
    result = json.loads(response.text)

    # Сохраняем фото на сервере и получаем id
    method_url = 'https://api.vk.com/method/audio.save?'
    data = dict(access_token=token, gid=gid, audio=result['audio'], hash=result['hash'], server=result['server'])
    response = requests.post(method_url, data)
    resultAid = json.loads(response.text)['response']['aid']
    result = json.loads(response.text)['response']['owner_id']
    a = api.audio.get()
    api.wall.post(message='#MadeByWaveRiderChatbot', attachments='{0},audio{1}_{2}'.format(resultPhoto, result, resultAid))


def generate_markup():
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Опубликовать в VK')
    markup.add('Хочу еще')
    markup.add('Отмена')
    return markup


def process_item(message, text=None, attachment=None, date=None, *args, **kwargs):
    if attachment:
        typeof = attachment.get("type", False)
        if typeof == "photo":
            file = urllib2.urlopen(attachment["photo"]["src_big"])
            raw_bytes = BytesIO(file.read())  # Байты картинки
            raw_bytes.name = "photo.png"
            bot.send_photo(message.chat.id, raw_bytes)  # Отправить фото адресату
            # Закрыть соединение
            file.close()
            raw_bytes.close()
        elif typeof == "link":
            # Если вложение - ссылка, то просто отпралвляем
            bot.send_message(message.chat.id, "%s|%s" % (attachment["link"]["url"], attachment["link"]["title"]))
    bot.send_message(message.chat.id, time.strftime("%d.%m.%y %X", time.gmtime(date)))
    if text:
        # Отправить текст
        for partial in telebot.util.split_string(text.replace("<br>", "\n"), 3000):
            bot.send_message(message.chat.id, partial)  # Отправляем частями
            time.sleep(2)
        bot.send_message(message.chat.id, "-----------------------------------------")  # Разделитель


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(chat_id=message.chat.id,
                     text='Привет, {0} {1}!\nТебе нужно что-то запостить?\nЯ подберу подходящую музыку {2} под пост и опубликую его для тебя в vk.\n'
                          'Я могу работать как с текстом и фотографиями. Просто отправь мне всё необходимое.\n\n'
                     .format(message.from_user.first_name, '\xE2\x9C\x8B', '\xF0\x9F\x8E\xB6'))


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(chat_id=message.chat.id,
                     text='Я подберу для тебя музыку {0}, подходящую под загруженную фотографию или текст. '
                          'Уточню результат, если потребуется. Загружу найденную песню, '
                          'а также смогу опубликовать сгенерированный пост на твоей старнице в VK.'
                     .format('\xF0\x9F\x8E\xA7'))


@bot.message_handler(func=lambda message: True, content_types=['text'])
def parse_message(message):
    users_id = read_users(config.users_token)
    strToFind = 'https:.+access_token=(.+)\&expires_in=.+'
    if u"Опубликовать в VK" == message.text:
        if not users_id.get(str(message.chat.id)):

            keyboard = telebot.types.InlineKeyboardMarkup()
            url_button = telebot.types.InlineKeyboardButton(text="Перейти в VK", url=link)
            keyboard.add(url_button)
            bot.send_message(chat_id=message.chat.id,
                             text='Прости {0}, но я не смогу обновить твою стену, '
                                  'пока ты не пришлешь мне текст из адресной строки, '
                                  'после перехода по ссылке:'
                             .format('\xF0\x9F\x98\x94'), reply_markup=keyboard)
        else:
            make_post(token=users_id[str(message.chat.id)]['token'], imgPath='/home/andrew/Projects/WaveRiderChatbot/photos/tmp.jpg',
            mp3Path='/home/andrew/Projects/WaveRiderChatbot/music/{}.mp3'.format(message.chat.id))
            bot.send_message(chat_id=message.chat.id,
                             text='Отлично! Не будем останавливаться)\n'
                                  'Отправь мне фотографию или текст.', reply_markup=generate_markup())
    elif 'https' in message.text:
        try:
            users_id[str(message.chat.id)] = {'token': findall(strToFind, message.text)[0]}
            try:
                with open(config.users_token, 'w') as base:
                    base.write(json.dumps(users_id))
            except:
                bot.send_message(chat_id=message.chat.id,
                                 text='Память у меня сдает в последнее время{0}.\n'
                                      'не могу тебя запомнить.'.format('\xF0\x9F\x98\x94'), reply_markup=generate_markup())
        except:
            bot.send_message(chat_id=message.chat.id,
                             text='Не могу найти токен.\n '
                                 'Проверь, пожалуйста, скопированную строку и пришли мне ее еще раз')
        else:
            make_post(token=users_id[str(message.chat.id)]['token'], imgPath='/home/andrew/Projects/WaveRiderChatbot/photos/tmp.jpg',
            mp3Path='/home/andrew/Projects/WaveRiderChatbot/music/{}.mp3'.format(message.chat.id))
            bot.send_message(chat_id=message.chat.id,
                             text='Отлично! Не будем останавливаться)\n'
                                  'Отправь мне фотографию или текст.', reply_markup=generate_markup())
    elif u"Хочу еще" == message.text:
        if str(message.chat.id) in users.keys():
            print "dddd"
            lyrics = users[str(message.chat.id)]["nbest"]
            print len(lyrics.keys())
            sent_key = users[str(message.chat.id)]["sent_song"]
            lyrics.pop(sent_key)
            print len(lyrics.keys())
        else:
            lyrics = {}

        if lyrics:
            id_song = list(lyrics.keys())[0]
            song = request_sender.getSong(id_song)
            users[str(message.chat.id)] = {}
            users[str(message.chat.id)]["nbest"] = lyrics
            users[str(message.chat.id)]["sent_song"] = id_song
            # bot.send_audio(message.chat.id, song, reply_markup=generate_markup())

            if not os.path.isdir('music'):
                os.mkdir('music')
            fileMP3 = 'music/'+ str(message.chat.id) + '.mp3'
            f = open(fileMP3, 'wb')
            f.write(urllib2.urlopen('http://f.muzis.ru/' + song['file_mp3']).read())
            f.close()
            bot.send_chat_action(message.chat.id, 'upload_audio')
            audio = open(fileMP3, 'rb')

            temp = bot.send_audio(message.chat.id, audio, title='%s' % (song['track_name']),
             timeout = 1000, reply_markup = generate_markup() ) # reply_to_message_id=message.message_id) #, reply_markup=markup)
            audio.close()
        else:
            bot.send_message(chat_id=message.chat.id,
                             text='Подходящие песни закончились(. Может попробуем снова?\n'
                                  'Отправь мне фотографию или текст.', reply_markup=telebot.types.ReplyKeyboardHide())
            users[str(message.chat.id)] = {}
            users[str(message.chat.id)]["nbest"] = {}
            users[str(message.chat.id)]["sent_song"] = ''
    elif u"Отмена" == message.text:
        bot.send_message(chat_id=message.chat.id,
                         text='Прости, что не получилось. Может попробуем еще раз?\n'
                              'Отправь мне фотографию или текст.', reply_markup=telebot.types.ReplyKeyboardHide())
    else:
        users_discr = message.text.encode("utf-8")
        if str(message.chat.id) in users.keys():
            if "pic_seen" not in users[str(message.chat.id)].keys():
                users[str(message.chat.id)]["user_discr"] = users_discr
                print "pic_seen"
                lyrics = {}
                users[str(message.chat.id)]["song_styles"] = {}
                for style in big_lyrics.keys():
                    cur_lyrics = big_lyrics[style]
                    if cur_lyrics:
                        best_song_id = TextMatcher.find_song_with_the_best_text(users_discr, cur_lyrics, text_matcher)
                        lyrics[best_song_id] = cur_lyrics[best_song_id]
                        users[str(message.chat.id)]["song_styles"][best_song_id] = style
            else:
                lyrics = users[str(message.chat.id)]["nbest"]
                print len(lyrics.keys())
                sent_key = users[str(message.chat.id)]["sent_song"]
                lyrics.pop(sent_key)
        else:
            print "notident"
            users[str(message.chat.id)] = {}
            users[str(message.chat.id)]["user_discr"] = users_discr
            lyrics = {}
            users[str(message.chat.id)]["song_styles"] = {}
            for style in big_lyrics.keys():
                print style
                cur_lyrics = big_lyrics[style]
                # print cur_lyrics.keys()
                if cur_lyrics:
                    best_song_id = TextMatcher.find_song_with_the_best_text(users_discr, cur_lyrics, text_matcher)
                    lyrics[best_song_id] = cur_lyrics[best_song_id]
                    users[str(message.chat.id)]["song_styles"][best_song_id] = style
            print lyrics.keys()
            # lyrics = {}

        if lyrics:

            best_song_id = TextMatcher.find_song_with_the_best_text(users_discr, lyrics, text_matcher)
            song = request_sender.getSong(best_song_id)
            users[str(message.chat.id)]["sent_song"] = best_song_id
            users[str(message.chat.id)]["nbest"] = lyrics

            if not os.path.isdir('music'):
                os.mkdir('music')
            fileMP3 = 'music/'+ str(message.chat.id) + '.mp3'
            f = open(fileMP3, 'wb')
            f.write(urllib2.urlopen('http://f.muzis.ru/' + song['file_mp3']).read())
            f.close()
            bot.send_chat_action(message.chat.id, 'upload_audio')
            audio = open(fileMP3, 'rb')

            temp = bot.send_audio(message.chat.id, audio, title='%s' % (song['track_name']),
             timeout = 1000, reply_markup = generate_markup() ) # reply_to_message_id=message.message_id) #, reply_markup=markup)
            audio.close()
        else:
            bot.send_message(chat_id=message.chat.id,
                             text='Подходящие песни закончились(. Может попробуем снова?\n'
                                  'Отправь мне фотографию или текст.', reply_markup=telebot.types.ReplyKeyboardHide())

            if str(message.chat.id) not in users.keys():
                users[str(message.chat.id)] = {}
            users[str(message.chat.id)]["nbest"] = {}
            users[str(message.chat.id)]["sent_song"] = ''


@bot.message_handler(func=lambda message: True, content_types=['photo'])
def get_image(message):
    bot.send_chat_action(message.chat.id, "upload_photo")

    height_list = []
    for ph in message.photo:
        height_list.append(ph.height)
    photo_ind = np.argmax(height_list)

    file_info = bot.get_file(message.photo[photo_ind].file_id)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(config.bot_token, file_info.file_path))
    photo_name = os.path.join('photos', 'tmp.jpg')
    if not os.path.isdir('photos'):
        os.mkdir('photos')
    f = open(photo_name, 'wb')
    f.write(file.content)
    f.close()

    img = np.array(Image.open(photo_name))
    res = net.predict([img])

    styles = []
    with open('style_names.txt') as style_f:
        for line in style_f:
            styles.append(line.strip())

    print styles[np.argmax(res[0])]

    style = request_sender.parseVector(res[0])
    print type(style)
    print "q"
    # print users[str(message.chat.id)].keys()
    if str(message.chat.id) in users.keys():
        users[str(message.chat.id)]["pic_seen"] = True
        print "r"
        if "song_styles" in users[str(message.chat.id)].keys():
            print "t"
            song_styles = users[str(message.chat.id)]["song_styles"]
            song_styles_inv = {song_styles[c_key]:c_key for c_key in song_styles.keys()}
            if style in song_styles_inv.keys():
                id_song = song_styles_inv[style]
            else:
                id_song = np.random.choice(song_styles.keys())
            song_styles.pop(id_song)
            users[str(message.chat.id)]["song_styles"] = song_styles

            song = request_sender.getSong(id_song)
            if not os.path.isdir('music'):
                os.mkdir('music')
            fileMP3 = 'music/'+ str(message.chat.id) + '.mp3'
            f = open(fileMP3, 'wb')
            f.write(urllib2.urlopen('http://f.muzis.ru/' + song['file_mp3']).read())
            f.close()
            bot.send_chat_action(message.chat.id, 'upload_audio')
            audio = open(fileMP3, 'rb')

            temp = bot.send_audio(message.chat.id, audio, title='%s' % (song['track_name']),
            timeout = 1000, reply_markup = generate_markup() ) # reply_to_message_id=message.message_id) #, reply_markup=markup)
            audio.close()
        else:
            print "y"
            lyrics = request_sender.sendRequest(style, 200)

            if lyrics:
                id_song = list(lyrics.keys())[0]
                song = request_sender.getSong(id_song)
                if str(message.chat.id) not in users.keys():
                    users[str(message.chat.id)] = {}
                users[str(message.chat.id)]["nbest"] = lyrics
                users[str(message.chat.id)]["sent_song"] = id_song
                # bot.send_audio(message.chat.id, song, reply_markup=generate_markup())

                if not os.path.isdir('music'):
                    os.mkdir('music')
                fileMP3 = 'music/'+ str(message.chat.id) + '.mp3'
                f = open(fileMP3, 'wb')
                f.write(urllib2.urlopen('http://f.muzis.ru/' + song['file_mp3']).read())
                f.close()
                bot.send_chat_action(message.chat.id, 'upload_audio')
                audio = open(fileMP3, 'rb')

                temp = bot.send_audio(message.chat.id, audio, title='%s' % (song['track_name']),
                 timeout = 1000, reply_markup = generate_markup() ) # reply_to_message_id=message.message_id) #, reply_markup=markup)
                audio.close()
            else:
                bot.send_message(chat_id=message.chat.id,
                                 text='Прости, что неполучилось. Может попробуем еще раз?\n'
                                      'Отправь мне фотографию или текст.', reply_markup=telebot.types.ReplyKeyboardHide())

                if str(message.chat.id) not in users.keys():
                    users[str(message.chat.id)] = {}
                users[str(message.chat.id)]["nbest"] = {}
                users[str(message.chat.id)]["sent_song"] = ''
    else:
        users[str(message.chat.id)] = {}
        users[str(message.chat.id)]["pic_seen"] = True
        print "b"
        lyrics = request_sender.sendRequest(style, 200)

        if lyrics:
            id_song = list(lyrics.keys())[0]
            song = request_sender.getSong(id_song)
            if str(message.chat.id) not in users.keys():
                users[str(message.chat.id)] = {}
            users[str(message.chat.id)]["nbest"] = lyrics
            users[str(message.chat.id)]["sent_song"] = id_song
            # bot.send_audio(message.chat.id, song, reply_markup=generate_markup())

            if not os.path.isdir('music'):
                os.mkdir('music')
            fileMP3 = 'music/'+ str(message.chat.id) + '.mp3'
            f = open(fileMP3, 'wb')
            f.write(urllib2.urlopen('http://f.muzis.ru/' + song['file_mp3']).read())
            f.close()
            bot.send_chat_action(message.chat.id, 'upload_audio')
            audio = open(fileMP3, 'rb')

            temp = bot.send_audio(message.chat.id, audio, title='%s' % (song['track_name']),
             timeout = 1000, reply_markup = generate_markup() ) # reply_to_message_id=message.message_id) #, reply_markup=markup)
            audio.close()
        else:
            bot.send_message(chat_id=message.chat.id,
                             text='Прости, что неполучилось. Может попробуем еще раз?\n'
                                  'Отправь мне фотографию или текст.', reply_markup=telebot.types.ReplyKeyboardHide())

            if str(message.chat.id) not in users.keys():
                users[str(message.chat.id)] = {}
            users[str(message.chat.id)]["nbest"] = {}
            users[str(message.chat.id)]["sent_song"] = ''


if __name__ == '__main__':
    users = read_users(config.users_name)

    bot.polling(none_stop=True)
