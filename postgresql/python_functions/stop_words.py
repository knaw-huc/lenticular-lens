from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer

# import nltk
# nltk.download('stopwords')
# nltk.download('punkt')


custom_dictionaries = {
    'dutch_names': [
        '\'s', '\'t', 'a', 'ab', 'aux', 'd\'', 'da', 'de', 'de\'', 'del', 'dela', 'della', 'den', 'dem', 'der', 'des',
        'di', 'die', 'die', 'dye', 'men', 'het', 'heet', 'doe', 'du', 'gravin', 'in', 'in\'t', 'l\'', 'l’', 'la', 'las',
        'le', 'met', 'metten', 'metter', 'onder', 'op', 's\'', 't\'', 'te', 'ten', 'ter', 'toe', 'tom', 'tot', 'uijt',
        'uit', 'uwten', 'uyt', 'van', 'vande', 'vanden', 'vander', 'von', 'voor', 'wt', 'zu'
    ]
}


def init_dictionary(dictionary, additional_stopwords=None):
    stopwords_set = []
    if dictionary and dictionary in custom_dictionaries:
        stopwords_set = custom_dictionaries[dictionary]
    elif dictionary:
        stopwords_set = stopwords.words(dictionary)

    if additional_stopwords:
        stopwords_set.extend(additional_stopwords)

    return stopwords_set


def remove_stopwords(stopwords_set, language, text):
    tokens = word_tokenize(text, language=language if language else 'english')
    filtered = [token for token in tokens if token not in stopwords_set]

    return TreebankWordDetokenizer().detokenize(filtered)
