import requests

params = {'lyrics': 'black', 'size': 1}
r = requests.post("http://muzis.ru/api/stream_from_lyrics.api", data=params)
print(r.content)