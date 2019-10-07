CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS plpython3u;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS reconciliation_jobs (
  job_id text primary key,
  job_title text not null,
  job_description text not null,
  resources_form_data json,
  mappings_form_data json,
  resources json,
  mappings json,
  created_at timestamp default now() not null,
  updated_at timestamp default now() not null,
  UNIQUE (job_title, job_description)
);

CREATE TABLE IF NOT EXISTS timbuctoo_tables (
  table_name text primary key,
  dataset_id text not null,
  collection_id text not null,
  title text not null,
  description text,
  columns json not null,
  create_time timestamp not null,
  update_start_time timestamp,
  next_page text,
  rows_count int default 0 not null,
  last_push_time timestamp,
  update_finish_time timestamp,
  UNIQUE (dataset_id, collection_id)
);

CREATE TABLE IF NOT EXISTS alignments (
  job_id text not null,
  alignment int not null,
  status text not null,
  failed_message text,
  kill boolean not null,
  requested_at timestamp,
  processing_at timestamp,
  finished_at timestamp,
  links_count bigint,
  sources_count bigint,
  targets_count bigint,
  PRIMARY KEY (job_id, alignment)
);

CREATE TABLE IF NOT EXISTS clusterings (
  job_id text not null,
  alignment int not null,
  clustering_type text not null,
  association_file text null,
  status text not null,
  requested_at timestamp,
  processing_at timestamp,
  finished_at timestamp,
  clusters_count bigint,
  extended_count int,
  cycles_count int,
  PRIMARY KEY (job_id, alignment)
);

CREATE OR REPLACE FUNCTION public.ecartico_full_name(text) RETURNS text IMMUTABLE AS $$
  DECLARE
    first_name text;
    infix text;
    family_name text;
  BEGIN
    first_name = coalesce(trim(substring($1 from ', ([^[]*)')), '');
    infix = coalesce(trim(substring($1 from '\[(.*)\]')), '');
    family_name = coalesce(trim(substring($1 from '^[^,]*')), '');

    RETURN first_name || ' ' || CASE WHEN infix != '' THEN infix || ' ' ELSE '' END || family_name;
  END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.jsonb_to_array(jsonb) RETURNS text[] IMMUTABLE AS $$
  BEGIN
    RETURN ARRAY(SELECT jsonb_array_elements_text($1));
  END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.ecartico_full_name_list(jsonb) RETURNS jsonb IMMUTABLE AS $$
  DECLARE
    ecartico_full_name_list text[];
    full_name text;
