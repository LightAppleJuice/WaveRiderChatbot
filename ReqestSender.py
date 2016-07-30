import requests
from settings import settings
import Commands
import io

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
         #parsing
         targetStyle = None
         for idx, value in enumerate(vector):
             elem = self.matching[self.CNNstyles[idx]]
             minValue = 0.0#elem[0]
             maxValue = 1.0#elem[1]
             if (value > minValue) & (value < maxValue):
                 targetStyle = elem[2]
                 break
         return targetStyle

     def sendRequest(self, style):
         params = {'values': str(style), 'size': 200}
         try:
            r = requests.post("http://muzis.ru/api/stream_from_values.api", data=params)
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
         try:
             r = requests.post("http://muzis.ru/api/stream_from_obj.api", data=params)
             parsed_string = r.json()
             songs = parsed_string['songs']
             song = songs[0]['file_mp3']

             return song
         except:
             self.logger.siteWarning()
         return


# RS = RequestSender()
# targetStyle = RS.parseVector([0.02495627,  0.01625971, 0.05735248,  0.03012436, 0.01382483,  0.01830654,
#   0.02935727,  0.02657287,  0.02752874,  0.00897765,  0.01500904,  0.01215811,
#   0.02771803,  0.23560295,  0.01554973,  0.01857543, 0.03318637,  0.17324899,
#   0.18867876,  0.02701183])
# lyr = RS.sendRequest(targetStyle)
# s = RS.getSong(33301)


