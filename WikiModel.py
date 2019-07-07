from bs4 import BeautifulSoup
from textblob import TextBlob

from LinkedListModel import LinkedText
from data_extraction import PageDistances
from entity_trees import WalkableEntityTree
from text_extraction import getInp, get_text
from utils import lemmatize_term, get_wiki_url


class WikiPage:

    def __init__(self, soup, text_blob, start_term, target_term, discovered_from):
        self.discovered_from = discovered_from
        self.start_term = start_term
        self.target_term = target_term
        self.lemmatized_target_term = lemmatize_term(target_term)
        self.distances = PageDistances(LinkedText(text_blob), start_term)
        self.links = self.extract_links(soup)
        if target_term not in self.links:
            self.links[target_term] = Link(target_term, self.lemmatized_target_term, self.lemmatized_target_term, self.discovered_from)

    @staticmethod
    def generate(start_term, end_term, discovered_from):
        url = get_wiki_url(start_term)
        htext = getInp(url)
        soup = BeautifulSoup(htext, "html.parser")
        text = get_text(soup)
        text_blob = TextBlob(text)
        if len(text_blob.sentences) > 0:
            return WikiPage(soup, text_blob, start_term, end_term, discovered_from)
        return None

    def distance_generator(self):
        link_locator = WalkableEntityTree()
        for link in self.links.values():
            link_locator.push_lemmas(link.lemmatized_link_text.split(" "), associated_data=link)
        return self.distances.read(link_locator)

    def __repr__(self):
        return repr(self.distances)

    def extract_links(self, soup):
        def lemmatized_generator():
            for link_text, link_href in extract_links_generator(soup):
                yield link_text, lemmatize_term(link_text), link_href
        return {lemmatized: Link(link_text, lemmatized, self.lemmatized_target_term, self.discovered_from, link_href=link_href) for
                link_text, lemmatized, link_href in lemmatized_generator()}


class Link:
    def __init__(self, link_text, lemmatized_link_text, lemmatized_target_term, discovered_from, link_href=None):
        self.original_link_text = link_text
        self.lemmatized_link_text = lemmatized_link_text
        self.link_href = link_href
        self.discovered_from = discovered_from
        self.lemmatized_target_term = lemmatized_target_term
        self.text_func = None
        self.is_target = self.lemmatized_link_text == lemmatized_target_term

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

    def __repr__(self):
        return self.lemmatized_link_text


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
