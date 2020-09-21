from psycopg2 import sql, extras
from collections import defaultdict

from ll.data.joins import Joins
from ll.data.property_field import PropertyField

from ll.util.config_db import db_conn, fetch_one
from ll.util.helpers import hasher, hash_string, get_pagination_sql


def get_property_values(query, dict=True):
    results = {}
    for graph_set in query['query_data']:
        graph = graph_set['graph']
        for datatype_set in graph_set['data']:
            entity_type = datatype_set['entity_type']
            query_results = get_property_values_for_query(
                query['queries'][graph][entity_type], query['parameters'], datatype_set['properties'],
                graph=graph, entity_type=entity_type, dict=dict)

            for uri, values in query_results.items():
                uri_values = results.get(uri, [])
                uri_values += values
                results[uri] = uri_values

    return results


def get_property_values_for_query(query, parameters, property_paths, graph=None, entity_type=None, dict=True):
    property_values = defaultdict(list) if dict else []
    with db_conn() as conn, conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
        cur.execute(query, parameters)
        for values in cur:
            prop_and_values = [{
                'dataset': graph if graph else None,
                'entity': entity_type if entity_type else None,
                'property': property_path,
                'values': list(filter(None, values[hasher(property_path)]))
            } for property_path in property_paths]

            if dict:
                property_values[values['uri']] = prop_and_values
            else:
                property_values.append({'uri': values['uri'], 'properties': prop_and_values})

    return property_values


def get_property_values_queries(query_data, uris=None, joins=None):
    condition = None
    if uris:
        condition = sql.SQL('target.uri IN %(uris)s')
        uris = [uri.replace('<', '').replace('>', '')
                if uri.startswith('<') and uri.endswith('>') else uri for uri in uris]

    queries = {}
    for graph_set in query_data:
        entities = {}
        for datatype_set in graph_set['data']:
            table_info = get_table_info(graph_set['graph'], datatype_set['entity_type'])
            if table_info:
                entities[datatype_set['entity_type']] \
                    = create_query_for_properties(graph_set['graph'], 'target',
                                                  table_info['table_name'], table_info['columns'],
                                                  datatype_set['properties'],
                                                  joins=joins, condition=condition)
        queries[graph_set['graph']] = entities

    return {
        'queries': queries,
        'parameters': {'uris': tuple(uris)} if uris else {},
        'query_data': query_data
    }


def create_count_query_for_properties(resource, target, joins=None, condition=None):
    return sql.SQL('''
        SELECT COUNT({parent_resource}.uri) AS total
        FROM {table_name} AS {parent_resource} 
        {joins}
        {condition}
    ''').format(
        parent_resource=sql.Identifier(resource),
        table_name=sql.Identifier(target),
        joins=get_initial_joins(joins).sql,
        condition=sql.SQL('WHERE {}').format(condition) if condition and condition != sql.SQL('') else sql.SQL(''),
    )


def create_query_for_properties(graph, resource, target, columns, property_paths,
                                joins=None, condition=None, invert=False, limit=None, offset=0):
    selection_joins = Joins()
    properties = []
    parent_resource = resource

    for property_path in property_paths:
        property_name = hasher(property_path)
        property_path = property_path if type(property_path) is list else [property_path]

        property = get_property_field(graph, selection_joins, resource, columns, property_path)
        property_sql = sql.SQL('array_agg(DISTINCT {value}) AS {name}').format(
            value=property.sql,
            name=sql.Identifier(property_name))
        properties.append(property_sql)

        if property.is_list:
            selection_joins.add_join(property.left_join, property.extended_prop_label)

    condition_sql = sql.SQL('')
    if condition and condition != sql.SQL(''):
        condition_sql = sql.SQL('WHERE {}').format(condition) if not invert \
            else sql.SQL('WHERE NOT ({})').format(condition)
    elif invert:
        condition_sql = sql.SQL('WHERE 1 != 1')

    return sql.SQL('''
        SELECT {parent_resource}.uri AS uri, {selection}
        FROM {table_name} AS {parent_resource} 
        {selection_joins}
        WHERE {parent_resource}.uri IN (
            SELECT {parent_resource}.uri
            FROM {table_name} AS {parent_resource}
            {joins}
            {condition}
            GROUP BY {parent_resource}.uri
            ORDER BY {parent_resource}.uri ASC {limit_offset}
        )
        GROUP BY {parent_resource}.uri
        ORDER BY {parent_resource}.uri
    ''').format(
        parent_resource=sql.Identifier(parent_resource),
        selection=sql.SQL(', ').join(properties),
        table_name=sql.Identifier(target),
        selection_joins=selection_joins.sql,
        joins=get_initial_joins(joins).sql,
        condition=condition_sql,
        limit_offset=sql.SQL(get_pagination_sql(limit, offset))
    )


