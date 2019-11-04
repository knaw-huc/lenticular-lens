CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS plpython3u;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS reconciliation_jobs
(
    job_id              text primary key,
    job_title           text                    not null,
    job_description     text                    not null,
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
    job_id           text not null,
    alignment        int  not null,
    clustering_type  text not null,
    association_file text,
    status           text not null,
    status_message   text,
    requested_at     timestamp,
    processing_at    timestamp,
    finished_at      timestamp,
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

CREATE OR REPLACE FUNCTION to_date_immutable(text) RETURNS date
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
BEGIN
    RETURN to_date($1, 'YYYY-MM-DD');
EXCEPTION
    WHEN SQLSTATE '22008' THEN
        RETURN NULL;
    WHEN SQLSTATE '22007' THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_year(text) RETURNS int
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
DECLARE
    year text;
BEGIN
    year = substr($1, 0, 5);
    IF year ~ E'^\\d+$' THEN
        RETURN year::int;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_month(text) RETURNS int
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
DECLARE
    month text;
BEGIN
    month = substr($1, 6, 2);
    IF month ~ E'^\\d+$' THEN
        RETURN month::int;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_year_month(text) RETURNS text
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
DECLARE
    month int;
    year  int;
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

CREATE OR REPLACE FUNCTION levenshtein_distance(source text, target text) RETURNS integer
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
import Levenshtein

return Levenshtein.distance(source, target)
$$ LANGUAGE plpython3u;

CREATE OR REPLACE FUNCTION levenshtein_similarity(source text, target text) RETURNS decimal
    STRICT IMMUTABLE PARALLEL SAFE AS
$$
DECLARE
    longest int;
BEGIN
    longest = greatest(char_length(source), char_length(target));
    RETURN 1 - (levenshtein_distance(source, target)::decimal / longest);
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