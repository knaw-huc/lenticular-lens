from csv import reader as csv_reader

# COUNTRY CODE OF TWO CHARACTERS
iso_3166_1 = {
    'name': 'code',
    'afghanistan': 'af',
    'ã…land islands': 'ax',
    'albania': 'al',
    'algeria': 'dz',
    'american samoa': 'as',
    'andorra': 'ad',
    'angola': 'ao',
    'anguilla': 'ai',
    'antarctica': 'aq',
    'antigua and barbuda': 'ag',
    'argentina': 'ar',
    'armenia': 'am',
    'aruba': 'aw', 'australia': 'au', 'austria': 'at',
    'azerbaijan': 'az', 'bahamas': 'bs', 'bahrain': 'bh', 'bangladesh': 'bd', 'barbados': 'bb',
    'belarus': 'by', 'belgium': 'be', 'belize': 'bz', 'benin': 'bj', 'bermuda': 'bm',
    'bhutan': 'bt', 'bolivia, plurinational state of': 'bo',
    'bonaire, sint eustatius and saba': 'bq', 'bosnia and herzegovina': 'ba',
    'botswana': 'bw', 'bouvet island': 'bv', 'brazil': 'br',
    'british indian ocean territory': 'io', 'brunei darussalam': 'bn',
    'bulgaria': 'bg', 'burkina faso': 'bf', 'burundi': 'bi', 'cambodia': 'kh',
    'cameroon': 'cm', 'canada': 'ca', 'cape verde': 'cv', 'cayman islands': 'ky',
    'central african republic': 'cf', 'chad': 'td', 'chile': 'cl', 'china': 'cn',
    'christmas island': 'cx', 'cocos (keeling) islands': 'cc', 'colombia': 'co',
    'comoros': 'km', 'congo': 'cg', 'congo, the democratic republic of the': 'cd',
    'cook islands': 'ck', 'costa rica': 'cr', "cã´te d'ivoire": 'ci', 'croatia': 'hr',
    'cuba': 'cu', 'curaã§ao': 'cw', 'cyprus': 'cy', 'czech republic': 'cz', 'denmark': 'dk',
    'djibouti': 'dj', 'dominica': 'dm', 'dominican republic': 'do', 'ecuador': 'ec',
    'egypt': 'eg', 'el salvador': 'sv', 'equatorial guinea': 'gq', 'eritrea': 'er',
    'estonia': 'ee', 'ethiopia': 'et', 'falkland islands (malvinas)': 'fk',
    'faroe islands': 'fo', 'fiji': 'fj', 'finland': 'fi', 'france': 'fr',
    'french guiana': 'gf', 'french polynesia': 'pf', 'french southern territories': 'tf',
    'gabon': 'ga', 'gambia': 'gm', 'georgia': 'ge', 'germany': 'de', 'ghana': 'gh',
    'gibraltar': 'gi', 'greece': 'gr', 'greenland': 'gl', 'grenada': 'gd', 'guadeloupe': 'gp',
    'guam': 'gu', 'guatemala': 'gt', 'guernsey': 'gg', 'guinea': 'gn',
    'guinea-bissau': 'gw', 'guyana': 'gy', 'haiti': 'ht', 'heard island and mcdonald islands': 'hm',
    'holy see (vatican city state)': 'va', 'honduras': 'hn', 'hong kong': 'hk', 'hungary': 'hu',
    'iceland': 'is', 'india': 'in', 'indonesia': 'id', 'iran, islamic republic of': 'ir',
    'iraq': 'iq', 'ireland': 'ie', 'isle of man': 'im', 'israel': 'il', 'italy': 'it',
    'jamaica': 'jm', 'japan': 'jp', 'jersey': 'je', 'jordan': 'jo', 'kazakhstan': 'kz',
    'kenya': 'ke', 'kiribati': 'ki', "korea, democratic people's republic of": 'kp',
    'korea, republic of': 'kr', 'kuwait': 'kw', 'kyrgyzstan': 'kg', "lao people's democratic republic": 'la',
    'latvia': 'lv', 'lebanon': 'lb', 'lesotho': 'ls', 'liberia': 'lr', 'libya': 'ly', 'liechtenstein': 'li',
    'lithuania': 'lt', 'luxembourg': 'lu', 'macao': 'mo', 'macedonia, the former yugoslav republic of': 'mk',
    'madagascar': 'mg', 'malawi': 'mw', 'malaysia': 'my', 'maldives': 'mv', 'mali': 'ml', 'malta': 'mt',
    'marshall islands': 'mh', 'martinique': 'mq', 'mauritania': 'mr', 'mauritius': 'mu', 'mayotte': 'yt',
    'mexico': 'mx', 'micronesia, federated states of': 'fm', 'moldova, republic of': 'md', 'monaco': 'mc',
    'mongolia': 'mn', 'montenegro': 'me', 'montserrat': 'ms', 'morocco': 'ma', 'mozambique': 'mz', 'myanmar': 'mm',
    'namibia': 'na', 'nauru': 'nr', 'nepal': 'np', 'netherlands': 'nl', 'new caledonia': 'nc', 'new zealand': 'nz',
    'nicaragua': 'ni', 'niger': 'ne', 'nigeria': 'ng', 'niue': 'nu', 'norfolk island': 'nf',
    'northern mariana islands': 'mp', 'norway': 'no', 'oman': 'om', 'pakistan': 'pk', 'palau': 'pw',
    'palestine, state of': 'ps', 'panama': 'pa', 'papua new guinea': 'pg', 'paraguay': 'py', 'peru': 'pe',
    'philippines': 'ph', 'pitcairn': 'pn', 'poland': 'pl', 'portugal': 'pt', 'puerto rico': 'pr', 'qatar': 'qa',
    'rã©union': 're', 'romania': 'ro', 'russian federation': 'ru', 'rwanda': 'rw', 'saint barthã©lemy': 'bl',
    'saint helena, ascension and tristan da cunha': 'sh', 'saint kitts and nevis': 'kn', 'saint lucia': 'lc',
    'saint martin (french part)': 'mf', 'saint pierre and miquelon': 'pm', 'saint vincent and the grenadines': 'vc',
    'samoa': 'ws', 'san marino': 'sm', 'sao tome and principe': 'st', 'saudi arabia': 'sa', 'senegal': 'sn',
    'serbia': 'rs', 'seychelles': 'sc', 'sierra leone': 'sl', 'singapore': 'sg', 'sint maarten (dutch part)': 'sx',
    'slovakia': 'sk', 'slovenia': 'si', 'solomon islands': 'sb', 'somalia': 'so', 'south africa': 'za',
    'south georgia and the south sandwich islands': 'gs', 'south sudan': 'ss', 'spain': 'es', 'sri lanka': 'lk',
    'sudan': 'sd', 'suriname': 'sr', 'svalbard and jan mayen': 'sj', 'swaziland': 'sz', 'sweden': 'se',
    'switzerland': 'ch', 'syrian arab republic': 'sy', 'taiwan, province of china': 'tw', 'tajikistan': 'tj',
    'tanzania, united republic of': 'tz', 'thailand': 'th', 'timor-leste': 'tl', 'togo': 'tg', 'tokelau': 'tk',
    'tonga': 'to', 'trinidad and tobago': 'tt', 'tunisia': 'tn', 'turkey': 'tr', 'turkmenistan': 'tm',
    'turks and caicos islands': 'tc', 'tuvalu': 'tv', 'uganda': 'ug', 'ukraine': 'ua', 'united arab emirates': 'ae',
    'united kingdom': 'gb', 'united states': 'us', 'united states minor outlying islands': 'um', 'uruguay': 'uy',
    'uzbekistan': 'uz', 'vanuatu': 'vu', 'venezuela, bolivarian republic of': 've', 'viet nam': 'vn',
    'virgin islands, british': 'vg', 'virgin islands, u.s.': 'vi', 'wallis and futuna': 'wf', 'western sahara': 'eh',
    'yemen': 'ye', 'zambia': 'zm', 'zimbabwe': 'zw'}

