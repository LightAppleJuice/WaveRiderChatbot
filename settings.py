# coding=UTF-8
from ConfigParser import ConfigParser
from os import path


class settings():
    """
    Класс, в котором содержатся все настройки параметров бота, базы и т.д.
    """

    def __init__(self):
        _parser = ConfigParser()
        _parser.read(path.join(path.dirname(__file__), 'config.ini'))

        self.bot_token = _parser.get('COMMON', 'bot_token')
        self.id_vkapi = _parser.get('COMMON', 'id_vkapi')

        self.database_name = _parser.get('DIRS', 'database_name')
        self.styles_codes = _parser.get('DIRS', 'styles_codes')
        self.styles_names = _parser.get('DIRS', 'styles_names')
        self.users_name = _parser.get('DIRS', 'users_name')
        self.users_token = _parser.get('DIRS', 'users_token')
        self.log = _parser.get('DIRS', 'log')
        self.w2vec_model = _parser.get('DIRS', 'w2v_model')
        self.w2vec_dict = _parser.get('DIRS', 'w2v_dict')
        self.eng_rus_dict = _parser.get('DIRS', 'eng_rus_dict')
        self.cnn_style_model = _parser.get('DIRS', 'cnn_style_model')
        self.cnn_style_pretrained = _parser.get('DIRS', 'cnn_style_pretrained')
        self.cnn_style_mean = _parser.get('DIRS', 'cnn_style_mean')
