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
  status text,
  requested_at timestamp,
  processing_at timestamp,
  finished_at timestamp,
  UNIQUE (job_title, job_description)
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