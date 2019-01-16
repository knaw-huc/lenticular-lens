DROP TABLE IF EXISTS reconciliation_jobs;
CREATE TABLE reconciliation_jobs (
  job_id text primary key,
  resources_form_data json,
  mappings_form_data json,
  resources_filename text,
  mappings_filename text,
  status text,
  requested_at timestamp,
  processing_at timestamp,
  finished_at timestamp
)