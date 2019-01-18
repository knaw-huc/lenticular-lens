from config_db import db_conn
import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql
from helpers import get_job_data, hash_string, update_job_data
from datasets_config import DatasetsConfig
import pathlib
import os


class S(SimpleHTTPRequestHandler):
    def _set_headers(self, content_type=None):
        if not content_type:
            content_type = 'application/json'

        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')

        if content_type == 'application/json':
            self.end_headers()

    def do_GET(self):
        self.directory = '/web'

        path = self.path.strip('/')

        if path == '':
            self.path = 'index.html'

        if path == 'datasets':
            self._set_headers()
            response = json.dumps(DatasetsConfig().data)
        elif path.startswith('job/'):
            path_parts = path.split('/')
            job_id = path_parts[1]

            if len(path_parts) > 2 and path_parts[2] == 'result':
                if self.headers['Accept'] == 'application/json':
                    self._set_headers()
                    mapping_name = path_parts[3]
                    view_name = hash_string(mapping_name)
                    count_query = psycopg2_sql.SQL('SELECT count(*) FROM {schema}.{view}').format(
                        schema=psycopg2_sql.Identifier('job_' + job_id),
                        view=psycopg2_sql.Identifier(view_name)
                    )
                    rows_query = psycopg2_sql.SQL('SELECT * FROM {schema}.{view} LIMIT 100').format(
                        schema=psycopg2_sql.Identifier('job_' + job_id),
                        view=psycopg2_sql.Identifier(view_name)
                    )

                    with db_conn() as conn:
                        with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
                            cur.execute(count_query)
                            rows_count = cur.fetchone()['count']
                            cur.execute(rows_query)
                            rows = cur.fetchall()
                            response = json.dumps({
                                'mapping_name': mapping_name,
                                'rows': rows,
                                'rows_total': rows_count,
                            })
                else:
                    self.path = 'index.html'
                    self._set_headers('text/html')
                    return super().do_GET()
            else:
                self._set_headers()
                response = json.dumps(get_job_data(job_id), default=str)
        else:
            self._set_headers('text/html')
            return super().do_GET()

        self.wfile.write(response.encode('utf-8'))

    def do_POST(self):
        path = self.path.strip('/')

        if path == 'handle_json_upload':
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))

            resources_json = json.dumps(post_data['resources'], indent=2)
            resources_filename = './generated_json/resources_' + hash_string(resources_json) + '.json'

            matches_json = json.dumps(post_data['matches'], indent=2)
            matches_filename = './generated_json/matches_' + hash_string(matches_json) + '.json'

            job_id = hash_string(resources_filename.split('/')[-1] + matches_filename.split('/')[-1])

            response = json.dumps({'job_id': job_id})

            if not get_job_data(job_id):
                json_file = open(resources_filename, 'w')
                json_file.write(resources_json)
                json_file.close()

                json_file = open(matches_filename, 'w')
                json_file.write(matches_json)
                json_file.close()

                job_data = {
                    'resources_form_data': json.dumps(post_data['resources_original']),
                    'mappings_form_data': json.dumps(post_data['matches_original']),
                    'resources_filename': resources_filename,
                    'mappings_filename': matches_filename,
                    'status': 'Requested',
                    'requested_at': str(datetime.datetime.now()),
                }

                update_job_data(job_id, job_data)
        else:
            self.send_response(404)
            self.end_headers()
            return

        self._set_headers()
        self.wfile.write(response.encode('utf-8'))


if __name__ == '__main__':
    pathlib.Path('generated_json').mkdir(exist_ok=True)

    HTTPServer(('', 8000), S).serve_forever()
