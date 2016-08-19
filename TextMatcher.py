#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'a.smirnov'

import numpy as np
import logging
import re
import os
from scipy.spatial.distance import cosine
from scipy.spatial.distance import cdist


def preprocess_train_data(train_data_in):
    train_data_out = []
    for sent in train_data_in:
        sent = preprocess_sentence(sent)
        train_data_out.append(re.split("\s+", sent))
    return train_data_out


def preprocess_sentence(sent):
    sent = sent.decode('utf-8').lower().encode('utf-8')
    sent = re.sub(r"[/\\\.,\?!\":;\(\)\*#\'\d]", " ", sent)
    sent = re.sub("\-\s+", " ", sent)
    sent = re.sub("[a-z]", "", sent)
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


def load_eng_rus_dict(dict_path):
    dict_out = {}
    with open(dict_path) as file_in:
        for line in file_in:
            line = line.strip()
            e_w, r_w = re.split("=", line)
            if e_w not in dict_out.keys():
                dict_out[e_w] = r_w
    return dict_out


class TextMatcher:
    """
     to calc matching score for two strings of text
    """
    def __init__(self, path2model, path2dict, path2engrusdict=""):
        """
        :param path2model: path to word2vec model
        :param path2dict:  path to word2vec dict
        """
        self.model_path = path2model
        self.dict_path = path2dict
        self.eng_rus_path = path2engrusdict
        self.word2vec = Word2Vec()
        self.word2vec.load_word2vec_model(self.model_path)
        self.word2vec.load_word2vec_dictionary(self.dict_path)
        if self.eng_rus_path:
            self.eng_rus_dict = load_eng_rus_dict(self.eng_rus_path)

    def text_to_vec(self, text):
        """
        convert sentence to vector
        :param text: sentence
        :return: vector shape = (1, dim)
        """
        text_proc = self.preprocess_sentence(text)
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

    def translate_eng_to_rus(self, sent):
        words_in = sent.split()
        words_out = []
        for cw in words_in:
            if cw in self.eng_rus_dict.keys():
                words_out.append(self.eng_rus_dict[cw])
            else:
                words_out.append(cw)
        return " ".join(words_out)

    def preprocess_sentence(self, sent):
        sent = sent.decode('utf-8').lower().encode('utf-8')
        sent = re.sub(r"[/\\\.,\?!\":;\(\)\*#\'\d]", " ", sent)
        sent = re.sub("\-\s+", " ", sent)
        if self.eng_rus_path:
            sent = self.translate_eng_to_rus(sent)
        sent = re.sub("[a-z]", "", sent)
        sent = re.sub("\s+", " ", sent)
        sent = sent.strip()
        return sent


class TextModels:
    def __init__(self, path2model, path2dict, path2engrusdict=""):
        """
        :param path2model: path to word2vec model
        :param path2dict:  path to word2vec dict
        """
        self.model_path = path2model
        self.dict_path = path2dict
        self.eng_rus_path = path2engrusdict
        self.word2vec = Word2Vec()
        self.word2vec.load_word2vec_model(self.model_path)
        self.word2vec.load_word2vec_dictionary(self.dict_path)
        if self.eng_rus_path:
            self.eng_rus_dict = load_eng_rus_dict(self.eng_rus_path)
        else:
            self.eng_rus_dict = {}

    def translate_eng_to_rus(self, sent):
        words_in = sent.split()
        words_out = []
        for cw in words_in:
            if cw in self.eng_rus_dict.keys():
                words_out.append(self.eng_rus_dict[cw])
            else:
                words_out.append(cw)
        return " ".join(words_out)

    def preprocess_sentence(self, sent):
        sent = sent.decode('utf-8').lower().encode('utf-8')
        sent = re.sub(r"[/\\\.,\?!\":;\(\)\*#\'\d]", " ", sent)
        sent = re.sub("\-\s+", " ", sent)
        if self.eng_rus_path and len(re.findall(u"[а-яА-я]", sent.decode("utf-8"))) < 20:
            sent = self.translate_eng_to_rus(sent)
        sent = re.sub("[a-z]", "", sent)
        sent = re.sub("\s+", " ", sent)
        sent = sent.strip()
        return sent