BEGIN
  FOREACH full_name IN ARRAY jsonb_to_array($1)
  LOOP
    ecartico_full_name_list = ecartico_full_name_list || (ecartico_full_name(full_name));
  end loop;
  RETURN to_jsonb(ecartico_full_name_list);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.to_date_immutable(text) RETURNS date IMMUTABLE AS $$
  BEGIN
    RETURN to_date($1, 'YYYY-MM-DD');
  EXCEPTION
    WHEN SQLSTATE '22008' THEN
      RETURN NULL;
    WHEN SQLSTATE '22007' THEN
      RETURN NULL;
  END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.get_year(text) RETURNS int IMMUTABLE AS $$
  DECLARE
    year text;
  BEGIN
    year = substr($1, 0, 5);
    IF year~E'^\\d+$' THEN
      RETURN year::int;
    ELSE
      RETURN NULL;
    END IF;
  END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.get_month(text) RETURNS int IMMUTABLE AS $$
  DECLARE
    month text;
  BEGIN
    month = substr($1, 6, 2);
    IF month~E'^\\d+$' THEN
      RETURN month::int;
    ELSE
      RETURN NULL;
    END IF;
  END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.get_year_month(text) RETURNS text IMMUTABLE AS $$
  DECLARE
    month int;
    year int;
  BEGIN
    month = get_month($1);
    year = get_year($1);

    IF month IS NULL OR year IS NULL THEN
        RETURN NULL;
    ELSE
        RETURN year::text || '-' || month::text;
    END IF;
  END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.ll_soundex(input text) RETURNS text IMMUTABLE AS $$
    if input is None:
        return None

    from unidecode import unidecode
    vowels = ('a', 'e', 'i', 'o', 'u', 'y', 'h', 'w')

    # CONSONANTS TO ENCODE
    consonants = {'b': 1, 'f': 1, 'p': 1, 'v': 1,
        'c': 2, 'g': 2, 'j': 2, 'k': 2, 'q': 2, 's': 2, 'x': 2, 'z': 2,
        'd': 3, 't': 3, 'l': 4, 'm': 5, 'n': 5, 'r': 6}

    size = 3

    name_object = input.split(' ')

    def helper(name_object, size):
        # start = time.time()
        # APPENDER FOR ASSURING THE RETURN OF A CODEX OF THE REQUIRED SIZE
        appender = [0 * x for x in range(size)]

        # CLEANING UP THE STRING BY REMOVING ACCENTED AND NON ALPHABETIC CHARACTERS
        cleaned = [char for char in unidecode(name_object.lower()) if char.isalpha()]

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
        # print(consonants)
        # print(vowel_free)
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
        final_code = first_letter.upper() + ''.join(str(char) for char in adjacent_free[1:size])\
        if first_letter in consonants and consonants[first_letter] == adjacent_free[0]\
        else first_letter.upper() + ''.join(str(char) for char in adjacent_free[:size])


        # if __name__ == "__main__":
        #     display = F"{name_object:.<30} {final_code}"
        #     print("{:^100}".format(display))
        # print(timedelta(microseconds=time.time() - start))

        return final_code

        # PROCESS THE INPUT AS A STRING


    if isinstance(name_object, str):
        return helper(name_object, size)

        # PROCESS THE INPUT AS A LIST
    elif isinstance(name_object, list):
        result = []
        for text in name_object:
            try:
                result.append(helper(text, size))
            except:
                result.append("None")
        return '_'.join(result)

    else:
        print("\n\tTHIS TYPE" + type(name_object) + " IS NOT SUPPORTED.")
        return None
$$ LANGUAGE plpython3u;

CREATE FUNCTION bloothooft_bootstrap()
  RETURNS text
