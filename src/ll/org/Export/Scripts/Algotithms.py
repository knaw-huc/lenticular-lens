from rdflib import URIRef, Literal
from ll.org.Export.Scripts.Variables import PREF_SIZE, LL

scale = {}
descriptions = {}

# SCRIPT OVERVIEW ######################################################################################################
#                                                                                                                      #
#   This lists the matching algorithms available in the Lenticular Lens Tool in order to provide them with consistent  #
#    URL, and information for a better understanding of what they are designed for. For each algorithm, is provided:   #
#       01. A full URL.                                                                                                #
#       02. A URL in a Turtle format.                                                                                  #
#       03. A description of the method.                                                                               #
#       04. The range of the algorithm matching result.                                                                #
#       05. Soundex: a standard phonetic-based algorithm.                                                              #
#       06. Bloothooft: an algorithm for normalising dutch names.                                                      #
#       07. Word intersection: designed to find a subset of words within a larger text.                                #
#       08. TeAML designed for matching text segments.                                                                 #
#       09. Numbers: For matching numbers within a Delta difference.                                                   #
#       10. Complex: Methods that combine multiple of ghe above algorithms.                                            #
#                                                                                                                      #
#   These algorithms include:                                                                                          #
#       1. Unknown: used for any imported linksets or lenses for which there is no information on the methodology used #
#          for generating links.                                                                                       #
#       2. Embedded: for extracting existing links within one or more datasets.                                        #
#       3. Intermediate: for matching resources across datasets using an intermediate authoritative dataset.           #
#       4. EditDistance: the Levenshtein distance.                                                                     #
#       5.                                                                                                             #
#                                                                                                                      #
# ######################################################################################################################


