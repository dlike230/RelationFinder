from bs4 import BeautifulSoup
from textblob import TextBlob

from LinkedListModel import LinkedText
from data_extraction import PageDistances
from entity_trees import WalkableEntityTree
from text_extraction import getInp, get_text
from utils import lemmatize_term


class WikiPage:

    def __init__(self, url, target_term):
        htext = getInp(url)
        soup = BeautifulSoup(htext, "html.parser")
        text = get_text(soup)
        text_blob = TextBlob(text)
        self.distances = PageDistances(LinkedText(text_blob), target_term)
        self.links = self.extract_links(soup, target_term)
        if target_term not in self.links:
            self.links[target_term] = Link(target_term, lemmatize_term(target_term), self)

    def distance_generator(self):
        link_locator = WalkableEntityTree()
        for link in self.links.values():
            link_locator.push_lemmas(link.link_text_lemmas, associated_data=link)
        return self.distances.read(link_locator)

    def __repr__(self):
        return repr(self.distances)

    def extract_links(self, soup, target_term):
        lemmatized_text, target_term_lemmas = lemmatize_term(target_term)
        return {lemmatized_text: Link(link_text, target_term_lemmas, self, link_href=link_href) for link_text, link_href in
                extract_links_generator(soup)}


class Link:
    def __init__(self, link_text, target_term_lemmas, discovered_from, link_href=None):
        self.original_link_text = link_text
        self.lemmatized_link_text, self.link_text_lemmas = lemmatize_term(link_text)
        self.link_href = link_href
        self.discovered_from = discovered_from
        self.target_term_lemmas = target_term_lemmas
        self.text_func = None
        self.is_target = self.link_text_lemmas == target_term_lemmas

    def set_text_func(self, text_func):
        self.text_func = text_func
        return self

    def get_linked_text_generator(self):
        selected = self
        while selected is not None:
            yield selected.text_func()
            selected = selected.discovered_from

    def get_linked_text(self):
        return " ".join(self.get_linked_text_generator())

    def __hash__(self):
        return hash(self.lemmatized_link_text)

    def __eq__(self, other):
        return self.lemmatized_link_text == other.lemmatized_link_text


def extract_links_generator(soup: BeautifulSoup):
    if soup.name == "a" and soup.has_attr("href"):
        link = soup["href"]
        if "/wiki/" not in link:
            # not a valid wiki link
            return
        yield soup.get_text(), link
    elif hasattr(soup, "children") and soup.children is not None:
        for child in soup.children:
            yield from extract_links_generator(child)
