from textblob import TextBlob


def lemmatize_term(term):
    term_blob = TextBlob(term)
    lemma_list = [word.lemmatize().lower() for word in term_blob.words]
    return " ".join(lemma_list), lemma_list

def get_wiki_url(term):
    return "https://en.wikipedia.org/wiki/" + term