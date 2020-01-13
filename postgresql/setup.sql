CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS plpython3u;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS reconciliation_jobs
(
    job_id              text primary key,
    job_title           text                    not null,
    job_description     text                    not null,
    job_link            text,
    resources_form_data json,
    mappings_form_data  json,
    resources           json,
    mappings            json,
    created_at          timestamp default now() not null,
    updated_at          timestamp default now() not null,
    UNIQUE (job_title, job_description)
);

CREATE TABLE IF NOT EXISTS timbuctoo_tables
(
    table_name         text primary key,
    graphql_endpoint   text          not null,
    hsid               text          null,
    dataset_id         text          not null,
    collection_id      text          not null,
    dataset_name       text          not null,
    title              text          not null,
    description        text,
    collection_title   text,
    total              int           not null,
    columns            json          not null,
    create_time        timestamp     not null,
    update_start_time  timestamp,
    next_page          text,
    rows_count         int default 0 not null,
    last_push_time     timestamp,
    update_finish_time timestamp,
    UNIQUE (graphql_endpoint, hsid, dataset_id, collection_id)
);

CREATE TABLE IF NOT EXISTS alignments
(
    job_id                 text    not null,
    alignment              int     not null,
    status                 text    not null,
    status_message         text,
    kill                   boolean not null,
    requested_at           timestamp,
    processing_at          timestamp,
    finished_at            timestamp,
    links_count            bigint,
    sources_count          bigint,
    targets_count          bigint,
    distinct_links_count   bigint,
    distinct_sources_count bigint,
    distinct_targets_count bigint,
    PRIMARY KEY (job_id, alignment)
);

CREATE TABLE IF NOT EXISTS clusterings
(
    job_id           text    not null,
    alignment        int     not null,
    clustering_type  text    not null,
    association_file text,
    status           text    not null,
    status_message   text,
    kill             boolean not null,
    requested_at     timestamp,
    processing_at    timestamp,
    finished_at      timestamp,
    links_count      bigint,
    clusters_count   bigint,
    extended_count   int,
    cycles_count     int,
    PRIMARY KEY (job_id, alignment)
);

CREATE OR REPLACE FUNCTION increment_counter(sequence_name text) RETURNS boolean
    COST 10000 STRICT VOLATILE AS
$$
BEGIN
    RETURN nextval(sequence_name) != 0;
END;
$$ LANGUAGE plpgsql;

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
        WHEN 'year' THEN IF year ~ E'^\\d+$' THEN
            RETURN year;
        ELSE
            RETURN NULL;
        END IF;
        WHEN 'month' THEN IF month ~ E'^\\d+$' THEN
            RETURN month;
        ELSE
            RETURN NULL;
        END IF;
        WHEN 'year_month' THEN IF year ~ E'^\\d+$' AND month ~ E'^\\d+$' THEN
            RETURN year || '-' || month;
        ELSE
            RETURN NULL;
        END IF;
        END CASE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION ecartico_full_name(text) RETURNS text
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
DECLARE
    first_name  text;
    infix       text;
    family_name text;
BEGIN
    first_name = coalesce(trim(substring($1 from ', ([^[]*)')), '');
    infix = coalesce(trim(substring($1 from '\[(.*)\]')), '');
    family_name = coalesce(trim(substring($1 from '^[^,]*')), '');

    RETURN first_name || ' ' || CASE WHEN infix != '' THEN infix || ' ' ELSE '' END || family_name;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION levenshtein_distance(source text, target text) RETURNS integer
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
BEGIN
    IF greatest(octet_length(source), octet_length(target)) > 255 THEN
        RETURN levenshtein_python($1, $2);
    ELSE
        RETURN levenshtein($1, $2);
    END IF;
END
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION levenshtein_python(source text, target text) RETURNS integer
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
import Levenshtein

return Levenshtein.distance(source, target)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION similarity(source text, target text, distance decimal) RETURNS decimal
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
BEGIN
    RETURN 1 - (distance / greatest(char_length(source), char_length(target)));
END
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION ll_soundex(input text) RETURNS text
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
from functions import soundex

return soundex(input)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION bloothooft(input text, type text) RETURNS text
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
from functions import bloothooft_reduct

return bloothooft_reduct(input, type)
$$ LANGUAGE plpython3u;