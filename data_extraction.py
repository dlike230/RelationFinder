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
        sentence, (start_word, end_word) = central_term_range
        central_term_sentence_words = sentences[sentence].words
        self._tokens = [Token(self, 0, word=term_word) for term_word in
                        central_term_sentence_words[start_word:end_word + 1]]
        self._tokens += [token for token in self.after_central_term(central_term_range, sentences, end)]

    def after_central_term(self, central_term_range: tuple, sentences, end: tuple):
        central_sentence_index, (start_term_word, term_end_word) = central_term_range
        central_sentence_words = sentences[central_sentence_index].words
        cumulative_distance = 0
        end_sentence, end_word = end
        central_sentence_is_last_sentence = end_sentence == central_sentence_index
        central_sentence_end_index = term_end_word + 1 if central_sentence_is_last_sentence else len(central_sentence_words)

        # loop through all remaining words in the sentence with the central word
        for word in central_sentence_words[term_end_word + 1:central_sentence_end_index + 1]:
            cumulative_distance += 1
            yield Token(self, cumulative_distance, word=word)
        if central_sentence_end_index + 1 == len(central_sentence_words):
            yield Token(self, cumulative_distance, end_sentence=True)
        else:
            return

        # loop through all full sentences included in the segment
        for sentence in sentences[central_sentence_index + 1: end_sentence]:
            for word in sentence.words:
                cumulative_distance += 1
                yield Token(self, cumulative_distance, word=word)
            yield Token(self, cumulative_distance, end_sentence=True)

        # loop through all words in the last sentence
        last_sentence_words = sentences[end_sentence].words
        for word in last_sentence_words[:end_word + 1]:
            cumulative_distance += 1
            yield Token(self, cumulative_distance, word=word)
        if end_word + 1 == len(last_sentence_words):
            yield Token(self, cumulative_distance, end_sentence=True)



    def after_central_term(self, central_term_range: tuple, sentences, end: tuple):
        central_sentence_index, (start_term_word, term_end_word) = central_term_range
        central_sentence_words = sentences[central_sentence_index].words
        cumulative_distance = 0
        end_sentence, end_word = end
        central_sentence_is_last_sentence = end_sentence == central_sentence_index
        central_sentence_end_index = term_end_word + 1 if central_sentence_is_last_sentence else len(central_sentence_words)

        # loop through all remaining words in the sentence with the central word
        for word in central_sentence_words[term_end_word + 1:central_sentence_end_index]:
            cumulative_distance += 1
            yield Token(self, cumulative_distance, word=word)
        yield Token(self, cumulative_distance, end_sentence=True)

        # loop through all full sentences included in the segment
        for sentence in sentences[central_sentence_index + 1: end_sentence]:
            for word in sentence.words:
                cumulative_distance += 1
                yield Token(self, cumulative_distance, word=word)

        # loop through all words in the last sentence
        last_sentence_words = sentences[end_sentence].words
        for word in last_sentence_words[:end_word + 1]:
            cumulative_distance += 1
            yield Token(self, cumulative_distance, word=word)


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
