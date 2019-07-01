from bs4 import BeautifulSoup

from link_extraction import extract_links
from text_extraction import getInp, get_text


def get_text_and_links_from_url(url):
    htext = getInp(url)
    soup = BeautifulSoup(htext, "html.parser")
    return get_text(soup), extract_links(soup)