AS $$
def bloothooft(input, type):
  import re

  result = input
  result = result.upper()
  result = re.sub(r"[Ééèëê]", 'E', result, flags=re.I)
  result = re.sub(r"[áàâäª]", 'A', result, flags=re.I)
  result = re.sub(r"[ÄäÆæ]", 'æ', result, flags=re.I)
  result = re.sub(r"[Üúùü]", 'U', result, flags=re.I)
  result = re.sub(r"[ìíïî]", 'I', result, flags=re.I)
  result = re.sub(r"[óòôº]", 'O', result, flags=re.I)
  result = re.sub(r"[ÿ]", 'Y', result, flags=re.I)

  result = re.sub(r"(.)\1{2,}", r'\1\1', result)  # 134

  result = re.sub(r"AJ$", 'Æ', result)  # 137
  if len(result) > 2:
      result = re.sub(r"(?<=[^AI])J$", '', result)  # 126
      result = re.sub(r"NTJ$", 'N', result)  # 100
  result = re.sub(r"([^I])J([QWRTPSDFGHJKLZXCVBNM])", r'\1I\2', result)  # 127

  result = re.sub(r"IE(?!U)|E[IY]|I[IJY]|Y[IJY]", r'Y', result)  # 89
  result = re.sub(r"Aæ|AE(?!U)|EA(?![EU])", r'æ', result)  # 145
  result = re.sub(r"AU|OU|Aα|Oα", r'α', result)  # 224
  result = re.sub(r"OA|AO|ÅA", r'Å', result)  # 143
  result = re.sub(r"AI|AY|AÆ|æI|æY", r'Æ', result)  # 146
  result = re.sub(r"EU|AEU|EÖ", r'Ö', result)  # 153
  result = re.sub(r"OE", r'û', result)  # 150
  result = re.sub(r"UI|UY|UÜ", r'Ü', result)  # 154
  if type != 'family_name':
      result = re.sub(r"([QWRTPSDFGHJKLZXCVBNM])YE(.)$", r'\1Y\2', result)  # 89

  if type != 'family_name':
      result = re.sub(r"PH", r'F', result)  # 70
  else:
      result = re.sub(r"^PH(?=[IYL])", r'F', result)  # 189
      result = re.sub(r"PH$", r'F', result)  # 160
      result = re.sub(r"PHUS$", r'F', result)  # 161
      result = re.sub(r"PHER$", r'FER', result)  # 162
      result = re.sub(r"PHERS$", r'FERS', result)  # 163
      result = re.sub(r"PH(?=[QWRTPSDFGHJKLZXCVBNM])", r'F', result)  # 164
      result = re.sub(r"(^[^OU])PH", r'\1F', result)  # 165
      result = re.sub(r"(^.[LMPRS])PH", r'\1F', result)  # 166
      result = re.sub(r"([^EYUIOALMPRS])PH", r'\1F', result)  # 166a
      result = re.sub(r"([QWRTPSDFGHJKLZXCVBNM][LMPRS])PH", r'\1F', result)  # 167
      result = re.sub(r"PH(?=[QWRTPSDFGHJKLZXCVBNM]+$|[EYUIOA]+$)", r'F', result)  # 169

  result = re.sub(r"^TSJ", r'TJ', result)  # 2

  result = re.sub(r"Z", r'S', result)  # 3

  result = re.sub(r"^QU(?=[EYUIOA])", r'KW', result)  # 4
  if type != 'family_name':
      result = re.sub(r"Q(?=.{0,2}$)", r'K', result)  # 5
  result = re.sub(r"QU(?=[EYUIOA])", r'K', result)  # 6
  result = re.sub(r"Q(?!U[EYUIOA])", r'K', result)  # 7
  result = re.sub(r"UI|UY|UÜ", r'Ü', result)  # 154

  result = re.sub(r"C$", r'K', result)  # 8
  result = re.sub(r"SC(?=[EYUIOA])", r'SK', result)  # 9
  result = re.sub(r"COI", r'SOI', result)  # 130
  result = re.sub(r"C(?![æEHIKSXY])", r'K', result)  # 10
  result = re.sub(r"CEES", r'KEES', result)  # 131
  result = re.sub(r"CæT", r'KæT', result)  # 132
  result = re.sub(r"C(?=[æÖEIY])", r'S', result)  # 11
  result = re.sub(r"^CS", r'S', result)  # 12

  result = re.sub(r"KXS", r'KS', result)  # 13
  result = re.sub(r"KX(?=[^S]$)", r'KS', result)  # 14
  result = re.sub(r"KX$", r'KS', result)  # 15
  if len(result) > 2:
      result = re.sub(r"([αÖÆS]|OI)X$", r'\1', result)  # 16
  result = re.sub(r"^X", r'S', result)  # 123
  result = re.sub(r"X", r'KS', result)  # 17

  result = re.sub(r"(?<=[EYUIOA])CK(?=[EYUIOA])", r'KK', result)  # 18
  result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])CK|CK(?=[QWRTPSDFGHJKLZXCVBNM])", r'K', result)  # 19
  result = re.sub(r"CK$", r'K', result)  # 20

  result = re.sub(r"^CHR", r'KR', result)  # 21
  result = re.sub(r"(?<=[GTS])CH$", r'', result)  # 22
  result = re.sub(r"(?<![GLMNST])CH$", r'G', result)  # 23
  if len(result) > 4:
      if type == 'family_name':
          result = re.sub(r"(?<=[EYUIOA])SCH(?=[EYUIOA]$)", r'SS', result)  # 113
      else:
          result = re.sub(r"(?<=[EYUIOA])SCH(?=[EYUIOA]$)", r'SJ', result)  # 140
      result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])SCH(?=[EYUIOA]$)", r'S', result)  # 114
      result = re.sub(r"(?!(?<=[EYUIOA])CH(?=[EYUIOA]))(?<=[^N])CH(?=.$)", r'G', result)  # 25
  if len(result) > 5:
      result = re.sub(r"(?<=[EYUIOA]S)CH(?=E.$)", r'S', result)  # 115
      result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM]S)CH(?=E.$)", r'', result)  # 116
  if len(result) > 6:
      result = re.sub(r"(?<=[EYUIOA]S)CH(?=E.S$)", r'S', result)  # 117
      result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM]S)CH(?=E.S$)", r'', result)  # 118
  result = re.sub(r"(?<=S)CH(?![EYUIOA]R)", r'', result)  # 26
  result = re.sub(r"(?<=[EYUIOA]S)CH(?=E)", r'S', result)  # 119
  result = re.sub(r"(?<=S)SCH(?=E)", r'S', result)  # 120
  result = re.sub(r"^SCH", r'SG', result)  # 27
  result = re.sub(r"(<=[QWRTPSDFGHJKLZXCVBNM])CH|CH(?=[QWRTPSDFGHJKLZXCVBNM])", r'G', result)  # 28
  result = re.sub(r"CH", r'X', result)  # 88

  if len(result) > 2:
      result = re.sub(r"H$", r'', result)  # 29
  result = re.sub(r"H(?=[QWRTPSDFGHJKLZXCVBNM])", r'', result)  # 30
  if type == 'family_name':
      result = re.sub(r"^D(?=H)", r'', result)  # 31
  result = re.sub(r"(?<=^[QWRTPSDFGHJKLZXCVBNM])H", r'', result)  # 32
  result = re.sub(r"(?<=[GT])H(?=.)", r'', result)  # 141
  result = re.sub(r"SH(?=.$)", r'SJ', result)  # 142
  if type != 'family_name':
      result = re.sub(r"(?<=[GT])H(?=..$)", r'', result)  # 133
  else:
      result = re.sub(r"(?<=[LNREYUIOA]G)H", r'', result)  # 33

  result = re.sub(r"(?<!^)D(?![EYUIOADHRW]|$)", r'T', result)  # 124

  if len(result) > 5:
      result = re.sub(r"^GUAL", r'WAL', result)  # 35
      result = re.sub(r"^GÜL", r'WIL', result)  # 35a

  if len(result) > 2:
      result = re.sub(r"^[IY](?=[æ±ÅÆAIYOûUÜÖ])", r'J', result)  # 125
  result = re.sub(r"I$", r'Y', result)  # 136
  result = re.sub(r"I(?=[EYUIOA])", r'Y', result)  # 138
  result = re.sub(r"I(?=[QWRTPSDFGHJKLZXCVBNM][EYUIOA])", r'Y', result)  # 139

  if len(result) > 2:
      result = re.sub(r"(.)(?=\1$)", r'', result)  # 38

  return result

