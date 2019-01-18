from config_db import run_query
import os
import psycopg2


if __name__ == '__main__':
    has_errors = False

    try:
        db_response = run_query("SELECT 1")

        if db_response != (1,):
            raise psycopg2.OperationalError('Unexpected response "%s"' % str(db_response))
    except psycopg2.DatabaseError as e:
        has_errors = True
        print("There is a problem with my connection to the database: " + str(e))
    else:
        print("Connection to database ok")

    statvfs = os.statvfs('/output/rdf')
    bytes_available = statvfs.f_frsize * statvfs.f_bavail
    if bytes_available < 10737418240:
        has_errors = True
        space_status = "\033[1m\033[91mLOW"
    else:
        space_status = "ok"
    print("Free space: %s (%i bytes available)\033[0m" % (space_status, bytes_available))

    try:
        test_file_path = '/output/rdf/jobs_worker_write_test'
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        open(test_file_path, 'w').close()
        os.remove(test_file_path)
    except OSError as e:
        has_errors = True
        print("\033[1m\033[91mAn error occurred while trying to write a test file: %s\033[0m" % str(e))
    else:
        print("Writing test file ok")

    if has_errors:
        print("\033[1m\033[91mThere were errors while testing the jobs worker\033[0m")
    else:
        print("All jobs worker tests ok")
