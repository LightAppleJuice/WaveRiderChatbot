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




from settings import settings
import telebot
from re import findall

config = settings()
bot = telebot.TeleBot(config.bot_token)

link = "https://oauth.vk.com/authorize?\
client_id=%s&display=mobile&scope=friends,wall,offline&response_type=token&v=5.45" % config.id_vkapi


def read_users(pathToBase=''):
    res = {}
    if os.path.isfile(pathToBase):
        with open(pathToBase, 'r') as base:
            res = json.loads(base.read())
    return res


def make_post(token=''):
    session = vk.Session(access_token=token)
    api = vk.API(session)
    api.wall.post(message='Hello, World!')


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
                     text='Привет, {0} {1}!\n Тебе нужно что-то запостить?\n Я подберу подходящую музыку под пост и опубликую его для тебя в vk.\n'
                          'Я могу работать как с текстом и фотографиями. Просто отправь мне всё необходимое. {2}\n\n'
                     .format(message.from_user.first_name, '\xE2\x9C\x8B', '\xF0\x9F\x99\x8A', '\xF0\x9F\x94\x8E'))


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(chat_id=message.chat.id,
                     text='В настоящий момент я могу выполнить следующие действия:\n\n'
                          '1. Определяю доминирующую эмоцию по фотографии и подобираю под нее песню {0}\n'
                          '2. Анализирую реакцию на предложенную музыку\n'
                          '3. В случае неудовольствия результатом {1}, '
                          'изучаю ответ и стараюсь выполнить поиск более точно\n'
                          '4. Публикую результат на странице в VK'
                     .format('\xF0\x9F\x8E\xA7', '\xF0\x9F\x98\xA0'))


@bot.message_handler(func=lambda message: True, content_types=['text'])
def parse_message(message):
    users = read_users(config.users_name)
    strToFind = 'https:.+access_token=(.+)\&expires_in=.+'
    if u"Опубликовать в VK" == message.text:
        if not users.get(str(message.chat.id)):

            keyboard = telebot.types.InlineKeyboardMarkup()
            url_button = telebot.types.InlineKeyboardButton(text="Перейти в VK", url=link)
            keyboard.add(url_button)
            bot.send_message(chat_id=message.chat.id,
                             text='Прости {0}, но я не смогу обновить твою стену, '
                                  'пока ты не пришлешь мне текст из адресной строки, '
                                  'после перехода по ссылке:'
                             .format('\xF0\x9F\x98\x94'), reply_markup=keyboard)
        else:
            make_post(token=users[str(message.chat.id)])
            # process_item(message=message, attachment={"type": "photo", "photo": {"src_big": r'C:\Users\1\Desktop\hockey\IMG-20160108-WA0001.jpg'}})
            bot.send_message(chat_id=message.chat.id,
                             text='Отлично! Не будем останавливаться)\n'
                                  'Отправь мне фотографию или текст.', reply_markup=generate_markup())
    elif 'https' in message.text:
        try:
            users[str(message.chat.id)] = findall(strToFind, message.text)[0]
            try:
                with open(config.users_name, 'w') as base:
                    base.write(json.dumps(users))
            except:
                bot.send_message(chat_id=message.chat.id,
                                 text='Память у меня сдает в последнее время{0}.\n'
                                      'не могу тебя запомнить.'.format('\xF0\x9F\x98\x94'), reply_markup=generate_markup())
            make_post(token=users[str(message.chat.id)])
        except:
            bot.send_message(chat_id=message.chat.id,
                             text='Не могу найти токен.\n '
                                 'Проверь, пожалуйста, скопированную строку и пришли мне ее еще раз')
        else:
            make_post(token=users[str(message.chat.id)])
            #process_item(message=message, attachment={"type": "photo", "photo": {"src_big": r'C:\Users\1\Desktop\hockey\IMG-20160108-WA0001.jpg'}})
            bot.send_message(chat_id=message.chat.id,
                             text='Отлично! Не будем останавливаться)\n'
                                  'Отправь мне фотографию или текст.', reply_markup=generate_markup())
    elif u"Хочу другую" == message.text:
        pass
    elif u"Отмена" == message.text:
        bot.send_message(chat_id=message.chat.id,
                         text='Прости, что неполучилось. Может попробуем еще раз?\n'
                              'Отправь мне фотографию или текст.', reply_markup=generate_markup())






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

    cur_style = styles[np.argmax(res[0])]

    bot.send_message(chat_id=message.chat.id, text=cur_style)


if __name__ == '__main__':
    bot.polling(none_stop=True)
