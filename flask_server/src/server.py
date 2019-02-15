from datasets_config import DatasetsConfig
from flask import Flask, jsonify
app = Flask(__name__)


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/datasets')
def datasets():
    return jsonify(DatasetsConfig().data)
