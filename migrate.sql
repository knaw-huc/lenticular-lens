CREATE FUNCTION create_dataset_id(graphql_endpoint text, dataset_id text) RETURNS text AS $$
SELECT md5(concat('timbuctoo__', CASE
    WHEN graphql_endpoint = 'https://repository.goldenagents.org/v5/graphql' THEN 'ga__'
    WHEN graphql_endpoint = 'https://repository.huygens.knaw.nl/v5/graphql' THEN 'huygens__'
    WHEN graphql_endpoint = 'https://data.anansi.clariah.nl/v5/graphql' THEN 'clariah__' END, dataset_id))
$$ LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE;

INSERT INTO datasets (dataset_id, dataset_type, title, description, prefix_mappings)
SELECT DISTINCT create_dataset_id(graphql_endpoint, dataset_id),
                'timbuctoo'::dataset_type, title, description, prefix_mappings
FROM timbuctoo_tables;

INSERT INTO timbuctoo (dataset_id, graphql_endpoint, timbuctoo_id)
SELECT DISTINCT create_dataset_id(graphql_endpoint,dataset_id),
                graphql_endpoint, dataset_id AS timbuctoo_id
FROM timbuctoo_tables;

DROP FUNCTION create_dataset_id;

INSERT INTO entity_types
SELECT t.dataset_id, collection_id, table_name, collection_title,
       tt.collection_uri, collection_shortened_uri, total, rows_count, next_page, 'downloadable' AS status,
       create_time, update_start_time, last_push_time, update_finish_time,
       uri_prefix_mappings, dynamic_uri_prefix_mappings
FROM timbuctoo_tables tt
INNER JOIN timbuctoo t ON tt.dataset_id = t.timbuctoo_id;

INSERT INTO entity_type_properties
SELECT t.dataset_id, collection_id, column_data->>'name', column_name,
       column_data->>'uri',
       column_data->>'shortenedUri',
       ceil(((column_data->>'density')::int * tt.rows_count) / 100),
       ARRAY(SELECT jsonb_array_elements_text(column_data->'referencedCollections') AS ref),
       (column_data->>'isLink')::boolean,
       (column_data->>'isList')::boolean,
       (column_data->>'isInverse')::boolean,
       (column_data->>'isValueType')::boolean
FROM timbuctoo_tables tt
CROSS JOIN jsonb_each(columns) AS columns(column_name, column_data)
INNER JOIN timbuctoo t ON tt.dataset_id = t.timbuctoo_id;

ALTER SCHEMA timbuctoo RENAME TO entity_types_data;
