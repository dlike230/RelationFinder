from typing import NamedTuple

from textblob import TextBlob


class SimpleLinkedListNode:

    def __init__(self, value):
        self.value = value
        self.next = None
        self.previous = None


class SimpleLinkedList:

    def __init__(self):
        self._head = None
        self._tail = None

    def append(self, val):
        new_node = SimpleLinkedListNode(val)
        if self._head is None:
            self._head = new_node
            self._tail = new_node
        else:
            new_node.previous = self._tail
            self._tail.next = new_node

    def walk(self):
        current_node_record = [self._head]
        def remove():
            current_node = current_node_record[0]
            if current_node.prev is None:
                self._head = current_node.next
                if self._head is None:
                    self._tail = None
                    current_node_record[0] = None
                else:
                    current_node.next.previous = None
                    current_node_record[0] = current_node.next
            else:
                walk_record[0].next = walk_record[1].next
                if walk_record[0].next is None:
                    self._tail = walk_record[0]
                walk_record[1]
        return NamedTuple(remove=remove)


class EntityTreeNode:
    def __init__(self):
        self._lemmas = {}

    def push(self, lemma_list, lemma_list_index=0):
        lemma_selected = lemma_list[lemma_list_index]
        selected_node = None
        if lemma_selected in self._lemmas:
            selected_node = self._lemmas[lemma_selected]
        else:
            selected_node = EntityTreeNode()
            self._lemmas[lemma_selected] = selected_node
        new_index = lemma_list_index + 1
        if new_index == len(lemma_list):
            return
        selected_node.push(lemma_list, new_index)


class WalkableEntityTree:

    def __init__(self):
        self._root = None
        self._potential_terms_queue = []

    def push(self, term):
        term_blob = TextBlob(term)
        lemmas = [word.lemmatize() for word in term_blob]
        if self._root is None:
            self._root = EntityTreeNode()
        self._root.push(lemmas)

    def test(self, word):
        lemma = word.lemmatize()
