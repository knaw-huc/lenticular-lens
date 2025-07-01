from psycopg import sql


def write_data_helper(db_conn, cursor, next_cursor, table_name, rows_count, total_insert, results):
    with db_conn.cursor() as cur:
        cur.execute('SET search_path TO "$user", entity_types_data, public; '
                    'LOCK TABLE entity_types IN ACCESS EXCLUSIVE MODE;')

        # Check if the data we have is still the data that is expected to be inserted
        if cursor:
            cur.execute('SELECT 1 FROM entity_types WHERE "table_name" = %s AND "cursor" = %s',
                        (table_name, str(cursor)))
        else:
            cur.execute('''
                SELECT 1
                FROM entity_types
                WHERE "table_name" = %s AND "cursor" IS NULL 
                  AND (update_finish_time IS NULL OR update_finish_time < update_start_time)
            ''', (table_name,))

        if cur.fetchone() != (1,):
            raise Exception('This is weird... '
                            'Someone else updated the job for table %s '
                            'while I was fetching data.' % table_name)

        cur.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table_name)))
        table_rows = cur.fetchone()[0]

        if table_rows != rows_count + total_insert:
            raise Exception('Table %s has %i rows, expected %i. Quitting job.'
                            % (table_name, table_rows, rows_count + total_insert))

        if len(results) > 0:
            with cur.copy(sql.SQL('COPY {} ({}) FROM STDIN').format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join([sql.Identifier(column) for column in results[0].keys()])
            )) as copy:
                for result in results:
                    copy.write_row(list(result.values()))

            total_insert += len(results)
            cur.execute('''
                UPDATE entity_types
                SET last_push_time = now(), "cursor" = %s, rows_count = %s
                WHERE "table_name" = %s
            ''', (str(next_cursor), table_rows + len(results), table_name))

        db_conn.commit()

        return total_insert
