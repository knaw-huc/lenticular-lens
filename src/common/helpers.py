import collections
from common.config_db import db_conn, execute_query, run_query
import datetime
from hashlib import md5
from os import listdir
from os.path import join, isfile, dirname, realpath
import psycopg2
from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql
from psycopg2.extensions import AsIs
import random
import re
from common.ll.LLData.CSV_Associations import CSV_ASSOCIATIONS_DIR
import time


def hasher(object):
    h = md5()
    h.update(bytes(object.__str__(), encoding='utf-8'))
    return F"H{h.hexdigest()[:15]}"


def file_date():
    today = datetime.date.isoformat(datetime.date.today()).replace('-', '')
    return f"{today}_{re.findall('..:.*', str(datetime.datetime.now()))[0]}"


def table_to_csv(table_name, columns, file):
    table_name = [psycopg2_sql.Identifier(name_part) for name_part in table_name.split('.')]

    with db_conn() as conn, conn.cursor() as cur:
        sql = cur.mogrify(
            psycopg2_sql.SQL("COPY (SELECT {columns} FROM {schema}.{table}) TO STDOUT WITH CSV DELIMITER ','")
                .format(columns=psycopg2_sql.SQL(', ').join(columns), schema=table_name[0], table=table_name[1]))
        cur.copy_expert(sql, file)


def get_absolute_property(property_array, parent_label=None):
    property_array[len(property_array) - 1] = property_array[len(property_array) - 1].lower()
    property_array = list(map(hash_string, property_array))

    if parent_label and len(property_array) == 1:
        property_array.insert(0, parent_label)

    return property_array


def get_property_sql(property_array):
    return psycopg2_sql.SQL('.').join(map(psycopg2_sql.Identifier, property_array))


def get_extended_property_sql(property_array):
    return get_property_sql([get_extended_property_name(property_array), 'value'])


def get_extended_property_name(property_array):
    return hash_string('.'.join(property_array)) + '_extended'


def is_property_object(value):
    return 'property' in value and len(value) == 1 and isinstance(value['property'], list)


def get_json_from_file(filename):
    import jstyleson

    json_file = open(join(dirname(realpath(__file__)), 'json', filename), 'r')
    json_config = jstyleson.load(json_file)
    json_file.close()

    return json_config


def get_string_from_sql(sql):
    conn = db_conn()
    sql_string = sql.as_string(conn)
    conn.close()

    return sql_string


def hash_string(to_hash):
    return md5(to_hash.encode('utf-8')).hexdigest()


def get_unnested_list(nest):
    unnested = []

    for element in nest:
        if isinstance(element, list):
            unnested += get_unnested_list(element)
        else:
            unnested.append(element)

    return unnested


def get_job_data(job_id):
    n = 0
    while True:
        try:
            conn = db_conn()
            with conn:
                with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
                    cur.execute('SELECT * FROM reconciliation_jobs WHERE job_id = %s', (job_id,))
                    job_data = cur.fetchone()
            break
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))

    return job_data


def get_job_alignments(job_id):
    return execute_query({
        'query': "SELECT * FROM alignments WHERE job_id = %s",
        'parameters': (job_id,)
    }, {'cursor_factory': psycopg2_extras.RealDictCursor})


def get_job_clusterings(job_id):
    n = 0
    while True:
        try:
            conn = db_conn()
            with conn:
                with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
                    cur.execute('SELECT * FROM clusterings WHERE job_id = %s', (job_id,))
                    clusterings = cur.fetchall()
            break
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))

    return clusterings


def get_association_files():
    return [f for f in listdir(CSV_ASSOCIATIONS_DIR)
            if isfile(join(CSV_ASSOCIATIONS_DIR, f)) and f.endswith(('.csv', '.csv.gz'))]


def update_alignment_job(job_id, alignment, job_data):
    n = 0
    while True:
        try:
            with db_conn() as conn, conn.cursor() as cur:
                cur.execute(
                    psycopg2_sql.SQL("UPDATE alignments SET ({}) = ROW %s WHERE job_id = %s AND alignment = %s")
                        .format(psycopg2_sql.SQL(', '.join(job_data.keys()))),
                    (tuple(job_data.values()), job_id, alignment))

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
        else:
            break


def update_clustering_job(job_id, alignment, job_data):
    n = 0
    while True:
        try:
            with db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        psycopg2_sql.SQL("UPDATE clusterings SET ({}) = ROW %s WHERE job_id = %s AND alignment = %s")
                            .format(
                            psycopg2_sql.SQL(', '.join(job_data.keys()))),
                        (tuple(job_data.values()), job_id, alignment))

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
        else:
            break


