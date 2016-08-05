# Image and text processing
__author__ = 'g.lavrentyeva'

import logging
from settings import settings
#import TextProcessing
#import ImageProcessing


class InfoToMusic:
    def __init__(self):
        self.config = settings()

        self.logger = logging.getLogger('BotLogger.InfoToMusic')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(self.config.log)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        #self.textProc = TextProcessing()
        #self.imgProc = ImageProcessing()
        self.userImage = []
        self.userText = ''
        self.imgFilePath = ''
        self.songFilePath = ''

    def process(self):
        if len(self.userImage) != 0:
            self.logger.info('Process users image.')
        elif len(self.userText) != 0:
            self.logger.info('Process users text.')
        else:
            self.logger.warning('No text no image to process')
        return

    def clearAll(self):
        self.imgFilePath = ''
        self.userImage = []
        self.userText = ''
        self.songFilePath = ''

