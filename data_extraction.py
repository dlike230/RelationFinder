from textblob import TextBlob

from LinkedListModel import LinkedText, midpoint
from entity_trees import WalkableEntityTree


class Token:

    def __init__(self, segment, distance, word=None, end_sentence=False):
        self.word = word
        self.end_sentence = end_sentence
        self.segment = segment
        self.distance = distance

    def __repr__(self):
        return repr(self.word if self.word is not None else ".") + " " + "(%d)" % self.distance

    @property
    def text_generator(self):
        def sentence_text_generator():
            center_sentence = self.segment.center
            if center_sentence is None:
                return " ".join(sentence.text for sentence in self.segment.all_sentences)
            center_sentence_index = center_sentence.parent_index
            my_sentence = self.word.parent
            word_sentence_index = my_sentence.parent_index
            relevant_sentences = self.segment.all_sentences[
                                 min(center_sentence_index, word_sentence_index): max(center_sentence_index,
                                                                                      word_sentence_index)]
            return " ".join(sentence.text for sentence in relevant_sentences)

        return sentence_text_generator()


class Segment:

    def __init__(self, start, center, end, sentences):
        self.start = start
        self.center = center
        self.end = end
        self.all_sentences = sentences

    def tokens(self):
        selected = self.start
        end_index = self.end.index
        center_index = self.center.index if self.center is not None else 1E99
        while selected is not None and selected.index <= end_index:
            distance = abs(selected.index - center_index)
            yield Token(self, distance, word=selected)
            if selected.next is None:
                yield Token(self, distance, end_sentence=True)
            selected = selected.after

    def __repr__(self):
        return " ".join(repr(token) for token in self.tokens())


class PageDistances:
    def __init__(self, linked_text, start_term):
        self.linked_text = linked_text
        self.start_term = start_term
        self.lemmatized_start_term = None
        self.segments = [segment for segment in self._compute_segments()]

    def _find_term_instances(self):
        start_term_finder = WalkableEntityTree()
        self.lemmatized_start_term = start_term_finder.push(self.start_term)
        for sentence in self.linked_text:
            start_term_finder.reset()
            for word in sentence:
                target_term_list = list(start_term_finder.accept_lemma(word.lemma))
                if len(target_term_list) == 0:
                    continue
                yield word

    def _compute_segments(self):
        start = self.linked_text[0][0]
        last_center = None
        for center in self._find_term_instances():
            if last_center is not None:
                center_midpoint = midpoint(last_center, center)
                yield Segment(start, last_center, center_midpoint, self.linked_text.sentences)
                start = center_midpoint.after
            last_center = center
        yield Segment(start, last_center, self.linked_text[-1][-1], self.linked_text.sentences)

    def read(self, term_locator: WalkableEntityTree):
        for segment in self.segments:
            for token in segment.tokens():
                if token.word is None:
                    term_locator.reset()
                    continue
                for potential_result in term_locator.accept_lemma(token.word.lemma):
                    if potential_result.contained_data.lemmatized_link_text == self.lemmatized_start_term:
                        continue
                    yield potential_result.contained_data, token.distance, token.text_generator

    def __repr__(self):
        return "\n\n".join("\tSEGMENT:\n" + repr(segment) for segment in self.segments)
