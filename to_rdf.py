#!/usr/bin/python
import gc
import psycopg2
import psycopg2.extras
from config_db import config
from mpipe import Pipeline, UnorderedStage


def process_rows(rows):
    rdf = []
    for row in rows:
        rdf.append(process_row(row))

    return rdf


def process_row(row):
    uri = row['uri_1'] + '+' + row['uri_2']
    rdf = '<http://lenticular-lenses.di.huc.knaw.nl/job/1/%s> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://lenticular-lenses.di.huc.knaw.nl/job/1/PersonLink> .\n' % uri
    rdf += '<%s> <http://www.w3.org/2002/07/owl#sameAs> <http://lenticular-lenses.di.huc.knaw.nl/job/1/%s> .\n' % (row['uri_1'], uri)
    rdf += '<%s> <http://www.w3.org/2002/07/owl#sameAs> <http://lenticular-lenses.di.huc.knaw.nl/job/1/%s> .\n' % (row['uri_2'], uri)
    for key, value in row:
        if key.startswith('similarity_'):
            rdf += '<http://lenticular-lenses.di.huc.knaw.nl/job/1/%s> <http://lenticular-lenses.di.huc.knaw.nl/vocab/%s> "%s" .\n' % (uri, key, value)

    return rdf


def export(args):
    rows_per_fetch = 100000
    # read connection parameters
    params = config()

    # create a cursor
    conn = psycopg2.connect(**params)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor, name='cursor')
    cur.itersize = rows_per_fetch

    cur.execute("SELECT * FROM matching.matches_1_ecartico WHERE ctid = ANY (ARRAY(SELECT ('(' || p.i || ',' || s.i || ')')::tid FROM generate_series(0,current_setting('block_size')::int/4) AS s(i), generate_series(%i,%i) p(i)));" % (args["first_page"], args["last_page"]))

    rows = cur.fetchmany(rows_per_fetch)

    w_result = []
    while rows is not None and len(rows) > 0:

        for row in rows:
            w_result.append(process_row(row))

        rows = cur.fetchmany(rows_per_fetch)

    # close the communication with the PostgreSQL
    conn.close()
    gc.collect()

    return w_result


if __name__ == '__main__':
    workers = 5

    params_t = config()
    conn_t = psycopg2.connect(**params_t)
    cur_t = conn_t.cursor()
    cur_t.execute("SELECT pg_relation_size('matching.matches_1_ecartico') / current_setting('block_size')::int;")
    total_pages = cur_t.fetchone()[0]
    conn_t.close()
    pipe = Pipeline(UnorderedStage(export, workers))
    last_page = -1
    records_printed = 0

    while last_page < total_pages - 1:
        first_page = last_page + 1
        last_page += 1000
        if last_page > total_pages - 1:
            last_page = total_pages - 1

        pipe.put({"first_page": first_page, "last_page": last_page})

    pipe.put(None)

    for result in pipe.results():
        for record in result:
            print(record)
            records_printed += 1

        report_file = open('rdf_output/report.txt', 'w+')
        report_file.write(str(records_printed))
        report_file.close()