GD['bloothooft'] = bloothooft
$$ LANGUAGE plpython3u;

SELECT bloothooft_bootstrap();
DROP FUNCTION IF EXISTS bloothooft_reduct;
CREATE FUNCTION bloothooft_reduct (input text, type text)
  RETURNS text IMMUTABLE
AS $$


import re

result = GD['bloothooft'](input, type)
result = result.upper()

if type != 'first_name' and len(result) > 4:
  result = re.sub(r"(?<=S)D$", r'', result) # 40
  result = re.sub(r"(?<=S)N$", r'', result) # 41
  result = re.sub(r"DR$", r'', result) # 42
  result = re.sub(r"(?<=[EYUIOAR]S)E$", r'', result) # 43
  result = re.sub(r"(?<=[^EYUIOAR])SE$", r'', result) # 45
  if len(result) > 5:
      result = re.sub(r"(?<=[EYUIOAR]S)[EO]N$", r'', result) # 46
      result = re.sub(r"(?<=[^EYUIOAR])S[EO]N$", r'', result) # 48
  if len(result) > 6:
      result = re.sub(r"(?<=[EYUIOAR]S)[EO]NS$", r'', result) # 49
      result = re.sub(r"(?<=[^EYUIOAR])S[EO]NS$", r'', result) # 51
      result = re.sub(r"SO[HO]N$", r'', result) # 52
  if len(result) > 8:
      result = re.sub(r"DO[XG]TER$", r'', result) # 53

