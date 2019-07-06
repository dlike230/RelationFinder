from textblob import TextBlob


def lemmatize_term(term):
    term_blob = TextBlob(term)
    return " ".join(word.lemmatize().lower() for word in term_blob.words)

def get_wiki_url(term):
    return "https://en.wikipedia.org/wiki/" + term