# LANGUAGE CODE OF TWO CHARACTERS
iso_639_1 = {'zulu': 'zu', 'zhuang': 'za', ' chuang': 'za', 'yoruba': 'yo', 'yiddish': 'yi', 'xhosa': 'xh', 'wolof': 'wo', 'western frisian': 'fy', 'welsh': 'cy', 'walloon': 'wa', 'volapük': 'vo', 'vietnamese': 'vi', 'venda': 've', 'uzbek': 'uz', 'urdu': 'ur', 'ukrainian': 'uk', 'uighur': 'ug', ' uyghur': 'ug', 'twi': 'tw', 'turkmen': 'tk', 'turkish': 'tr', 'tswana': 'tn', 'tsonga': 'ts', 'tonga (tonga islands)': 'to', 'tigrinya': 'ti', 'tibetan': 'bo', 'thai': 'th', 'telugu': 'te', 'tatar': 'tt', 'tamil': 'ta', 'tajik': 'tg', 'tahitian': 'ty', 'tagalog': 'tl', 'swedish': 'sv', 'swati': 'ss', 'swahili': 'sw', 'sundanese': 'su', 'spanish': 'es', ' castilian': 'es', 'sotho, southern': 'st', 'somali': 'so', 'slovenian': 'sl', 'slovak': 'sk', 'sinhala': 'si', ' sinhalese': 'si', 'sindhi': 'sd', 'sichuan yi': 'ii', ' nuosu': 'ii', 'shona': 'sn', 'serbian': 'sr', 'sardinian': 'sc', 'sanskrit': 'sa', 'sango': 'sg', 'samoan': 'sm', 'russian': 'ru', 'rundi': 'rn', 'romansh': 'rm', 'romanian': 'ro', ' moldavian': 'ro', ' moldovan': 'ro', 'quechua': 'qu', 'pushto': 'ps', ' pashto': 'ps', 'portuguese': 'pt', 'polish': 'pl', 'persian': 'fa', 'panjabi': 'pa', ' punjabi': 'pa', 'pali': 'pi', 'ossetian': 'os', ' ossetic': 'os', 'oromo': 'om', 'oriya': 'or', 'ojibwa': 'oj', 'occitan (post 1500)': 'oc', 'norwegian nynorsk': 'nn', 'norwegian bokmål': 'nb', 'norwegian': 'no', 'northern sami': 'se', 'nepali': 'ne', 'ndonga': 'ng', 'ndebele, south': 'nr', ' south ndebele': 'nr', 'ndebele, north': 'nd', ' north ndebele': 'nd', 'navajo': 'nv', ' navaho': 'nv', 'nauru': 'na', 'mongolian': 'mn', 'marshallese': 'mh', 'marathi': 'mr', 'maori': 'mi', 'manx': 'gv', 'maltese': 'mt', 'malayalam': 'ml', 'malay': 'ms', 'malagasy': 'mg', 'macedonian': 'mk', 'luxembourgish': 'lb', ' letzeburgesch': 'lb', 'luba-katanga': 'lu', 'lithuanian': 'lt', 'lingala': 'ln', 'limburgan': 'li', ' limburger': 'li', ' limburgish': 'li', 'latvian': 'lv', 'latin': 'la', 'lao': 'lo', 'kurdish': 'ku', 'kuanyama': 'kj', ' kwanyama': 'kj', 'korean': 'ko', 'kongo': 'kg', 'komi': 'kv', 'kirghiz': 'ky', ' kyrgyz': 'ky', 'kinyarwanda': 'rw', 'kikuyu': 'ki', ' gikuyu': 'ki', 'kazakh': 'kk', 'kashmiri': 'ks', 'kanuri': 'kr', 'kannada': 'kn', 'kalaallisut': 'kl', ' greenlandic': 'kl', 'javanese': 'jv', 'japanese': 'ja', 'italian': 'it', 'irish': 'ga', 'inupiaq': 'ik', 'inuktitut': 'iu', 'interlingue': 'ie', ' occidental': 'ie', 'interlingua': 'ia', 'indonesian': 'id', 'igbo': 'ig', 'ido': 'io', 'icelandic': 'is', 'hungarian': 'hu', 'hiri motu': 'ho', 'hindi': 'hi', 'herero': 'hz', 'hebrew': 'he', 'hausa': 'ha', 'haitian': 'ht', ' haitian creole': 'ht', 'gujarati': 'gu', 'guarani': 'gn', 'greek, modern (1453-)': 'el', 'german': 'de', 'georgian': 'ka', 'ganda': 'lg', 'galician': 'gl', 'gaelic': 'gd', ' scottish gaelic': 'gd', 'fulah': 'ff', 'french': 'fr', 'finnish': 'fi', 'fijian': 'fj', 'faroese': 'fo', 'ewe': 'ee', 'estonian': 'et', 'esperanto': 'eo', 'english': 'en', 'dzongkha': 'dz', 'dutch': 'nl', ' flemish': 'nl', 'divehi': 'dv', ' dhivehi': 'dv', ' maldivian': 'dv', 'danish': 'da', 'czech': 'cs', 'croatian': 'hr', 'cree': 'cr', 'corsican': 'co', 'cornish': 'kw', 'chuvash': 'cv', 'old bulgarian': 'cu', 'chinese': 'zh', 'chichewa': 'ny', ' chewa': 'ny', ' nyanja': 'ny', 'chechen': 'ce', 'chamorro': 'ch', 'central khmer': 'km', 'catalan': 'ca', ' valencian': 'ca', 'burmese': 'my', 'bulgarian': 'bg', 'breton': 'br', 'bosnian': 'bs', 'bislama': 'bi', 'bihari languages': 'bh', 'bengali': 'bn', 'belarusian': 'be', 'basque': 'eu', 'bashkir': 'ba', 'bambara': 'bm', 'azerbaijani': 'az', 'aymara': 'ay', 'avestan': 'ae', 'avaric': 'av', 'assamese': 'as', 'armenian': 'hy', 'aragonese': 'an', 'arabic': 'ar', 'amharic': 'am', 'albanian': 'sq', 'akan': 'ak', 'afrikaans': 'af', 'afar': 'aa', 'abkhazian': 'ab'}

