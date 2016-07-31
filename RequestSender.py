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
         self.CNNstyles = [];
         self.loadMatching()

     def loadMatching(self):
         with io.open(config.database_name) as file:
             for idx, line in enumerate(file):
                 lineSplit = line.strip('\n').split(' ')
                 self.CNNstyles.append(str(lineSplit[0]))
                 self.matching[str(lineSplit[0])] = lineSplit[1:len(lineSplit)]
         return

     def parseVector(self, vector):
         print vector
         targetStyle = None
         idx = np.argmax(vector)
         elem = self.matching[self.CNNstyles[idx]]
         targetStyle = elem[2]
         return targetStyle

     def sendRequest(self, style, size):
         params = {'values': str(style), 'size': size}
         try:
            r = requests.post("http://muzis.ru/api/stream_from_values.api", data=params)
            if r.status_code == 403:
                raise Exception('Muzis exception: Access denied')
            if r.status_code == 404:
                raise Exception('Muzis exception: Object not found')
            if r.status_code != 200:
                raise Exception('Muzis exception: Unknown exception')
            parsed_string = r.json()
            songs = parsed_string['songs']
            allLyrics = dict()
            for j, song in enumerate(songs):
                id = song['id']
                lyrics = song['lyrics'].encode('utf-8')
                allLyrics[str(id)] = lyrics
            return allLyrics
         except:
             self.logger.siteWarning()
         return

     def getSong(self, id):
         params = {'type': 2, 'id': id}
         song = None
         try:
             r = requests.post("http://muzis.ru/api/stream_from_obj.api", data=params)
             if r.status_code == 403:
                 raise Exception('Muzis exception: Access denied')
             if r.status_code == 404:
                 raise Exception('Muzis exception: Object not found')
             if r.status_code != 200:
                 raise Exception('Muzis exception: Unknown exception')
             parsed_string = r.json()
             songs = parsed_string['songs']
            #  song = songs[0]['file_mp3']
             return songs[0]
         except:
             self.logger.siteWarning()
         return


# RS = RequestSender()
# targetStyle = RS.parseVector([0.02495627,  0.01625971, 0.05735248,  0.03012436, 0.01382483,  0.01830654,
#   0.02935727,  0.02657287,  0.02752874,  0.00897765,  0.01500904,  0.01215811,
#   0.02771803,  0.23560295,  0.01554973,  0.01857543, 0.03318637,  0.17324899,
#   0.18867876,  0.02701183])
# lyr = RS.sendRequest(targetStyle, 1)
# s = RS.getSong(33301)
