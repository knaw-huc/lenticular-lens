import time
from datetime import timedelta
from unidecode import unidecode


# VOWELS TO REMOVE
vowels = ('a', 'e', 'i', 'o', 'u', 'y', 'h', 'w')

# CONSONANTS TO ENCODE
consonants = {'b': 1, 'f': 1, 'p': 1, 'v': 1,
    'c': 2, 'g': 2, 'j': 2, 'k': 2, 'q': 2, 's': 2, 'x': 2, 'z': 2,
    'd': 3, 't': 3, 'l': 4, 'm': 5, 'n': 5, 'r': 6}

def soundex(object, size=3):

    """
    :param object: A STRING OR A LIST OF STRINGS
    :param size: THE SIZE OF THE CODEX EXLUDING THE FIRST CHARACTER
    :return: RETURNS A STRING IF GHE INPUT IS STRING AND RETURNS A LIST IF THE INPUT IS A LIST
    """

    def helper(object, size):

        # start = time.time()
        # APPENDER FOR ASSURING THE RETURN OF A CODEX OF THE REQUIRED SIZE
        appender = [0*x for x in range(size)]

        # CLEANING UP THE STRING BY REMOVING ACCENTED AND NON ALPHABETIC CHARACTERS
        cleaned = [char for char in unidecode(object.lower()) if char.isalpha()]

        # >>> 1.0 SAVE THE FIRST LETTER
        first_letter = cleaned[0].upper()

        # IF AFTER CLEANING THE INPUT IS OF ONE LETTER, RETURN TEXT +"000"
        if len(cleaned) == 1:
            return F"{first_letter}{''.join(str(char) for char in appender[:])}"

        # >>> 1.1 REMOVE ALL OCCURRENCES OF ('a', 'e', 'i', 'o', 'u', 'y', 'h', 'w')
        vowel_free = [char for char in cleaned[1:] if char not in vowels]

        # IF AFTER REMOVING VOWELS THE INPUT IS OF ONE LETTER, RETURN TEXT +"000"
        if len(vowel_free) == 0:
            return F"{first_letter}{''.join(str(char) for char in appender[:])}"

        # >>> 2. REPLACE ALL CONSONANTS WITH DIGITS
        print(consonants)
        print(vowel_free)
        code = [consonants[char] for char in vowel_free]

        # >>> 3. REPLACE ALL ADJACENT SAME DIGITS WITH ONE DIGIT
        previous = ""
        adjacent_free = []
        for i in range(len(code)):
            if code[i] != previous:
                adjacent_free.append(code[i])
            previous = code[i]

        # >>> 5. APPEND N ZEROS IF THE RESULT CONTAINS LESS THAT THE DESIRED CODE SIZE.
        # REMOVE ALL EXCEPT THE FIRST AND N SIZE DIGIT AFTER IT
        adjacent_free += appender

        # >>> 4. IF THE SAVED LETTER'S DIGIT IS THE SAME AS THE
        # RESULTING FIRST DIGIT, REMOVE THE DIGIT (KEEP THE LETTER)
        final_code = F"{first_letter.upper()}{''.join(str(char) for char in adjacent_free[1:size])}" \
            if first_letter in consonants and consonants[first_letter] == adjacent_free[0] \
            else F"{first_letter.upper()}{''.join(str(char) for char in adjacent_free[:size])}"


        # if __name__ == "__main__":
        #     display = F"{object:.<30} {final_code}"
        #     print("{:^100}".format(display))
        # print(timedelta(microseconds=time.time() - start))

        return final_code

    # PROCESS THE INPUT AS A STRING
    if isinstance(object, str):
        return helper(object, size)

    # PROCESS THE INPUT AS A LIST
    elif isinstance(object, list):
        result = []
        for text in object:
            try:
                result.append(soundex(text, size))
            except:
                result.append("None")
        return result

    else:
        print(F"\n\tTHIS TYPE {type(object)} IS NOT SUPPORTED.")
        return None