# LANGUAGE CODE OF THREE CHARACTERS
iso_639_2 = {'zulu': 'zul', 'zhuang; chuang': 'zha', 'yoruba': 'yor', 'yiddish': 'yid', 'xhosa': 'xho', 'wolof': 'wol', 'western frisian': 'fry', 'welsh': 'wel', 'walloon': 'wln', 'volapük': 'vol', 'vietnamese': 'vie', 'venda': 'ven', 'uzbek': 'uzb', 'urdu': 'urd', 'ukrainian': 'ukr', 'uighur; uyghur': 'uig', 'twi': 'twi', 'turkmen': 'tuk', 'turkish': 'tur', 'tswana': 'tsn', 'tsonga': 'tso', 'tonga (tonga islands)': 'ton', 'tigrinya': 'tir', 'tibetan': 'tib', 'thai': 'tha', 'telugu': 'tel', 'tatar': 'tat', 'tamil': 'tam', 'tajik': 'tgk', 'tahitian': 'tah', 'tagalog': 'tgl', 'swedish': 'swe', 'swati': 'ssw', 'swahili': 'swa', 'sundanese': 'sun', 'spanish; castilian': 'spa', 'sotho, southern': 'sot', 'somali': 'som', 'slovenian': 'slv', 'slovak': 'slo', 'sinhala; sinhalese': 'sin', 'sindhi': 'snd', 'sichuan yi; nuosu': 'iii', 'shona': 'sna', 'serbian': 'srp', 'sardinian': 'srd', 'sanskrit': 'san', 'sango': 'sag', 'samoan': 'smo', 'russian': 'rus', 'rundi': 'run', 'romansh': 'roh', 'romanian; moldavian; moldovan': 'rum', 'quechua': 'que', 'pushto; pashto': 'pus', 'portuguese': 'por', 'polish': 'pol', 'persian': 'per', 'panjabi; punjabi': 'pan', 'pali': 'pli', 'ossetian; ossetic': 'oss', 'oromo': 'orm', 'oriya': 'ori', 'ojibwa': 'oji', 'occitan (post 1500)': 'oci', 'norwegian nynorsk': 'nno', 'norwegian bokmål': 'nob', 'norwegian': 'nor', 'northern sami': 'sme', 'nepali': 'nep', 'ndonga': 'ndo', 'ndebele, south; south ndebele': 'nbl', 'ndebele, north; north ndebele': 'nde', 'navajo; navaho': 'nav', 'nauru': 'nau', 'mongolian': 'mon', 'marshallese': 'mah', 'marathi': 'mar', 'maori': 'mao', 'manx': 'glv', 'maltese': 'mlt', 'malayalam': 'mal', 'malay': 'may', 'malagasy': 'mlg', 'macedonian': 'mac', 'luxembourgish; letzeburgesch': 'ltz', 'luba-katanga': 'lub', 'lithuanian': 'lit', 'lingala': 'lin', 'limburgan; limburger; limburgish': 'lim', 'latvian': 'lav', 'latin': 'lat', 'lao': 'lao', 'kurdish': 'kur', 'kuanyama; kwanyama': 'kua', 'korean': 'kor', 'kongo': 'kon', 'komi': 'kom', 'kirghiz; kyrgyz': 'kir', 'kinyarwanda': 'kin', 'kikuyu; gikuyu': 'kik', 'kazakh': 'kaz', 'kashmiri': 'kas', 'kanuri': 'kau', 'kannada': 'kan', 'kalaallisut; greenlandic': 'kal', 'javanese': 'jav', 'japanese': 'jpn', 'italian': 'ita', 'irish': 'gle', 'inupiaq': 'ipk', 'inuktitut': 'iku', 'interlingue; occidental': 'ile', 'interlingua': 'ina', 'indonesian': 'ind', 'igbo': 'ibo', 'ido': 'ido', 'icelandic': 'ice', 'hungarian': 'hun', 'hiri motu': 'hmo', 'hindi': 'hin', 'herero': 'her', 'hebrew': 'heb', 'hausa': 'hau', 'haitian; haitian creole': 'hat', 'gujarati': 'guj', 'guarani': 'grn', 'greek, modern (1453-)': 'gre', 'german': 'ger', 'georgian': 'geo', 'ganda': 'lug', 'galician': 'glg', 'gaelic; scottish gaelic': 'gla', 'fulah': 'ful', 'french': 'fre', 'finnish': 'fin', 'fijian': 'fij', 'faroese': 'fao', 'ewe': 'ewe', 'estonian': 'est', 'esperanto': 'epo', 'english': 'eng', 'dzongkha': 'dzo', 'dutch; flemish': 'dut', 'divehi; dhivehi; maldivian': 'div', 'danish': 'dan', 'czech': 'cze', 'croatian': 'hrv', 'cree': 'cre', 'corsican': 'cos', 'cornish': 'cor', 'chuvash': 'chv', 'old bulgarian': 'chu', 'chinese': 'chi', 'chichewa; chewa; nyanja': 'nya', 'chechen': 'che', 'chamorro': 'cha', 'central khmer': 'khm', 'catalan; valencian': 'cat', 'burmese': 'bur', 'bulgarian': 'bul', 'breton': 'bre', 'bosnian': 'bos', 'bislama': 'bis', 'bihari languages': 'bih', 'bengali': 'ben', 'belarusian': 'bel', 'basque': 'baq', 'bashkir': 'bak', 'bambara': 'bam', 'azerbaijani': 'aze', 'aymara': 'aym', 'avestan': 'ave', 'avaric': 'ava', 'assamese': 'asm', 'armenian': 'arm', 'aragonese': 'arg', 'arabic': 'ara', 'amharic': 'amh', 'albanian': 'alb', 'akan': 'aka', 'afrikaans': 'afr', 'afar': 'aar', 'abkhazian': 'abk'}

# cc= "/Users/al/Dropbox/@VU/Ve/Al Docs/CountryCode2"
# iso_639_1 = {}
# with open(cc) as data:
#     # data = csv_reader(data,)
#     for line in data:
#
#         split = line.lower().strip().split("\t")
#
#         if len(split) > 1:
#             code = split[2].strip()
#             lang = split[0].strip()
#             lang = lang.split(";")
#
#             # print(code)
#             for language in lang:
#                 if len(code) == 3:
#                     iso_639_1[language] = code
#
#     print(iso_639_1)
