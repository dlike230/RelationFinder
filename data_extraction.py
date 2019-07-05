import itertools
import math

from bs4 import BeautifulSoup
from textblob import TextBlob

from LinkedListModel import LinkedText, midpoint
from entity_trees import WalkableEntityTree
from link_extraction import extract_links
from text_extraction import getInp, get_text


def lemmatize_term(term):
    term_blob = TextBlob(term)
    return " ".join(word.lemmatize().lower() for word in term_blob.words)


def lemmatize_links_dict(links: dict):
    return {lemmatize_term(key): link for key, link in links.items()}


class Token:

    def __init__(self, segment, distance, word=None, end_sentence=False):
        self.word = word
        self.end_sentence = end_sentence
        self.segment = segment
        self.distance = distance

    def __repr__(self):
        return repr(self.word if self.word is not None else ".") + " " + "(%d)" % self.distance


class Segment:

    def __init__(self, start, center, end):
        self.start = start
        self.center = center
        self.end = end

    def tokens(self):
        selected = self.start
        end_index = self.end.index
        center_index = self.center.index
        while selected is not None and selected.index <= end_index:
            distance = abs(selected.index - center_index)
            yield Token(self, distance, word=selected)
            if selected.next is None:
                yield Token(self, distance, end_sentence=True)
            selected = selected.after

    def __repr__(self):
        return " ".join(repr(token) for token in self.tokens())


class DistanceModel:
    def __init__(self, linked_text, target_term):
        self.linked_text = linked_text
        self.target_term = target_term
        self._target_term_length = -1
        self.segments = [segment for segment in self._compute_segments()]

    def _find_term_instances(self):
        target_term_finder = WalkableEntityTree()
        self._target_term_length = target_term_finder.push(self.target_term)
        for sentence in self.linked_text:
            target_term_finder.reset()
            for word in sentence:
                target_term_list = list(target_term_finder.accept_lemma(word.lemma))
                if len(target_term_list) == 0:
                    continue
                yield word

    def _compute_segments(self):
        start = self.linked_text[0][0]
        last_center = None
        for center in self._find_term_instances():
            if last_center is not None:
                center_midpoint = midpoint(last_center, center)
                yield Segment(start, last_center, center_midpoint)
                start = center_midpoint.after
            last_center = center
        yield Segment(start, last_center, self.linked_text[-1][-1])

    def __repr__(self):
        return "\n\n".join("\tSEGMENT:\n" + repr(segment) for segment in self.segments)


class WikiPage:

    def __init__(self, url, target_term):
        htext = getInp(url)
        soup = BeautifulSoup(htext, "html.parser")
        text = get_text(soup)
        text_blob = TextBlob(text)
        self.distance_model = DistanceModel(LinkedText(text_blob), target_term)
        self.links = lemmatize_links_dict(extract_links(soup))

    def __repr__(self):
        return repr(self.distance_model)
