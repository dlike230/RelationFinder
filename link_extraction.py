from bs4 import BeautifulSoup


def extract_links(soup: BeautifulSoup):
    return {link_text: link_href for link_text, link_href in extract_links_generator(soup)}


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