def soundex_2(query: str):
    """
    https://en.wikipedia.org/wiki/Soundex
    :param query:
    :return:
    """
    # start = time.time()
    # Step 0: Clean up the query string
    query = query.lower()
    letters = [char for char in query if char.isalpha()]
    # print(letters)

    # Step 1: Save the first letter. Remove all occurrences of a, e, i, o, u, y, h, w.

    # If query contains only 1 letter, return query+"000" (Refer step 5)
    if len(query) == 1:
        return query + "000"

    to_remove = ('a', 'e', 'i', 'o', 'u', 'y', 'h', 'w')

    first_letter = letters[0]
    letters = letters[1:]
    letters = [char for char in letters if char not in to_remove]
    # print(letters)

    if len(letters) == 0:
        return first_letter + "000"

    # Step 2: Replace all consonants (include the first letter) with digits according to rules

    to_replace = {('b', 'f', 'p', 'v'): 1, ('c', 'g', 'j', 'k', 'q', 's', 'x', 'z'): 2,
                  ('d', 't'): 3, ('l',): 4, ('m', 'n'): 5, ('r',): 6}

    first_letter = [value if first_letter else first_letter for group, value in to_replace.items()
                    if first_letter in group]
    letters = [value if char else char
               for char in letters
               for group, value in to_replace.items()
               if char in group]
    # print(letters)

    # Step 3: Replace all adjacent same digits with one digit.
    letters = [char for ind, char in enumerate(letters)
               if (ind == len(letters) - 1 or (ind+1 < len(letters) and char != letters[ind+1]))]

    # Step 4: If the saved letter’s digit is the same the resulting first digit, remove the digit (keep the letter)
    if first_letter == letters[0]:
        letters[0] = query[0]
    else:
        letters.insert(0, query[0])

    # Step 5: Append 3 zeros if result contains less than 3 digits.
    # Remove all except first letter and 3 digits after it.

    first_letter = letters[0]
    letters = letters[1:]

    letters = [char for char in letters if isinstance(char, int)][0:3]

    while len(letters) < 3:
        letters.append(0)

    letters.insert(0, first_letter)

    string = "".join([str(l) for l in letters])
    # print(timedelta(seconds=time.time() - start))
    return string


if __name__ == "__main__":

    SIZE_1, SIZE_2 = 3, 5

    test = ["A.", "al", "ali", "albert", "alberto", "albertine", "Robert", "Rupert", "Rubin", "Ashcraft", "Ashcroft",
            "Tymczak", "Pfister", "honeyman", "Wux", "bomapen", "VEROUSKA", " Cäsar   ", "Cesar",
            "Übel", "Männer", "Müller", "miller", "Frédéric", "Frederic", "Ahmed", "Hamed", "Moskowitz", "Moskovitz",
            "Levine", "Lewne"]

    # print("\n{:.^100}\n{:.^100}\n".format(f" TESTING SOUNDEX ALGORITHM WITH CODE LENGTH {SIZE_1} ", ""))
    result_1 = soundex(test, SIZE_1)

    # print("\n{:.^100}\n{:.^100}\n".format(f" TESTING SOUNDEX ALGORITHM WITH CODE LENGTH {SIZE_2} ", ""))
    result_2 = soundex(test, SIZE_2)

    print("\n{:.^100}\n{:.^100}\n".format(f" TESTING SOUNDEX ALGORITHM WITH CODE LENGTH {SIZE_1} and {SIZE_2} ", ""))
    print("{:^100}".format("{:<35}".format("---------------------------------")))
    print("{:^100}".format("{:<15}{:^10}{:^10}".format("INPUT", F"SIZE {SIZE_1}", F"SIZE {SIZE_2}")))
    print("{:^100}".format("{:<35}".format("---------------------------------")))
    for a, b, c in zip(test, result_1, result_2):
        print("{:^100}".format(F"{a.upper():<15}{b:^10}{c:^10}"))
    print("{:^100}".format("{:<35}".format("---------------------------------")))






# ITERATION = 1000000
# INPUT = "FRÉDÉRIC ARMANDEZ ROBERTO ZAMBORLINI"
#
# start = time.time()
# for i in range(ITERATION):
#     (soundex_2(INPUT))
# print(F"SOUNDEX 2 COMPUTES {ITERATION} ITERATIONS OF {INPUT} IN {timedelta(seconds=time.time() - start)}")
#
# start = time.time()
# for j in range(ITERATION):
#     (soundex(INPUT))
# print(F"SOUNDEX 1 COMPUTES {ITERATION} ITERATIONS OF {INPUT} IN {timedelta(seconds=time.time() - start)}")
#
#
# start = time.time()
# for k in range(ITERATION):
#     (soundex(INPUT))
# print(F"SOUNDEX 1 COMPUTES {ITERATION} ITERATIONS OF {INPUT} IN {timedelta(seconds=time.time() - start)}")
#
# start = time.time()
# for m in range(ITERATION):
#     (soundex_2(INPUT))
# print(F"SOUNDEX 2 COMPUTES {ITERATION} ITERATIONS OF {INPUT} IN {timedelta(seconds=time.time() - start)}")