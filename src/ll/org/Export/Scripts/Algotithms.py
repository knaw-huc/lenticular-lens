from rdflib import URIRef, Literal
from ll.org.Export.Scripts.Variables import LL, PREF_SIZE

scale = {}
seeAlso = {}
also_ttl = {}
algorithm_lbl = {}
algorithm_ttl = {}
descriptions = {}
short_descriptions = {}

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

    see_also = "https://lenticularlens.github.io/04.Algorithms/#{}"
    see_also_ttl = "algorithm:{}"
    see_also_prefix = F"@prefix {'algorithm':>{PREF_SIZE}}: <https://lenticularlens.github.io/04.Algorithms/#> ."

    # algorithm_prefix = F"@prefix {'ll_algorithm':>{PREF_SIZE}}: <{algorithm}> ."

    # METHOD 1: UNKNOWN
    unknown = F"{algorithm}Unknown"
    unknown_ttl = "resource:Unknown"
    unknown_short_description = unknown_description = "A resource used to denote that the method used to generate the " \
                                                      "current set of links is unknown."
    unknown_see_also = [see_also.format("unknown")]
    unknown_see_also_ttl = [see_also_ttl.format("unknown")]

    simple_clustering = F"{algorithm}SimpleClustering"
    simple_clustering_ttl = "resource:SimpleClustering"
    simple_clustering_short_description = simple_clustering_ttl_description = """
            A Collection of clusters of resources where each cluster is obtained by the transitivity of links.
            In case these links are identity links, the clustered resources could be seen as CO-REFERENTS and
            the network formed from the CO-REFERENTS resources is an IDENTITY (LINK) NETWORK."""

    # ---------------------------------------------- #
    # EXACT SEARCH                                   #
    # ---------------------------------------------- #

    # METHOD 2: EXACT
    exact = F"{algorithm}Exact"
    exact_ttl = "resource:Exact"
    exact_range = "1"
    exact_description = """
        Aligns source and target’s IRIs whenever their respective user selected property values are identical."""
    exact_short_description = exact_description
    exact_see_also = [see_also.format("exact")]
    exact_see_also_ttl = [see_also_ttl.format("exact")]

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
    embedded_short_description = embedded_description
    embedded_see_also = [see_also.format("embedded")]
    embedded_see_also_ttl = [see_also_ttl.format("embedded")]

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
    jaro_short_description = """
        This  method is used to align source and target's IRIs whenever the similarity score of their respective user 
        selected property values are above a given threshold in the range ]0, 1]​.
        
        Jaro distance is a measure of similarity between two strings. The higher the Jaro distance for two strings is, 
        the more similar the strings are. The score is normalised such that 0 equates to no similarity and 1 is an exact 
        match.
        
        Given two strings S1 and S2, the method consists in finding common characters (xi = yj) xi of S1 and yj of S2 
        such that xi and yj are not more than d characters away from each other. The acceptable matching distance d is 
        half the longest input string.
    """
    jaro_see_also = [see_also.format("jaro"), "https://rosettacode.org/wiki/Jaro_distance"]
    jaro_see_also_ttl = [see_also_ttl.format("jaro"), "https://rosettacode.org/wiki/Jaro_distance"]

    # METHOD 5: JARO WINKLER
    jaro_winkler = F"{algorithm}Jaro_Winkler"
    jaro_winkler_ttl = "resource:Jaro_Winkler"
    jaro_winkler_description = """
        It aligns source and target's IRIs whenever the similarity score of their respective user 
        selected property values are above a given threshold in the range ]0, 1]​.
        
        The similarity score is computed as follows:
        
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
    jaro_winkler_short_description = """
        It aligns source and target's IRIs whenever the similarity score of their respective user selected property 
        values are above a given threshold in the range ]0, 1]​.
        
        Given two strings s1 and s2, the Winkler similarity score is computed such that the winkler equation boosts up 
        the Jaro algorithm’s result dj by increasing it whenever the compared strings share a prefix of a maximum of 
        four characters.
    """
    jaro_winkler_see_also = [see_also.format("jaro-winkler"),
                             "https://www.geeksforgeeks.org/jaro-and-jaro-winkler-similarity/"]
    jaro_winkler_see_also_ttl = [see_also_ttl.format("jaro-winkler"),
                             "https://www.geeksforgeeks.org/jaro-and-jaro-winkler-similarity/"]

    # METHOD 6: EDIT DISTANCE
    normalisedEditDistance = F"{algorithm}Normalised-Edit-Distance"
    normalisedEditDistance_ttl = "resource:Normalised-Edit-Distance"
    normalisedEditDistance_description = """
        This ​method is used to align ​​source a​nd ​​target’s IRIs whenever the similarity score of their respective 
        user selected property values are ​​above a given ​Levenshtein (edit) Distance threshold​. 
        Edit distance is a way of quantifying how ​dissimilar two strings (e.g., words) are to one another by counting 
        the minimum number of operations ​ε (​removal, insertion, or substitution of a character in the string)​ required 
        to transform one string into the other. For example, ​the ​Levenshtein distance between kitten and sitting is ​
        ε ​= 3 as it requires a two substitutions (s for k and i for e) and one insertion  of g at the end​. 
        The normalisation is obtained by dividing the computed distance by the length of the longest string and then 
        inverting the result such that 0 indicates no similarity 1 indicates exact similarity and any score in between
        indicates various degree of similarity. 
        For more information the reader is advised to read [https://en.wikipedia.org/wiki/Edit_distance].
        """
    normalisedEditDistance_short_description = normalisedEditDistance_description
    normalisedEditDistance_see_also = [see_also.format("levenshtein"),
                                       "https://en.wikipedia.org/wiki/Edit_distance"]
    normalisedEditDistance_see_also_ttl = [see_also_ttl.format("levenshtein"),
                                           "https://en.wikipedia.org/wiki/Edit_distance"]

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
        of g at the end​.
        For more information the reader is advised to read [https://en.wikipedia.org/wiki/Edit_distance].
        """
    editDistance_short_description = editDistance_description
    editDistance_see_also = [see_also.format("levenshtein"),
                                       "https://en.wikipedia.org/wiki/Edit_distance"]
    editDistance_see_also_ttl = [see_also_ttl.format("levenshtein"),
                             "https://en.wikipedia.org/wiki/Edit_distance"]

    # METHOD 8: TRIGRAM
    trigram = F"{algorithm}trigram"
    trigram_ttl = "resource:Trigram"
    trigram_description = """
        Trigrams are a special case of the n-gram, where n is 3. It is a contiguous sequence of three items from a 
        given sample. To be more concrete, In the case of string similarity, where an application of NAME is a sample 
        and a CHARACTER is an item, we obtain a sequence of 4 trigrams { mar art rth tha } from the sample “martha”. If 
        we consider a WORD as an item in the sample "the quick red fox jumps over the lazy brown dog", we then obtain a 
        sequence of 8 WORD-LEVEL TRIGRAMS { the quick red | quick red fox | red fox jumps | fox jumps over | jumps over 
        the | over the lazy | the lazy brown | lazy brown dog }. 

        N-grams can be used for approximate matching by comparing two trigram sequences using metrics such as 
        cosine distance, z-scores or g-test.

        see [https://en.wikipedia.org/wiki/Trigram], [https://en.wikipedia.org/wiki/N-gram] for more information. 
        """
    trigram_short_description = trigram_description
    trigram_see_also = [see_also.format("trigram"),
                             "https://en.wikipedia.org/wiki/Trigram", "https://en.wikipedia.org/wiki/N-gram"]
    trigram_see_also_ttl = [see_also_ttl.format("trigram"),
                        "https://en.wikipedia.org/wiki/Trigram", "https://en.wikipedia.org/wiki/N-gram"]

    # ---------------------------------------------- #
    # PHONETIC                                       #
    # ---------------------------------------------- #

    # METHOD 9: SOUNDEX
    soundexDistance = F"{algorithm}Soundex-Distance"
    soundexDistance_ttl = "resource:Soundex-Distance"
    soundexDistance_description = """
        "Soundex is a phonetic algorithm for indexing names by sound, as pronounced in English. The goal is for ho-
        mophones to be encoded to the same representation so that they can be matched despite minor differences in
        spelling. The algorithm mainly encodes consonants; a vowel will not be encoded unless it is the first let-
        ter” [https://en.wikipedia.org/wiki/Soundex]. 
        In the Lenticular Lens, Soundex is used as a normaliser in the sense that an edit distance is run over the 
        soundex code version of a name. For example, in the table below, the normalisation of both Louijs Roc-
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
    soundexDistance_short_description = """
        "Soundex is a phonetic algorithm for indexing names by sound, as pronounced in English. The goal is for homophones 
        to be encoded to the same representation so that they can be matched despite minor differences in spelling. The 
        algorithm mainly encodes consonants; a vowel will not be encoded unless it is the first letter.” 
        [https://en.wikipedia.org/wiki/Soundex]
        In the Lenticular Lens, Soundex is used in two other matching approaches:
            1. As a normaliser in the sense that a second scalar matching metric such as an edit distance, trigram... is 
            run over the soundex code version of a name. For example, the normalisation of both Louijs Rocourt and Lowis 
            Ricourt becomes L200 R263 leading to an edit distance of 0 and a relative strength of 1. 
            2. As a blocking strategy, in the sens that a second scalar matching metric is run the non encoded property 
            values only when those values share the same encoding. Here, computing the same names Louijs Rocourt and Lowis 
            Ricourt as they share the same encoding results in an edit distance of 3 and a relative matching strength of 
            0.79.
        For similarity score generated not in the interval ]0,1] a normalisation is applied such that it falls back in 
        the interval ]0,1] where 0 indicates no similarity, 1 indicates exact similarity and any score in between
        indicates various degree of similarity.
        """
    soundexDistance_see_also = [see_also.format("soundex"),
                                see_also.format("soundex-approximation"),
                                see_also.format("approx-over-same-soundex"),
                                "https://en.wikipedia.org/wiki/Soundex"]
    soundexDistance_see_also_ttl = [see_also_ttl.format("soundex"),
                                    see_also_ttl.format("soundex-approximation"),
                                    see_also_ttl.format("approx-over-same-soundex"),
                                    "https://en.wikipedia.org/wiki/Soundex"]

    normalisedSoundex = F"{algorithm}Normalised-Soundex"
    normalisedSoundex_ttl = "resource:Normalised-Soundex"
    normalisedSoundex_description = """
        "Soundex is a phonetic algorithm for indexing names by sound, as pronounced in English. The goal is for homophones 
        to be encoded to the same representation so that they can be matched despite minor differences in spelling. 
        The algorithm mainly encodes consonants; a vowel will not be encoded unless it is the first letter.” 
        [https://en.wikipedia.org/wiki/Soundex] 
        In the Lenticular Lens, Soundex is used as a normaliser in the sense that an approximation algorithm such as edit 
        distance, trigram... is run over the soundex code version of a name. For example, the encoding of both Louijs 
        Rocourt and Lowis Ricourt becomes L200 R263 leading to an edit distance of 0 and a relative strength of 1. 
        However, computing the same names using directly an edit distance results in an edit distance of 3 and a relative 
        matching strength of 0.79.

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
    normalisedSoundex_short_description = """
    "Soundex is a phonetic algorithm for indexing names by sound, as pronounced in English. The goal is for homophones 
        to be encoded to the same representation so that they can be matched despite minor differences in spelling. The 
        algorithm mainly encodes consonants; a vowel will not be encoded unless it is the first letter.” 
        [https://en.wikipedia.org/wiki/Soundex]
        In the Lenticular Lens, Soundex is used in two other matching approaches:
            1. As a normaliser in the sense that a second scalar matching metric such as an edit distance, trigram... is 
            run over the soundex code version of a name. For example, the normalisation of both Louijs Rocourt and Lowis 
            Ricourt becomes L200 R263 leading to an edit distance of 0 and a relative strength of 1. 
            2. As a blocking strategy, in the sens that a second scalar matching metric is run over the not encoded 
            property values of interest ONLY when those values share the same encoding. For example, computing the 
            similarity score for Louijs Rocourt and Lowis Ricourt (as they share the same encoding) using an edit 
            distance metric results in an edit distance of 3 and a relative matching strength of 0.79.
        For similarity score generated not in the interval ]0,1] a normalisation is applied such that it falls back in 
        the interval ]0,1] where 0 indicates no similarity, 1 indicates exact similarity and any score in between
        indicates various degree of similarity."""
    normalisedSoundex_see_also = [see_also.format("soundex"),
                                  see_also.format("soundex-approximation"),
                                  see_also.format("approx-over-same-soundex"),
                                  "https://en.wikipedia.org/wiki/Soundex"]
    normalisedSoundex_see_also_ttl = [see_also_ttl.format("soundex"),
                                      see_also_ttl.format("soundex-approximation"),
                                      see_also_ttl.format("approx-over-same-soundex"),
                                      "https://en.wikipedia.org/wiki/Soundex"]

    # METHOD 10: METAPHONE
    metaphone = F"{algorithm}Metaphone"
    metaphone_ttl = "resource:Metaphone"
    metaphone_short_description = metaphone_description = """
        Designed by Lawrence Philips in 1990, it is a phonetic algorithm for a more accurate encoding of words by sound 
        (as compared to SOUNDEX) as pronounced in English. In this algorithm as with SOUNDEX, similar-sounding words
        should share the same encoding key which is an approximate phonetic representation of the original word.
        For more accuracy, consider the use of DOUBLE METAPHONE as it is an improvement of the Original Metaphone. 
        In turn, for an even better improved accuracy consider the use of METAPHONE 3. 
        See [https://en.wikipedia.org/wiki/Metaphone] for mor information.
        
        In the Lenticular Lens, Metaphone is used in two other matching approaches:
            1. As a normaliser in the sense that a second scalar matching metric such as an edit distance, trigram... is 
            run over the soundex code version of a name. For example, the normalisation of both Louijs Rocourt and Lowis 
            Ricourt becomes L200 R263 leading to an edit distance of 0 and a relative strength of 1. 
            2. As a blocking strategy, in the sens that a second scalar matching metric is run the non encoded property 
            values only when those values share the same encoding. Here, computing the same names Louijs Rocourt and Lowis 
            Ricourt as they share the same encoding results in an edit distance of 3 and a relative matching strength of 
            0.79.
        For similarity score generated not in the interval ]0,1] a normalisation is applied such that it falls back in 
        the interval ]0,1] where 0 indicates no similarity, 1 indicates exact similarity and any score in between
        indicates various degree of similarity.
        """

    metaphone_see_also = [see_also.format("metaphone"), "https://en.wikipedia.org/wiki/Metaphone"]
    metaphone_see_also_ttl = [see_also_ttl.format("metaphone"), "https://en.wikipedia.org/wiki/Metaphone"]

    # METHOD 11: DOUBLE METAPHONE
    doubleMetaphone = F"{algorithm}DoubleMetaphone"
    doubleMetaphone_ttl = "resource:DoubleMetaphone"
    doubleMetaphone_short_description = doubleMetaphone_description = """
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
        
        In the Lenticular Lens, Metaphone is used in two other matching approaches:
            1. As a normaliser in the sense that a second scalar matching metric such as an edit distance, trigram... is 
            run over the soundex code version of a name. For example, the normalisation of both Louijs Rocourt and Lowis 
            Ricourt becomes L200 R263 leading to an edit distance of 0 and a relative strength of 1. 
            2. As a blocking strategy, in the sens that a second scalar matching metric is run the non encoded property 
            values only when those values share the same encoding. Here, computing the same names Louijs Rocourt and Lowis 
            Ricourt as they share the same encoding results in an edit distance of 3 and a relative matching strength of 
            0.79.
        For similarity score generated not in the interval ]0,1] a normalisation is applied such that it falls back in 
        the interval ]0,1] where 0 indicates no similarity, 1 indicates exact similarity and any score in between
        indicates various degree of similarity.
        """
    doubleMetaphone_see_also = [see_also.format("double-metaphone"), "https://en.wikipedia.org/wiki/Metaphone"]
    doubleMetaphone_see_also_ttl = [see_also_ttl.format("double-metaphone"), "https://en.wikipedia.org/wiki/Metaphone"]

    # METHOD 12: BLOOTHOOFT
    bloothooft = F"{algorithm}Bloothooft"
    bloothooft_ttl = "resource:Bloothooft"
    bloothooft_range = "]0, 1]"
    bloothooft_see_also = [see_also.format("bloothooft")]
    bloothooft_see_also_ttl = [see_also_ttl.format("bloothooft")]

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
    intermediate_short_description = """
        The method aligns the source and the target’s IRIs via an intermediate database by using properties that 
        potentially present different descriptions of the same entity, such as country name and country code. This 
        is possible by providing an intermediate dataset that binds the two alternative descriptions to the very 
        same identifier.
    """
    intermediate_see_also = [see_also.format("intermediate")]
    intermediate_see_also_ttl = [see_also_ttl.format("intermediate")]

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
    wordIntersection_short_description = """
    This approximation method is originally designed to find a subset of words within a larger text. However, it 
    could also be used for any pair of strings regardless of the strings sizes.
    """
    wordIntersection_see_also = [see_also.format("word-intersection")]
    wordIntersection_see_also_ttl = [see_also_ttl.format("word-intersection")]

    # METHOD 15: TeAM
    TeAM = F"{algorithm}TeAM"
    TeAM_ttl = "resource:TeAM"
    TeAM_short_description = TeAM_description = """
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
    TeAM_see_also = [see_also.format("team"), "https://team-algo.github.io/"]
    TeAM_see_also_ttl = [see_also_ttl.format("team"), "https://team-algo.github.io/"]

    # ---------------------------------------------- #
    # NUMERICAL                                      #
    # ---------------------------------------------- #

    # METHOD 16: NUMBERS
    numbers = F"{algorithm}Numbers"
    numbers_ttl = "resource:Numbers"
    numbers_short_description = numbers_description = """
        Numbers. The method is used to align the source and the target by approximating the match of the (number/
        date) values of the selected properties according to a delta. For example, if two entities have been ali-
        gned based on the similarity of their names but an extra check is to be investigated based on their res-
        pective year of birth, setting the delta to 1 will ensure that the two entities are born within the same 
        year, give or take a year.
        """
    numbers_see_also = [see_also.format("numbers")]
    numbers_see_also_ttl = [see_also_ttl.format("numbers")]

    # METHOD 17: TIME DELTA
    time_delta = F"{algorithm}Time-Delta"
    time_delta_ttl = "resource:Time-Delta"
    time_delta_short_description = time_delta_description = """
        Time Delta. This function allows for finding co-referent entities on the basis of a minimum time dif-
        ference between the times reported by the source and the target entities. For example, if the value zero is 
        assigned to the time difference parameter, then, for a matched to be found, the time of the target and the 
        one of the source are to be the exact same time. While accounting for margins of error, one may consider a 
        pair of entities to be co-referent if the referred date-times occur delta days, months or years apart among 
        other-things (similar name, place..).
        """
    time_delta_see_also = [see_also.format("time-delta")]
    time_delta_see_also_ttl = [see_also_ttl.format("time-delta")]

    # METHOD 18: TIME DELTA
    same_year_month = F"{algorithm}same_year_month"
    same_year_month_ttl = "resource:same_year_month"
    same_year_month_short_description = same_year_month_description = """
        This option is used to align source and target’s IRIs whenever an exact match of
        the year or year and month is observed between source and target's input dates. 
    """
    same_year_month_see_also = [see_also.format("same-year-month")]
    same_year_month_see_also_ttl = [see_also_ttl.format("same-year-month")]

    bloothooftReduction = """To come"""

    global algorithm_lbl
    algorithm_lbl = {

        'unknown': "Unknown",
        URIRef(unknown.lower()).n3(): "Unknown",
        unknown_ttl.lower(): "Unknown",

        URIRef(embedded.lower()).n3(): "Embedded",
        embedded_ttl.lower(): "Embedded",

        'same_year_month': "Same_Year_Month",

        "=": "Exact",
        "exact": "Exact",
        URIRef(exact.lower()).n3(): "Exact",
        exact_ttl.lower(): "Exact",

        'intermediate': "Intermediate",
        URIRef(intermediate.lower()).n3(): "Intermediate",
        intermediate_ttl.lower(): "Intermediate",

        'levenshtein': "Levenshtein",
        'levenshtein_distance': "Levenshtein",
        URIRef(editDistance.lower()).n3(): "Levenshtein",
        editDistance_ttl.lower(): "Levenshtein",

        'levenshtein_approx': "Levenshtein_Normalised",
        'levenshtein_normalised': "Levenshtein_Normalised",
        'levenshtein_normalized': "Levenshtein_Normalised",
        URIRef(normalisedEditDistance.lower()).n3(): "Levenshtein_Normalised",
        normalisedEditDistance_ttl.lower(): "Levenshtein_Normalised",

        'trigram': "Trigram",

        'jaro': "Jaro",
        'jaro_winkler': "Jaro_Winkler",

        'soundex': "Soundex",
        URIRef(soundexDistance.lower()).n3(): "Soundex",
        soundexDistance_ttl.lower(): "Soundex",

        'll_soundex': "Soundex_Normalised",
        URIRef(normalisedSoundex.lower()).n3(): "Soundex_Normalised",
        normalisedSoundex_ttl.lower(): "Soundex_Normalised",

        "metaphone": "Metaphone",
        URIRef(metaphone.lower()).n3(): "Metaphone",
        metaphone_ttl.lower(): "Metaphone",

        "dmetaphone": "DoubleMetaphone",
        "doublemetaphone": "DoubleMetaphone",
        URIRef(doubleMetaphone.lower()).n3(): "DoubleMetaphone",
        doubleMetaphone_ttl.lower(): "DoubleMetaphone",

        "word_intersection": "Word_Intersection",
        URIRef(wordIntersection.lower()).n3(): "Word_Intersection",
        wordIntersection_ttl.lower(): "Word_Intersection",

        'numbers': "Numbers",
        'numbers_delta': "Numbers",
        URIRef(numbers.lower()).n3(): "Numbers",
        numbers_ttl.lower(): "Numbers",

        URIRef(TeAM.lower()).n3(): "TeAM",
        TeAM_ttl.lower(): "TeAM",

        "time_delta": "Time_Delta",
        URIRef(time_delta.lower()).n3(): "Time_Delta",
        time_delta_ttl.lower(): "Time_Delta",

        "bloothooft": "Bloothooft",
        "bloothooft_reduct": "Bloothooft",
    }

    global algorithm_ttl
    algorithm_ttl = {

        'unknown': unknown_ttl,
        URIRef(unknown.lower()).n3(): unknown_ttl,
        unknown_ttl.lower(): unknown_ttl,

        URIRef(embedded.lower()).n3(): embedded_ttl,
        embedded_ttl.lower(): embedded_ttl,

        'same_year_month': same_year_month_ttl,

        "=": exact_ttl,
        "exact": exact_ttl,
        URIRef(exact.lower()).n3(): exact_ttl,
        exact_ttl.lower(): exact_ttl,

        'intermediate': intermediate_ttl,
        URIRef(intermediate.lower()).n3(): intermediate_ttl,
        intermediate_ttl.lower(): intermediate_ttl,

        'levenshtein': editDistance_ttl,
        'levenshtein_distance': editDistance_ttl,
        URIRef(editDistance.lower()).n3(): editDistance_ttl,
        editDistance_ttl.lower(): editDistance_ttl,

        'levenshtein_approx': normalisedEditDistance_ttl,
        "levenshtein_normalised": normalisedEditDistance_ttl,
        'levenshtein_normalized': normalisedEditDistance_ttl,
        URIRef(normalisedEditDistance.lower()).n3(): normalisedEditDistance_ttl,
        normalisedEditDistance_ttl.lower(): normalisedEditDistance_ttl,

        'trigram': trigram_ttl,

        'jaro': jaro_ttl,
        'jaro_winkler': jaro_winkler_ttl,

        'soundex': soundexDistance_ttl,
        URIRef(soundexDistance.lower()).n3(): soundexDistance_ttl,
        soundexDistance_ttl.lower(): soundexDistance_ttl,

        'll_soundex': normalisedSoundex_ttl,
        URIRef(normalisedSoundex.lower()).n3(): normalisedSoundex_ttl,
        normalisedSoundex_ttl.lower(): normalisedSoundex_ttl,


        "metaphone": metaphone_ttl,
        URIRef(metaphone.lower()).n3(): metaphone_ttl,
        metaphone_ttl.lower(): metaphone_ttl,

        "dmetaphone": doubleMetaphone_ttl,
        "doublemetaphone": doubleMetaphone_ttl,
        URIRef(doubleMetaphone.lower()).n3(): doubleMetaphone_ttl,
        doubleMetaphone_ttl.lower(): doubleMetaphone_ttl,

        "word_intersection": wordIntersection_ttl,
        URIRef(wordIntersection.lower()).n3(): wordIntersection_ttl,
        wordIntersection_ttl.lower(): wordIntersection_ttl,

        'numbers_delta': numbers_ttl,
        URIRef(numbers.lower()).n3(): numbers_ttl,
        numbers_ttl.lower(): numbers_ttl,

        URIRef(TeAM.lower()).n3(): TeAM_ttl,
        TeAM_ttl.lower(): TeAM_ttl,

        "time_delta": time_delta_ttl,
        URIRef(time_delta.lower()).n3(): time_delta_ttl,
        time_delta_ttl.lower(): time_delta_ttl,

        "bloothooft": bloothooft_ttl,
        "bloothooft_reduct": bloothooft_ttl,
    }

    global scale
    scale = {

        'unknown': "undefined",

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
        'levenshtein_normalised': interval,
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
        "doublemetaphone": natural,
        doubleMetaphone.lower(): natural,
        doubleMetaphone_ttl.lower(): natural,
        URIRef(doubleMetaphone.lower()).n3(): natural,

        "trigram": interval,
        trigram.lower(): interval,
        trigram_ttl.lower(): interval,
        URIRef(trigram.lower()).n3(): interval,

        "word_intersection":  interval,
        'wordIntersection': interval,
        wordIntersection.lower():  interval,
        wordIntersection_ttl.lower(): interval,
        URIRef(wordIntersection.lower()).n3(): interval,

        time_delta.lower(): natural,
        'time_delta': natural,
        time_delta_ttl.lower(): natural,
        URIRef(time_delta.lower()).n3(): natural,

        'numbers': natural,
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

        'unknown': Literal(unknown_description, lang="en").n3(),

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

        'levenshtein': Literal(normalisedEditDistance_description, lang="en").n3(),
        'levenshtein_distance': Literal(normalisedEditDistance_description, lang="en").n3(),
        'levenshtein_normalized': Literal(normalisedEditDistance_description, lang="en").n3(),
        'levenshtein_normalised': Literal(normalisedEditDistance_description, lang="en").n3(),
        URIRef(editDistance.lower()).n3(): Literal(normalisedEditDistance_description, lang="en").n3(),
        editDistance_ttl.lower(): Literal(normalisedEditDistance_description, lang="en").n3(),

        'trigram': Literal(trigram_description, lang="en").n3(),
        'jaro': Literal(jaro_description, lang="en").n3(),
        'jaro_winkler': Literal(jaro_winkler_description, lang="en").n3(),

        'levenshtein_approx': Literal(normalisedEditDistance_description, lang="en").n3(),
        URIRef(normalisedEditDistance.lower()).n3(): Literal(normalisedEditDistance_description, lang="en").n3(),
        normalisedEditDistance_ttl.lower(): Literal(normalisedEditDistance_description, lang="en").n3(),

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
        "doublemetaphone": Literal(doubleMetaphone_description, lang="en").n3(),
        URIRef(doubleMetaphone.lower()).n3(): Literal(doubleMetaphone_description, lang="en").n3(),
        doubleMetaphone_ttl.lower(): Literal(doubleMetaphone_description, lang="en").n3(),

        "word_intersection": Literal(wordIntersection_description, lang="en").n3(),
        URIRef(wordIntersection.lower()).n3(): Literal(wordIntersection_description, lang="en").n3(),
        wordIntersection_ttl.lower(): Literal(wordIntersection_description, lang="en").n3(),

        'numbers': Literal(numbers_description, lang="en").n3(),
        'numbers_delta': Literal(numbers_description, lang="en").n3(),
        URIRef(numbers.lower()).n3(): Literal(numbers_description, lang="en").n3(),
        numbers_ttl.lower(): Literal(numbers_description, lang="en").n3(),

        URIRef(TeAM.lower()).n3(): Literal(TeAM_description, lang="en").n3(),
        TeAM_ttl.lower(): Literal(TeAM_description, lang="en").n3(),

        "time_delta": Literal(time_delta_description, lang="en").n3(),
        URIRef(time_delta.lower()).n3(): Literal(time_delta_description, lang="en").n3(),
        time_delta_ttl.lower(): Literal(time_delta_description, lang="en").n3(),

        "bloothooft": Literal(bloothooftReduction, lang="en").n3(),
        "bloothooft_reduct": Literal(bloothooftReduction, lang="en").n3(),
    }

    global short_descriptions
    short_descriptions = {

        'unknown': Literal(unknown_short_description, lang="en").n3(),
        URIRef(unknown.lower()).n3(): Literal(unknown_short_description, lang="en").n3(),
        unknown_ttl.lower(): Literal(unknown_short_description, lang="en").n3(),

        'same_year_month': Literal(exact_short_description, lang="en").n3(),

        "=": Literal(exact_short_description, lang="en").n3(),
        "exact": Literal(exact_short_description, lang="en").n3(),
        URIRef(exact.lower()).n3(): Literal(exact_short_description, lang="en").n3(),
        exact_ttl.lower(): Literal(exact_short_description, lang="en").n3(),

        URIRef(embedded.lower()).n3(): Literal(embedded_short_description, lang="en").n3(),
        embedded_ttl.lower(): Literal(embedded_short_description, lang="en").n3(),

        'intermediate': Literal(intermediate_short_description, lang="en").n3(),
        URIRef(intermediate.lower()).n3(): Literal(intermediate_short_description, lang="en").n3(),
        intermediate_ttl.lower(): Literal(intermediate_short_description, lang="en").n3(),

        'levenshtein': Literal(normalisedEditDistance_short_description, lang="en").n3(),
        'levenshtein_distance': Literal(normalisedEditDistance_short_description, lang="en").n3(),
        'levenshtein_normalized': Literal(normalisedEditDistance_short_description, lang="en").n3(),
        'levenshtein_normalised': Literal(normalisedEditDistance_short_description, lang="en").n3(),
        URIRef(editDistance.lower()).n3(): Literal(normalisedEditDistance_short_description, lang="en").n3(),
        editDistance_ttl.lower(): Literal(normalisedEditDistance_short_description, lang="en").n3(),

        'trigram': Literal(trigram_short_description, lang="en").n3(),
        'jaro': Literal(jaro_short_description, lang="en").n3(),
        'jaro_winkler': Literal(jaro_winkler_short_description, lang="en").n3(),

        'levenshtein_approx': Literal(normalisedEditDistance_short_description, lang="en").n3(),
        URIRef(normalisedEditDistance.lower()).n3(): Literal(normalisedEditDistance_short_description, lang="en").n3(),
        normalisedEditDistance_ttl.lower(): Literal(normalisedEditDistance_short_description, lang="en").n3(),

        URIRef(soundexDistance.lower()).n3(): Literal(normalisedSoundex_short_description, lang="en").n3(),
        soundexDistance_ttl.lower(): Literal(normalisedSoundex_short_description, lang="en").n3(),

        'soundex': Literal(normalisedSoundex_short_description, lang="en").n3(),
        'll_soundex': Literal(normalisedSoundex_short_description, lang="en").n3(),
        URIRef(normalisedSoundex.lower()).n3(): Literal(normalisedSoundex_short_description, lang="en").n3(),
        normalisedSoundex_ttl.lower(): Literal(normalisedSoundex_short_description, lang="en").n3(),

        "metaphone": Literal(metaphone_short_description, lang="en").n3(),
        URIRef(metaphone.lower()).n3(): Literal(metaphone_short_description, lang="en").n3(),
        metaphone_ttl.lower(): Literal(metaphone_short_description, lang="en").n3(),

        "dmetaphone": Literal(doubleMetaphone_short_description, lang="en").n3(),
        "doublemetaphone": Literal(doubleMetaphone_short_description, lang="en").n3(),
        URIRef(doubleMetaphone.lower()).n3(): Literal(doubleMetaphone_short_description, lang="en").n3(),
        doubleMetaphone_ttl.lower(): Literal(doubleMetaphone_short_description, lang="en").n3(),

        "word_intersection": Literal(wordIntersection_short_description, lang="en").n3(),
        URIRef(wordIntersection.lower()).n3(): Literal(wordIntersection_short_description, lang="en").n3(),
        wordIntersection_ttl.lower(): Literal(wordIntersection_short_description, lang="en").n3(),

        'numbers': Literal(numbers_short_description, lang="en").n3(),
        'numbers_delta': Literal(numbers_short_description, lang="en").n3(),
        URIRef(numbers.lower()).n3(): Literal(numbers_short_description, lang="en").n3(),
        numbers_ttl.lower(): Literal(numbers_short_description, lang="en").n3(),

        URIRef(TeAM.lower()).n3(): Literal(TeAM_short_description, lang="en").n3(),
        TeAM_ttl.lower(): Literal(TeAM_short_description, lang="en").n3(),

        "time_delta": Literal(time_delta_short_description, lang="en").n3(),
        URIRef(time_delta.lower()).n3(): Literal(time_delta_short_description, lang="en").n3(),
        time_delta_ttl.lower(): Literal(time_delta_short_description, lang="en").n3(),

        "bloothooft": Literal(bloothooftReduction, lang="en").n3(),
        "bloothooft_reduct": Literal(bloothooftReduction, lang="en").n3(),
    }

    global also
    also = {

        'unknown': unknown_see_also,

        'same_year_month': same_year_month_see_also,

        "=": exact_see_also,
        "exact": exact_see_also,
        URIRef(exact.lower()).n3(): exact_see_also,
        exact_ttl.lower(): exact_see_also,

        URIRef(unknown.lower()).n3(): Literal(unknown_description, lang="en").n3(),
        unknown_ttl.lower(): Literal(unknown_description, lang="en").n3(),

        URIRef(embedded.lower()).n3(): embedded_see_also,
        embedded_ttl.lower(): embedded_see_also,

        'intermediate':  intermediate_see_also,
        URIRef(intermediate.lower()).n3(): intermediate_see_also,
        intermediate_ttl.lower(): intermediate_see_also,

        'levenshtein': editDistance_see_also,
        'levenshtein_distance': editDistance_see_also,
        'levenshtein_normalized': normalisedEditDistance_see_also,
        'levenshtein_normalised': normalisedEditDistance_see_also,
        URIRef(editDistance.lower()).n3(): editDistance_see_also,
        editDistance_ttl.lower(): editDistance_see_also,

        'trigram': trigram_see_also,
        'jaro': jaro_see_also,
        'jaro_winkler': jaro_winkler_see_also,

        'levenshtein_approx': normalisedEditDistance_see_also,
        URIRef(normalisedEditDistance.lower()).n3(): normalisedEditDistance_see_also,
        normalisedEditDistance_ttl.lower(): normalisedEditDistance_see_also,

        URIRef(soundexDistance.lower()).n3(): normalisedSoundex_see_also,
        soundexDistance_ttl.lower(): normalisedSoundex_see_also,

        'soundex': normalisedSoundex_see_also,
        'll_soundex': normalisedSoundex_see_also,
        URIRef(normalisedSoundex.lower()).n3(): normalisedSoundex_see_also,
        normalisedSoundex_ttl.lower(): normalisedSoundex_see_also,

        "metaphone": metaphone_see_also,
        URIRef(metaphone.lower()).n3(): metaphone_see_also,
        metaphone_ttl.lower(): metaphone_see_also,

        "dmetaphone": doubleMetaphone_see_also,
        "doublemetaphone": doubleMetaphone_see_also,
        URIRef(doubleMetaphone.lower()).n3(): doubleMetaphone_see_also,
        doubleMetaphone_ttl.lower(): doubleMetaphone_see_also,

        "word_intersection": wordIntersection_see_also,
        URIRef(wordIntersection.lower()).n3(): wordIntersection_see_also,
        wordIntersection_ttl.lower(): wordIntersection_see_also,

        'numbers': numbers_see_also,
        'numbers_delta': numbers_see_also,
        URIRef(numbers.lower()).n3(): numbers_see_also,
        numbers_ttl.lower(): numbers_see_also,

        URIRef(TeAM.lower()).n3(): TeAM_see_also,
        TeAM_ttl.lower(): TeAM_see_also,

        "time_delta": time_delta_see_also,
        URIRef(time_delta.lower()).n3(): time_delta_see_also,
        time_delta_ttl.lower(): time_delta_see_also,

        "bloothooft": bloothooft_see_also,
        "bloothooft_reduct": bloothooft_see_also,
        "bloothooft_reduction": bloothooft_see_also,
    }

    global also_ttl
    also_ttl = {

        'unknown': unknown_see_also_ttl,

        'same_year_month': same_year_month_see_also_ttl,

        "=": exact_see_also_ttl,
        "exact": exact_see_also_ttl,
        URIRef(exact.lower()).n3(): exact_see_also_ttl,
        exact_ttl.lower(): exact_see_also_ttl,

        URIRef(unknown.lower()).n3(): Literal(unknown_description, lang="en").n3(),
        unknown_ttl.lower(): Literal(unknown_description, lang="en").n3(),

        URIRef(embedded.lower()).n3(): embedded_see_also_ttl,
        embedded_ttl.lower(): embedded_see_also_ttl,

        'intermediate': intermediate_see_also_ttl,
        URIRef(intermediate.lower()).n3(): intermediate_see_also_ttl,
        intermediate_ttl.lower(): intermediate_see_also_ttl,

        'levenshtein': editDistance_see_also_ttl,
        'levenshtein_distance': editDistance_see_also_ttl,
        'levenshtein_normalized': normalisedEditDistance_see_also_ttl,
        'Levenshtein_Normalized': normalisedEditDistance_see_also_ttl,
        URIRef(editDistance.lower()).n3(): editDistance_see_also_ttl,
        editDistance_ttl.lower(): editDistance_see_also_ttl,

        'trigram': trigram_see_also_ttl,
        'jaro': jaro_see_also_ttl,
        'jaro_winkler': jaro_winkler_see_also_ttl,

        'levenshtein_approx': normalisedEditDistance_see_also_ttl,
        URIRef(normalisedEditDistance.lower()).n3(): normalisedEditDistance_see_also_ttl,
        normalisedEditDistance_ttl.lower(): normalisedEditDistance_see_also_ttl,

        URIRef(soundexDistance.lower()).n3(): normalisedSoundex_see_also_ttl,
        soundexDistance_ttl.lower(): normalisedSoundex_see_also_ttl,

        'soundex': normalisedSoundex_see_also_ttl,
        'll_soundex': normalisedSoundex_see_also_ttl,
        URIRef(normalisedSoundex.lower()).n3(): normalisedSoundex_see_also_ttl,
        normalisedSoundex_ttl.lower(): normalisedSoundex_see_also_ttl,

        "metaphone": metaphone_see_also_ttl,
        URIRef(metaphone.lower()).n3(): metaphone_see_also_ttl,
        metaphone_ttl.lower(): metaphone_see_also_ttl,

        "dmetaphone": doubleMetaphone_see_also_ttl,
        "doublemetaphone": doubleMetaphone_see_also_ttl,
        URIRef(doubleMetaphone.lower()).n3(): doubleMetaphone_see_also_ttl,
        doubleMetaphone_ttl.lower(): doubleMetaphone_see_also_ttl,

        "word_intersection": wordIntersection_see_also_ttl,
        URIRef(wordIntersection.lower()).n3(): wordIntersection_see_also_ttl,
        wordIntersection_ttl.lower(): wordIntersection_see_also_ttl,

        'numbers': numbers_see_also_ttl,
        'numbers_delta': numbers_see_also_ttl,
        URIRef(numbers.lower()).n3(): numbers_see_also_ttl,
        numbers_ttl.lower(): numbers_see_also_ttl,

        URIRef(TeAM.lower()).n3(): TeAM_see_also_ttl,
        TeAM_ttl.lower(): TeAM_see_also_ttl,

        "time_delta": time_delta_see_also_ttl,
        URIRef(time_delta.lower()).n3(): time_delta_see_also_ttl,
        time_delta_ttl.lower(): time_delta_see_also_ttl,

        "bloothooft": bloothooft_see_also_ttl,
        "bloothooft_reduct": bloothooft_see_also_ttl,
        "bloothooft_reduction": bloothooft_see_also_ttl,
    }

    @staticmethod
    def algorithm_name(key):
        return algorithm_lbl.get(key.lower(), algorithm_lbl['unknown'])

    @staticmethod
    def algorithm_rsc(key):
        return algorithm_ttl.get(key.lower(), algorithm_ttl['unknown'])

    @staticmethod
    def illustration(key):
        global descriptions
        return descriptions[key.lower()]

    @staticmethod
    def short_illustration(key):
        global short_descriptions
        return short_descriptions[key.lower()]

    @staticmethod
    def seeAlso(key):
        return also[key.lower()]

    @staticmethod
    def seeAlso_ttl(key):
        return also_ttl[key.lower()]

    @staticmethod
    def range(key):
        global scale
        return scale[key.lower()]
