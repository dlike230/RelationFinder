import re
import urllib
from urllib.request import Request

web = ["www.", "://", ".com", ".net", ".org", ".us", ".gov"]
accepted_tags = ["p", "span", "article", "font", "blockquote"]
exclude = ["cite"]
accepted_classes = {"paragraph", "text"}
bad_phrases = ["back to top", "home", "welcome", "you are here:", "itunes", "google", "facebook", "twitter", "comment"]
bad_subphrases = ["powered by", "around the web", "around the internet", "et al", "ndl", "view source", "view history",
                  "edit links", "last modified", "text is available under", "creative commons"]
bad_headers = ["References", "Citations", "Further Reading", "External Links", "Footnotes", "See Also"]
a = lambda x: x == x.lower()

A = re.compile("[a-zA-Z]{2,}[0-9]{2,}[ \\.]*")
B = re.compile("([0-9]+[a-zA-Z]+)+[\\s\\.]+")
C = re.compile("[\\[\\{].*[\\]\\}]")
D = re.compile("[A-Z]{2,3}: {0,2}[0-9]{3,}.{0,2}[0-9]*")
E = re.compile("\\([a-zA-Z\\s]+ ([0-9]+[.]*)+\\)")
F = re.compile("(\\\\[a-zA-Z0-9]{1,5})")
def add_item(goods, parent):
    goods.append(parent)


def find_good(parent, goods, wiki_mode):
    if parent is not None:
        if not parent.__class__.__name__ == "NavigableString" and not parent.__class__.__name__ == "Comment":
            if hasattr(parent, "name"):
                if parent.name in accepted_tags:
                    add_item(goods, parent)
                else:
                    classes_proto = parent.get("class")
                    classes = set() if classes_proto is None else set(filter(a, classes_proto))
                    ids_proto = parent.get("id")
                    # ids = set() if ids_proto is None else set(filter(a, ids_proto))
                    # converts all lists of ids and classes to sets with their lowercase versions
                    # ids are not currently used, but may be used later
                    if bool(classes & accepted_classes):
                        add_item(goods, parent)
                    # if the class is an accepted class, add the item to the list
                    else:
                        if hasattr(parent, "children"):
                            for item in parent.children:
                                if hasattr(item, "get_text"):
                                    if not(item.name=="a" or item.parent.name=="a"):
                                        t = item.get_text().strip()
                                        if t in bad_headers:
                                            add_item(goods, None)
                                            return False
                                find_good(item, goods, wiki_mode)
                                # searches through the child's child nodes
        elif parent.__class__.__name__ == "NavigableString":
            add_item(goods, parent)


def decide(factors, threshold):
    totalWeight = 0
    totalValue = 0
    for value, weight in factors:
        totalValue += value * weight
        totalWeight += weight
    adjusted = totalValue / totalWeight
    return adjusted > threshold


def check(text):
    texts = text.split("\n")
    result = ""
    for item in texts:
        new = (checkIndividual(item) + "\n")
        result += new
    return result


def checkIndividual(text):
    if "°" in text and len(text) < 100:
        return ""
    text = destroy_citations(text.replace("\r", "\n"))
    stripped = text.lower().strip("\n").strip("\t").strip(" ").strip("\r")
    if stripped in bad_phrases:
        return ""
    for item in bad_subphrases:
        if item in stripped:
            return ""
    for item in web:
        if item in text:
            text = text.replace(item, "")
    if len(stripped) < 7:
        return ""
    if not text[0].isalnum() and not text[0] == " " and not text[0] == "/t" and not text[0] == "\n":
        return ""
    lastchr = stripped[len(stripped) - 1]
    if not lastchr.isalnum() and not (lastchr == "." or lastchr == "?" or lastchr == " "):
        return ""
    if stripped.isdigit():
        return ""
    endsWithPunc = 0 if stripped[len(stripped) - 1] == '.' else 1
    length = 1 / (len(stripped) - 6)
    numSpaces = 1 / (stripped.count(' ') + 1)
    if numSpaces > 1 / 3:
        return ""
    factors = [(endsWithPunc, 2), (length, 1), (numSpaces, 3)]
    if decide(factors, 0.4):
        return ""
    return text


def extract(item):
    result = ""
    if hasattr(item, "children"):
        for text in item.children:
            if not hasattr(text, "name") or not text.name in exclude:
                result += extract(text)
    elif hasattr(item, "get_text"):
        result = item.get_text()
    else:
        result = item
    return result.replace("\n", " ")


def check_spaces(text):
    obj = re.compile("[\\s \\t\\n]{2,}]")
    text = obj.sub(" ", text)
    text = re.compile("[ ]{2,}").sub(" ", text)
    text = text.replace("\n ", "\n").replace(" \n", "\n")
    text = re.compile("[\\r\\n]{3,}").sub("\n", text)
    return text


def destroy_citations(text):
    return A.sub(" ", B.sub(" ", C.sub("", D.sub(" ", E.sub(" ", F.sub(" ", text))))))


def get_text(soup):
    soup = soup.html
    wiki_mode = False
    if ("wikipedia.org" in str(soup)):
        wiki_mode = True
    goods = list()
    find_good(soup, goods, wiki_mode)
    text = ""
    for item in goods:
        if item is None:
            break
        extraction = extract(item)
        if extraction is not None:
            text += extraction + "\n"
    text = check_spaces(text)
    text = check(text)
    text = check_spaces(text)
    #return text.split(BAD_STUFF)[0]
    return text

def getInp(url):
    req = Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')
    response = urllib.request.urlopen(req).read()
    html = response.decode('utf-8', errors='ignore').strip()
    html = html.replace("\\n", '\n').replace("\\'", "'").replace("\'", "'").replace("\\r", " ").replace("\\t", " ")
    return html


