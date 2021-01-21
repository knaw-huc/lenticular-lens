CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS plpython3u;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TYPE spec_type AS ENUM ('linkset', 'lens');
CREATE TYPE link_order AS ENUM ('source_target', 'both', 'target_source');
CREATE TYPE link_validity AS ENUM ('accepted', 'rejected', 'not_validated', 'mixed');

CREATE SCHEMA IF NOT EXISTS timbuctoo;
CREATE SCHEMA IF NOT EXISTS linksets;
CREATE SCHEMA IF NOT EXISTS lenses;

CREATE TABLE IF NOT EXISTS jobs
(
    job_id                           text primary key,
    job_title                        text                    not null,
    job_description                  text                    not null,
    job_link                         text,
    entity_type_selections_form_data json,
    linkset_specs_form_data          json,
    lens_specs_form_data             json,
    entity_type_selections           json,
    linkset_specs                    json,
    lens_specs                       json,
    created_at                       timestamp default now() not null,
    updated_at                       timestamp default now() not null,
    UNIQUE (job_title, job_description)
);

CREATE TABLE IF NOT EXISTS timbuctoo_tables
(
    table_name               text primary key,
    graphql_endpoint         text          not null,
    hsid                     text,
    dataset_id               text          not null,
    collection_id            text          not null,
    dataset_uri              text          not null,
    dataset_name             text          not null,
    title                    text          not null,
    description              text,
    collection_uri           text          not null,
    collection_title         text,
    collection_shortened_uri text          not null,
    total                    int           not null,
    columns                  json          not null,
    create_time              timestamp     not null,
    update_start_time        timestamp,
    next_page                text,
    rows_count               int default 0 not null,
    last_push_time           timestamp,
    update_finish_time       timestamp,
    UNIQUE (graphql_endpoint, hsid, dataset_id, collection_id)
);

CREATE TABLE IF NOT EXISTS linksets
(
    job_id                         text    not null,
    spec_id                        int     not null,
    status                         text    not null,
    status_message                 text,
    kill                           boolean not null,
    requested_at                   timestamp,
    processing_at                  timestamp,
    finished_at                    timestamp,
    links_count                    bigint,
    distinct_links_count           bigint,
    distinct_sources_count         bigint,
    distinct_targets_count         bigint,
    distinct_linkset_sources_count bigint,
    distinct_linkset_targets_count bigint,
    PRIMARY KEY (job_id, spec_id)
);

CREATE TABLE IF NOT EXISTS lenses
(
    job_id         text    not null,
    spec_id        int     not null,
    status         text    not null,
    status_message text,
    kill           boolean not null,
    requested_at   timestamp,
    processing_at  timestamp,
    finished_at    timestamp,
    links_count    bigint,
    PRIMARY KEY (job_id, spec_id)
);

CREATE TABLE IF NOT EXISTS clusterings
(
    job_id           text      not null,
    spec_id          int       not null,
    spec_type        spec_type not null,
    clustering_type  text      not null,
    association_file text,
    status           text      not null,
    status_message   text,
    kill             boolean   not null,
    requested_at     timestamp,
    processing_at    timestamp,
    finished_at      timestamp,
    links_count      bigint,
    clusters_count   bigint,
    extended_count   int,
    cycles_count     int,
    PRIMARY KEY (job_id, spec_id, spec_type)
);

CREATE OR REPLACE FUNCTION increment_counter(sequence_name text) RETURNS boolean
    COST 10000000 STRICT VOLATILE AS
$$
BEGIN
    RETURN nextval(sequence_name) > -1;
END;
$$ LANGUAGE plpgsql;

