from datasets_config import DatasetsConfig
import datetime
from flask import Flask, jsonify, request
from helpers import get_job_data, hash_string, update_job_data
import json
app = Flask(__name__)


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/datasets')
def datasets():
    return jsonify(DatasetsConfig().data)


@app.route('/handle_json_upload/', methods=['POST'])
def handle_json_upload():
    resources_json = json.dumps(request.json['resources'], indent=2)
    resources_filename = './generated_json/resources_' + hash_string(resources_json) + '.json'

    matches_json = json.dumps(request.json['matches'], indent=2)
    matches_filename = './generated_json/matches_' + hash_string(matches_json) + '.json'

    job_id = hash_string(resources_filename.split('/')[-1] + matches_filename.split('/')[-1])

    response = {'job_id': job_id}

    if not get_job_data(job_id):
        json_file = open(resources_filename, 'w')
        json_file.write(resources_json)
        json_file.close()

        json_file = open(matches_filename, 'w')
        json_file.write(matches_json)
        json_file.close()

        job_data = {
            'resources_form_data': json.dumps(request.json['resources_original']),
            'mappings_form_data': json.dumps(request.json['matches_original']),
            'resources_filename': resources_filename,
            'mappings_filename': matches_filename,
            'status': 'Requested',
            'requested_at': datetime.datetime.now(),
        }

        update_job_data(job_id, job_data)

    return jsonify(response)


@app.route('/job/<job_id>')
def job_data(job_id):
    return jsonify(get_job_data(job_id))
