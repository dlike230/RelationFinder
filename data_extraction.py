from bs4 import BeautifulSoup
from textblob import TextBlob

from link_extraction import extract_links
from text_extraction import getInp, get_text


def lemmatize_term(term):
    term_blob = TextBlob(term)
    return " ".join(word.lemmatize() for word in term_blob.words)


def lemmatize_links_dict(links: dict):
    return {lemmatize_term(key): link for key, link in links.items()}

class CorpusModel:

    def __init__(self, base_term):
        self.base_term = base_term

        class DistanceModel:

            def __init__(self0, sentences):
                self0.word_dict =

        class WikiPage:

            def __init(self0, url):
                htext = getInp(url)
                soup = BeautifulSoup(htext, "html.parser")
                text = get_text(soup)
                text_blob = TextBlob(text)
                sentences = text_blob.sentences
                self0.distance_model = DistanceModel(sentences)
                self0.links = lemmatize_links_dict(extract_links(soup))

        self.DistanceModel = DistanceModel
        self.WikiPage = WikiPage
