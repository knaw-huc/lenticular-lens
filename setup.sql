CREATE EXTENSION IF NOT EXISTS lenticular_lens CASCADE;

CREATE TYPE spec_type AS ENUM ('linkset', 'lens');
CREATE TYPE link_order AS ENUM ('source_target', 'both', 'target_source');
CREATE TYPE link_validity AS ENUM ('accepted', 'rejected', 'uncertain', 'unchecked', 'disputed');

CREATE SCHEMA IF NOT EXISTS timbuctoo;
CREATE SCHEMA IF NOT EXISTS linksets;
CREATE SCHEMA IF NOT EXISTS lenses;

CREATE TABLE IF NOT EXISTS jobs
(
    job_id                           text primary key,
    job_title                        text                    not null,
    job_description                  text                    not null,
    job_link                         text,
    entity_type_selections_form_data jsonb,
    linkset_specs_form_data          jsonb,
    lens_specs_form_data             jsonb,
    views_form_data                  jsonb,
    entity_type_selections           jsonb,
    linkset_specs                    jsonb,
    lens_specs                       jsonb,
    views                            jsonb,
    created_at                       timestamp default now() not null,
    updated_at                       timestamp default now() not null
);

CREATE TABLE IF NOT EXISTS timbuctoo_tables
(
    table_name                  text primary key,
    graphql_endpoint            text                      not null,
    dataset_id                  text                      not null,
    collection_id               text                      not null,
    dataset_uri                 text                      not null,
    dataset_name                text                      not null,
    title                       text                      not null,
    description                 text,
    collection_uri              text                      not null,
    collection_title            text,
    collection_shortened_uri    text                      not null,
    total                       int                       not null,
    columns                     jsonb                     not null,
    prefix_mappings             jsonb                     not null,
    uri_prefix_mappings         jsonb default '{}'::jsonb not null,
    dynamic_uri_prefix_mappings jsonb default '{}'::jsonb not null,
    create_time                 timestamp                 not null,
    update_start_time           timestamp,
    next_page                   text,
    rows_count                  int   default 0           not null,
    last_push_time              timestamp,
    update_finish_time          timestamp,
    UNIQUE (graphql_endpoint, dataset_id, collection_id)
);

CREATE TABLE IF NOT EXISTS linksets
(
    job_id                 text    not null,
    spec_id                int     not null,
    status                 text    not null,
    status_message         text,
    kill                   boolean not null,
    requested_at           timestamp,
    processing_at          timestamp,
    finished_at            timestamp,
    links_progress         bigint,
    links_count            bigint,
    sources_count          bigint,
    targets_count          bigint,
    entities_count         bigint,
    linkset_sources_count  bigint,
    linkset_targets_count  bigint,
    linkset_entities_count bigint,
    PRIMARY KEY (job_id, spec_id)
);

CREATE TABLE IF NOT EXISTS lenses
(
    job_id              text    not null,
    spec_id             int     not null,
    status              text    not null,
    status_message      text,
    kill                boolean not null,
    requested_at        timestamp,
    processing_at       timestamp,
    finished_at         timestamp,
    links_count         bigint,
    lens_sources_count  bigint,
    lens_targets_count  bigint,
    lens_entities_count bigint,
    PRIMARY KEY (job_id, spec_id)
);

CREATE TABLE IF NOT EXISTS clusterings
(
    job_id           text      not null,
    spec_id          int       not null,
    spec_type        spec_type not null,
    clustering_type  text      not null,
    status           text      not null,
    status_message   text,
    kill             boolean   not null,
    requested_at     timestamp,
    processing_at    timestamp,
    finished_at      timestamp,
    links_count      bigint,
    clusters_count   bigint,
    resources_size   bigint,
    extended_count   int,
    cycles_count     int,
    smallest_size    bigint,
    largest_size     bigint,
    smallest_count   bigint,
    largest_count    bigint,
    PRIMARY KEY (job_id, spec_id, spec_type)
);

/* UTILITY FUNCTIONS */

