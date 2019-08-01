from common.config_db import run_query
import os
import psycopg2
from common.ll.LLData import GENERATED_JSON_DIR

if __name__ == '__main__':
    has_errors = False

    try:
        db_response = run_query("SELECT 1")

        if db_response != (1,):
            raise psycopg2.OperationalError('<span style="color: red;font-weight: bold">Unexpected response "%s"</span>' % str(db_response))
    except psycopg2.DatabaseError as e:
        has_errors = True
        print('<span style="color: red;font-weight: bold">There is a problem with my connection to the database: %s</span>' % str(e))
    else:
        print("Connection to database ok")

    statvfs = os.statvfs(GENERATED_JSON_DIR)
    bytes_available = statvfs.f_frsize * statvfs.f_bavail
    if bytes_available < 10737418240:
        has_errors = True
        space_status = '<span style="color: red;font-weight: bold">LOW</span>'
    else:
        space_status = "ok"
    print("Free space: %s (%i bytes available)" % (space_status, bytes_available))

    try:
        test_file_path = os.path.join(GENERATED_JSON_DIR, 'web_server_write_test')
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        open(test_file_path, 'w').close()
        os.remove(test_file_path)
    except OSError as e:
        has_errors = True
        print('<span style="color: red;font-weight: bold">An error occurred while trying to write a test file: %s</span>' % str(e))
    else:
        print("Writing test file ok")

    if has_errors:
        print('<span style="color: red;font-weight: bold">There were errors while testing the jobs worker</span>')
    else:
        print("All web server tests ok")
