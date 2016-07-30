import numpy as np
import logging
import re

class Word2Vec:
    def __init__(self):
        self.w2v = 0  # word2vec model
        self.dict = {}  # word2vec dictionary
        self.num_of_occur = []  # number of occurrences for words in the dictionary
        self.dim = 0  # dimensionality of words vector space
        self.num_words = 0  # the total number of words

    def load_word2vec_model(self, w2v_file):
        """
            loads word2vec model
            w2v_file -- file with word2vec model
            w2v_file: format: first 8 bytes = 2 uints for the number of words and dimensionality of w2v space
                         the rest of the file -- w2v matrix [dim, num_words]
        """
        self.w2v = np.load(w2v_file)
        self.num_words = np.shape(self.w2v)[1]-1
        self.dim = np.shape(self.w2v)[0]

    def covert_from_words_to_vecs(self, word_data):
        """
            convert words from word_data to vectors representations
            :param word_data: list of lists of words
            :return: list of np arrays of vector representations ((dim w2v) x (number of words))
        """
        num_sent = len(word_data)
        wordvec_data = [None] * num_sent
        for sent_num in range(num_sent):
            num_words = len(word_data[sent_num])
            # in the last column of w2v there is a vector for unknown words
            wordvec_data[sent_num] = np.zeros((self.dim, num_words)) + np.reshape(self.w2v[:, -1], (self.dim, 1))
            for word_num in range(num_words):
                try:
                    cur_word_position = self.dict[word_data[sent_num][word_num]]
                    wordvec_data[sent_num][:, word_num] = self.w2v[:, cur_word_position]
                except KeyError:
                    curWord = word_data[sent_num][word_num]
                    logging.debug("Can't find the word " + curWord + " in dictionary. ")
        return wordvec_data
        
        
    def load_word2vec_dictionary(self, dict_file):
            """
                loads word2vec dictionary
                dict_file -- file with word2vec dictionary
                dict_file: format: word number_of_occurrences
            """
            with open(dict_file) as dictionary:
                line_num = 0
                if self.num_of_occur:
                    self.num_of_occur = []
                    logging.info("Nonempty vocabulary in Word2Vec Class. That's weird.")
                for line in dictionary:
                    line = re.sub('\s+$', '', line)
                    cur_word, cur_num_of_occur = re.split('\s+', line)
                    self.dict[cur_word] = line_num
                    self.num_of_occur.append(float(cur_num_of_occur))
                    line_num += 1