CREATE OR REPLACE FUNCTION increment_counter(sequence_name text) RETURNS boolean AS $$
BEGIN
    RETURN nextval(sequence_name) > -1;
END;
$$ LANGUAGE plpgsql COST 10000000 STRICT VOLATILE;

CREATE AGGREGATE array_cat_agg(anycompatiblearray) (
    sfunc = array_cat,
    stype = anycompatiblearray
);

CREATE OR REPLACE FUNCTION array_perc_size(source anyarray, target anyarray, perc integer) RETURNS integer AS $$
SELECT ceil(greatest(cardinality(source), cardinality(target)) * (perc / 100.0));
$$ LANGUAGE sql STRICT IMMUTABLE PARALLEL SAFE;

CREATE OR REPLACE FUNCTION array_distinct_merge(l anyarray, r anyarray) RETURNS anyarray AS $$
SELECT ARRAY(SELECT DISTINCT unnest(l || r));
$$ LANGUAGE sql STRICT IMMUTABLE PARALLEL SAFE;

CREATE AGGREGATE array_distinct_merge_agg(anyarray) (
    sfunc = array_distinct_merge,
    stype = anyarray
);

CREATE OR REPLACE FUNCTION jsonb_merge(l jsonb, r jsonb) RETURNS jsonb AS $$
SELECT jsonb_object_agg(
    coalesce(left_set.key, right_set.key),
    coalesce(left_set.value || right_set.value, left_set.value, right_set.value)
)
FROM jsonb_each(l) AS left_set
FULL JOIN jsonb_each(r) AS right_set
ON left_set.key = right_set.key;
$$ LANGUAGE sql STRICT IMMUTABLE PARALLEL SAFE;

CREATE OR REPLACE FUNCTION combinations(arr anyarray, size integer) RETURNS SETOF anyarray AS $$
WITH RECURSIVE
    items(item) AS ( SELECT * FROM unnest(arr) ),
    combinations AS (
        SELECT ARRAY[item] AS combo, item, 1 AS count
        FROM items
        UNION ALL
        SELECT array_prepend(items.item, combo), items.item, count + 1
        FROM combinations, items
        WHERE count < size AND items.item < combo[1]
    )
SELECT combo FROM combinations
WHERE CASE WHEN cardinality(arr) <= size THEN count = cardinality(arr) ELSE count = size END;
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE OR REPLACE FUNCTION match_array_meets_size(arr anyarray, min_count numeric) RETURNS boolean AS $$
DECLARE
    unique_source_size numeric;
    unique_target_size numeric;
BEGIN
    IF min_count > 0 THEN
        unique_source_size = cardinality(ARRAY(SELECT DISTINCT unnest(arr[:][1:1])));
        unique_target_size = cardinality(ARRAY(SELECT DISTINCT unnest(arr[:][2:2])));

        IF array_length(arr, 1) < min_count OR unique_source_size < min_count OR unique_target_size < min_count THEN
            RETURN FALSE;
        END IF;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql STRICT IMMUTABLE PARALLEL SAFE;

/* NOTIFICATIONS */

CREATE OR REPLACE FUNCTION notify_job_update() RETURNS trigger AS $$
DECLARE
    notification json;
BEGIN
    IF NEW.job_title != OLD.job_title OR
       NEW.job_description != OLD.job_description OR
       NEW.job_link != OLD.job_link OR
       NEW.entity_type_selections_form_data != OLD.entity_type_selections_form_data OR
       NEW.linkset_specs_form_data != OLD.linkset_specs_form_data OR
       NEW.lens_specs_form_data != OLD.lens_specs_form_data OR
       NEW.views_form_data != OLD.views_form_data THEN
        notification = json_build_object(
            'job_id', NEW.job_id,
            'updated_at', NEW.updated_at,
            'is_title_update', NEW.job_title != OLD.job_title,
            'is_description_update', NEW.job_description != OLD.job_description,
            'is_link_update', NEW.job_link != OLD.job_link,
            'is_entity_type_selections_update',
                NEW.entity_type_selections_form_data != OLD.entity_type_selections_form_data,
            'is_linkset_specs_update', NEW.linkset_specs_form_data != OLD.linkset_specs_form_data,
            'is_lens_specs_update', NEW.lens_specs_form_data != OLD.lens_specs_form_data,
            'is_views_update', NEW.views_form_data != OLD.views_form_data
        );

        PERFORM pg_notify('job_update', notification::text);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION notify_timbuctoo_update() RETURNS trigger AS $$
