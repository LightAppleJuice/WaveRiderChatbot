import requests
from settings import settings
import Commands
import io
import numpy as np

config = settings()

class RequestSender:
     def __init__(self):
         self.logger = Commands.workWithLog(config.log)
         self.matching = dict()
         self.CNNstyles = []
         self.loadMatching()

     def loadMatching(self):
         stylesCodes = {}
         with io.open(config.styles_codes) as f_styles:
             for line in f_styles:
                 lineSplit = line.strip('\n').split('\t')
                 stylesCodes[lineSplit[1]] = lineSplit[0].encode('utf-8')

         with io.open(config.database_name) as file:
             for line in file:
                 lineSplit = line.strip('\n').split('\t')
                 imgStyle = lineSplit[0]
                 muzisStyle = lineSplit[1].split(', ')
                 self.CNNstyles.append(imgStyle)
                 self.matching[imgStyle] = []
                 for s in muzisStyle:
                     code = stylesCodes[s]
                     self.matching[imgStyle].append(stylesCodes[s])
         return

     def parseVector(self, vector):
         print vector
         targetStyle = None
         idx = np.argmax(vector)
         targetStyles = self.matching[self.CNNstyles[idx]]
         return targetStyles

     def sendRequest(self, styles, size):
         allLyrics = dict()
         for currStyle in styles:
             params = {'values': currStyle, 'size': size}
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
                            lyrics = song['lyrics'].encode('utf-8')
                            allLyrics[str(id)] = lyrics
             except:
                 self.logger.siteWarning()
         return allLyrics

     def getSong(self, id):
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
             self.logger.siteWarning()
         return song


# RS = RequestSender()
# targetStyle = RS.parseVector([0.02495627,  0.01625971, 0.05735248,  0.03012436, 0.01382483,  0.01830654,
#    0.02935727,  0.02657287,  0.02752874,  0.00897765,  0.01500904,  0.51215811,
#    0.02771803,  0.23560295,  0.01554973,  0.01857543, 0.03318637,  0.17324899,
#    0.18867876,  0.02701183])
# lyr = RS.sendRequest(targetStyle, 3)
#s = RS.getSong(33301)