class TextProcessing:
    """
    resorting songs according to the matching scores between their lyrics&title and the text from user
    """
    def __init__(self, text_models):
        """
        :param text_models: instance of theTextModels class
        """
        self.tm = text_models

    def text_to_vec(self, text):
        """
        convert sentence to vector
        :param text: sentence
        :return: vector shape = (1, dim)
        """
        text_proc = self.tm.preprocess_sentence(text)
        if not text_proc:  # :))))
            text_proc = "клмншмидт"
        word_vecs = self.tm.word2vec.covert_from_words_to_vecs(text_proc.split())
        sent_vec = np.average(word_vecs, axis=1)
        return sent_vec.T

    def text_dict_to_vec_dict(self, text_dict):
        for songIdx in text_dict.keys():
            song_name_vec = self.text_to_vec(text_dict[songIdx][0])
            song_text_vec = self.text_to_vec(text_dict[songIdx][1])
            text_dict[songIdx] = song_name_vec, song_text_vec
        return

    def calc_scores(self, text_to_cmp, list_of_texts):
        vec_to_cmp = self.text_to_vec(text_to_cmp)
        vec_to_cmp = np.reshape(vec_to_cmp, [1, len(vec_to_cmp)])
        list_of_vecs = []
        for csn in range(len(list_of_texts)):
            # if csn % 100 == 0:
            #     print csn
            cur_text = list_of_texts[csn]
            list_of_vecs.append(self.text_to_vec(cur_text))
        # list_of_vecs = [self.text_to_vec(cur_text) for cur_text in list_of_texts]
        # print "translated"
        matrix_to_cmp = np.array(list_of_vecs)
        scores = 1 - cdist(vec_to_cmp, matrix_to_cmp, metric='cosine')  # similarity scores!!!
        # print "multiplied"
        return scores

    def calc_scores_vecs(self, text_to_cmp, list_of_vecs):
        # TODO: обрабатывать list_of_vect
        vec_to_cmp = self.text_to_vec(text_to_cmp)
        vec_to_cmp = np.reshape(vec_to_cmp, [1, len(vec_to_cmp)])
        matrix_to_cmp = np.array(list_of_vecs)
        scores = 1 - cdist(vec_to_cmp, matrix_to_cmp, metric='cosine')  # similarity scores!!!
        # print "multiplied"
        return scores

    def calc_songs_scores(self, text_from_user, songs_titles, songs_lyrics):
        title_scores = self.calc_scores(text_from_user, songs_titles)
        lyrics_scores = self.calc_scores(text_from_user, songs_lyrics)
        return 0.25 * title_scores + 0.75 * lyrics_scores

    def calc_songs_scores_vecs(self, text_from_user, songs_titles_vecs, songs_lyrics_vecs):
        title_scores = self.calc_scores_vecs(text_from_user, songs_titles_vecs)
        lyrics_scores = self.calc_scores_vecs(text_from_user, songs_lyrics_vecs)
        return 0.25 * title_scores + 0.75 * lyrics_scores

    def resort_songs_by_lyrics_and_title(self, text_from_user, dict_with_songs):
        """
        :param text_from_user: text of the post on vk
        :param dict_with_songs: keys -- songs ids, values (song_title, song_lyrics)
        :return: resorted
        """
        songs_ids = list(dict_with_songs.keys())
        songs_titles = [dict_with_songs[c_id][0] for c_id in songs_ids]
        songs_lyrics = [dict_with_songs[c_id][1] for c_id in songs_ids]
        scores = self.calc_songs_scores(text_from_user, songs_titles, songs_lyrics)  # similarity scores!!!
        sorted_ids = np.argsort(scores).flatten()[::-1]
        # print "sorted"
        # print np.shape(sorted_ids)
        return [songs_ids[c_id] for c_id in sorted_ids]

    def resort_songs_by_vecs(self, text_from_user, dict_with_vecs_of_songs):
        """
        :param text_from_user: text of the post on vk
        :param dict_with_vecs_of_songs: keys -- songs ids, values (vec of song_title, vec of song_lyrics)
        :return: resorted
        """
        songs_ids = list(dict_with_vecs_of_songs.keys())
        songs_titles_vecs = [dict_with_vecs_of_songs[c_id][0] for c_id in songs_ids]
        songs_lyrics_vecs = [dict_with_vecs_of_songs[c_id][1] for c_id in songs_ids]
        scores = self.calc_songs_scores_vecs(text_from_user, songs_titles_vecs, songs_lyrics_vecs)  # similarity scores!!!
        sorted_ids = np.argsort(scores).flatten()[::-1]
        # print "sorted"
        # print np.shape(sorted_ids)
        return [songs_ids[c_id] for c_id in sorted_ids]



