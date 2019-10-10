from common.config_db import run_query
import psycopg2

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

    if has_errors:
        print('<span style="color: red;font-weight: bold">There were errors while testing the jobs worker</span>')
    else:
        print("All web server tests ok")
