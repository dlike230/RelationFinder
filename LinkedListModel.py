from textblob import TextBlob
from textblob import Word as blob_word
from textblob import Sentence as blob_sentence


class LinkedText:
    def __init__(self, text_blob: TextBlob):
        self.sentences = [LinkedSentence(sentence) for sentence in text_blob.sentences]
        for sentence_a, sentence_b in zip(self.sentences[:-1], self.sentences[1:]):
            sentence_a.next = sentence_b
            sentence_b.previous = sentence_a
        index = 0
        for sentence in self.sentences:
            for word in sentence.words:
                word.index = index
                index += 1

    def __iter__(self):
        return iter(self.sentences)

    def __len__(self):
        return len(self.sentences)

    def __getitem__(self, item):
        return self.sentences[item]


class LinkedSentence:

    def __init__(self, sentence: blob_sentence):
        self.words = [LinkedWord(word, self, i) for i, word in enumerate(sentence.words)]
        self.text = sentence.string
        for word_a, word_b in zip(self.words[:-1], self.words[1:]):
            word_a.next = word_b
            word_b.previous = word_a
        self.next = None
        self.previous = None

    def __iter__(self):
        return iter(self.words)

    def __len__(self):
        return len(self.words)

    def __getitem__(self, item):
        return self.words[item]


class LinkedWord:
    def __init__(self, word: blob_word, parent: LinkedSentence, parent_index):
        self.lemma = word.lemmatize().lower()
        self.next = None
        self.previous = None
        self.index = -1
        self.parent_index = parent_index
        self.parent = parent

    @property
    def after(self):
        if self.next is not None:
            return self.next
        parent_next = self.parent.next
        if parent_next is None:
            return None
        return parent_next[0]

    def __str__(self):
        return self.lemma

    def __repr__(self):
        return self.lemma


def midpoint(word_a: LinkedWord, word_b: LinkedWord):
    desired_index = (word_a.index + word_b.index) // 2
    selected_parent = word_a.parent
    while selected_parent[-1].index < desired_index:
        selected_parent = selected_parent.next
    end_offset = selected_parent[-1].index - desired_index
    return selected_parent[end_offset - 1]