DECLARE
    notification json;
BEGIN
    IF NEW IS NULL THEN
        notification = json_build_object(
            'graphql_endpoint', OLD.graphql_endpoint,
            'dataset_id', OLD.dataset_id,
            'collection_id', OLD.collection_id
        );

        PERFORM pg_notify('timbuctoo_delete', notification::text);
    ELSIF OLD IS NULL OR NEW.rows_count != OLD.rows_count THEN
        notification = json_build_object(
            'graphql_endpoint', NEW.graphql_endpoint,
            'dataset_id', NEW.dataset_id,
            'collection_id', NEW.collection_id,
            'total', NEW.total,
            'rows_count', NEW.rows_count
        );

        PERFORM pg_notify('timbuctoo_update', notification::text);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION notify_linkset_update() RETURNS trigger AS $$
DECLARE
    notification json;
BEGIN
    IF NEW IS NULL THEN
        notification = json_build_object(
            'job_id', OLD.job_id,
            'spec_type', 'linkset',
            'spec_id', OLD.spec_id
        );

        PERFORM pg_notify('alignment_delete', notification::text);
    ELSIF OLD IS NULL OR NEW.status != OLD.status OR NEW.links_progress != OLD.links_progress THEN
        notification = json_build_object(
            'job_id', NEW.job_id,
            'spec_type', 'linkset',
            'spec_id', NEW.spec_id,
            'status', NEW.status,
            'status_message', NEW.status_message,
            'links_progress', NEW.links_progress
        );

        PERFORM pg_notify('alignment_update', notification::text);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION notify_lens_update() RETURNS trigger AS $$
DECLARE
    notification json;
BEGIN
    IF NEW IS NULL THEN
        notification = json_build_object(
            'job_id', OLD.job_id,
            'spec_type', 'lens',
            'spec_id', OLD.spec_id
        );

        PERFORM pg_notify('alignment_delete', notification::text);
    ELSIF OLD IS NULL OR NEW.status != OLD.status THEN
        notification = json_build_object(
            'job_id', NEW.job_id,
            'spec_type', 'lens',
            'spec_id', NEW.spec_id,
            'status', NEW.status,
            'status_message', NEW.status_message
        );

        PERFORM pg_notify('alignment_update', notification::text);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION notify_clustering_update() RETURNS trigger AS $$
DECLARE
    notification json;
BEGIN
    IF NEW IS NULL THEN
        notification = json_build_object(
            'job_id', OLD.job_id,
            'spec_type', OLD.spec_type,
            'spec_id', OLD.spec_id,
            'clustering_type', OLD.clustering_type
        );

        PERFORM pg_notify('clustering_delete', notification::text);
    ELSIF OLD IS NULL OR NEW.status != OLD.status OR
       NEW.links_count != OLD.links_count OR NEW.clusters_count != OLD.clusters_count THEN
        notification = json_build_object(
            'job_id', NEW.job_id,
            'spec_type', NEW.spec_type,
            'spec_id', NEW.spec_id,
            'clustering_type', NEW.clustering_type,
            'status', NEW.status,
            'status_message', NEW.status_message,
            'links_count', NEW.links_count,
            'clusters_count', NEW.clusters_count
        );

        PERFORM pg_notify('clustering_update', notification::text);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER job_notify AFTER UPDATE ON jobs
FOR EACH ROW EXECUTE PROCEDURE notify_job_update();

CREATE TRIGGER timbuctoo_notify AFTER INSERT OR UPDATE OR DELETE ON timbuctoo_tables
FOR EACH ROW EXECUTE PROCEDURE notify_timbuctoo_update();

