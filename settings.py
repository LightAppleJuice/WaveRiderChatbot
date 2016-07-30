# coding=UTF-8
"""
Created on 17.06.2016

@author: A. Plistik
"""
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
        self.target_url = _parser.get('COMMON', 'target_url')
        self.post_mask_url = _parser.get('COMMON', 'post_mask_url')
        self.sleep_time = _parser.get('COMMON', 'sleep_time')

        self.database_name = _parser.get('DIRS', 'database_name')
        self.database_styles = _parser.get('DIRS', 'database_styles')
        self.last_post = _parser.get('DIRS', 'last_post')
        self.log = _parser.get('DIRS', 'log')