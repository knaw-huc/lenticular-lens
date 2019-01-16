#!/home/cedric/PycharmProjects/postgres_reconciliation/venv/bin/python

import datetime
import subprocess
import sys


if __name__ == '__main__':
    with open('scripted_matching/output/%s_output.nq.gz' % str(datetime.datetime.now()), 'wb') as output_file:
        with subprocess.Popen(['./run_json.py'] + sys.argv[1:],
                              stdout=subprocess.PIPE) as converting_process:
            subprocess.Popen(['gzip'], stdin=converting_process.stdout, stdout=output_file)
