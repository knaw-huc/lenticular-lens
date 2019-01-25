from links_to_rdf import convert_link
import datetime
from config_db import db_conn
from helpers import get_absolute_property, get_job_data, get_property_sql, hash_string, update_job_data
import jstyleson
from match import Match
from psycopg2 import extras
from psycopg2 import sql
import re
from resource import Resource
import time


class LinksetsCollection:
    sql_only = False

    def __init__(self, resources_filename, matches_filename, sql_only=False, resources_only=False, matches_only=False, return_limit=None):
        self.sql_only = sql_only
        self.resources_only = resources_only
        self.matches_only = matches_only
        self.return_limit = return_limit or 0
        self.results = []
        self.job_id = hash_string(resources_filename.split('/')[-1] + matches_filename.split('/')[-1])
        self.job_data = get_job_data(self.job_id)

        self.__matches = None
        self.__resources = None

        self.data = {
            'resources': self.get_json_config(resources_filename),
            'matches': self.get_json_config(matches_filename),
        }

        if not self.sql_only:
            datetime_string = str(datetime.datetime.now())
            # self.output_file = gzip.open('scripted_matching/output/%s_output.nq.gz' % datetime_string, 'wb')
            self.statistics_file = open('rdf/%s_statistics.txt' % datetime_string, 'w')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.sql_only:
            # self.output_file.close()
            self.statistics_file.close()
            # if exc_type:
            #     self.updateJobData({'status': 'Error1', 'mappings_form_data': '{}'})

    def __del__(self):
        pass

    @property
    def has_queued_view(self):
        for resource in self.resources:
            if resource.view_queued:
                return True

        return False

    @property
    def matches(self):
        if not self.__matches:
            self.__matches = list(map(Match, self.data['matches']))
        return self.__matches

    @property
    def resources(self):
        if not self.__resources:
            self.__resources = list(map(lambda resource: Resource(resource, self), self.data['resources']))
        return self.__resources

    def add_statistics(self, for_object, statistics):
        if isinstance(for_object, Match):
            self.statistics_file.write('Processing alignment mapping "%s" resulted in %i matches in %s.\n' %
                                       (for_object.name, statistics['processed'], statistics['duration']))
        elif isinstance(for_object, Resource):
            self.statistics_file.write('Processing collection "%s" affected %i rows in %s.\n' %
                                       (for_object.label, statistics['affected'], statistics['duration']))

        self.statistics_file.write('')

    def generate_matches(self):
        for match in self.matches:
            if not self.get_option('skip', options=match.meta):
                result = self.process_sql(self.generate_match_sql(match))
                if not self.sql_only:
                    self.add_statistics(match, result)

    def generate_resources(self):
        generated = []
        resources = self.resources

        materialize = []
        for match in self.matches:
            for resource in match.resources:
                resource_label = hash_string(resource['resource'])
                if resource_label not in materialize:
                    materialize.append(resource_label)

        if not self.has_queued_view:
            while len(generated) < len(resources):
                for resource in resources:
                    if resource.label not in generated:
                        if resource.label in materialize:
                            result = self.process_sql(self.generate_resource_sql(resource))
                            if not self.sql_only:
                                self.add_statistics(resource, result)
                        generated.append(resource.label)

    def process_sql(self, composed):
        query_starting_time = time.time()

        schema_name_sql = sql.Identifier('job_' + self.job_id)
        composed = sql.Composed([
            sql.SQL('CREATE SCHEMA IF NOT EXISTS {};\n').format(schema_name_sql),
            sql.SQL('SET SEARCH_PATH TO "$user", {}, public;\n').format(schema_name_sql),
            composed,
        ])
        conn = db_conn()

        sql_string = composed.as_string(conn)

        if self.sql_only:
            print(composed.as_string(conn))
        else:
            cur = conn.cursor()
            named_cur = conn.cursor(cursor_factory=extras.DictCursor, name='cursor')

            processed_count = 0
            affected_count = 0
            for statement in sql_string.split(';'):
                if re.search(r'\S', statement):
                    if re.match(r'^\s*SELECT', statement) and not re.search(r'set_config\(', statement):
                        named_cur.execute(statement)
                        for record in named_cur:
                            if self.return_limit > 0:
                                self.results.append(record)
                                self.return_limit -= 1

                            print(convert_link(record))
                            processed_count += 1
                    else:
                        cur.execute(statement)
                        if cur.rowcount > 0:
                            affected_count += cur.rowcount

            conn.commit()
            conn.close()

            return {'processed': processed_count, 'affected': affected_count,
                    'duration': str(datetime.timedelta(seconds=time.time() - query_starting_time))}

    def get_join_sql(self, resource):
        joins = []

        for relation in resource.related:
            joins = self.r_get_join_sql(resource.label, relation, joins)

        return sql.Composed(joins)

    def r_get_join_sql(self, parent_resource, relation, joins, left_join=False):
        if isinstance(relation, list):
            left_join = True
            for sub_relation in relation:
                joins = self.r_get_join_sql(parent_resource, sub_relation, joins, left_join)
            return joins

        resource = self.get_resource_by_label(hash_string(relation['resource']))

        left = 'LEFT ' if left_join else ''

        extra_filter = resource.filter_sql
        if extra_filter != sql.SQL(''):
            extra_filter = self.replace_sql_variables(extra_filter)
            extra_filter = sql.SQL('\nAND ({resource_filter})').format(resource_filter=extra_filter)

        joins.append(sql.SQL('\n{left}JOIN {resource_view} AS {alias}\nON {lhs} = {rhs}{extra_filter}')
                        .format(
                            left=sql.SQL(left),
                            resource_view=sql.Identifier(resource.cached_view),
                            alias=sql.Identifier(hash_string(relation['resource'])),
                            lhs=get_property_sql(get_absolute_property(relation['local_property'], parent_resource)),
                            rhs=get_property_sql(get_absolute_property(relation['remote_property'], hash_string(relation['resource']))),
                            extra_filter=extra_filter,
        ))

        for relation in resource.related:
            joins = self.r_get_join_sql(resource.label, relation, joins)

        return joins

    def get_resource_by_label(self, label):
        for resource in self.resources:
            if resource.label == label:
                return resource

        return None

    @staticmethod
    def related_labels_in(related_list, check_list):
        for related in related_list:
            if isinstance(related, list):
                for sub_related in related:
                    if sub_related['resource'] not in check_list:
                        return False
            elif related['resource'] not in check_list:
                return False

        return True

    def generate_match_sql(self, match):
        match_sql = sql.SQL("""
SELECT source.uri AS source_uri,
       target.uri AS target_uri,
       {fields}
FROM ({source}) AS source
JOIN ({target}) AS target
  ON {conditions};
"""
                            )\
            .format(
                fields=match.similarity_fields_sql,
                source=match.source_sql,
                target=match.target_sql,
                conditions=match.conditions_sql,
        )

        if match.materialize:
            match_sql = (sql.SQL("""
DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;
CREATE MATERIALIZED VIEW {view_name} AS""").format(view_name=sql.Identifier(match.name))
                         + match_sql + sql.SQL("""
SELECT * FROM {view_name};
"""
                                               ).format(view_name=sql.Identifier(match.name)))

        match_sql = match.index_sql + match_sql

        return match_sql

    def generate_resource_sql(self, resource):
        sql_composed = sql.SQL("""
DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;
CREATE MATERIALIZED VIEW {view_name} AS{sub_query};
"""
                               )\
            .format(
                view_name=sql.Identifier(resource.label),
                sub_query=self.generate_resource_sub_query_sql(resource)
        )

        return sql_composed

    def generate_resource_sql_for_join(self, resource):
        return self.generate_resource_sub_query_sql(resource, matching_fields=sql.SQL('*'), joins=sql.SQL(''))

    def generate_resource_sub_query_sql(self, resource, matching_fields=None, joins=None):
        if matching_fields is None:
            matching_fields = resource.matching_fields_sql

        if joins is None:
            joins = self.get_join_sql(resource)

        return sql.SQL("""
SELECT {matching_fields}
FROM {table_name} AS {alias}{joins}{wheres}{group_by}
"""
                       )\
            .format(
                matching_fields=matching_fields,
                table_name=sql.Identifier(resource.cached_view),
                alias=sql.Identifier(resource.label),
                joins=joins,
                wheres=self.replace_sql_variables(resource.where_sql),
                group_by=resource.group_by_sql,
        )

    def get_json_config(self, filename=None):
        if filename is None:
            filename = self.filename

        json_file = open(filename, 'r')
        json_config = jstyleson.load(json_file)
        json_file.close()

        return json_config

    def get_option(self, option, default=False, options=None):
        if options is None:
            options = self.data['options']

        return options[option] if option in options else default

    def replace_sql_variables(self, sql_template):
        return self.r_replace_sql_variables(sql_template)

    def r_replace_sql_variables(self, sql_part):
        if isinstance(sql_part, sql.Composed):
            sql_parts = []
            for sub_sql_part in sql_part:
                sql_parts.append(self.r_replace_sql_variables(sub_sql_part))

            return sql.Composed(sql_parts)

        if isinstance(sql_part, sql.Identifier):
            sql_part_string = sql_part.string

            if sql_part_string.endswith('__original'):
                resource_label = re.search(r'.*(?=__original$)', sql_part_string)[0]
                sql_part = sql.Identifier(self.get_resource_by_label(resource_label).cached_view)

            relation_reg_match = re.search(r'(.+)__(.+)__relation__(.+)', sql_part_string)
            if relation_reg_match:
                resource = self.get_resource_by_label(relation_reg_match[1])
                for relation in resource.related:
                    if relation['resource'] == relation_reg_match[2]:
                        break

                related_property_name = relation_reg_match[3]
                property_with_index = re.search(r'(.+)__([0-9]+)', related_property_name)
                if property_with_index:
                    related_property_name = property_with_index[1]
                    property_index = property_with_index[2]
                if related_property_name == 'local_property':
                    sql_part = get_absolute_property(relation[related_property_name], relation_reg_match[1])
                elif related_property_name == 'remote_property':
                    sql_part = get_absolute_property(relation[related_property_name], relation_reg_match[2])
                else:
                    sql_part = sql.Literal(relation[related_property_name])

                if property_with_index:
                    sql_part = sql.Identifier(sql_part[int(property_index[0])])

                if isinstance(sql_part, list):
                    sql_part = get_property_sql(sql_part)

        return sql_part

    def updateJobData(self, update_data):
        self.job_data = {**self.job_data, **update_data}

        if not self.sql_only:
            update_job_data(self.job_id, update_data)

    def run(self):
        # self.updateJobData({
        #     'status': 'Processing',
        #     'processing_at': str(datetime.datetime.now()),
        # })

        # try:
        if not self.matches_only:
            self.generate_resources()
        if not self.resources_only and not self.has_queued_view:
            self.generate_matches()
        # except:
            # self.updateJobData({'status': 'Error'})
            # raise
        # else:
            # self.updateJobData({'status': 'Finished', 'finished_at': str(datetime.datetime.now())})

        return self
