CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS plpython3u;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS reconciliation_jobs (
  job_id text primary key,
  job_title text not null,
  job_description text not null,
  resources_form_data json,
  mappings_form_data json,
  resources_filename text,
  mappings_filename text,
  UNIQUE (job_title, job_description)
);

CREATE TABLE IF NOT EXISTS alignment_jobs (
    job_id text not null,
    alignment int not null,
    status text,
    requested_at timestamp,
    processing_at timestamp,
    finished_at timestamp,
    links_count bigint,
    PRIMARY KEY (job_id, alignment)
);

CREATE TABLE IF NOT EXISTS timbuctoo_tables (
  table_name text primary key,
  dataset_id text not null,
  collection_id text not null,
  create_time timestamp not null,
  update_start_time timestamp,
  next_page text,
  rows_count int default 0 not null,
  last_push_time timestamp,
  update_finish_time timestamp,
  UNIQUE (dataset_id, collection_id)
);

CREATE TABLE IF NOT EXISTS clusterings (
  clustering_id text unique not null,
  job_id text not null,
  mapping_name text not null,
  alignment_csv text not null,
  association_csv text,
  clustering_type text not null
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
    IF year = '' THEN
      RETURN 0;
    ELSE
      RETURN year;
    END IF;
  END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.ll_soundex(input text) RETURNS text IMMUTABLE AS $$
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