CREATE TRIGGER linkset_notify AFTER INSERT OR UPDATE OR DELETE ON linksets
FOR EACH ROW EXECUTE PROCEDURE notify_linkset_update();

CREATE TRIGGER lens_notify AFTER INSERT OR UPDATE OR DELETE ON lenses
FOR EACH ROW EXECUTE PROCEDURE notify_lens_update();

CREATE TRIGGER clustering_notify AFTER INSERT OR UPDATE OR DELETE ON clusterings
FOR EACH ROW EXECUTE PROCEDURE notify_clustering_update();

/* LOGIC OPS FUNCTIONS */

CREATE OR REPLACE FUNCTION t_min(a numeric, b numeric) RETURNS numeric AS $$
SELECT least(a, b);
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE OR REPLACE FUNCTION t_prod(a numeric, b numeric) RETURNS numeric AS $$
SELECT a * b;
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE OR REPLACE FUNCTION t_luk(a numeric, b numeric) RETURNS numeric AS $$
SELECT greatest(0, a + b - 1);
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE OR REPLACE FUNCTION t_d(a numeric, b numeric) RETURNS numeric AS $$
SELECT CASE WHEN b = 1 THEN a WHEN a = 1 THEN b ELSE 0 END;
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE OR REPLACE FUNCTION t_nm(a numeric, b numeric) RETURNS numeric AS $$
SELECT CASE WHEN a + b > 1 THEN least(a, b) ELSE 0 END;
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE OR REPLACE FUNCTION t_h0(a numeric, b numeric) RETURNS numeric AS $$
SELECT CASE WHEN NOT a = 0 AND NOT b = 0 THEN a * b / (a + b - (a * b)) ELSE 0 END;
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE OR REPLACE FUNCTION s_max(a numeric, b numeric) RETURNS numeric AS $$
SELECT greatest(a, b);
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE OR REPLACE FUNCTION s_sum(a numeric, b numeric) RETURNS numeric AS $$
SELECT a + b - (a * b);
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE OR REPLACE FUNCTION s_luk(a numeric, b numeric) RETURNS numeric AS $$
SELECT least(a + b, 1);
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE OR REPLACE FUNCTION s_d(a numeric, b numeric) RETURNS numeric AS $$
SELECT CASE WHEN b = 0 THEN a WHEN a = 0 THEN b ELSE 1 END;
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE OR REPLACE FUNCTION s_nm(a numeric, b numeric) RETURNS numeric AS $$
SELECT CASE WHEN a + b < 1 THEN greatest(a, b) ELSE 1 END;
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE OR REPLACE FUNCTION s_h2(a numeric, b numeric) RETURNS numeric AS $$
SELECT (a + b) / (1 + a * b);
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

CREATE AGGREGATE t_min_agg(numeric) (sfunc = t_min, stype = numeric);
CREATE AGGREGATE t_prod_agg(numeric) (sfunc = t_prod, stype = numeric);
CREATE AGGREGATE t_luk_agg(numeric) (sfunc = t_luk, stype = numeric);
CREATE AGGREGATE t_d_agg(numeric) (sfunc = t_d, stype = numeric);
CREATE AGGREGATE t_nm_agg(numeric) (sfunc = t_nm, stype = numeric);
CREATE AGGREGATE t_h0_agg(numeric) (sfunc = t_h0, stype = numeric);
CREATE AGGREGATE s_max_agg(numeric) (sfunc = s_max, stype = numeric);
CREATE AGGREGATE s_sum_agg(numeric) (sfunc = s_sum, stype = numeric);
CREATE AGGREGATE s_luk_agg(numeric) (sfunc = s_luk, stype = numeric);
CREATE AGGREGATE s_d_agg(numeric) (sfunc = s_d, stype = numeric);
CREATE AGGREGATE s_nm_agg(numeric) (sfunc = s_nm, stype = numeric);
CREATE AGGREGATE s_h2_agg(numeric) (sfunc = s_h2, stype = numeric);
