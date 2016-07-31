#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'a.smirnov'

import numpy as np
import logging
import re, os
from scipy.spatial.distance import cosine


def preprocess_train_data(train_data_in):
    train_data_out = []
    for sent in train_data_in:
        sent = preprocess_sentence(sent)
        train_data_out.append(re.split("\s+", sent))
    return train_data_out


def preprocess_sentence(sent):
    sent = sent.decode('utf-8').lower().encode('utf-8')
    sent = re.sub("[a-z]", "", sent)
    sent = re.sub(r"[/\\\.,\?!\":;\(\)\*#\'\d]", " ", sent)
    sent = re.sub("\-\s+", " ", sent)
    sent = re.sub("\s+", " ", sent)
    sent = sent.strip()
    return sent


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
            :param word_data: lists of words
            :return: np array of vector representations ((dim w2v) x (number of words))
        """

        num_words = len(word_data)
        # in the last column of w2v there is a vector for unknown words
        wordvec_data = np.zeros((self.dim, num_words)) + np.reshape(self.w2v[:, -1], (self.dim, 1))
        for word_num in range(num_words):
            try:
                cur_word_position = self.dict[word_data[word_num]]
                wordvec_data[:, word_num] = self.w2v[:, cur_word_position]
            except KeyError:
                curWord = word_data[word_num]
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


class TextMatcher:
    """
     to calc matching score for two strings of text
    """
    def __init__(self, path2model, path2dict):
        """
        :param path2model: path to word2vec model
        :param path2dict:  path to word2vec dict
        """
        self.model_path = path2model
        self.dict_path = path2dict
        self.word2vec = Word2Vec()
        self.word2vec.load_word2vec_model(self.model_path)
        self.word2vec.load_word2vec_dictionary(self.dict_path)

    def text_to_vec(self, text):
        """
        convert sentence to vector
        :param text: sentence
        :return: vector shape = (1, dim)
        """
        text_proc = preprocess_sentence(text)
        word_vecs = self.word2vec.covert_from_words_to_vecs(text_proc.split())
        sent_vec = np.average(word_vecs, axis=1)
        return sent_vec.T

    def calc_matching_score(self, text_from_user, text_from_song):
        """
            convert
        """
        u_vec = self.text_to_vec(text_from_user)
        s_vec = self.text_to_vec(text_from_song)
        # return np.dot(u_vec, s_vec)/np.sqrt(np.dot(u_vec, u_vec)*np.dot(s_vec, s_vec))
        try:
            return 1-cosine(u_vec, s_vec)
        except ValueError:
            return -1


def test_word2vec_scorer(list_song_text_files, list_test_phrases, matcher):

    def load_songs(list_songs_files):
        song_text_dict = {}
        with open(list_songs_files) as list_in:
            for f_name in list_in:
                f_name = f_name.strip()
                with open(f_name) as file_in:
                    cur_text = file_in.read()
                    song_text_dict[f_name] = cur_text
        return song_text_dict

    def load_phrs(phr_file):
        phr_list = []
        with open(phr_file) as file_in:
            for line in file_in:
                phr_list.append(line.strip())
        return phr_list

    out_file = "matchers_test.log"
    song_texts = load_songs(list_song_text_files)
    test_phrs = load_phrs(list_test_phrases)
    with open(out_file, "w") as file_out:
        for cur_phr in test_phrs:
            max_score = -1
            best_song = ""
            for c_song in song_texts.keys():
                cur_song_text = song_texts[c_song]
                cur_score = matcher.calc_matching_score(cur_phr, cur_song_text)
                if cur_score > max_score:
                    max_score = cur_score
                    best_song = c_song
            best_song_class = os.path.basename(best_song)
            file_out.write(cur_phr+"\t"+best_song_class + "\n")


def find_song_with_the_best_text(users_discr, text_dict, matcher):
    """
    :param users_discr: text that was input by user
    :param text_dict: dictionary, keys -- song_id, values -- lyrics
    :param matcher: of TextMatcher class
    :return: the best key
    """
    #TODO wtf? make it fast
    best_score = -2
    best_key = ""
    for cur_id in text_dict.keys():
        cur_text = text_dict[cur_id]
        cur_score = matcher.calc_matching_score(users_discr, cur_text)
        if cur_score > best_score:
            best_score = cur_score
            best_key = cur_id
    return best_key


if __name__ == "__main__":
    # path_to_w2v_model = "C:\\Work\\wiki word2vec\\cbow_ns_wikirumy.npy"
    # path_to_w2v_dict = "C:\\Work\\wiki word2vec\\vocab_wikirumy.dic"
    path_to_w2v_model = "/home/andrew/Projects/model/cbow_ns300_fullrostelLK4.npy"
    path_to_w2v_dict = "/home/andrew/Projects/model/cbow_ns300_fullrostelLK4.dic"

    s1 = "Привет!"
    s2 = "приветkk"
    s3 = "здравствуй а как дела"
    s4 = "пока"
    text_matcher = TextMatcher(path_to_w2v_model, path_to_w2v_dict)
    print text_matcher.calc_matching_score(s1, s2)
    print text_matcher.calc_matching_score(s1, s3)
    print text_matcher.calc_matching_score(s1, s4)

    songs_files = "list_all_ru_songs.txt"
    test_phrs_files = "list_phrs.txt"
    test_word2vec_scorer(songs_files, test_phrs_files, text_matcher)
