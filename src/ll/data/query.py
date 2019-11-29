from collections import defaultdict
from psycopg2 import sql as psycopg2_sql

from ll.job.property_field import PropertyField
from ll.util.helpers import hash_string, get_pagination_sql
from ll.util.config_db import execute_query, fetch_one


def get_property_values(targets, resources=None, cluster_id=None,
                        linkset_table_name=None, clusters_table_name=None, limit=None, offset=0):
    query = get_property_values_query(targets, uris=resources, cluster_id=cluster_id,
                                      linkset_table_name=linkset_table_name, clusters_table_name=clusters_table_name,
                                      limit=limit, offset=offset)
    result = execute_query(query)

    response = defaultdict(list)
    res_idx = result[0].index('resource')
    for row in result[1:]:
        row_dict = {label: row[idx] for idx, label in enumerate(result[0])}
        del row_dict['resource']

        if row_dict['value']:
            targets = response[row[res_idx]]
            matching_targets = [target for target in targets
                                if target['dataset'] == row_dict['dataset']
                                and target['property'] == row_dict['property']]
            if matching_targets:
                matching_targets[0]['values'].append(row_dict['value'])
            else:
                row_dict['values'] = [row_dict['value']]
                del row_dict['value']
                targets.append(row_dict)

    return response


def get_property_values_query(query_data, uris=None, cluster_id=None,
                              linkset_table_name=None, clusters_table_name=None, limit=None, offset=0):
    if uris:
        uris = [uri.replace('<', '').replace('>', '')
                if uri.startswith('<') and uri.endswith('>') else uri for uri in uris]

    sqls = []
    for graph_set in query_data:
        for datatype_set in graph_set['data']:
            table_info = get_table_info(graph_set['graph'], datatype_set['entity_type'])
            if table_info:
                for property_path in datatype_set['properties']:
                    sql = create_query_for(table_info, graph_set['graph'], property_path,
                                           cluster_id=cluster_id, linkset_table_name=linkset_table_name,
                                           clusters_table_name=clusters_table_name, limit=limit, offset=offset)
                    sqls.append(sql)

    return {
        'query': psycopg2_sql.SQL('\nUNION ALL\n').join(sqls),
        'header': ('resource', 'dataset', 'property', 'value'),
        'parameters': {'uris': tuple(uris)} if uris else {}
    }


def create_query_for(table_info, graph, property_path, cluster_id=None,
                     linkset_table_name=None, clusters_table_name=None, limit=None, offset=0):
    table_name = table_info['table_name']
    property_name = property_path
    resource = 'target'
    columns = table_info['columns']
    joins = []
    if type(property_path) is list:
        property_sql_info = get_property_sql_info(graph, resource, columns, list(property_path))
        property_name = property_sql_info['property_name']
        resource = property_sql_info['resource']
        columns = property_sql_info['columns']
        joins = property_sql_info['joins']

    property = PropertyField(property_name, parent_label=resource, columns=columns)
    where_sql = psycopg2_sql.SQL('WHERE target.uri IN %(uris)s') if not linkset_table_name else psycopg2_sql.SQL('')

    joins.append(property.left_join)
    if linkset_table_name and clusters_table_name:
        linkset_cluster_join_sql = get_linkset_cluster_join_sql(linkset_table_name, clusters_table_name, limit, offset)
        joins.append(linkset_cluster_join_sql)
    elif linkset_table_name:
        linkset_join_sql = get_linkset_join_sql(linkset_table_name, cluster_id, limit, offset)
        joins.append(linkset_join_sql)

    return psycopg2_sql.SQL('''
        SELECT DISTINCT target.uri AS table_name, {graph_name} AS dataset, {property} AS property, {value} AS value
        FROM {table_name} AS target 
        {joins}
        {where_sql}
    ''').format(
        graph_name=psycopg2_sql.Literal(graph),
        property=psycopg2_sql.Literal(property_name),
        value=property.sql,
        table_name=psycopg2_sql.Identifier(table_name),
        joins=psycopg2_sql.Composed(joins),
        where_sql=where_sql
    )


def get_property_sql_info(graph, cur_resource, cur_columns, property_path):
    joins = []

    while len(property_path) > 1:
        column = property_path.pop(0)
        target_resource = property_path.pop(0)

        next_table_info = get_table_info(graph, target_resource)
        next_resource = hash_string(cur_resource + '_' + target_resource + '_' + column)

        local_property = PropertyField(column, parent_label=cur_resource, columns=cur_columns)
        remote_property = PropertyField('uri', parent_label=next_resource, columns=next_table_info['columns'])

        if local_property.is_list:
            joins.append(local_property.left_join)

        lhs = local_property.sql
        rhs = remote_property.sql

        joins.append(psycopg2_sql.SQL('\nLEFT JOIN {target} AS {alias}\nON {lhs} = {rhs}').format(
            target=psycopg2_sql.Identifier(next_table_info['table_name']),
            alias=psycopg2_sql.Identifier(next_resource),
            lhs=lhs, rhs=rhs
        ))

        cur_resource = next_resource
        cur_columns = next_table_info['columns']

    return {'property_name': property_path[0], 'resource': cur_resource, 'columns': cur_columns, 'joins': joins}


def get_linkset_join_sql(linkset_table_name, cluster_id=None, limit=None, offset=0):
    limit_offset_sql = get_pagination_sql(limit, offset)

    cluster_criteria = psycopg2_sql.SQL('WHERE cluster_id = {}').format(psycopg2_sql.Literal(cluster_id)) \
        if cluster_id else psycopg2_sql.SQL('')

    linkset = psycopg2_sql.SQL('''(
        (SELECT source_uri AS uri FROM {linkset} {cluster_criteria} {limit_offset})
        UNION
        (SELECT target_uri AS uri FROM {linkset} {cluster_criteria} {limit_offset})
    )''').format(
        linkset=psycopg2_sql.Identifier(linkset_table_name),
        cluster_criteria=cluster_criteria,
        limit_offset=psycopg2_sql.SQL(limit_offset_sql)
    )

    return psycopg2_sql.SQL('INNER JOIN {} AS linkset ON target.uri = linkset.uri').format(linkset)


def get_linkset_cluster_join_sql(linkset_table_name, clusters_table_name, limit=None, offset=0):
    limit_offset_sql = get_pagination_sql(limit, offset)

    linkset = psycopg2_sql.SQL('''(
        SELECT source_uri AS uri 
        FROM {linkset} 
        WHERE cluster_id IN (
            SELECT id 
            FROM {clusters}
            ORDER BY size DESC
            {limit_offset}
        )
        
        UNION 
    
        SELECT target_uri AS uri 
        FROM {linkset} 
        WHERE cluster_id IN (
            SELECT id 
            FROM {clusters}
            ORDER BY size DESC
            {limit_offset}
        )
    )''').format(
        linkset=psycopg2_sql.Identifier(linkset_table_name),
        clusters=psycopg2_sql.Identifier(clusters_table_name),
        limit_offset=psycopg2_sql.SQL(limit_offset_sql)
    )

    return psycopg2_sql.SQL('INNER JOIN {} AS linkset ON target.uri = linkset.uri').format(linkset)


def get_table_info(dataset_id, collection_id):
    result = fetch_one(
        'SELECT table_name, columns FROM timbuctoo_tables WHERE dataset_id = %s AND collection_id = %s',
        (dataset_id, collection_id)
    )

    return {'table_name': result[0], 'columns': result[1]} if result else result


def get_column_name(property_name):
    return hash_string(property_name.lower())