def load_songs_with_titles(list_songs_files):
    song_text_dict = {}
    with open(list_songs_files) as list_in:
        for f_name in list_in:
            f_name = f_name.strip()
            with open(f_name) as file_in:
                cur_text = file_in.read()
                song_text_dict[f_name] = (f_name, cur_text)
    return song_text_dict


def load_test_phrases(phr_file):
    phr_list = []
    with open(phr_file) as file_in:
        for line in file_in:
            phr_list.append(line.strip())
    return phr_list


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

    out_file = "./nlp part/matchers_test.log"
    song_texts = load_songs(list_song_text_files)
    test_phrs = load_phrs(list_test_phrases)
    with open(out_file, "w") as file_out:
        for cur_phr in test_phrs:
            # print cur_phr.decode("utf-8")
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
    # path_to_w2v_model = "/home/andrew/Projects/model/cbow_ns300_fullrostelLK4.npy"
    # path_to_w2v_dict = "/home/andrew/Projects/model/cbow_ns300_fullrostelLK4.dic"


    path_to_w2v_model = "C:\\Work\\wiki word2vec\\cbow_ns300_fullrostelLK4.npy"
    path_to_w2v_dict = "C:\\Work\\wiki word2vec\\cbow_ns300_fullrostelLK4.dic"
    path_to_eng_rus_dict = "./nlp part/dict_eng_rus.txt"

    test_eng = 0
    test_scorer = 1

    if test_eng:
        s1 = "Привет!"
        s2 = "приветkk"
        s3 = "здравствуй а как дела"
        s4 = "пока"
        text_matcher = TextMatcher(path_to_w2v_model, path_to_w2v_dict, path_to_eng_rus_dict)
        # print text_matcher.calc_matching_score(s1, s2)
        # print text_matcher.calc_matching_score(s1, s3)
        # print text_matcher.calc_matching_score(s1, s4)

        songs_files = "./nlp part/list_all_ru_songs.txt"
        test_phrs_files = "./nlp part/list_phrs.txt"
        test_word2vec_scorer(songs_files, test_phrs_files, text_matcher)

    if test_scorer:
        path_to_w2v_model = "D:\\_Projects___CURRENT_\\CalendarBot\\data\\cbow_ns300_fullrostelLK4.npy"
        path_to_w2v_dict = "D:\\_Projects___CURRENT_\\CalendarBot\\data\\cbow_ns300_fullrostelLK4.dic"

        text_model = TextModels(path_to_w2v_model, path_to_w2v_dict, path_to_eng_rus_dict)
        text_processer = TextProcessing(text_model)

        songs_files = "./nlp part/all_lang_songs.txt"
        test_phrs_file = "./nlp part/list_phrs.txt"

        songs_dict = load_songs_with_titles(songs_files)
        test_phrs = load_test_phrases(test_phrs_file)
        # for c_test_phr in test_phrs:
        #     print c_test_phr.decode("utf-8")
        #     print text_processer.resort_songs_by_lyrics_and_title(c_test_phr, songs_dict)[0:5]



