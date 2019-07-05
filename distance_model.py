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


class PriorityQueue:

    def __init__(self, init_values=None):
        if init_values is None:
            init_values = []
        self.entries = init_values
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

    def pop(self):
        first_entry = self.entries[0]
        self.entries[0] = self.entries[-1]
        del self.entries[-1]
        self.min_heapify()
        return first_entry.value


class DistanceModel:

    def __init__(self, start_page):
        init_entries = [Entry(distance, link) for link, distance in start_page.distance_generator()]
        self.queue = PriorityQueue(init_entries)

    def process_link(self, link, distance):
        if link.is_target:
            pass
