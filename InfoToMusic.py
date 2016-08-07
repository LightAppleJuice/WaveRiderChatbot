# Image and text processing
__author__ = 'g.lavrentyeva'

import logging
from settings import settings
import os
import numpy as np
import urllib2
#import TextProcessing


class InfoToMusic:
    def __init__(self, user_id, request_sender, allLyrics, _textProcModels, _image_processor):
        self.config = settings()
        self.user_id = user_id

        self.request_sender = request_sender
        self.allLyrics = allLyrics

        self.logger = logging.getLogger('BotLogger.InfoToMusic')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(self.config.log)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        self.image_processor = _image_processor
        #self.textProc = TextProcessing(_textProcModels)

        self.userImage = None
        self.userText = None

        data_path = os.path.join('..', 'wave_rider_bot_data')
        if not os.path.isdir(data_path):
            os.mkdir(data_path)

        photo_data_path = os.path.join(data_path, 'photos')
        if not os.path.isdir(photo_data_path):
            os.mkdir(photo_data_path)
        self.imgFileName = os.path.join(photo_data_path, '%s_photo.jpg' % self.user_id)

        music_data_path = os.path.join(data_path, 'music')
        if not os.path.isdir(music_data_path):
            os.mkdir(music_data_path)
        self.userSongFilePath = os.path.join(music_data_path, self.user_id)
        if not os.path.isdir(self.userSongFilePath):
            os.mkdir(self.userSongFilePath)

        self.relevantSongs = {}

    def save_photo(self, photo_file):
        with open(self.imgFileName, 'wb') as f:
            f.write(photo_file.content)
        self.userImage = True
        self.logger.info('Image saved: ' + self.imgFileName)

    def process(self):
        if self.userImage:
            self.process_img()
            self.userImage = False
        elif self.userText:
            self.process_text()

    def process_img(self):
        batch_size = 200

        self.logger.info('Process users image.')
        styles_prob = self.image_processor.process_styles(self.imgFileName)
        target_styles = self.request_sender.parseVector(styles_prob)
        self.relevantSongs = self.request_sender.sendRequest(target_styles, batch_size, 2)

    def process_text(self):
        self.logger.info('Process users text.')

    def get_song(self):
        random_key = np.random.permutation(self.relevantSongs.keys())[0]
        id_song = self.relevantSongs[random_key]
        song = self.request_sender.getSong(id_song)

        file_mp3_name = os.path.join(self.userSongFilePath, '%s.mp3' % id_song)
        with open(file_mp3_name, 'wb') as f:
            f.write(urllib2.urlopen('http://f.muzis.ru/' + song['file_mp3']).read())

        del self.relevantSongs[id_song]

        return song, file_mp3_name

    def clearAll(self):
        self.userImage = []
        self.userText = ''
        self.songFilePath = ''

