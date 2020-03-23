from inspect import cleandoc
from psycopg2 import sql as psycopg2_sql


class Elements:
    SELECT_SQL = cleandoc('''
        SELECT
            CASE WHEN r.source_uri IS NULL THEN l.source_uri ELSE r.source_uri END AS source_uri,
            CASE WHEN r.target_uri IS NULL THEN l.target_uri ELSE r.target_uri END AS target_uri,
            CASE WHEN l.link_order = r.link_order THEN l.link_order ELSE 'both'::link_order END AS link_order,
            ARRAY(SELECT DISTINCT unnest(l.source_collections || r.source_collections)) AS source_collections,
            ARRAY(SELECT DISTINCT unnest(l.target_collections || r.target_collections)) AS target_collections,
            CASE WHEN l.similarity IS NULL THEN r.similarity
                 WHEN r.similarity IS NULL THEN l.similarity
                 ELSE l.similarity || r.similarity END AS similarity,
            NULL AS cluster_id,
            CASE WHEN l.valid = r.valid THEN l.valid 
                 WHEN l.valid IS NULL THEN r.valid 
                 WHEN r.valid IS NULL THEN l.valid
                 ELSE 'mixed'::link_validity END AS valid,
            0 AS sort_order
    ''') + '\n'

    def __init__(self, data, type, job):
        self._data = data
        self._type = type.lower()
        self._job = job
        self._left = None
        self._right = None

    @property
    def left(self):
        if not self._left:
            elem = self._data[0]
            if type(elem) is dict and 'alignments' in elem and 'type' in elem:
                self._left = Elements(elem['alignments'], elem['type'], self._job)
            else:
                self._left = elem

        return self._left

    @property
    def right(self):
        if not self._right:
            elem = self._data[1]
            if type(elem) is dict and 'alignments' in elem and 'type' in elem:
                self._right = Elements(elem['alignments'], elem['type'], self._job)
            else:
                self._right = elem

        return self._right

    @property
    def alignments(self):
        alignments = []

        if isinstance(self.left, int):
            alignments.append(self.left)
        else:
            alignments += self.left.alignments

        if isinstance(self.right, int):
            alignments.append(self.right)
        else:
            alignments += self.right.alignments

        return alignments

    @property
    def left_sql(self):
        if isinstance(self.left, int):
            return psycopg2_sql.Identifier(self._job.linkset_table_name(self.left))

        return psycopg2_sql.SQL('(\n{sql}\n)').format(sql=self.left.joins_sql)

    @property
    def right_sql(self):
        if isinstance(self.right, int):
            return psycopg2_sql.Identifier(self._job.linkset_table_name(self.right))

        return psycopg2_sql.SQL('(\n{sql}\n)').format(sql=self.right.joins_sql)

    @property
    def joins_sql(self):
        if self._type == 'union':
            return psycopg2_sql.SQL(Elements.SELECT_SQL + cleandoc('''
                FROM {left} AS l
                FULL JOIN {right} AS r
                ON l.source_uri = r.source_uri AND l.target_uri = r.target_uri
            ''')).format(left=self.left_sql, right=self.right_sql)
        elif self._type == 'intersection':
            return psycopg2_sql.SQL(Elements.SELECT_SQL + cleandoc('''
                FROM {left} AS l
                INNER JOIN {right} AS r
                ON l.source_uri = r.source_uri AND l.target_uri = r.target_uri
            ''')).format(left=self.left_sql, right=self.right_sql)
        elif self._type == 'difference':
            return psycopg2_sql.SQL(Elements.SELECT_SQL + cleandoc('''
                FROM {left} AS l
                LEFT JOIN {right} AS r
                ON l.source_uri = r.source_uri AND l.target_uri = r.target_uri
                WHERE r.source_uri IS NULL AND r.target_uri IS NULL
            ''')).format(left=self.left_sql, right=self.right_sql)
        elif self._type == 'sym_difference':
            return psycopg2_sql.SQL(Elements.SELECT_SQL + cleandoc('''
                FROM {left} AS l
                FULL JOIN {right} AS r
                ON l.source_uri = r.source_uri AND l.target_uri = r.target_uri
                WHERE (l.source_uri IS NULL AND l.target_uri IS NULL) 
                OR (r.source_uri IS NULL AND r.target_uri IS NULL)
            ''')).format(left=self.left_sql, right=self.right_sql)
