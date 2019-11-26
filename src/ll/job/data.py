from enum import IntFlag
from decimal import Decimal

from psycopg2 import extras as psycopg2_extras, sql as psycopg2_sql
from psycopg2.extensions import AsIs

from ll.job.job_config import JobConfig

from ll.data.collection import Collection
from ll.data.query import get_property_values

from ll.util.config_db import db_conn, execute_query, fetch_one
from ll.util.helpers import hash_string, hasher, get_pagination_sql


class ExportLinks(IntFlag):
    ALL = 7
    ACCEPTED = 4
    DECLINED = 2
    NOT_VALIDATED = 1


class Job:
    def __init__(self, job_id):
        self.job_id = job_id
        self._data = None

    @property
    def data(self):
        if not self._data:
            self._data = fetch_one('SELECT * FROM reconciliation_jobs WHERE job_id = %s', (self.job_id,), dict=True)

        return self._data

    @property
    def resources(self):
        return self.data['resources']

    @property
    def mappings(self):
        return self.data['mappings']

    @property
    def config(self):
        return JobConfig(self.job_id, self.resources, self.mappings)

    @property
    def alignments(self):
        return execute_query({
            'query': "SELECT * FROM alignments WHERE job_id = %s",
            'parameters': (self.job_id,)
        }, {'cursor_factory': psycopg2_extras.RealDictCursor})

    @property
    def clusterings(self):
        return execute_query({
            'query': "SELECT * FROM clusterings WHERE job_id = %s",
            'parameters': (self.job_id,)
        }, {'cursor_factory': psycopg2_extras.RealDictCursor})

    def alignment(self, alignment):
        return fetch_one('SELECT * FROM alignments WHERE job_id = %s AND alignment = %s',
                         (self.job_id, alignment), dict=True)

    def clustering(self, alignment):
        return fetch_one('SELECT * FROM clusterings WHERE job_id = %s AND alignment = %s',
                         (self.job_id, alignment), dict=True)

    def update_data(self, data):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL("""
                    INSERT INTO reconciliation_jobs (job_id, %s) VALUES %s
                    ON CONFLICT (job_id) DO 
                    UPDATE SET (%s) = ROW %s, updated_at = NOW()
                """), (
                AsIs(', '.join(data.keys())),
                tuple([self.job_id] + list(data.values())),
                AsIs(', '.join(data.keys())),
                tuple(data.values()),
            ))

    def update_alignment(self, alignment, data):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('UPDATE alignments SET (%s) = ROW %s WHERE job_id = %s AND alignment = %s'), (
                AsIs(', '.join(data.keys())),
                tuple(data.values()),
                self.job_id,
                alignment
            ))

    def update_clustering(self, alignment, data):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute(psycopg2_sql.SQL('UPDATE clusterings SET (%s) = ROW %s WHERE job_id = %s AND alignment = %s'), (
                AsIs(', '.join(data.keys())),
                tuple(data.values()),
                self.job_id,
                alignment
            ))

    def run_alignment(self, alignment, restart=False):
        with db_conn() as conn, conn.cursor() as cur:
            if restart:
                cur.execute(psycopg2_sql.SQL("DELETE FROM alignments WHERE job_id = %s AND alignment = %s"),
                            (self.job_id, alignment))
                cur.execute(psycopg2_sql.SQL("DELETE FROM clusterings WHERE job_id = %s AND alignment = %s"),
                            (self.job_id, alignment))

            cur.execute(psycopg2_sql.SQL("INSERT INTO alignments (job_id, alignment, status, kill, requested_at) "
                                         "VALUES (%s, %s, %s, false, now())"), (self.job_id, alignment, 'waiting'))

    def run_clustering(self, alignment, association_file, clustering_type='default'):
        clustering = self.clustering(alignment)

        with db_conn() as conn, conn.cursor() as cur:
            if clustering:
                cur.execute(psycopg2_sql.SQL("""
                    UPDATE clusterings 
                    SET association_file = %s, status = %s, 
                        kill = false, requested_at = now(), processing_at = null, finished_at = null
                    WHERE job_id = %s AND alignment = %s
                """), (association_file, 'waiting', self.job_id, alignment))
            else:
                cur.execute(psycopg2_sql.SQL("""
                    INSERT INTO clusterings (job_id, alignment, clustering_type, association_file, 
                                             status, kill, requested_at) 
                    VALUES (%s, %s, %s, %s, %s, false, now())
                """), (self.job_id, alignment, clustering_type, association_file, 'waiting'))

    def kill_alignment(self, alignment):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute('UPDATE alignments SET kill = true WHERE job_id = %s AND alignment = %s',
                        (self.job_id, alignment))

    def kill_clustering(self, alignment):
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute('UPDATE clusterings SET kill = true WHERE job_id = %s AND alignment = %s',
                        (self.job_id, alignment))

    def validate_link(self, alignment, source_uri, target_uri, valid):
        with db_conn() as conn, conn.cursor() as cur:
            linkset_table = 'linkset_' + self.job_id + '_' + str(alignment)
            cur.execute(psycopg2_sql.SQL('UPDATE {} SET valid = %s WHERE source_uri = %s AND target_uri = %s')
                        .format(psycopg2_sql.Identifier(linkset_table)), (valid, source_uri, target_uri))

    def value_targets(self, alignment, downloaded_only=True):
        def is_downloaded(dataset_id, collection_id):
            return any(download['dataset_id'] == dataset_id and download['collection_id'] == collection_id
                       for download in downloaded)

        value_targets = next((mapping['value_targets'] for mapping in self.mappings if mapping['id'] == alignment))
        if not downloaded_only:
            return value_targets

        new_value_targets = []
        downloaded = Collection.download_status()['downloaded']

        for value_target in value_targets:
            graph = value_target['graph']
            new_graph_data = []

            for data_of_entity in value_target['data']:
                entity_type = data_of_entity['entity_type']

                if is_downloaded(graph, entity_type):
                    new_properties = []
                    for properties in data_of_entity['properties']:
                        if len(properties) == 1 or all(is_downloaded(graph, entity) for entity in properties[1::2]):
                            new_properties.append(properties)

                    if len(new_properties) > 0:
                        new_graph_data.append({'entity_type': entity_type, 'properties': new_properties})

            if len(new_graph_data) > 0:
                new_value_targets.append({'graph': graph, 'data': new_graph_data})

        return new_value_targets

    def get_resource_sample(self, resource_label, limit=None, offset=0, total=False):
        job_config = self.config

        resource_label = hash_string(resource_label)
        resource = job_config.get_resource_by_label(resource_label)
        if not resource:
            return []

        selection = psycopg2_sql.SQL('count(*) AS total') if total else resource.properties_sql
        order_limit = psycopg2_sql.SQL('') if total else \
            psycopg2_sql.SQL('ORDER BY {view_name}.uri ' + get_pagination_sql(limit, offset)) \
                .format(view_name=psycopg2_sql.Identifier(resource.label))

        with db_conn() as conn, conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
            cur.execute(psycopg2_sql.SQL("""
                SELECT {selection}
                FROM {table_name} AS {view_name} {joins} {wheres} 
                {order_limit}; 
            """).format(
                selection=selection,
                table_name=psycopg2_sql.Identifier(resource.table_name),
                view_name=psycopg2_sql.Identifier(resource.label),
                joins=resource.joins_related_sql,
                wheres=resource.where_sql,
                order_limit=order_limit,
            ))

            return cur.fetchone() if total else cur.fetchall()

    def get_links(self, alignment, export_links=ExportLinks.ALL, cluster_id=None,
                  limit=None, offset=0, include_props=False):
        linkset_table = 'linkset_' + self.job_id + '_' + str(alignment)
        limit_offset_sql = get_pagination_sql(limit, offset)

        values = None
        if include_props:
            targets = self.value_targets(alignment)
            if targets:
                values = get_property_values(targets, linkset_table_name=linkset_table, cluster_id=cluster_id,
                                             limit=limit, offset=offset)

        cluster_sql = 'cluster_id = %s' if cluster_id else ''
        export_links_sql = []
        if export_links < ExportLinks.ALL and ExportLinks.ACCEPTED in export_links:
            export_links_sql.append('valid = true')
        if export_links < ExportLinks.ALL and ExportLinks.DECLINED in export_links:
            export_links_sql.append('valid = false')
        if export_links < ExportLinks.ALL and ExportLinks.NOT_VALIDATED in export_links:
            export_links_sql.append('valid IS NULL')

        where_sql = ''
        if cluster_id and export_links < ExportLinks.ALL:
            where_sql = 'WHERE {} AND ({})'.format(cluster_sql, ' OR '.join(export_links_sql))
        elif cluster_id:
            where_sql = 'WHERE {}'.format(cluster_sql)
        elif export_links < ExportLinks.ALL:
            where_sql = 'WHERE {}'.format(' OR '.join(export_links_sql))

        query = 'SELECT source_uri, target_uri, strengths, cluster_id, valid FROM {} {} {}' \
            .format(linkset_table, where_sql, limit_offset_sql)

        with db_conn() as conn, conn.cursor() as cur:
            cur.itersize = 1000
            cur.execute(query, (cluster_id,) if cluster_id else None)

            for link in cur:
                yield {
                    'source': link[0],
                    'source_values': values[link[0]] if values else None,
                    'target': link[1],
                    'target_values': values[link[1]] if values else None,
                    'strengths': [float(strength) if isinstance(strength, Decimal)
                                  else strength for strength in link[2]],
                    'cluster_id': link[3],
                    'valid': link[4]
                }

    def get_cluster_nodes(self, alignment):
        with db_conn() as conn, conn.cursor() as cur:
            linkset_table = 'linkset_' + self.job_id + '_' + str(alignment)

            cur.execute("""
                SELECT nodes.node AS node, ARRAY_AGG(DISTINCT nodes.cluster_id) AS clusters
                FROM (
                    SELECT source_uri AS node, cluster_id FROM {}
                    UNION
                    SELECT target_uri AS node, cluster_id FROM {}
                ) AS nodes
                GROUP BY nodes.node
            """.format(linkset_table, linkset_table))

            return {cluster_node[0]: set(cluster_node[1]) for cluster_node in cur}

    def get_clusters(self, alignment, limit=None, offset=0, include_props=False):
        linkset_table = 'linkset_' + self.job_id + '_' + str(alignment)
        clusters_table = 'clusters_' + self.job_id + '_' + str(alignment)
        limit_offset_sql = get_pagination_sql(limit, offset)

        values = None
        if include_props:
            targets = self.value_targets(alignment)
            if targets:
                values = get_property_values(targets, linkset_table_name=linkset_table,
                                             clusters_table_name=clusters_table, limit=limit, offset=offset)

        with db_conn() as conn, conn.cursor() as cur:
            cur.itersize = 1000

            if values:
                cur.execute("""
                    SELECT clusters.id, clusters.size, clusters.links, 
                           ARRAY_AGG(DISTINCT links.source_uri) || ARRAY_AGG(DISTINCT links.target_uri) AS nodes
                    FROM {} AS clusters
                    LEFT JOIN {} AS links ON clusters.id = links.cluster_id
                    GROUP BY clusters.id
                    ORDER BY clusters.size DESC {}
                """.format(clusters_table, linkset_table, limit_offset_sql))
            else:
                cur.execute(
                    'SELECT id, size, links FROM {} ORDER BY size DESC {}'.format(clusters_table, limit_offset_sql))

            for cluster in cur:
                cluster_values = {}
                cluster_keys = {}

                if values:
                    for uri, uri_values in values.items():
                        if uri in cluster[3]:
                            for prop_value in uri_values:
                                key = prop_value['dataset'] + '_' + prop_value['property']

                                if key not in cluster_values:
                                    cluster_values[key] = {
                                        'dataset': prop_value['dataset'],
                                        'property': prop_value['property'],
                                        'values': set()
                                    }

                                if key not in cluster_keys:
                                    cluster_keys[key] = 0

                                cluster_prop_values = prop_value['values'][:5]
                                cluster_keys[key] = cluster_keys[key] + len(cluster_prop_values)

                                if cluster_keys[key] < 5:
                                    cluster_values[key]['values'].update(cluster_prop_values)

                yield {
                    'id': cluster[0],
                    'size': cluster[1],
                    'links': cluster[2],
                    'values': [{
                        'dataset': cluster_value['dataset'],
                        'property': cluster_value['property'],
                        'values': list(cluster_value['values'])
                    } for key, cluster_value in cluster_values.items()] if values else None
                }

    def cluster(self, alignment, cluster_id):
        linkset_table = 'linkset_' + self.job_id + '_' + str(alignment)
        links = execute_query({
            'query': f'SELECT source_uri, target_uri, strengths FROM {linkset_table} WHERE cluster_id = %s',
            'parameters': (cluster_id,)
        })

        all_links = []
        strengths = {}
        nodes = []
        for link in links:
            source = '<' + link[0] + '>'
            target = '<' + link[1] + '>'

            current_link = (source, target) if source < target else (target, source)
            link_hash = "key_{}".format(str(hasher(current_link)).replace("-", "N"))

            all_links.append([source, target])
            strengths[link_hash] = link[2]

            if source not in nodes:
                nodes.append(source)
            if target not in nodes:
                nodes.append(target)

        return {'links': all_links, 'strengths': strengths, 'nodes': nodes}