class Algorithm:

    point = "1"
    natural = "ℕ"
    interval = "]0, 1]"
    set = "{0, 1}"

    algorithm = F"{LL}resource/"
    complex = F"{algorithm}Complex"
    complex_ttl = "resource:Complex"

    # algorithm_prefix = F"@prefix {'ll_algorithm':>{PREF_SIZE}}: <{algorithm}> ."

    # METHOD 1: UNKNOWN
    unknown = F"{algorithm}Unknown"
    unknown_ttl = "resource:Unknown"
    unknown_description = "The method used to generate the current link is unknown."

    # ---------------------------------------------- #
    # EXACT SEARCH                                   #
    # ---------------------------------------------- #

    # METHOD 2: EXACT
    exact = F"{algorithm}Exact"
    exact_ttl = "resource:Exact"
    exact_range = "1"
    exact_description = """
        Aligns source and target’s IRIs whenever their respective user selected property values are identical."""

    # ---------------------------------------------- #
    # MAPPING                                        #
    # ---------------------------------------------- #

    # METHOD 3: EMBEDDED
    embedded = F"{algorithm}Embedded"
    embedded_ttl = "resource:Embedded"
    embedded_description = """
        It extracts an alignment already provided within the source dataset. The extraction relies on the value of 
        the liking property, i.e. property of the source that holds the identifier of the target. The inconvenience 
        in generating a linkset in such way is that the real mechanism used to create the existing alignment is not 
        explicitly provided by the source dataset."""

    # ---------------------------------------------- #
    # CHANGE / EDIT                                  #
    # ---------------------------------------------- #

    # METHOD 4: JARO
    jaro = F"{algorithm}Jaro"
    jaro_ttl = "resource:Jaro"
    jaro_description = """
        This  method is used to align source and target's IRIs whenever the similarity score of their respective user 
        selected property values are above a given threshold in the range ]0, 1]​.
        
        Jaro distance is a measure of similarity between two strings. The higher the Jaro distance for two strings is, 
        the more similar the strings are. The score is normalised such that 0 equates to no similarity and 1 is an exact 
        match.
        
        Given two strings S1 and S2, the method consists in finding common characters (xi = yj) xi of S1 and yj of S2 
        such that xi and yj are not more than d characters away from each other. The acceptable matching distance d is 
        half the longest input string.
        
        EXAMPLES:
        ---------
        
           SOURCE                : |s| = |source| = 6
           TARGET                : |t| = |target| = 6
           MATCHING DISTANCE     : d = max(6, 6) = 3
           COMMON CHARACTERS     : m = |re| = |re| = 2
           TRANSPOSITIONS        : t = 0
           STRENGTH              : s = 1/3 * ( 2/6 + 2/6 + (2 - 0/2)/2) = 0.55556
        
        
           SOURCE                : |s| = |jono| = 4
           TARGET                : |t| = |ojhono| = 6
           MATCHING DISTANCE     : d = max(4, 6) = 3
           COMMON CHARACTERS     : m = |jono| = |ojon| = 4
           TRANSPOSITIONS        : t = 4
           STRENGTH              : s = 1/3 * ( 4/4 + 4/6 + (4 - 4/2)/4) = 0.72222
        
        
           SOURCE                : |s| = |DUANE| = 5
           TARGET                : |t| = |DWAYNE| = 6
           MATCHING DISTANCE     : d = max(5, 6) = 3
           COMMON CHARACTERS     : m = |DANE| = |DANE| = 4
           TRANSPOSITIONS        : t = 0
           STRENGTH              : s = 1/3 * ( 4/5 + 4/6 + (4 - 0/2)/4) = 0.82222
        
        
           SOURCE                : |s| = |DIXON| = 5
           TARGET                : |t| = |DICKSONX| = 8
           MATCHING DISTANCE     : d = max(5, 8) = 4
           COMMON CHARACTERS     : m = |DION| = |DION| = 4
           TRANSPOSITIONS        : t = 0
           STRENGTH              : s = 1/3 * ( 4/5 + 4/8 + (4 - 0/2)/4) = 0.76667
        
        
           SOURCE                : |s| = |JELLYFISH| = 9
           TARGET                : |t| = |SMELLYFISH| = 10
           MATCHING DISTANCE     : d = max(9, 10) = 5
           COMMON CHARACTERS     : m = |ELLYFISH| = |ELLYFISH| = 8
           TRANSPOSITIONS        : t = 0
           STRENGTH              : s = 1/3 * ( 8/9 + 8/10 + (8 - 0/2)/8) = 0.8963
        """

    # METHOD 5: JARO WINKLER
    jaro_winkler = F"{algorithm}Jaro_Winkler"
    jaro_winkler_ttl = "resource:Jaro_Winkler"
    jaro_winkler_description = """
        Given two strings s1 and s2, the Winkler similarity equation boosts up the Jaro algorithm’s result dj by 
        increasing it whenever the compared strings share a prefix of a maximum of four characters. In this shared 
        prefix scenario, the boost is computed as:
    
        w = Pl * Pw ( 1 - dj )
    
        where 
            - Pl is the length of the set of shared prefix and 
            - Pw is a user dependent scaling factor for how much the score is adjusted upwards for having common prefixes. 
            Because four is the maximum number of shared prefix to consider, the user’s choice of Pw lies between 0 and ¼. 
            Setting Pw to ¼ implies a similarity of always 1 whenever the strings share the maximum of 4 prefixes, no matter 
            the real dissimilarity between the strings.
    
        The Jaro Winkler is computed as: d_jw = dj + w
        """

    # METHOD 6: EDIT DISTANCE
    normalisedEditDistance = F"{algorithm}Normalised-EditDistance"
    normalisedEditDistance_ttl = "resource:Normalised-EditDistance"
    NormalisedEditDistance_description = """
        This ​method is used to align ​​source a​nd ​​target’s IRIs whenever the similarity score of their respective 
        user selected property values are ​​above a given ​Levenshtein (edit) Distance threshold​. 
        Edit distance is a way of quantifying how ​dissimilar two strings (e.g., words) are to one another by 
        counting the minimum number of operations ​ε ​(​removal, insertion, or substitution of a character in the 
        string)​ required to transform one string into the other. For example, ​the ​Levenshtein distance between 
        kitten and sitting is ​ε ​= 3 as it requires a two substitutions (s for k and i for e) and one insertion  
        of g at the end [https://en.wikipedia.org/wiki/Edit_distance]​.
        """

    # METHOD 7: EDIT DISTANCE
    editDistance = F"{algorithm}Edit-Distance"
    editDistance_ttl = "resource:Edit-Distance"
    editDistance_description = """
        This ​method is used to align ​​source a​nd ​​target’s IRIs whenever the similarity score of their respective 
        user selected property values are ​​above a given ​Levenshtein (edit) Distance threshold​. 
        Edit distance is a way of quantifying how ​dissimilar two strings (e.g., words) are to one another by 
        counting the minimum number of operations ​ε ​(​removal, insertion, or substitution of a character in the 
        string)​ required to transform one string into the other. For example, ​the ​Levenshtein distance between 
        kitten and sitting is ​ε ​= 3 as it requires a two substitutions (s for k and i for e) and one insertion  
        of g at the end [https://en.wikipedia.org/wiki/Edit_distance]​.
        """

    # METHOD 8: TRIGRAM
    trigram = F"{algorithm}trigram"
    trigram_ttl = "resource:Trigram"
    trigram_description = """
        Trigrams are a special case of the n-gram, where n is 3. It is a contiguous sequence of three items from a 
        given sample. 

        To be mre concrete, In the case of string similarity, where an application of NAME is a sample and a 
        CHARACTER is an item, we obtain a sequence of 4 trigrams { mar art rth tha } from the sample “martha”. 

        If we consider a WORD as an item in the sample "the quick red fox jumps over the lazy brown dog", 
        we then obtain a sequence of 8 WORD-LEVEL TRIGRAMS { the quick red | quick red fox | red fox jumps | 
        fox jumps over | jumps over the | over the lazy | the lazy brown | lazy brown dog }. 

        N-grams can be used for approximate matching by comparing two trigram sequences using metrics such as 
        cosine distance, z-scores or g-test.

        see [https://en.wikipedia.org/wiki/Trigram], [https://en.wikipedia.org/wiki/N-gram] for more information. 
        """

    # ---------------------------------------------- #
    # PHONETIC                                       #
    # ---------------------------------------------- #

    # METHOD 9: SOUNDEX
    normalisedSoundex = F"{algorithm}Normalised-Soundex"
    normalisedSoundex_ttl = "resource:Normalised-Soundex"
    normalisedSoundex_description = """
        "Soundex is a phonetic algorithm for indexing names by sound, as pronounced in English. The goal is for ho-
        mophones to be encoded to the same representation so that they can be matched despite minor differences in
        spelling. The algorithm mainly encodes consonants; a vowel will not be encoded unless it is the first let-
        ter” [https://en.wikipedia.org/wiki/Soundex]. 
        In the Lenticular Lens, Soundex is used as a normaliser in the sense that an edit distance is run over the 
        soundex code version of a name. For example, the in the table below, the normalisation of both Louijs Roc-
        ourt and `Lowis Ricourt becomes L200 R263 leading to an edit distance of 0 and a relative strength of 1. 
        However, computing the same names using directly an edit distance results in an edit distance of 3 and a 
        relative matching strength of 0. 79.

        --------------
        -- Example -- THE USE OF SOUNDEX CODE FOR STRING APPROXIMATION
        --------------
        The example below shows the implementation of Soundex Distance 
        in the Lenticular Lens and how it compares with Edit Distance
        over the original names (no soundex-based normalisation).

        ------------------------------------------------------------------------------------------------------------------------------------------------------
        Source                      Target                     E. Dist  Rel. distance  Source soundex       Target  soundex       Code E. Dist  Code Rel. Dist
        ------------------------------------------------------------------------------------------------------------------------------------------------------
        Jasper Cornelisz. Lodder    Jaspar Cornelisz Lodder          2           0.92  J216 C654 L360       J216 C654 L360                   0             1.0
        Barent Teunis               Barent Teunisz gen. Drent       12           0.52  B653 T520            B653 T520 G500 D653             10            0.47
        Louijs Rocourt              Louys Rocourt                    2           0.86  L200 R263            L200 R263                        0             1.0
        Louijs Rocourt              Lowis Ricourt                    3           0.79  L200 R263            L200 R263                        0             1.0
        Louys Rocourt               Lowis Ricourt                    3           0.77  L200 R263            L200 R263                        0             1.0
        Cornelis Dircksz. Clapmus   Cornelis Clapmuts               10            0.6  C654 D620 C415       C654 C415                        5            0.64
        Geertruydt van den Breemde  Geertruijd van den Bremde        4           0.85  G636 V500 D500 B653  G636 V500 D500 B653  
        """

    soundexDistance = F"{algorithm}SoundexDistance"
    soundexDistance_ttl = "resource:SoundexDistance"
    soundexDistance_description = """
        "Soundex is a phonetic algorithm for indexing names by sound, as pronounced in English. The goal is for ho-
        mophones to be encoded to the same representation so that they can be matched despite minor differences in
        spelling. The algorithm mainly encodes consonants; a vowel will not be encoded unless it is the first let-
        ter” [https://en.wikipedia.org/wiki/Soundex]. 
        In the Lenticular Lens, Soundex is used as a normaliser in the sense that an edit distance is run over the 
        soundex code version of a name. For example, the in the table below, the normalisation of both Louijs Roc-
        ourt and `Lowis Ricourt becomes L200 R263 leading to an edit distance of 0 and a relative strength of 1. 
        However, computing the same names using directly an edit distance results in an edit distance of 3 and a 
        relative matching strength of 0. 79.

        --------------
        -- Example -- THE USE OF SOUNDEX CODE FOR STRING APPROXIMATION
        --------------
        The example below shows the implementation of Soundex Distance 
        in the Lenticular Lens and how it compares with Edit Distance
        over the original names (no soundex-based normalisation).

        ------------------------------------------------------------------------------------------------------------------------------------------------------
        Source                      Target                     E. Dist  Rel. distance  Source soundex       Target  soundex       Code E. Dist  Code Rel. Dist
        ------------------------------------------------------------------------------------------------------------------------------------------------------
        Jasper Cornelisz. Lodder    Jaspar Cornelisz Lodder          2           0.92  J216 C654 L360       J216 C654 L360                   0             1.0
        Barent Teunis               Barent Teunisz gen. Drent       12           0.52  B653 T520            B653 T520 G500 D653             10            0.47
        Louijs Rocourt              Louys Rocourt                    2           0.86  L200 R263            L200 R263                        0             1.0
        Louijs Rocourt              Lowis Ricourt                    3           0.79  L200 R263            L200 R263                        0             1.0
        Louys Rocourt               Lowis Ricourt                    3           0.77  L200 R263            L200 R263                        0             1.0
        Cornelis Dircksz. Clapmus   Cornelis Clapmuts               10            0.6  C654 D620 C415       C654 C415                        5            0.64
        Geertruydt van den Breemde  Geertruijd van den Bremde        4           0.85  G636 V500 D500 B653  G636 V500 D500 B653  
        """

    # METHOD 10: METAPHONE
    metaphone = F"{algorithm}Metaphone"
    metaphone_ttl = "resource:Metaphone"
    metaphone_description = """
        Designed by Lawrence Philips in 1990, it is a phonetic algorithm for a more accurate encoding of words by sound 
        (as compared to SOUNDEX) as pronounced in English. In this algorithm as with SOUNDEX, similar-sounding words
        should share the same encoding key which is an approximate phonetic representation of the original word.
        For more accuracy, consider the use of DOUBLE METAPHONE as it is an improvement of the Original Metaphone. 
        In turn, for an even better improved accuracy consider the use of METAPHONE 3. 
        
        See [https://en.wikipedia.org/wiki/Metaphone] for mor information.
        """

    # METHOD 11: DOUBLE METAPHONE
    doubleMetaphone = F"{algorithm}DoubleMetaphone"
    doubleMetaphone_ttl = "resource:DoubleMetaphone"
    doubleMetaphone_description = """
        it is a third generation phonetic algorithm improvement after SOUNDEX and METAPHONE for an accurately encoding  
        words by sound as pronounced in English. For more accuracy, consider the use of METAPHONE 3 as it is an 
        improvement of the DOUBLE METAPHONE.
        
        It is called "Double" because it can return both a primary and a secondary code for a string; this accounts 
        for some ambiguous cases as well as for multiple variants of surnames with common ancestry. For example, 
        encoding the name "Smith" yields a primary code of SM0 and a secondary code of XMT, while the name "Schmidt" 
        yields a primary code of XMT and a secondary code of SMT—both have XMT in common.
        
        Double Metaphone tries to account for myriad irregularities in English of Slavic, Germanic, Celtic, Greek, 
        French, Italian, Spanish, Chinese, and other origin. Thus it uses a much more complex ruleset for coding 
        than its predecessor; for example, it tests for approximately 100 different contexts of the use of the letter 
        C alone.
        
        See [https://en.wikipedia.org/wiki/Metaphone] for mor information.
        """

    # METHOD 12: BLOOTHOOFT
    bloothooft = F"{algorithm}Bloothooft"
    bloothooft_ttl = "resource:Bloothooft"
    bloothooft_range = "]0, 1]"

    # ---------------------------------------------- #
    # HYBRID                                         #
    # ---------------------------------------------- #

    # METHOD 13: INTERMEDIATE
    intermediate = F"{algorithm}Intermediate"
    intermediate_ttl = "resource:Intermediate"
    intermediate_description = """
        The method aligns the source and the target’s IRIs via an intermediate database by using properties that 
        potentially present different descriptions of the same entity, such as country name and country code. This 
        is possible by providing an intermediate dataset that binds the two alternative descriptions to the very 
        same identifier.

        -------------
        -- Example -- INTERMEDIATE DATASET
        -------------
        In the example below, it is possible to align the source and target country 
        entities using the properties country and iso-3 via the intermediate dataset
        because it contains the information described at both, the Source and Target.

        dataset:Source-Dataset                       dataset:Intermediate-Dataset
        {                                            {
            ex:1  rdfs:label  "Benin" .                 ex:7
            ex:2  rdfs:label  "Cote d'Ivoire" .              ex:name "Cote d'Ivoire" ;
            ex:3  rdfs:label  "Netherlands" .                ex:code "CIV" .
        }	
                                                        ex:8                             
        dataset:Target-Datas                                ex:name "Benin" ;
        {                                                   ex:code "BEN" .
            ex:4 ex:iso-3 "CIV" .
            ex:5 ex:iso-3 "NLD" .                       ex:9
            ex:6 ex:iso-3 "BEN" .                           ex:name "Netherlands" ;
        }	                                                ex:code "NLD" .
                                                     }

        ALIGNMENT: 
          • If rdfs:label is aligned with ex:name 
          • AND ex:iso-3 is aligned with ex:code,
          • We then get the following linkset:

            linkset:Match-Via-Intermediate
            {
                ex:1 owl:sameAs ex:6 .
                ex:2 owl:sameAs ex:4 .
                ex:3 owl:sameAs ex:5 .
            }

        dataset:Source-Dataset                       dataset:Intermediate-Dataset
        {                                            {
            ex:10  rdfs:label  "Rembrandt" .             ex:70
            ex:20  rdfs:label  "van Gogh" .                  ex:name "Vincent Willem van Gogh" ;
            ex:30  rdfs:label  "Vermeer" .                   ex:name "Vincent van Gogh" ;
        }	                                                 ex:name "van Gogh" .
                                                        ex:80                             
        dataset:Target-Datas                                ex:name "Rembrandt" ;
        {                                                   ex:name "Rembrandt van Rijn" .
            ex:40 schema:name "Rembrandt van Rijn" .
            ex:50 schema:name "Vincent van Gogh" .       ex:90
            ex:60 schema:name "Johannes Vermeer" .           ex:name "Johannes Vermeer" ;
        }	                                                 ex:name "Vermeer" .
                                                     }

        ALIGNMENT: 
          • If rdfs:label is aligned with ex:name 
          • AND schema:name is also aligned with ex:name,
          • we then get the following linkset:

            linkset:Match-Via-Intermediate
            {
                ex:10 owl:sameAs ex:40 .
                ex:20 owl:sameAs ex:50 .
                ex:30 owl:sameAs ex:60 .
            }

        """

    # METHOD 14: WORLD INTERSECTION
    wordIntersection = F"{algorithm}Word-Intersection"
    wordIntersection_ttl = "resource:Word-Intersection"
    wordIntersection_description = """
    This approximation method is originally designed to find a subset of words within a larger text. However, it 
    could also be used for any pair of strings regardless of the strings sizes. Several options are available: 
    * Whether or not the order in which the words are found is important.
    * Whether or not the computed strength of each word should be approximated or identical.
    * Whether or not abbreviation should be detected.
    * Whether the default stopping character should be used, not used or modified.
    * A threshold on the number of words not approximated/identical.
    * An overall  threshold for accepting or rejecting a match.

    -------------
    -- Example -- EXPECTATIONS
    -------------
        For example, it can be used for aligning 
         - [Rembrand van Rijn] and [van Rijn Rembrandt]
         - [Herdoopers anslagh op Amsterdam] and [Herdoopers anslagh op Amsterdam. 
            Den x. may: 1535. Treur-spel.]
        regardless of the words' order.
    """

    # METHOD 15: TeAM
    TeAM = F"{algorithm}TeAM"
    TeAM_ttl = "resource:TeAM"
    TeAM_description = """
        The Amsterdam’s city archives (SAA) possesses physical handwritten inventories records where a record may 
        be for example an inventory of goods (paintings, prints, sculpture, furniture, porcelain, etc.) owned by 
        an Amsterdamer and mentioned in a last will. Interested in documenting the ownership of paintings from 
        the 17th century, the Yale University Professor John Michael Montias compiled a database by transcribing 
        1280 physical handwritten inventories (scattered in the Netherlands) of goods. Now that a number of these 
        physical inventories have been digitised using handwriting recognition, one of the goals of the Golden 
        Agent project is to identify Montias' transcriptions of painting selections within the digitised invento-
        ries. This problem can be generically reformulated as, given a source-segment database (e.g. Montias DB) 
        and a target-segment database (e.g. SAA), find the best similar target segment for each source segment.
        """

    # ---------------------------------------------- #
    # NUMERICAL                                      #
    # ---------------------------------------------- #

    # METHOD 16: NUMBERS
    numbers = F"{algorithm}Numbers"
    numbers_ttl = "resource:Numbers"
    numbers_description = """
        Numbers. The method is used to align the source and the target by approximating the match of the (number/
        date) values of the selected properties according to a delta. For example, if two entities have been ali-
        gned based on the similarity of their names but an extra check is to be investigated based on their res-
        pective year of birth, setting the delta to 1 will ensure that the two entities are born within the same 
        year, give or take a year.
        """

    # METHOD 17: TIME DELTA
    time_delta = F"{algorithm}Time-Delta"
    time_delta_ttl = "resource:Time-Delta"
    time_delta_description = """
        Time Delta. This function allows for finding co-referent entities on the basis of a minimum time dif-
        ference between the times reported by the source and the target entities. For example, if the value zero is 
        assigned to the time difference parameter, then, for a matched to be found, the time of the target and the 
        one of the source are to be the exact same times. While accounting for margins of error, one may consider a 
        pair of entities to be co-referent if the real entities are born lambda days, months or years apart among 
        other-things (similar name, place..).
        """

    # METHOD 18: TIME DELTA
    same_year_month = F"{algorithm}same_year_month"
    same_year_month_ttl = "resource:same_year_month"
    same_year_month_description = """
        AN exact match of the year and month from the dates inputs. 
    """

    bloothooftReduct= """To come"""

    global scale
    scale = {

        'interval': interval,

        'unknown': point,
        unknown.lower(): point,
        unknown_ttl.lower(): point,
        URIRef(unknown.lower()).n3(): point,

        'embedded': point,
        embedded.lower(): point,
        embedded_ttl.lower(): point,
        URIRef(unknown.lower()).n3(): point,

        'intermediate': point,
        intermediate.lower(): point,
        intermediate_ttl.lower(): point,
        URIRef(intermediate.lower()).n3(): point,

        '=': set,
        'exact': set,
        exact.lower(): set,
        exact_ttl.lower(): set,
        URIRef(exact.lower()).n3(): set,

        'levenshtein_distance': natural,

        'levenshtein_approx': interval,
        "normalised distance": interval,
        "normalised levenshtein": interval,
        'normalised edit distance': interval,
        "normalised levenshtein distance": interval,
        'levenshtein_normalized': interval,
        normalisedEditDistance.lower(): interval,
        normalisedEditDistance_ttl.lower(): interval,
        URIRef(normalisedEditDistance.lower()).n3(): interval,

        "distance": natural,
        "levenshtein": natural,
        'edit distance': natural,
        "levenshtein distance": natural,
        editDistance.lower(): natural,
        editDistance_ttl.lower(): natural,
        URIRef(editDistance.lower()).n3(): natural,

        'soundex': interval,
        'll_soundex': interval,
        "normalised soundex": interval,
        normalisedSoundex.lower(): interval,
        normalisedSoundex_ttl.lower(): interval,
        URIRef(normalisedSoundex.lower()).n3(): interval,

        "soundex distance": natural,
        soundexDistance.lower(): natural,
        soundexDistance_ttl.lower(): natural,
        URIRef(soundexDistance.lower()).n3(): natural,

        'metaphone': natural,
        metaphone.lower(): natural,
        metaphone_ttl.lower(): natural,
        URIRef(metaphone.lower()).n3(): natural,

        "dmetaphone": natural,
        doubleMetaphone.lower(): natural,
        doubleMetaphone_ttl.lower(): natural,
        URIRef(doubleMetaphone.lower()).n3(): natural,

        "trigram": interval,
        trigram.lower(): interval,
        trigram_ttl.lower(): interval,
        URIRef(trigram.lower()).n3(): interval,

        "word_intersection":  interval,
        wordIntersection.lower():  interval,
        'wordIntersection': interval,
        wordIntersection_ttl.lower(): interval,
        URIRef(wordIntersection.lower()).n3(): interval,

        time_delta.lower(): natural,
        'time_delta': natural,
        time_delta_ttl.lower(): natural,
        URIRef(time_delta.lower()).n3(): natural,

        'numbers_delta': natural,
        numbers.lower(): natural,
        numbers_ttl.lower(): natural,
        URIRef(numbers.lower()).n3(): natural,

        "TeAM": interval,
        TeAM_ttl.lower(): interval,
        URIRef(TeAM.lower()).n3(): interval,

        "bloothooft": interval,
        "bloothooft_reduct": interval,

        "jaro": interval,
        "Jaro": interval,
        "Jaro_Winkler": interval,
        "jaro_winkler": interval,
        "jaro winkler": interval,
        "Jaro Winkler": interval,
        jaro_winkler.lower(): interval,

        "same_year_month": natural,
        same_year_month: natural,
        same_year_month_ttl.lower(): interval,
        URIRef(wordIntersection.lower()).n3(): interval,
    }

    global descriptions
    descriptions = {

        'same_year_month': Literal(exact_description, lang="en").n3(),

        "=": Literal(exact_description, lang="en").n3(),
        "exact": Literal(exact_description, lang="en").n3(),
        URIRef(exact.lower()).n3(): Literal(exact_description, lang="en").n3(),
        exact_ttl.lower(): Literal(exact_description, lang="en").n3(),

        URIRef(unknown.lower()).n3(): Literal(unknown_description, lang="en").n3(),
        unknown_ttl.lower(): Literal(unknown_description, lang="en").n3(),

        URIRef(embedded.lower()).n3(): Literal(embedded_description, lang="en").n3(),
        embedded_ttl.lower(): Literal(embedded_description, lang="en").n3(),

        'intermediate':  Literal(intermediate_description, lang="en").n3(),
        URIRef(intermediate.lower()).n3(): Literal(intermediate_description, lang="en").n3(),
        intermediate_ttl.lower(): Literal(intermediate_description, lang="en").n3(),

        'levenshtein': Literal(NormalisedEditDistance_description, lang="en").n3(),
        'levenshtein_distance': Literal(NormalisedEditDistance_description, lang="en").n3(),
        'levenshtein_normalized': Literal(NormalisedEditDistance_description, lang="en").n3(),
        URIRef(editDistance.lower()).n3(): Literal(NormalisedEditDistance_description, lang="en").n3(),
        editDistance_ttl.lower(): Literal(NormalisedEditDistance_description, lang="en").n3(),

        'trigram': Literal(trigram_description, lang="en").n3(),
        'jaro': Literal(jaro_description, lang="en").n3(),
        'jaro_winkler': Literal(jaro_winkler_description, lang="en").n3(),

        'levenshtein_approx': Literal(NormalisedEditDistance_description, lang="en").n3(),
        URIRef(normalisedEditDistance.lower()).n3(): Literal(NormalisedEditDistance_description, lang="en").n3(),
        normalisedEditDistance_ttl.lower(): Literal(NormalisedEditDistance_description, lang="en").n3(),

        URIRef(soundexDistance.lower()).n3(): Literal(normalisedSoundex_description, lang="en").n3(),
        soundexDistance_ttl.lower(): Literal(normalisedSoundex_description, lang="en").n3(),

        'soundex': Literal(normalisedSoundex_description, lang="en").n3(),
        'll_soundex': Literal(normalisedSoundex_description, lang="en").n3(),
        URIRef(normalisedSoundex.lower()).n3(): Literal(normalisedSoundex_description, lang="en").n3(),
        normalisedSoundex_ttl.lower(): Literal(normalisedSoundex_description, lang="en").n3(),

        "metaphone": Literal(metaphone_description, lang="en").n3(),
        URIRef(metaphone.lower()).n3(): Literal(metaphone_description, lang="en").n3(),
        metaphone_ttl.lower(): Literal(metaphone_description, lang="en").n3(),

        "dmetaphone": Literal(doubleMetaphone_description, lang="en").n3(),
        URIRef(doubleMetaphone.lower()).n3(): Literal(doubleMetaphone_description, lang="en").n3(),
        doubleMetaphone_ttl.lower(): Literal(doubleMetaphone_description, lang="en").n3(),

        "word_intersection": Literal(wordIntersection_description, lang="en").n3(),
        URIRef(wordIntersection.lower()).n3(): Literal(wordIntersection_description, lang="en").n3(),
        wordIntersection_ttl.lower(): Literal(wordIntersection_description, lang="en").n3(),

        'numbers_delta': Literal(numbers_description, lang="en").n3(),
        URIRef(numbers.lower()).n3(): Literal(numbers_description, lang="en").n3(),
        numbers_ttl.lower(): Literal(numbers_description, lang="en").n3(),

        URIRef(TeAM.lower()).n3(): Literal(TeAM_description, lang="en").n3(),
        TeAM_ttl.lower(): Literal(TeAM_description, lang="en").n3(),

        "time_delta": Literal(time_delta_description, lang="en").n3(),
        URIRef(time_delta.lower()).n3(): Literal(time_delta_description, lang="en").n3(),
        time_delta_ttl.lower(): Literal(time_delta_description, lang="en").n3(),

        "bloothooft": Literal(bloothooftReduct, lang="en").n3(),
        "bloothooft_reduct": Literal(bloothooftReduct, lang="en").n3(),
    }


    @staticmethod
    def illustration(key):
        global descriptions
        return descriptions[key.lower()]

    @staticmethod
    def range(key):
        global scale
        return scale[key.lower()]
