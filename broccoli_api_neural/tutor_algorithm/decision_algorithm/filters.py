def is_markup(lemma):
    # characters that must not occur in a word that we want to learn
    stop_characters = set("""1234567890°^!"§$%&/()=?²³¼½¬{[]}\\`'*+~'#’-_–,;·.:…<>|/""")

    lemma = lemma.strip()
    lemma = lemma.lower()

    return len(set(lemma) & stop_characters) > 0

from broccoli_api_neural.config.stopwords import stopwords
def is_stop_word(lemma):
    return lemma.strip().lower() in stopwords