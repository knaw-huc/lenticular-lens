from unidecode import unidecode


def soundex(input, size):
    result = []
    for word in input.split(' '):
        try:
            result.append(soundex_word(word, size))
        except:
            pass

    return '_'.join(result) if len(result) > 0 else None


def soundex_word(word, size):
    vowels = ('a', 'e', 'i', 'o', 'u', 'y', 'h', 'w')

    # CONSONANTS TO ENCODE
    consonants = {'b': 1, 'f': 1, 'p': 1, 'v': 1,
                  'c': 2, 'g': 2, 'j': 2, 'k': 2, 'q': 2, 's': 2, 'x': 2, 'z': 2,
                  'd': 3, 't': 3, 'l': 4, 'm': 5, 'n': 5, 'r': 6}

    # APPENDER FOR ASSURING THE RETURN OF A CODEX OF THE REQUIRED SIZE
    appender = [0 * x for x in range(size)]

    # CLEANING UP THE STRING BY REMOVING ACCENTED AND NON ALPHABETIC CHARACTERS
    cleaned = [char for char in unidecode(word.lower()) if char.isalpha()]

    # >>> 1.0 SAVE THE FIRST LETTER
    first_letter = cleaned[0].upper()

    # IF AFTER CLEANING THE INPUT IS OF ONE LETTER, RETURN TEXT +"000"
    if len(cleaned) == 1:
        return first_letter + ''.join(str(char) for char in appender[:])

    # >>> 1.1 REMOVE ALL OCCURRENCES OF ('a', 'e', 'i', 'o', 'u', 'y', 'h', 'w')
    vowel_free = [char for char in cleaned[1:] if char not in vowels]

    # IF AFTER REMOVING VOWELS THE INPUT IS OF ONE LETTER, RETURN TEXT +"000"
    if len(vowel_free) == 0:
        return first_letter + ''.join(str(char) for char in appender[:])

    # >>> 2. REPLACE ALL CONSONANTS WITH DIGITS
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
    if first_letter in consonants and consonants[first_letter] == adjacent_free[0]:
        return first_letter.upper() + ''.join(str(char) for char in adjacent_free[1:size])

    return first_letter.upper() + ''.join(str(char) for char in adjacent_free[:size])
