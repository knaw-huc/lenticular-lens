from config_db import db_conn, run_query
from psycopg2 import extras as psycopg2_extras
import psycopg2
import random
import time


if __name__ == '__main__':
    n1 = 0

    while True:
        try:
            with db_conn() as conn:
                print('Looking for new Timbuctoo job...')

                job = None
                while not job:
                    with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                        cur.execute("LOCK TABLE timbuctoo_tables IN ACCESS EXCLUSIVE MODE;")
                        cur.execute("""
                            SELECT *
                            FROM timbuctoo_tables
                            WHERE update_start_time IS NULL
                            OR (
                                (update_finish_time IS NULL OR update_finish_time < update_start_time)
                                AND update_start_time < now() - interval '1 minute'
                                AND (last_push_time IS NULL OR last_push_time < now() - interval '1 minute')
                            )
                            ORDER BY create_time
                            LIMIT 1;""")

                        job = cur.fetchone()
                        n1 = 0

                        if not job:
                            conn.commit()
                            time.sleep(2)

                print('Job for table %s started.' % job['table_name'])

                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE timbuctoo_tables SET update_start_time = now() WHERE "table_name" = %s',
                        (job['table_name'],)
                    )
                conn.commit()
                n1 = 0

                for i in range(5):
                    print("Pretending I'm doing my job...")
                    time.sleep(3)
                    rows_inserted = 100

                    with conn.cursor() as cur:
                        cur.execute(
                            'UPDATE timbuctoo_tables SET last_push_time = now(), rows_count = rows_count + %s WHERE "table_name" = %s',
                            (rows_inserted, job['table_name'])
                        )

                    conn.commit()

                run_query(
                    'UPDATE timbuctoo_tables SET update_finish_time = now() WHERE "table_name" = %s',
                    (job['table_name'],)
                )

                print('Job for table %s finished.' % job['table_name'])

                job = None
                n1 = 0

        except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
            n1 += 1
            print('Database error: %s' % e)
            print('Waiting to retry...')
            time.sleep((2 ** n1) + (random.randint(0, 1000) / 1000))
            print('Retry %i...' % n1)

            continue
