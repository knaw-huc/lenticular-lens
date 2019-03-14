from config_db import db_conn, run_query
from helpers import hash_string
from psycopg2 import sql as psycopg2_sql


def get_node_values(query_data, uris):
    sqls = []

    for graph_set in query_data:
        for datatype_set in graph_set['data']:
            for property_name in datatype_set['properties']:
                sql = psycopg2_sql.SQL('''
                SELECT uri, {property_literal} AS property, {property_name} AS value
                FROM {table_name}
                WHERE uri IN %(uris)s
                ''').format(
                    property_literal=psycopg2_sql.Literal(property_name),
                    property_name=psycopg2_sql.Identifier(get_column_name(property_name)),
                    table_name=psycopg2_sql.Identifier(
                        get_table_name(graph_set['graph'], datatype_set['entity_datatype'])
                    ),
                )

                sqls.append(sql)

    union_sql = psycopg2_sql.SQL('\nUNION ALL\n').join(sqls)

    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(union_sql, {'uris': tuple(uris)})

        return cur.fetchall()


def get_table_name(dataset_id, collection_id):
    return run_query(
        'SELECT table_name FROM timbuctoo_tables WHERE dataset_id = %s AND collection_id = %s',
        (dataset_id, collection_id)
    )[0] + '_expanded'


def get_column_name(property_name):
    return hash_string(property_name.lower())


if __name__ == '__main__':
    test_query_data = [
        {
            "graph": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__saa_index_op_begraafregisters",
            "data": [
                {
                    "entity_datatype": "saaOnt_Person",
                    "properties": [
                        "saaOnt_full_name",
                        "saaOnt_first_name",
                    ]
                }
            ]
        },
        {
            "graph": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__saa_index_op_ondertrouwregister",
            "data": [
                {
                    "entity_datatype": "saaOnt_Person",
                    "properties": [
                        "saaOnt_full_nameList",
                    ]
                }
            ]
        },
    ]

    test_uris = [
        "http://goldenagents.org/uva/SAA/person/IndexOpBegraafregistersVoor1811/saaId11146456p2",
        "http://goldenagents.org/uva/SAA/person/IndexOpOndertrouwregister/saaId26543348p1"
    ]

    print(get_node_values(test_query_data, test_uris))