if len(result) > 3:
  result = re.sub(r"(?<=[EYUIOAKR])S$", r'', result) # 54

if type != 'family_name':
  if len(result) > 4 or re.search(r"[EYUIOA]{2}.{2}", result) is not None:
    result = re.sub(r"TRUS$", r'ER', result) # 56
    result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])[IY][UÜ]S$", r'', result) # 57
    result = re.sub(r"S[KC][UÜ]S$", r'S', result) # 58
    result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])[UÜ]S$", r'', result) # 59
    result = re.sub(r"(?:(?<=[QWRTPSDFGHJKLZXCVBNM])[IEÖ]S$)|(?:(?<=[QWRTPSDFGHJKLZXCVBNM])[EYUIOA]ÖS$)", r'', result) # 60

  if len(result) > 4 or (len(result) == 4 and re.search(r"[QWRTPSDFGHJKLZXCVBNM]", result) is not None):
    result = re.sub(r"[EYUIOA]$", r'', result) # 61

  if len(result) > 2:
    result = re.sub(r"(.)\1$", r'\1', result) # 38

  if len(result) > 5:
    result = re.sub(r"(?<=^.)([QWRTPSDFGHJKLZXCVBNM])\1E(?=(?:[BHVH]|[QWRTPSDFGHJKLZXCVBNM][EYUIOA]))", r'\1', result) # 62
  if len(result) > 6:
    result = re.sub(r"(?<=^..)([QWRTPSDFGHJKLZXCVBNM])\1E(?=(?:[BHVH]|[QWRTPSDFGHJKLZXCVBNM][EYUIOA]))", r'\1', result) # 63

  if len(result) > 3:
    result = re.sub(r"(?<=[EYUIOAR][GX])[IEY]N$", r'', result) # 64
    result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])[^EYUIOAR][GX][IEY]N$", r'', result) # 65 A lot of interpretation was needed
    result = re.sub(r"(?<=[BFKLNPSV])EN$", r'', result) # 66
  if len(result) > 4:
    result = re.sub(r"(?<=[EYUIOA][DRT])EN$", r'', result) # 68
  if len(result) > 5:
    result = re.sub(r"JE[NRS]$", r'', result) # 67

  if len(result) > 3:
    result = re.sub(r"(?<=IN)[GK]$", r'', result) # 69
    result = re.sub(r"(?<=N)G$", r'', result) # 69a

  if len(result) > 5:
    result = re.sub(r"ERL$", r'E', result) # 71

  if len(result) > 2:
    result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])J$", r'', result) # 72
    result = re.sub(r"(?<=[^EYUIOARNL])[GX]$", r'', result) # 73

  if len(result) > 3:
    result = re.sub(r"(?<=[^EYUIOAR])[CKPS]$", r'', result) # 74
    result = re.sub(r"(?<=[BFNVW])T$", r'', result) # 75

    result = re.sub(r"(?<=[^EYUIOAL])EK$", r'', result) # 76

  result = re.sub(r"(?<=[^EYUIOABHVW])[IY][DGKLNSTX]$", r'', result) # 77
  result = re.sub(r"(?<=[^EYUIOADGMRTX])[IY][DGKLTX]$", r'', result) # 77a
  if len(result) > 4:
    result = re.sub(r"(?<=[^EYUIOAR])KE.$", r'', result) # 78

  if len(result) > 5:
    result = re.sub(r"(?<=[EYUIOA][^EYUIOAR])[IY][AÆæ±].$", r'', result) # 79
  if len(result) > 6:
    result = re.sub(r"(?<=[EYUIOA][^EYUIOAR])[IY][AÆæ±][AÆæ±].$", r'', result) # 80

  if len(result) > 3:
    result = re.sub(r"([EYUIOA]T$|[EYUIOA]RT$|[EYUIOA]GT$|[^E]LT$)|T$", r'\1', result) # 82

  if len(result) > 2:
    result = re.sub(r"(?<=[^EYUIOACP])H$", r'', result) # 83

  if len(result) > 5:
    result = re.sub(r"(.+[EYUIOA].+)(?<=[^EYUIOABGHMRVWX])ET$", r'\1', result) # 84
    result = re.sub(r"(.+[EYUIOA].+)(?<=[^EYUIOAGHMNRVWX])EL$", r'\1', result) # 85
  if len(result) > 4:
    result = re.sub(r"(?<=[EYUIOA]([QWRTPSDFGHJKLZXCVBNM]))\1E[^MRW]$", r'', result) # 86
  if len(result) > 2:
    result = re.sub(r"(.)\1$", r'\1', result) # 38
