from bs4 import BeautifulSoup
from textblob import TextBlob

from entity_trees import WalkableEntityTree
from link_extraction import extract_links
from text_extraction import getInp, get_text


def lemmatize_term(term):
    term_blob = TextBlob(term)
    return " ".join(word.lemmatize() for word in term_blob.words)


def lemmatize_links_dict(links: dict):
    return {lemmatize_term(key): link for key, link in links.items()}


class DistanceModel:
    def __init__(self, sentences, target_term):
        self.sentences = sentences
        self.target_term = target_term
        self.segments = [segment for segment in self.compute_segments()]

    def compute_segment_centers(self):
        target_term_finder = WalkableEntityTree()
        target_term_finder.push(self.target_term)
        total_accumulation = 0
        for s, sentence in enumerate(self.sentences):
            target_term_finder.reset()
            for i, word in enumerate(sentence.words):
                target_term_list = list(target_term_finder.accept_word(word))
                if len(target_term_list) == 0:
                    continue
                yield i, total_accumulation, s
                total_accumulation += 1

    def compute_segments(self):
        segment_centers = [segment_center for segment_center in self.compute_segment_centers()]
        start = 0, self.sentences[0]
        if len(segment_centers) < 2:
            end = len(self.sentences[-1].words), self.sentences[-1]
            yield start, end
            return
        for (first_word_index, start_accumulation, start_sentence), (
        second_word_index, end_accumulation, end_sentence) in zip(segment_centers[:-1], segment_centers[1:]):
            current_accumulation = 0
            target_accumulation = (start_accumulation + end_accumulation) // 2
            for s, sentence in enumerate(self.sentences[start_sentence: end_sentence + 1]):
                for i, word in enumerate(sentence.words[first_word_index:]):
                    current_accumulation += 1
                    if current_accumulation == target_accumulation:
                        sentence_index = s + start_sentence
                        word_index = i + first_word_index


class WikiPage:

    def __init(self, url, target_term):
        htext = getInp(url)
        soup = BeautifulSoup(htext, "html.parser")
        text = get_text(soup)
        text_blob = TextBlob(text)
        sentences = text_blob.sentences
        self.distance_model = DistanceModel(sentences, target_term)
        self.links = lemmatize_links_dict(extract_links(soup))
