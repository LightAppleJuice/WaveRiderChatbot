import requests
from settings import settings
import os
import logging
import io
import numpy as np
import sys
import urllib2

__author__ = 'g.lavrentyeva'


class RequestSender:
    def __init__(self):
        self.config = settings()

        self.logger = logging.getLogger('BotLogger.RequestSender')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(self.config.log)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        self.matching = dict()
        self.CNNstyles = []
        self.loadMatching()

    # Loading muzis-img mathcing styles
    def loadMatching(self):
        self.logger.info('Loading Matching')
        stylesCodes = {}
        with io.open(self.config.styles_codes, encoding='cp1251') as f_styles:
            for line in f_styles:
                lineSplit = line.strip('\n').split('\t')
                stylesCodes[lineSplit[1]] = lineSplit[0].encode('utf-8')
        with io.open(self.config.database_name, encoding='cp1251') as file:
            for line in file:
                lineSplit = line.strip('\n').split('\t')
                imgStyle = lineSplit[0]
                muzisStyle = lineSplit[1].split(', ')
                self.CNNstyles.append(imgStyle)
                self.matching[imgStyle] = []
                for s in muzisStyle:
                    self.matching[imgStyle].append(stylesCodes[s])
        return

    # Parsing img CNN result vector
    # Return the appropriate muzis styles
    def parseVector(self, vector):
        self.logger.info('Parsing Vector: ' + str(vector))
        targetStyles = None
        idx = np.argmax(vector)
        targetStyles = self.matching[self.CNNstyles[idx]]
        self.logger.info('Target style: ' + str(targetStyles))
        return targetStyles

    # Send request by list of styles
    # Return dictionary with structure id: (track_name, lyrics)
    def sendRequest(self, styles, size, offset=0):
        self.logger.info('Sending Request for styles: ' + str(styles) + ' size: ' + str(size) + ' offset: ' + str(offset))
        allLyrics = dict()
        for currStyle in styles:
            params = {'values': currStyle, 'size': size, 'offset': offset}
            try:
                r = requests.post("http://muzis.ru/api/stream_from_values.api", data=params)
                parsed_string = r.json()
                if r.status_code != 200:
                    raise Exception('Muzis exception: Bad response')

                if 'error' in parsed_string:
                    if parsed_string['error'] == 403:
                        raise Exception('Muzis exception: Access denied')
                    if parsed_string['error'] == 404:
                        raise Exception('Muzis exception: Object not found')
                    if parsed_string['error'] == 402:
                        raise Exception('Muzis exception: Incorrect request')
                    else:
                        raise Exception('Muzis exception: Unknown exception')
                else:
                    songs = parsed_string['songs']
                    # print songs
                    for j, song in enumerate(songs):
                        id = song['id']
                        if id not in allLyrics:
                            name = song['track_name'].encode('utf-8')
                            lyrics = song['lyrics'].encode('utf-8')
                            allLyrics[str(id)] = name, lyrics
            except:
                self.logger.warning(sys.exc_info()[0])
        return allLyrics

    # Only for downloading all lyrics
    def sendSearchRequest(self, style, size, offset=0):
        self.logger.info('Sending Search Request for styles: ' + str(style) + ' size: ' + str(size) + ' offset: ' + str(offset))
        allLyrics = dict()
        params = {'q_value': style, 'size': size, 'offset': offset, 'sort': 'id'}
        try:
            r = requests.post("http://muzis.ru/api/search.api", data=params)
            parsed_string = r.json()
            if r.status_code != 200:
                raise Exception('Muzis exception: Bad response')

            if 'error' in parsed_string:
                error = parsed_string['error']
                if error['q_value'] == 403:
                    raise Exception('Muzis exception: Access denied')
                if error['q_value'] == 404:
                    raise Exception('Muzis exception: Object not found')
                if error['q_value'] == 402:
                    raise Exception('Muzis exception: Incorrect request')
                else:
                    raise Exception('Muzis exception: Unknown exception')
            else:
                songs = parsed_string['songs']
                # print songs
                for j, song in enumerate(songs):
                    id = song['id']
                    if id not in allLyrics:
                        lyrics = song['lyrics'].encode('utf-8')
                        allLyrics[str(id)] = lyrics
        except:
            self.logger.warning(sys.exc_info()[0])
        return allLyrics

    # Get song by id
    # Return muzis object
    def getSong(self, id):
        self.logger.info('Sending get Song Request for id: ' + str(id))
        params = {'type': 2, 'id': id}
        song = None
        try:
            r = requests.post("http://muzis.ru/api/stream_from_obj.api", data=params)
            parsed_string = r.json()
            if r.status_code != 200:
                raise Exception('Muzis exception: Bad response')

            if 'error' in parsed_string:
                if parsed_string['error'] == 403:
                    raise Exception('Muzis exception: Access denied')
                if parsed_string['error'] == 404:
                    raise Exception('Muzis exception: Object not found')
                if parsed_string['error'] == 402:
                    raise Exception('Muzis exception: Incorrect request')
                else:
                    raise Exception('Muzis exception: Unknown exception')
            else:
                songs = parsed_string['songs']
                song = songs[0]
        except:
            self.logger.warning(sys.exc_info()[0])
        return song

    def getSongLyric(self, id):
        self.logger.info('Sending get Song Lyrics Request for id: ' + str(id))
        song = self.getSong(id)
        lyrics = None
        if song:
            name = song['track_name']
            params = {'q_track': name, 'sort': 'id'}
            try:
                r = requests.post("http://muzis.ru/api/search.api", data=params)
                parsed_string = r.json()
                if r.status_code != 200:
                    raise Exception('Muzis exception: Bad response')

                if 'error' in parsed_string:
                    error = parsed_string['error']
                    if error['q_value'] == 403:
                        raise Exception('Muzis exception: Access denied')
                    if error['q_value'] == 404:
                        raise Exception('Muzis exception: Object not found')
                    if error['q_value'] == 402:
                        raise Exception('Muzis exception: Incorrect request')
                    else:
                        raise Exception('Muzis exception: Unknown exception')
                else:
                    songs = parsed_string['songs']
                    # print songs
                    for j, song in enumerate(songs):
                        id = song['id']
                        lyrics = song['lyrics'].encode('utf-8')
            except:
                self.logger.warning(sys.exc_info()[0])
            return lyrics

        else:
            return None

    def getSongPoster(self, id):
        self.logger.info('Sending get Song Poster Request for id: ' + str(id))
        song = self.getSong(id)
        poster = None
        if song:
            poster = urllib2.urlopen('http://f.muzis.ru/' + song['poster']).read()
        return poster

    def getAllStyles(self):
        self.logger.info('Getting all using styles.')
        styles = [];
        for imgStyle in self.CNNstyles:
            styles.append(muzStyle for muzStyle in self.matching[imgStyle])
        return styles

    def saveAllLyricsByID(self, path):
        self.logger.info('Saving all lyrics by id.')
        with io.open(self.config.styles_codes) as f_styles:
            #path = r'C:\ChatBot\WaveRiderChatbot\all_lyrics\\all_id'
            if not os.path.exists(path):
                os.makedirs(path)
            for id in range(1, 50000):
                lyrics = self.getSongLyric(str(id))
                if lyrics:
                    if not lyrics == '':
                        with open(path + "\\" + str(id) + '.txt', "w") as text_file:
                            text_file.write(lyrics)

    def saveAllPostersByID(self, path):
        self.logger.info('Saving all posters by id.')
        with io.open(self.config.styles_codes) as f_styles:
            # path = r'C:\ChatBot\WaveRiderChatbot\all_lyrics\\all_id'
            if not os.path.exists(path):
                os.makedirs(path)
            for id in range(1, 50000):
                img = self.getSongPoster(str(id))
                if img:
                    with open(path + "\\" + str(id) + '.jpg', 'wb') as img_file:
                        img_file.write(img)

    def saveAllLyricsByLang(self, path):
        self.logger.info('Saving all lyrics by language.')
        with io.open(self.config.styles_codes) as f_styles:
            language = {'1104': 'russian', '125': 'english'}
            for lan in language.keys():
                # path = r'C:\ChatBot\WaveRiderChatbot\all_lyrics\\' + language[lan]
                if not os.path.exists(path):
                    os.makedirs(path)
                for i in range(0, 50):
                    lyrics = self.sendSearchRequest(lan, 200, i * 200)
                    if lyrics:
                        for lyr in lyrics.keys():
                            if not lyrics[lyr] == '':
                                with open(path + "\\" + lyr + '.txt', "w") as text_file:
                                    text_file.write(lyrics[lyr])

# test
# rs = RequestSender()
# st = rs.parseVector([0.02495627,  0.01625971, 0.05735248,  0.03012436, 0.01382483,  0.01830654,
#                        0.02935727,  0.02657287,  0.02752874,  0.00897765,  0.01500904,  0.51215811,
#                        0.02771803,  0.23560295,  0.01554973,  0.01857543, 0.03318637,  0.17324899,
#                        0.18867876,  0.02701183])
#
# res = rs.sendRequest(st, 100)
# print len(res)