def get_initial_joins(initial_join=None):
    joins = Joins()
    if initial_join and isinstance(initial_join, Joins):
        joins.copy_from(initial_join)
    elif initial_join:
        joins.add_join(initial_join, 'initial_join')

    return joins


def get_property_field(graph, joins, cur_resource, cur_columns, property_path):
    property_path_copy = list(property_path)
    while len(property_path_copy) > 1:
        column = property_path_copy.pop(0)
        target_resource = property_path_copy.pop(0)

        next_table_info = get_table_info(graph, target_resource)
        next_resource = hash_string(cur_resource + '_' + target_resource + '_' + column)

        local_property = PropertyField(column, parent_label=cur_resource, columns=cur_columns)
        remote_property = PropertyField('uri', parent_label=next_resource, columns=next_table_info['columns'])

        if local_property.is_list:
            joins.add_join(local_property.left_join, local_property.extended_prop_label)

        lhs = local_property.sql
        rhs = remote_property.sql

        joins.add_join(sql.SQL('LEFT JOIN {target} AS {alias}\nON {lhs} = {rhs}').format(
            target=sql.Identifier(next_table_info['table_name']),
            alias=sql.Identifier(next_resource),
            lhs=lhs, rhs=rhs
        ), next_resource)

        cur_resource = next_resource
        cur_columns = next_table_info['columns']

    return PropertyField(property_path_copy[0], parent_label=cur_resource, columns=cur_columns)


def get_linkset_join_sql(linkset, where_sql=None, limit=None, offset=0):
    limit_offset_sql = get_pagination_sql(limit, offset)

    return sql.SQL('''
        INNER JOIN (
            SELECT DISTINCT nodes.uri
            FROM (
                SELECT links.source_uri, links.target_uri 
                FROM {linkset} AS links
                {where_sql} 
                ORDER BY sort_order ASC {limit_offset}
            ) AS ls, LATERAL (VALUES (ls.source_uri), (ls.target_uri)) AS nodes(uri)
        ) AS linkset ON target.uri = linkset.uri
    ''').format(
        linkset=linkset,
        where_sql=where_sql if where_sql else sql.SQL(''),
        limit_offset=sql.SQL(limit_offset_sql)
    )


def get_linkset_cluster_join_sql(linkset_table_name, limit=None, offset=0, uri_limit=5):
    return sql.SQL('''
        INNER JOIN (
            SELECT nodes.uri, ROW_NUMBER() OVER (PARTITION BY ls.cluster_id) AS cluster_row_number
            FROM {linkset} AS ls
            INNER JOIN (
                SELECT cluster_id
                FROM {linkset}
                CROSS JOIN LATERAL (VALUES (source_uri), (target_uri)) AS nodes(uri)
                GROUP BY cluster_id
                ORDER BY COUNT(DISTINCT nodes.uri) DESC, cluster_id ASC
                {limit_offset}
            ) AS clusters ON ls.cluster_id = clusters.cluster_id
            CROSS JOIN LATERAL (VALUES (source_uri), (target_uri)) AS nodes(uri)
        ) AS linkset 
        ON target.uri = linkset.uri AND linkset.cluster_row_number < {uri_limit}
    ''').format(
        linkset=sql.Identifier(linkset_table_name),
        limit_offset=sql.SQL(get_pagination_sql(limit, offset)),
        uri_limit=sql.Literal(uri_limit)
    )


def get_table_info(dataset_id, collection_id):
    result = fetch_one(
        'SELECT table_name, columns FROM timbuctoo_tables WHERE dataset_id = %s AND collection_id = %s',
        (dataset_id, collection_id)
    )

    return {'table_name': result[0], 'columns': result[1]} if result else result
