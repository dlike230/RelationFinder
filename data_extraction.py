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

    def __repr__(self):
        return (self.word if self.word is not None else ".") + " " + "(%d)" % self.distance


class Segment:

    def __init__(self, central_term_range, sentences, start, end):
        self._central_term_range = central_term_range
        self._sentences = sentences
        self._start = start
        self._end = end

    def tokens(self):
        yield from reversed(
            list(self._outside_central_term(self._central_term_range, self._sentences, self._start, False)))
        central_sentence_index, (start_word, end_word) = self._central_term_range
        for term_word in self._sentences[central_sentence_index][start_word: end_word + 1]:
            yield Token(self, 0, word=term_word)
        yield from self._outside_central_term(self._central_term_range, self._sentences, self._end, True)

    def _outside_central_term(self, central_term_range: tuple, sentences, outer_bound: tuple, move_right):
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
        if last_index + 1 != len(central_sentence_words) and move_right:
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

    def __repr__(self):
        return " ".join(repr(token) for token in self.tokens())


class DistanceModel:
    def __init__(self, sentences, target_term):
        self.sentences = sentences
        self.target_term = target_term
        self._target_term_length = -1
        self.segments = [segment for segment in self._compute_segments()]

    def _compute_segment_centers(self):
        target_term_finder = WalkableEntityTree()
        self._target_term_length = target_term_finder.push(self.target_term)
        total_accumulation = 0
        for s, sentence in enumerate(self.sentences):
            target_term_finder.reset()
            for i, word in enumerate(sentence.words):
                target_term_list = list(target_term_finder.accept_word(word))
                if len(target_term_list) == 0:
                    total_accumulation += 1
                    continue
                yield i, total_accumulation, s
                total_accumulation += 1

    def _compute_segment_endpoints(self):
        segment_centers = [segment_center for segment_center in self._compute_segment_centers()]
        if len(segment_centers) == 0:
            return
        if len(segment_centers) == 1:
            center_word_index, _, center_sentence_index = segment_centers[0]
            yield (center_word_index, center_sentence_index), (
                len(self.sentences) - 1, len(self.sentences[-1].words) - 1)
            return
        for first_center, second_center in zip(segment_centers[:-1], segment_centers[1:]):
            first_center_word_index, start_accumulation, first_center_sentence_index = first_center
            second_center_word_index, end_accumulation, second_center_sentence_index = second_center
            current_accumulation = 0
            target_accumulation = (start_accumulation + end_accumulation) // 2
            for enumerated_sentence_index, sentence in enumerate(
                    self.sentences[first_center_sentence_index: second_center_sentence_index + 1]):
                sentence_words = sentence.words
                accumulation_after_sentence = current_accumulation + len(sentence_words)
                if accumulation_after_sentence <= target_accumulation:
                    current_accumulation = accumulation_after_sentence
                    first_center_word_index = 0
                    continue
                for word_index, word in enumerate(sentence_words[first_center_word_index:]):
                    current_accumulation += 1
                    if current_accumulation >= target_accumulation:
                        boundary_sentence_index = enumerated_sentence_index + first_center_sentence_index
                        boundary_word_index = word_index + first_center_word_index
                        yield (first_center_word_index, first_center_sentence_index), (
                            boundary_sentence_index, boundary_word_index)
                        break
                first_center_word_index = 0
        last_center_word_index, end_accumulation, last_center_sentence_index = segment_centers[-1]
        yield (last_center_word_index, last_center_sentence_index), (
            len(self.sentences) - 1, len(self.sentences[-1]) - 1)

    def _compute_segments(self):
        last_endpoint = 0, 0
        for center_data, endpoint_data in self._compute_segment_endpoints():
            center_word_index_end, center_sentence_index = center_data
            center_word_index_start = center_word_index_end - self._target_term_length + 1
            yield Segment((center_sentence_index, (center_word_index_start, center_word_index_start)), self.sentences,
                          last_endpoint, endpoint_data)
            last_endpoint = endpoint_data

    def __repr__(self):
        return "\n\n\tSEGMENT:\n".join(repr(segment) for segment in self.segments)


class WikiPage:

    def __init__(self, url, target_term):
        htext = getInp(url)
        soup = BeautifulSoup(htext, "html.parser")
        text = get_text(soup)
        text_blob = TextBlob(text)
        sentences = text_blob.sentences
        self.distance_model = DistanceModel(sentences, target_term)
        self.links = lemmatize_links_dict(extract_links(soup))

    def __repr__(self):
        return repr(self.distance_model)
