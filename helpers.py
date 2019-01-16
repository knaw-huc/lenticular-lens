import collections
from .config_db import db_conn
from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql
from psycopg2.extensions import AsIs


def get_absolute_property(property_array, parent_label):
    property_array = list(map(hash_string, property_array))

    if len(property_array) == 1:
        property_array.insert(0, parent_label)

    return property_array


def get_property_sql(property_array):
    return psycopg2_sql.SQL('.').join(map(psycopg2_sql.Identifier, property_array))


def is_property_object(value):
    return 'property' in value and len(value) == 1 and isinstance(value['property'], list)


def get_json_from_file(filename):
    import jstyleson

    json_file = open('scripted_matching/' + filename, 'r')
    json_config = jstyleson.load(json_file)
    json_file.close()

    return json_config


def get_string_from_sql(sql):
    conn = db_conn()
    sql_string = sql.as_string(conn)
    conn.close()

    return sql_string


def hash_string(to_hash):
    import hashlib

    return hashlib.md5(to_hash.encode('utf-8')).hexdigest()


def get_job_data(job_id):
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM reconciliation_jobs WHERE job_id = %s', (job_id,))
            return cur.fetchone()


def update_job_data(job_id, job_data):
    with db_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2_extras.DictCursor) as cur:
            cur.execute(psycopg2_sql.SQL("""
            INSERT INTO reconciliation_jobs AS rj (job_id, %s) VALUES %s
                ON CONFLICT (job_id) DO UPDATE
                    SET {} WHERE rj.job_id = %s
                    """).format(psycopg2_sql.SQL(', '.join('%s = EXCLUDED.%s' % (key, key) for key in job_data.keys()))),
                        (
                            AsIs(', '.join(job_data.keys())),
                            tuple([job_id] + list(job_data.values())),
                            job_id
                        ))


class PropertyField:
    def __init__(self, data, parent_label, use_label_for_hash=False):
        self.is_aggregate = False
        self.parent_label = parent_label
        self.use_label_for_hash = use_label_for_hash
        self.__data = data
        self.__hash = None
        self.__sql = None
        self.__sql_string = None
        self.__transformers = None

        if 'property' in self.__data:
            self.__sql = get_property_sql(get_absolute_property(self.__data['property'], self.parent_label))
        elif isinstance(self.__data['value'], collections.Mapping):
            sql_function = SqlFunction(self.__data['value'], parent_label)
            self.is_aggregate = sql_function.is_aggregate
            self.__sql = sql_function.sql
        else:
            self.__sql = psycopg2_sql.Literal(self.__data['value'])

        for transformer in self.transformers[::-1]:
            self.__sql = psycopg2_sql.SQL('%s({})' % transformer).format(self.__sql)

    @property
    def hash(self):
        if not self.__hash:
            hashable = get_string_from_sql(get_property_sql([self.parent_label, self.label]))\
                if self.use_label_for_hash\
                else self.sql_string
            self.__hash = hash_string(hashable)

        return self.__hash

    @property
    def label(self):
        return self.__data['label']

    @property
    def sql(self):
        return self.__sql

    @property
    def sql_string(self):
        if not self.__sql_string:
            self.__sql_string = get_string_from_sql(self.sql)

        return self.__sql_string

    @property
    def transformers(self):
        if not self.__transformers:
            if 'transformers' in self.__data:
                white_list = get_json_from_file("transformers.json")

                self.__transformers = [transformer for transformer in self.__data['transformers'] if transformer in white_list]
                for transformer in self.__data['transformers']:
                    if transformer not in white_list:
                        raise self.TransformerUnknown('Transformer "%s" is not whitelisted.' % transformer)
            else:
                self.__transformers = []

        return self.__transformers

    class TransformerUnknown(ValueError):
        """This means the transformer is not whitelisted"""


class SqlFunction:
    def __init__(self, function_obj, parent_label):
        self.parent_label = parent_label
        for function_name, parameters in function_obj.items():
            self.function_name = function_name
            self.parameters = {}
            if isinstance(parameters, list):
                self.parameters['list_values'] = psycopg2_sql.SQL(', ')\
                    .join([self.get_value_sql(parameter) for parameter in parameters])
            elif isinstance(parameters, collections.Mapping):
                if is_property_object(parameters):
                    self.parameters['parameter'] =\
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
