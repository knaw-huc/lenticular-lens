from ll.util.config_db import conn_pool

stopwords = dict()
languages = {
    'arabic': 'ar',
    'azerbaijani': 'az',
    'danish': 'da',
    'dutch': 'nl',
    'dutch_names': 'nl',
    'english': 'en',
    'finnish': 'fi',
    'french': 'fr',
    'german': 'de',
    'greek': 'el',
    'hungarian': 'hu',
    'indonesian': 'id',
    'italian': 'it',
    'kazakh': 'kk',
    'nepali': 'ne',
    'norwegian': 'no',
    'portuguese': 'pt',
    'romanian': 'ro',
    'russian': 'ru',
    'slovene': 'sl',
    'spanish': 'es',
    'swedish': 'sv',
    'tajik': 'tg',
    'turkish': 'tr'
}


def get_stopwords(dictionary):
    if dictionary not in list(languages.keys()):
        raise Exception('Invalid dictionary')

    if dictionary not in stopwords:
        with conn_pool.connection() as conn:
            stopwords[dictionary] = conn.execute('SELECT get_stopwords(%s)', (dictionary,)).fetchone()[0]

    return stopwords[dictionary]


def get_iso_639_1_code(dictionary):
    if dictionary not in list(languages.keys()):
        raise Exception('Invalid dictionary')

    return languages[dictionary]
