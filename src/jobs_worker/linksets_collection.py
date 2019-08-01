import re
import sys
import time
import locale
import datetime

from psycopg2 import sql, extras

from jobs_worker.match import Match
from jobs_worker.resource import Resource
from jobs_worker.links_to_rdf import convert_link

from common.config_db import db_conn
from common.helpers import get_job_data, get_absolute_property, get_property_sql, \
    get_extended_property_sql, get_extended_property_name, get_unnested_list, hash_string

locale.setlocale(locale.LC_ALL, '')


class LinksetsCollection:
    def __init__(
            self,
            job_id,
            run_match=None,
            sql_only=False,
            resources_only=False,
            matches_only=False,
            return_limit=None
    ):
        self.sql_only = sql_only
        self.return_limit = return_limit or 0
        self.results = []
        self.job_id = job_id
        self.run_match = str(run_match)

        self.__matches = None
        self.__resources = None

        job_data = get_job_data(self.job_id, include_results=False)
        self.data = {
            'resources': job_data['resources'],
            'matches': job_data['matches'],
        }

        self.run_matches = []
        if self.run_match:
            for match in self.matches:
                if match.id == self.run_match:
                    self.run_matches.append(match.name_original)
                    self.run_matches += match.matches_dependencies

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

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
        pass

    def generate_matches(self):
        generated = []

        self.log(self.run_matches)
        while (not self.run_match and len(generated) < len(self.matches)) or (self.run_match and len(generated) < len(self.run_matches)):
            generated_this_cycle = 0
            for match in self.matches:
                if self.run_match and match.name_original not in self.run_matches:
                    continue

                if match.name_original not in generated and not self.get_option('skip', options=match.meta):
                    if not all(m in generated for m in match.matches_dependencies):
                        continue

                    generated.append(match.name_original)
                    generated_this_cycle += 1
                    self.log('Generating linkset %s.' % match.name)
                    result = self.process_sql(self.generate_match_sql(match), match.before_alignment)
                    self.log('Linkset %s generated. %s links created in %s.' % (
                        match.name, locale.format_string('%i', result['affected'], grouping=True), result['duration']))
                    if not self.sql_only:
                        self.add_statistics(match, result)
            if generated_this_cycle == 0:
                raise NameError('Invalid mappings configuration.')

    def generate_resources(self):
        generated = []
        resources = self.resources

        materialize = []
        for match in self.matches:
            if self.run_match and match.name_original not in self.run_matches:
                continue

            for resource in match.resources:
                resource_label = hash_string(resource)
                if resource_label not in materialize:
                    materialize.append(resource_label)

        if not self.has_queued_view or self.sql_only:
            while len(generated) < len(resources):
                for resource in resources:
                    if resource.label not in generated:
                        if resource.label in materialize:
                            self.log('Generating collection %s.' % resource.label)
                            result = self.process_sql(self.generate_resource_sql(resource))
                            self.log('Collection %s generated. Inserted %s records in %s' % (
                                resource.label,
                                locale.format_string('%i', result['affected'], grouping=True),
                                result['duration'],
                            ))
                            if not self.sql_only:
                                self.add_statistics(resource, result)
                        generated.append(resource.label)

    @staticmethod
    def log(message):
        print(message, file=sys.stderr)

    def process_sql(self, composed, inject=None):
        query_starting_time = time.time()

        schema_name_sql = sql.Identifier('job_' + self.job_id)
        composed = sql.Composed([
            sql.SQL('CREATE SCHEMA IF NOT EXISTS {};\n').format(schema_name_sql),
            sql.SQL('SET SEARCH_PATH TO "$user", {}, public;\n').format(schema_name_sql),
            composed,
        ])

        processed_count = 0
        affected_count = 0
        with db_conn() as conn:
            sql_string = composed.as_string(conn)
            inject = inject.as_string(conn) if inject else ''

            with open('%s.sql' % self.job_id, 'a') as sql_file:
                sql_file.write(sql_string)

            if self.sql_only:
                print(sql_string)
            else:
                for statement in sql_string.split(';\n'):
                    statement = statement.strip()

                    if statement.startswith('--'):
                        continue

                    if re.search(r'\S', statement):
                        if re.match(r'^\s*SELECT', statement) and not re.search(r'set_config\(', statement):
                            continue
                            with conn.cursor(cursor_factory=extras.DictCursor, name='cursor') as named_cur:
                                self.log('Converting linkset to RDF.')
                                named_cur.execute(statement)
                                for record in named_cur:
                                    if self.return_limit > 0:
                                        self.results.append(record)
                                        self.return_limit -= 1

                                    print(convert_link(record))
                                    processed_count += 1
                                    if processed_count % 100000 == 0:
                                        self.log('%s links converted.' % locale.format_string('%i', processed_count, grouping=True))
                            conn.commit()
                            self.log('Linkset converted, %s links total.' % locale.format_string('%i', processed_count, grouping=True))
                        else:
                            with conn.cursor() as cur:
                                if inject:
                                    cur.execute(inject)
                                    conn.commit()
                                cur.execute(statement)
                                conn.commit()
                                if cur.rowcount > 0:
                                    affected_count += cur.rowcount

            return {'processed': processed_count, 'affected': affected_count,
                    'duration': str(datetime.timedelta(seconds=time.time() - query_starting_time))}

    def get_join_sql(self, resource):
        joins = []
        property_join_added = []

        matching_fields = resource.matching_fields
        self.get_matching_fields_joins_sql(resource, matching_fields, property_join_added, joins)

        for relation in resource.related:
            self.r_get_join_sql(resource.label, relation, matching_fields, property_join_added, joins)

        return sql.Composed(joins)

    def get_matching_fields_joins_sql(self, resource, matching_fields, property_join_added, joins):
        for property_field in matching_fields:
            prop_resource = self.get_resource_by_label(property_field.resource_label)
            column_info = prop_resource.collection.table_data['columns'][property_field.prop_label]

            if property_field.resource_label == resource.label and column_info['LIST'] \
                    and property_field.absolute_property not in property_join_added:
                property_join_added.append(property_field.absolute_property)

                joins.append(sql.SQL("""
                LEFT JOIN jsonb_array_elements_text({table_name}.{column_name}) 
                AS {column_name_expanded} ON true""").format(
                    table_name=sql.Identifier(property_field.resource_label),
                    column_name=sql.Identifier(property_field.prop_label),
                    column_name_expanded=sql.Identifier(get_extended_property_name(property_field.absolute_property)),
                ))

        return joins

    def r_get_join_sql(self, parent_resource, relation, matching_fields, property_join_added, joins):
        if isinstance(relation, list):
            for sub_relation in relation:
                joins = self.r_get_join_sql(parent_resource, sub_relation, matching_fields, property_join_added, joins)
            return joins

        parent = self.get_resource_by_label(parent_resource)
        resource = self.get_resource_by_label(hash_string(relation['resource']))
        column_label = hash_string(relation['local_property'][0])
        local_column_info = parent.collection.table_data['columns'][column_label]

        if local_column_info['LIST'] and [parent_resource, column_label] not in property_join_added:
            property_join_added.append([parent_resource, column_label])

            joins.append(sql.SQL("""
                LEFT JOIN jsonb_array_elements_text({table_name}.{column_name}) 
                AS {column_name_expanded} ON true""").format(
                table_name=sql.Identifier(parent_resource),
                column_name=sql.Identifier(column_label),
                column_name_expanded=sql.Identifier(get_extended_property_name([parent_resource, column_label])),
            ))

        lhs = get_extended_property_sql(get_absolute_property(relation['local_property'], parent_resource)) \
            if local_column_info['LIST'] \
            else get_property_sql(get_absolute_property(relation['local_property'], parent_resource))

        rhs = get_property_sql(get_absolute_property(relation['remote_property'], hash_string(relation['resource'])))

        extra_filter = resource.filter_sql
        if extra_filter != sql.SQL(''):
            extra_filter = self.replace_sql_variables(extra_filter)
            extra_filter = sql.SQL('\nAND ({resource_filter})').format(resource_filter=extra_filter)

        joins.append(sql.SQL('\nLEFT JOIN {resource_view} AS {alias}\nON {lhs} = {rhs}{extra_filter}').format(
            resource_view=sql.Identifier(resource.collection.table_name),
            alias=sql.Identifier(hash_string(relation['resource'])),
            lhs=lhs, rhs=rhs,
            extra_filter=extra_filter,
        ))

        for relation in resource.related:
            joins = self.r_get_join_sql(resource.label, relation, matching_fields, property_join_added, joins)

        self.get_matching_fields_joins_sql(resource, matching_fields, property_join_added, joins)

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
    #         match_sql = sql.SQL("""
    # DROP SEQUENCE IF EXISTS {sequence_name} CASCADE;
    # CREATE SEQUENCE {sequence_name} MINVALUE 0 START 0;
    #
    # DROP MATERIALIZED VIEW IF EXISTS source CASCADE;
    # CREATE MATERIALIZED VIEW source AS {source};
    # ANALYZE source;
    # CREATE INDEX ON source (uri);
    #
    # DROP MATERIALIZED VIEW IF EXISTS target CASCADE;
    # CREATE MATERIALIZED VIEW target AS {target};
    # ANALYZE target;
    # CREATE INDEX ON target (uri);
    #
    # DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;
    # CREATE MATERIALIZED VIEW {view_name} AS
    # SELECT source.uri AS source_uri,
    #        target.uri AS target_uri,
    #        {fields}
    # FROM source
    # JOIN target
    # ON (source.collection != target.collection OR source.uri > target.uri) AND nextval({sequence_name}) != 0
    # AND ({conditions});
    #
    # SELECT * FROM {view_name};
    # """).format(
    #             fields=match.similarity_fields_sql,
    #             source=match.source_sql,
    #             target=match.target_sql,
    #             view_name=sql.Identifier(match.name),
    #             sequence_name=sql.Identifier(match.name + '_count'),
    #             conditions=match.conditions_sql,
    #         )
    #
    #         match_sql = match.index_sql + match_sql

        match_sql = sql.SQL("""
SELECT source.uri AS source_uri,
       target.uri AS target_uri,
       {fields}
FROM ({source}) AS source
JOIN ({target}) AS target
  ON (source.collection != target.collection OR source.uri > target.uri) AND ({conditions}) and nextval({sequence_name}) != 0;
"""
                            )\
            .format(
                fields=match.similarity_fields_sql,
                source=match.source_sql,
                target=match.target_sql,
                conditions=match.conditions_sql,
                sequence_name=sql.Literal(match.name + '_count'),
        )

        match_sql = (sql.SQL("""
DROP SEQUENCE IF EXISTS {sequence_name} CASCADE;
CREATE SEQUENCE {sequence_name} MINVALUE 0 START 0;
-- DROP MATERIALIZED VIEW IF EXISTS source CASCADE;
-- CREATE MATERIALIZED VIEW source AS {{source}};
-- ANALYZE source;
-- CREATE INDEX ON source (uri);
-- DROP MATERIALIZED VIEW IF EXISTS target CASCADE;
-- CREATE MATERIALIZED VIEW target AS {{target}};
-- ANALYZE target;
-- CREATE INDEX ON target (uri);
DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;
CREATE MATERIALIZED VIEW {view_name} AS""").format(
                source=match.source_sql,
                target=match.target_sql,
                view_name=sql.Identifier(match.name),
                sequence_name=sql.Identifier(match.name + '_count'),
            )
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
ANALYZE {view_name};
"""
                               )\
            .format(
                view_name=sql.Identifier(resource.label),
                sub_query=self.generate_resource_sub_query_sql(resource)
        )

        return sql_composed

    def generate_resource_sub_query_sql(self, resource):
        matching_fields = resource.matching_fields_sql
        joins = self.get_join_sql(resource)

        pre = sql.SQL('SELECT * FROM (') if resource.limit > -1 else sql.SQL('')

        return sql.SQL("""
{pre}SELECT DISTINCT {matching_fields}
FROM {table_name} AS {alias}{joins}{wheres}
ORDER BY uri{limit}
"""
                       )\
            .format(
                pre=pre,
                matching_fields=matching_fields,
                table_name=sql.Identifier(resource.collection.table_name),
                alias=sql.Identifier(resource.label),
                joins=joins,
                wheres=self.replace_sql_variables(resource.where_sql),
                limit=resource.limit_sql,
        )

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
                sql_part = sql.Identifier(self.get_resource_by_label(resource_label).collection.table_name)

            relation_reg_match = re.search(r'(.+)__(.+)__relation__(.+)', sql_part_string)
            if relation_reg_match:
                resource = self.get_resource_by_label(relation_reg_match[1])
                for relation in get_unnested_list(resource.related):
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

    def run(self):
        open('%s.sql' % self.job_id, 'w').close()

        # self.updateJobData({
        #     'status': 'Processing',
        #     'processing_at': str(datetime.datetime.now()),
        # })

        # try:
        if not self.matches_only:
            self.generate_resources()
        if not self.resources_only and (not self.has_queued_view or self.sql_only):
            self.generate_matches()
        # except:
            # self.updateJobData({'status': 'Error'})
            # raise
        # else:
            # self.updateJobData({'status': 'Finished', 'finished_at': str(datetime.datetime.now())})

        return self
