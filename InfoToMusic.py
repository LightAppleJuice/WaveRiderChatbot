# Image and text processing
__author__ = 'g.lavrentyeva'

import logging
import settings
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

    def process(self, img, text):
        if img:
            self.logger.info('Process users image.')
        elif text:
            self.logger.info('Process users text.')
        else:
            self.logger.warning('No text no image to process')
        return

