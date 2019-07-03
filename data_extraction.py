import itertools

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


class Token:

    def __init__(self, segment, distance, word=None, end_sentence=False):
        self.word = word
        self.end_sentence = end_sentence
        self.segment = segment
        self.distance = distance


class Segment:

    def __init__(self, central_term_range, sentences, start, end):
        self.central_term_range = central_term_range
        self.sentences = sentences
        self.start = start
        self.end = end

    def tokens(self):
        yield from self.outside_central_term(self.central_term_range, self.sentences, self.start, False)[::-1]
        central_sentence_index, (start_word, end_word) = self.central_term_range
        for term_word in self.sentences[central_sentence_index][start_word: end_word + 1]:
            yield Token(self, 0, word=term_word)
        yield from self.outside_central_term(self.central_term_range, self.sentences, self.end, True)

    def outside_central_term(self, central_term_range: tuple, sentences, outer_bound: tuple, move_right):
        central_sentence_index, (start_term_index, end_term_index) = central_term_range
        central_sentence_words = sentences[central_sentence_index].words
        cumulative_distance = 0
        outer_sentence_index, outer_word_index = outer_bound
        central_sentence_is_outer = outer_sentence_index == central_sentence_index

        # loop through all remaining words in the sentence with the central word
        central_sentence_start_index = -1
        central_sentence_end_index = -1
        if move_right:
            central_sentence_start_index = min(end_term_index + 1, len(central_sentence_words) - 1)
            central_sentence_end_index = outer_word_index if central_sentence_is_outer else len(
                central_sentence_words) - 1
        else:
            central_sentence_start_index = max(start_term_index - 1, 0)
            central_sentence_end_index = outer_word_index if central_sentence_is_outer else 0

        first_index = min(central_sentence_start_index, central_sentence_end_index)
        last_index = max(central_sentence_start_index, central_sentence_end_index)
        direction = 1 if move_right else -1
        for word in central_sentence_words[first_index: last_index + 1: direction]:
            cumulative_distance += 1
            yield Token(self, cumulative_distance, word=word)
        if first_index != 0 and not move_right:
            return
        if last_index != len(central_sentence_words) and move_right:
            return
        yield Token(self, cumulative_distance, end_sentence=True)
        first_sentence = min(central_sentence_index, outer_sentence_index)
        last_sentence = max(central_sentence_index, outer_sentence_index)

        # loop through all full sentences included in the segment between the first and the last
        for sentence in sentences[first_sentence + 1: last_sentence: direction]:
            for word in sentence.words[::-1]:
                cumulative_distance += 1
                yield Token(self, cumulative_distance, word=word)
            yield Token(self, cumulative_distance, end_sentence=True)

        # loop through all words in the last sentence
        outer_sentence_words = sentences[outer_sentence_index].words
        outer_sentence_inner_word_index = 0 if not move_right else len(outer_sentence_words) - 1
        first_word_index = min(outer_sentence_inner_word_index, outer_word_index)
        last_word_index = max(outer_sentence_inner_word_index, outer_word_index)
        for word in outer_sentence_words[first_word_index: last_word_index + 1: direction]:
            cumulative_distance += 1
            yield Token(self, cumulative_distance, word=word)
        if outer_word_index == 0 and not move_right or outer_word_index == len(
                outer_sentence_words) - 1 and not move_right:
            yield Token(self, cumulative_distance, end_sentence=True)


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

    def compute_segment_endpoints(self):
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
                sentence_words = sentence.words
                accumulation_after_sentence = current_accumulation + len(sentence_words)
                if accumulation_after_sentence <= target_accumulation:
                    current_accumulation += accumulation_after_sentence
                    first_word_index = 0
                    continue
                for i, word in enumerate(sentence_words[first_word_index:]):
                    current_accumulation += 1
                    if current_accumulation >= target_accumulation:
                        sentence_index = s + start_sentence
                        word_index = i + first_word_index
                        yield sentence_index, word_index
                first_word_index = 0

    def compute_segments(self):
        endpoints = [endpoint for endpoint in self.compute_segment_endpoints()]
        return zip([(0, 0)] + endpoints, endpoints + [(len(self.sentences) - 1, len(self.sentences[-1].words) - 1)])


class WikiPage:

    def __init(self, url, target_term):
        htext = getInp(url)
        soup = BeautifulSoup(htext, "html.parser")
        text = get_text(soup)
        text_blob = TextBlob(text)
        sentences = text_blob.sentences
        self.distance_model = DistanceModel(sentences, target_term)
        self.links = lemmatize_links_dict(extract_links(soup))