def update_job_data(job_id, job_data):
    n = 0
    while True:
        try:
            with db_conn() as conn:
                with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
                    if run_query('SELECT 1 FROM reconciliation_jobs WHERE job_id = %s', (job_id,)):
                        query = psycopg2_sql.SQL(
                            "UPDATE reconciliation_jobs SET ({}) = ROW %s, updated_at = NOW() WHERE job_id = %s"
                        ).format(psycopg2_sql.SQL(', '.join(job_data.keys())))
                        cur.execute(query, (tuple(job_data.values()), job_id))
                    else:
                        cur.execute(psycopg2_sql.SQL("INSERT INTO reconciliation_jobs (job_id, %s) VALUES %s"),
                                    (AsIs(', '.join(job_data.keys())), tuple([job_id] + list(job_data.values()))))

        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            n += 1
            print('Database error. Retry %i' % n)
            time.sleep((2 ** n) + (random.randint(0, 1000) / 1000))
        else:
            break


class PropertyField:
    def __init__(self, data):
        self.is_aggregate = False
        self.__data = data
        self.__hash = None
        self.__transformers = None

    @property
    def hash(self):
        if not self.__hash:
            self.__hash = hash_string(get_string_from_sql(self.sql(False)))

        return self.__hash

    @property
    def label(self):
        return self.__data['label']

    @property
    def absolute_property(self):
        return get_absolute_property(self.__data['property'])

    @property
    def resource_label(self):
        return self.absolute_property[0]

    @property
    def prop_label(self):
        return self.absolute_property[1]

    @property
    def transformers(self):
        if not self.__transformers:
            if 'transformers' in self.__data:
                white_list = get_json_from_file("transformers.json")

                self.__transformers = [transformer for transformer in self.__data['transformers'] if
                                       transformer in white_list]
                for transformer in self.__data['transformers']:
                    if transformer not in white_list:
                        raise self.TransformerUnknown('Transformer "%s" is not whitelisted.' % transformer)
            else:
                self.__transformers = []

        return self.__transformers

    def sql(self, is_list):
        if 'property' in self.__data:
            sql = get_extended_property_sql(get_absolute_property(self.__data['property'])) \
                if is_list else get_property_sql(get_absolute_property(self.__data['property']))
        elif isinstance(self.__data['value'], collections.Mapping):
            sql_function = SqlFunction(self.__data['value'])
            self.is_aggregate = sql_function.is_aggregate
            sql = sql_function.sql
        else:
            sql = psycopg2_sql.Literal(self.__data['value'])

        for transformer in self.transformers[::-1]:
            sql = psycopg2_sql.SQL('%s({})' % transformer).format(sql)

        return sql

    class TransformerUnknown(ValueError):
        """This means the transformer is not whitelisted"""


class SqlFunction:
    def __init__(self, function_obj, parent_label=None):
        self.parent_label = parent_label
        for function_name, parameters in function_obj.items():
            self.function_name = function_name
            self.parameters = {}
            if isinstance(parameters, list):
                self.parameters['list_values'] = psycopg2_sql.SQL(', ') \
                    .join([self.get_value_sql(parameter) for parameter in parameters])
            elif isinstance(parameters, collections.Mapping):
                if is_property_object(parameters):
                    self.parameters['parameter'] = \
                        get_property_sql(get_absolute_property(parameters['property'], self.parent_label))
                else:
                    for key, value in parameters.items():
                        self.parameters[key] = self.get_value_sql(value)
            else:
                self.parameters['parameter'] = psycopg2_sql.Literal(parameters)

        self.is_aggregate = self.function_name.startswith('AGG_')

        sql_functions = get_json_from_file('sql_functions.json')
        if self.function_name in sql_functions:
            self.sql_template = sql_functions[self.function_name]
        else:
            raise NameError('SQL function %s is not defined' % self.function_name)

    def get_value_sql(self, value):
        if isinstance(value, collections.Mapping):
            if is_property_object(value):
                return get_property_sql(get_absolute_property(value['property'], self.parent_label))

            return SqlFunction(value, self.parent_label).sql

        return psycopg2_sql.Literal(value)

    @property
    def sql(self):
        template = self.sql_template
        sql = psycopg2_sql.SQL(template).format(**self.parameters)

        return sql