result = re.sub(r"(?<=^[EYUIOA][QWRTPSDFGHJKLZXCVBNM])[EYUIOA]$", r'', result) # 61

if type != 'family_name':
  if len(result) > 2:
    result = re.sub(r"(?<=[DFMW])K$", r'', result) # 101
  result = re.sub(r"(?<=[EYUIOA]S)K$", r'', result) # 102
  if len(result) > 2:
    result = re.sub(r"(?<=[^EYUIOALR])T[NS]$", r'', result) # 95
  if len(result) > 3:
    result = re.sub(r"(?<=[^EYUIOA][^EYUIOAR])[NS]$", r'', result) # 96
  if len(result) > 2:
    result = re.sub(r"(?<=E[DT])S$", r'', result) # 97

  if len(result) > 4:
    result = re.sub(r"(?<![EYUIOA])D$", r'T', result) # 129

  result = re.sub(r"H(?=[QWRTPSDFGHJKLZXCVBNM])", r'', result) # 30
  result = re.sub(r"(?<=^[QWRTPSDFGHJKLZXCVBNM])H", r'', result) # 32

if len(result) > 3:
  result = re.sub(r"(?<=[^EYUIOAR])S", r'', result) # 54

if len(result) > 2:
  result = re.sub(r"(.)\1$", r'\1', result) # 38
if type == 'family_name':
  result = re.sub(r"PH$", r'F', result) # 160

  if len(result) > 2:
    result = re.sub(r"PH$", r'F', result) # 160

    result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])J.$", r'', result) # 90
  if len(result) > 5:
    result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])JE[NRS]$", r'', result) # 91
  if len(result) > 6:
    result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])JERS$", r'', result) # 92

  if len(result) > 5:
    result = re.sub(r"[IY]US$", r'', result) # 93
  result = re.sub(r"(?<=[^K][DKLMNPRSX])US$", r'', result) # 94

if len(result) > 4:
  result = re.sub(r"D$", r'T', result) # 129

if type == 'family_name':
  if len(result) > 2:
    result = re.sub(r"CS$", r'K', result) # 110
  result = re.sub(r"CS", r'S', result) # 122

if len(result) > 4:
  result = re.sub(r"INK$", r'ING', result) # 112

if len(result) > 3:
  result = re.sub(r"(?<=[^EYUIOAR])S", r'', result) # 54
if type == 'family_name':
  result = re.sub(r"PH$", r'F', result) # 160
if len(result) > 2:
  result = re.sub(r"(.)\1$", r'\1', result) # 38

result = re.sub(r"C$", r'K', result) # 8
result = re.sub(r"(?<=[^GLMNST])X$", r'G', result) # 106

if len(result) > 2:
  result = re.sub(r"TD$", r'T', result) # 99
result = re.sub(r"(?<=[QWRTPSDFGHJKLZXCVBNM])SK$", r'', result) # 103
result = re.sub(r"(?<=[FST])N$", r'', result) # 104
result = re.sub(r"(?<=[EYUIOA])VW$", r'', result) # 105
result = re.sub(r"V$", r'F', result) # 109

if len(result) > 2:
  result = re.sub(r"(.)\1$", r'\1', result) # 38

return result
$$ LANGUAGE plpython3u;
