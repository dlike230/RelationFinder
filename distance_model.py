from WikiModel import WikiPage
from utils import get_wiki_url


class Entry:

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __lt__(self, other):
        return self.key < other.key

    def __gt__(self, other):
        return self.key > other.key

    def __eq__(self, other):
        return self.key == other.key

    def __hash__(self):
        return hash(self.key)

    def __repr__(self):
        return repr(self.key) + ": " + repr(self.value)


class PriorityQueue:

    def __init__(self, init_entries=None):
        if init_entries is None:
            init_entries = []
        self.entries = init_entries
        self.value_to_index = {entry.value: i for i, entry in enumerate(self.entries)}
        for i in range(len(self.entries))[::-1]:
            self.min_heapify(i)

    @staticmethod
    def left_child(index):
        return index * 2 + 1

    @staticmethod
    def right_child(index):
        return index * 2 + 2

    @staticmethod
    def parent(index):
        return (index - 1) // 2

    def change_key(self, value, new_key):
        index = self.value_to_index[value]
        entry = self.entries[index]
        old_key = entry.key
        if old_key <= new_key:
            entry.key = old_key
        else:
            self.decrease_key(index, new_key)

    def decrease_key(self, index, new_key):
        target_entry = self.entries[index]
        target_entry.key = new_key
        selected_index = index
        while True:
            parent_index = PriorityQueue.parent(selected_index)
            if parent_index < 0:
                return
            parent_entry = self.entries[parent_index]
            parent_key = parent_entry.key
            if parent_key < new_key:
                return
            self.entries[parent_index] = target_entry
            self.value_to_index[target_entry.value] = parent_index
            self.entries[selected_index] = parent_entry
            self.value_to_index[parent_entry.value] = selected_index
            selected_index = parent_index

    def push(self, key, value):
        if value in self.value_to_index:
            old_entry_index = self.value_to_index[value]
            old_entry = self.entries[old_entry_index]
            old_key = old_entry.key
            if old_key < key:
                self.decrease_key(old_entry_index, key)
            return
        index = len(self.entries)
        self.entries.append(Entry(key, value))
        self.value_to_index[value] = index
        self.decrease_key(index, key)

    def min_heapify(self, start_index=0):
        start_entry = self.entries[start_index]
        left_index = PriorityQueue.left_child(start_index)
        right_index = PriorityQueue.right_child(start_index)
        n = len(self.entries)

        def get_candidates():
            if left_index < n:
                yield left_index, self.entries[left_index]
            if right_index < n:
                yield right_index, self.entries[right_index]
            yield start_index, start_entry

        min_index, min_entry = min(get_candidates(), key=lambda candidate: candidate[1].key)
        if min_index != start_index:
            self.entries[min_index] = start_entry
            self.value_to_index[start_entry.value] = min_index
            self.entries[start_index] = min_entry
            self.value_to_index[min_entry.value] = start_index
            self.min_heapify(min_index)

    def __contains__(self, item):
        return item in self.value_to_index

    def __repr__(self):
        return ", ".join(repr(entry) for entry in self.entries)

    def get_key(self, value):
        if value in self.value_to_index:
            return self.entries[self.value_to_index[value]].key
        return None

    def pop(self):
        first_entry = self.entries[0]
        self.entries[0] = self.entries[-1]
        del self.entries[-1]
        self.min_heapify()
        return first_entry


class DistanceModel:

    def __init__(self, start_term, target_term):
        self.result = None
        start_page = WikiPage.generate(start_term, target_term, None)
        self.start_term = start_term
        self.target_term = target_term
        init_entries = [Entry(distance, link.set_text_func(text_func)) for link, distance, text_func in start_page.distance_generator()]
        self.queue = PriorityQueue(init_entries)

    def process_link(self, link, distance):
        print("Processing", link, "at distance", distance)
        if link.is_target:
            self.result = " ".join(link.get_linked_text())
            return True
        new_page = WikiPage.generate(link.original_link_text, self.target_term, link)
        if new_page is None:
            return False
        for link, additional_distance, text_func in new_page.distance_generator():
            new_distance = additional_distance + distance
            old_distance = self.queue.get_key(link)
            if old_distance is None:
                self.queue.push(new_distance, link.set_text_func(text_func))
            elif new_distance < old_distance:
                self.queue.change_key(link, new_distance)
        return False

    def iterate(self):
        print(self.queue)
        entry = self.queue.pop()
        return self.process_link(entry.value, entry.key)

