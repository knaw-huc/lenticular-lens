from config_db import run_query
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

    if has_errors:
        print("\033[1m\033[91mThere were errors while testing the jobs worker\033[0m")
    else:
        print("All jobs worker tests ok")
