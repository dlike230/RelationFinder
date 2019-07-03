from typing import NamedTuple

from textblob import TextBlob


class SimpleLinkedListNode:

    def __init__(self, value):
        self.value = value
        self.next = None
        self.previous = None

    def replace_val(self, new_val):
        self.value = new_val


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
        current_node_record = [None]

        def remove():
            current_node = current_node_record[0]
            if current_node.previous is None:
                self._head = current_node.next
                if self._head is None:
                    self._tail = None
                    current_node_record[0] = None
                else:
                    current_node.next.previous = None
                    current_node_record[0] = current_node.next
            else:
                current_node_record[0] = current_node.next
                if current_node.next is None:
                    self._tail = current_node.previous
                current_node.previous.next = current_node.next

        def replace(new_val):
            current_node_record[0].replace_val(new_val)

        def iterate():
            current_node = current_node_record[0]
            if current_node is None:
                current_node = self._head
            else:
                current_node = current_node.next
            if current_node is None:
                return
            current_node_record[0] = current_node
            yield current_node.value

        return remove, replace, iterate()


class EntityTreeNode:
    def __init__(self):
        self._children = {}
        self.parent = None
        self.contains_term = False

    def back_trace(self):
        if self.parent is None:
            yield self
        else:
            yield from self.parent.back_trace()

    def push(self, lemma_list, lemma_list_index=0):
        lemma_selected = lemma_list[lemma_list_index]
        selected_node = None
        if lemma_selected in self._children:
            selected_node = self._children[lemma_selected]
        else:
            selected_node = EntityTreeNode()
            self._children[lemma_selected] = selected_node
            selected_node.parent = self
        new_index = lemma_list_index + 1
        if new_index == len(lemma_list):
            self.contains_term = True
            return
        selected_node.push(lemma_list, new_index)

    def traverse(self, lemma):
        if lemma in self._children:
            return self._children[lemma]
        else:
            return None


class WalkableEntityTree:

    def __init__(self):
        self._root = None
        self._potential_terms_queue = SimpleLinkedList()

    def push(self, term):
        term_blob = TextBlob(term)
        lemmas = [word.lemmatize() for word in term_blob.words]
        if self._root is None:
            self._root = EntityTreeNode()
        self._root.push(lemmas)
        return len(lemmas)

    def accept_word(self, word):
        lemma = word.lemmatize()
        potential_branch = self._root.traverse(lemma)
        new_branch_exists = potential_branch is not None
        if new_branch_exists and potential_branch.contains_term:
            yield potential_branch
        remover, replacer, iterator = self._potential_terms_queue.walk()
        for branch in iterator:
            new_branch = branch.traverse(lemma)
            if new_branch is None:
                remover()
            else:
                replacer(new_branch)
                if new_branch.contains_term:
                    yield new_branch
        if new_branch_exists:
            self._potential_terms_queue.append(potential_branch)

    def reset(self):
        self._potential_terms_queue = SimpleLinkedList()


