import requests
from settings import settings
import Commands
import io

config = settings()
# styles = [32500,
# 32501,
# 23508,
# 23509,
# 23515,
# 20226,
# 20229,
# 20753,
# 20230,
# 20255,
# 31723,
# 21954,
# 20259,
# 20256,
# 23556,
# 32492,
# 32491,
# 32487,
# 32486,
# 32493,
# 23481,
# 20225,
# 32494,
# 31670,
# 32489,
# 32488,
# 32490,
# 12782,
# 23561,
# 25544,
# 23471,
# 20968,
# 22464,
# 32454,
# 22453,
# 32430,
# 23472,
# 20993,
# 25126,
# 25739,
# 25543,
# 25201,
# 25203,
# 24794,
# 25357,
# 26255,
# 21159,
# 22575,
# 25938,
# ]
# for style in styles:
#     params = {'values': str(style), 'size': 1}
#     #params = {'lyrics': 'black', 'size': 1}
#     r = requests.post("http://muzis.ru/api/stream_from_values.api", data=params)
#     fid = open("D:/ChatBot/WaveRiderChatbot/test_lyrics/" + str(style) + '.txt', 'w')
#     parsed_string = r.json()
#     a = parsed_string['songs'][0]['lyrics']
#     b = a.encode('cp1251')
#     fid.write(b)
#     fid.close()

class RequestSender:
     def __init__(self):
         self.logger = Commands.workWithLog(config.log)
         self.matching = dict()
         self.loadMatching()

     def loadMatching(self):
         with io.open(config.database_styles) as file:
             for idx, line in enumerate(file):
                 lineSplit = line.split(' ')
                 self.matching[str(idx)] = lineSplit[1:len(lineSplit)]

RS = RequestSender()