-- CREATE OR REPLACE FUNCTION t_min(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT least(a, b);
-- $$ LANGUAGE sql;
--
-- CREATE OR REPLACE FUNCTION t_prod(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT a * b;
-- $$ LANGUAGE sql;
--
-- CREATE OR REPLACE FUNCTION t_luk(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT greatest(0, a + b - 1);
-- $$ LANGUAGE sql;
--
-- CREATE OR REPLACE FUNCTION t_d(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT CASE WHEN b = 1 THEN a WHEN a = 1 THEN b ELSE 0 END;
-- $$ LANGUAGE sql;
--
-- CREATE OR REPLACE FUNCTION t_nm(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT CASE WHEN a + b > 1 THEN least(a, b) ELSE 0 END;
-- $$ LANGUAGE sql;
--
-- CREATE OR REPLACE FUNCTION t_h0(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT CASE WHEN NOT a = 0 AND NOT b = 0 THEN a * b / (a + b - (a * b)) ELSE 0 END;
-- $$ LANGUAGE sql;
--
-- CREATE OR REPLACE FUNCTION t_h0(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT CASE WHEN NOT a = 0 AND NOT b = 0 THEN a * b / (a + b - (a * b)) ELSE 0 END;
-- $$ LANGUAGE sql;
--
-- CREATE OR REPLACE FUNCTION tc_max(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT greatest(a, b);
-- $$ LANGUAGE sql;
--
-- CREATE OR REPLACE FUNCTION tc_sum(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT a + b - (a * b);
-- $$ LANGUAGE sql;
--
-- CREATE OR REPLACE FUNCTION tc_luk(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT least(a + b, 1);
-- $$ LANGUAGE sql;
--
-- CREATE OR REPLACE FUNCTION tc_d(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT CASE WHEN b = 0 THEN a WHEN a = 0 THEN b ELSE 1 END;
-- $$ LANGUAGE sql;
--
-- CREATE OR REPLACE FUNCTION tc_nm(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT CASE WHEN a + b < 1 THEN greatest(a, b) ELSE 1 END;
-- $$ LANGUAGE sql;
--
-- CREATE OR REPLACE FUNCTION tc_h2(a numeric, b numeric) RETURNS numeric
--     STRICT IMMUTABLE PARALLEL SAFE AS
-- $$
-- SELECT (a + b) / (1 + a * b);
-- $$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION logic_ops(operation text, a numeric, b numeric) RETURNS numeric
    IMMUTABLE PARALLEL SAFE AS
$$
SELECT CASE
           WHEN a IS NULL
               THEN b
           WHEN b IS NULL
               THEN a
           WHEN operation = 'MINIMUM_T_NORM'
               THEN least(a, b)
           WHEN operation = 'PRODUCT_T_NORM'
               THEN a * b
           WHEN operation = 'LUKASIEWICZ_T_NORM'
               THEN greatest(0, a + b - 1)
           WHEN operation = 'DRASTIC_T_NORM'
               THEN CASE WHEN b = 1 THEN a WHEN a = 1 THEN b ELSE 0 END
           WHEN operation = 'NILPOTENT_MINIMUM'
               THEN CASE WHEN a + b > 1 THEN least(a, b) ELSE 0 END
           WHEN operation = 'HAMACHER_PRODUCT'
               THEN CASE WHEN NOT a = 0 AND NOT b = 0 THEN a * b / (a + b - (a * b)) ELSE 0 END
           WHEN operation = 'MAXIMUM_T_CONORM'
               THEN greatest(a, b)
           WHEN operation = 'PROBABILISTIC_SUM'
               THEN a + b - (a * b)
           WHEN operation = 'BOUNDED_SUM'
               THEN least(a + b, 1)
           WHEN operation = 'DRASTIC_T_CONORM'
               THEN CASE WHEN b = 0 THEN a WHEN a = 0 THEN b ELSE 1 END
           WHEN operation = 'NILPOTENT_MAXIMUM'
               THEN CASE WHEN a + b < 1 THEN greatest(a, b) ELSE 1 END
           WHEN operation = 'EINSTEIN_SUM'
               THEN (a + b) / (1 + a * b)
           END;
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION logic_ops(operation text, similarities numeric[]) RETURNS numeric
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
DECLARE
    similarity     numeric;
    cur_similarity numeric;
BEGIN
    FOREACH cur_similarity IN ARRAY similarities
        LOOP
            IF similarity IS NULL THEN
                similarity = cur_similarity;
            ELSE
                similarity = logic_ops(operation, similarity, cur_similarity);
            END IF;
        END LOOP;
    RETURN similarity;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION array_distinct_merge(l anyarray, r anyarray) RETURNS anyarray
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
SELECT ARRAY(SELECT DISTINCT unnest(l || r));
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION jsonb_merge(l jsonb, r jsonb) RETURNS jsonb
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
SELECT jsonb_object_agg(
    coalesce(left_set.key, right_set.key),
    coalesce(left_set.value || right_set.value, left_set.value, right_set.value)
)
FROM jsonb_each(l) AS left_set
FULL JOIN jsonb_each(r) AS right_set
ON left_set.key = right_set.key;
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION transform_last_name_format(name text, include_infix bool) RETURNS text
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
WITH name_parts (first_name, infix, last_name) AS (
    VALUES (coalesce(trim(substring(name from ', ([^\[]*)')), ''),
            coalesce(trim(substring(name from '\[(.*)\]')), ''),
            coalesce(trim(substring(name from '^[^,\[]*')), ''))
)
SELECT trim(first_name || ' ' || CASE WHEN include_infix AND infix != '' THEN infix || ' ' ELSE '' END || last_name)
FROM name_parts;
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION to_date_immutable(text, text) RETURNS date
    STRICT IMMUTABLE AS
$$
BEGIN
    RETURN to_date($1, $2);
EXCEPTION
    WHEN SQLSTATE '22008' THEN
        RETURN NULL;
    WHEN SQLSTATE '22007' THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION to_numeric_immutable(text) RETURNS numeric
    STRICT IMMUTABLE AS
$$
BEGIN
    RETURN $1::numeric;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_date_part(text, text) RETURNS text
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
DECLARE
    year  text;
    month text;
BEGIN
    year = substr($2, 0, 5);
    month = substr($2, 6, 2);

    CASE $1
        WHEN 'year'
            THEN IF year ~ E'^\\d+$' THEN
                RETURN year;
            ELSE
                RETURN NULL;
            END IF;
        WHEN 'month'
            THEN IF month ~ E'^\\d+$' THEN
                RETURN month;
            ELSE
                RETURN NULL;
            END IF;
        WHEN 'year_month'
            THEN IF year ~ E'^\\d+$' AND month ~ E'^\\d+$' THEN
                RETURN year || '-' || month;
            ELSE
                RETURN NULL;
            END IF;
        END CASE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION similarity(source text, target text, distance decimal) RETURNS decimal
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
SELECT 1 - (distance / greatest(char_length(source), char_length(target)));
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION delta(type text, source numeric, target numeric,
                                 start_delta numeric, end_delta numeric) RETURNS boolean
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
SELECT abs(source - target) BETWEEN start_delta AND end_delta AND
       CASE
           WHEN type = '<' THEN source <= target
           WHEN type = '>' THEN target <= source
           ELSE TRUE END;
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION delta(type text, source date, target date, no_days numeric) RETURNS boolean
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
SELECT abs(source - target) < no_days AND
       CASE
           WHEN type = '<' THEN source <= target
           WHEN type = '>' THEN target <= source
           ELSE TRUE END;
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION levenshtein_python(source text, target text) RETURNS integer
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
import Levenshtein

return Levenshtein.distance(source, target)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION levenshtein_distance(source text, target text, max_distance integer) RETURNS integer
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
SELECT CASE
           WHEN greatest(octet_length(source), octet_length(target)) > 255
               THEN levenshtein_python(source, target)
           ELSE levenshtein_less_equal(source, target, max_distance) END;
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION jaro(source text, target text) RETURNS decimal
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
import Levenshtein

return Levenshtein.jaro(source, target)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION jaro_winkler(source text, target text, prefix_weight decimal) RETURNS decimal
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
import Levenshtein

return Levenshtein.jaro_winkler(source, target, float(prefix_weight))
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION ll_soundex(input text, size integer) RETURNS text
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
from soundex import soundex

return soundex(input, size)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION soundex_words(input text, size integer) RETURNS text
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
SELECT string_agg(ll_soundex(word, size), '_')
FROM regexp_split_to_table(input, '\s+') AS word
WHERE trim(word) != '';
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION nysiis(input text) RETURNS text
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
import fuzzy

return fuzzy.nysiis(input)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION bloothooft(input text, type text) RETURNS text
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
from bloothooft import bloothooft_reduct

return bloothooft_reduct(input, type)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION word_intersection(source text, target text, ordered boolean, approximate boolean,
                                             stop_symbols text) RETURNS decimal
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
from word_intersection import word_intersection

return word_intersection(source, target, ordered, approximate, stop_symbols)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION init_dictionary(key text, dictionary text, additional_stopwords text[] = ARRAY[]::text[]) RETURNS void
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
from stop_words import init_dictionary

if '_' in dictionary:
    [language, specific_set] = dictionary.split('_', 1)
else:
    language = dictionary

GD['language_' + key] = language
GD['stopwords_' + key] = init_dictionary(dictionary, additional_stopwords)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION remove_stopwords(key text, input text) RETURNS text
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
from stop_words import remove_stopwords

stop_words_set = GD['stopwords_' + key]
language = GD['language_' + key]
return remove_stopwords(stop_words_set, language, input)
$$ LANGUAGE plpython3u;
