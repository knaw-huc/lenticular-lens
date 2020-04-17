from inspect import cleandoc
from psycopg2 import sql as psycopg2_sql

from ll.job.lens_element import LensElement


class LensElements:
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
            if type(elem) is dict and 'elements' in elem and 'type' in elem:
                self._left = LensElements(elem['elements'], elem['type'], self._job)
            else:
                self._left = LensElement(elem, self._job)

        return self._left

    @property
    def right(self):
        if not self._right:
            elem = self._data[1]
            if type(elem) is dict and 'elements' in elem and 'type' in elem:
                self._right = LensElements(elem['elements'], elem['type'], self._job)
            else:
                self._right = LensElement(elem, self._job)

        return self._right

    @property
    def linksets(self):
        linksets = []

        if isinstance(self.left, LensElement) and self.left.type == 'linkset':
            linksets.append(self.left.id)
        elif isinstance(self.left, LensElements):
            linksets += self.left.linksets

        if isinstance(self.right, LensElement) and self.right.type == 'linkset':
            linksets.append(self.right.id)
        elif isinstance(self.right, LensElements):
            linksets += self.right.linksets

        return linksets

    @property
    def lenses(self):
        lenses = []

        if isinstance(self.left, LensElement) and self.left.type == 'lens':
            lenses.append(self.left.id)
        elif isinstance(self.left, LensElements):
            lenses += self.left.lenses

        if isinstance(self.right, LensElement) and self.right.type == 'lens':
            lenses.append(self.right.id)
        elif isinstance(self.right, LensElements):
            lenses += self.right.lenses

        return lenses

    @property
    def select_sql(self):
        return self._join_sql(cleandoc('''
            SELECT
                CASE WHEN r.source_uri IS NULL THEN l.source_uri ELSE r.source_uri END AS source_uri,
                CASE WHEN r.target_uri IS NULL THEN l.target_uri ELSE r.target_uri END AS target_uri,
                CASE WHEN l.link_order = r.link_order THEN l.link_order ELSE 'both'::link_order END AS link_order,
                ARRAY(SELECT DISTINCT unnest(l.source_collections || r.source_collections)) AS source_collections,
                ARRAY(SELECT DISTINCT unnest(l.target_collections || r.target_collections)) AS target_collections,
                CASE WHEN l.similarity IS NULL THEN r.similarity
                     WHEN r.similarity IS NULL THEN l.similarity
                     ELSE l.similarity || r.similarity END AS similarity
        '''), False)

    @property
    def select_validity_sql(self):
        return self._join_sql(cleandoc('''
            SELECT
                CASE WHEN r.source_uri IS NULL THEN l.source_uri ELSE r.source_uri END AS source_uri,
                CASE WHEN r.target_uri IS NULL THEN l.target_uri ELSE r.target_uri END AS target_uri, 
                CASE WHEN l.valid = r.valid THEN l.valid 
                     WHEN l.valid IS NULL THEN r.valid 
                     WHEN r.valid IS NULL THEN l.valid
                     ELSE 'mixed'::link_validity END AS valid
        '''), True)

    def _left_sql(self, select_sql, view):
        if isinstance(self.left, LensElement):
            return self.left.sql(view)

        return psycopg2_sql.SQL('(\n{sql}\n)').format(sql=self.left._join_sql(select_sql, view))

    def _right_sql(self, select_sql, view):
        if isinstance(self.right, LensElement):
            return self.right.sql(view)

        return psycopg2_sql.SQL('(\n{sql}\n)').format(sql=self.right._join_sql(select_sql, view))

    def _join_sql(self, select_sql, view):
        if self._type == 'union':
            return psycopg2_sql.SQL(select_sql + '\n' + cleandoc('''
                FROM {left} AS l
                FULL JOIN {right} AS r
                ON l.source_uri = r.source_uri AND l.target_uri = r.target_uri
            ''')).format(left=self._left_sql(select_sql, view), right=self._right_sql(select_sql, view))
        elif self._type == 'intersection':
            return psycopg2_sql.SQL(select_sql + '\n' + cleandoc('''
                FROM {left} AS l
                INNER JOIN {right} AS r
                ON l.source_uri = r.source_uri AND l.target_uri = r.target_uri
            ''')).format(left=self._left_sql(select_sql, view), right=self._right_sql(select_sql, view))
        elif self._type == 'difference':
            return psycopg2_sql.SQL(select_sql + '\n' + cleandoc('''
                FROM {left} AS l
                LEFT JOIN {right} AS r
                ON l.source_uri = r.source_uri AND l.target_uri = r.target_uri
                WHERE r.source_uri IS NULL AND r.target_uri IS NULL
            ''')).format(left=self._left_sql(select_sql, view), right=self._right_sql(select_sql, view))
        elif self._type == 'sym_difference':
            return psycopg2_sql.SQL(select_sql + '\n' + cleandoc('''
                FROM {left} AS l
                FULL JOIN {right} AS r
                ON l.source_uri = r.source_uri AND l.target_uri = r.target_uri
                WHERE (l.source_uri IS NULL AND l.target_uri IS NULL) 
                OR (r.source_uri IS NULL AND r.target_uri IS NULL)
            ''')).format(left=self._left_sql(select_sql, view), right=self._right_sql(select_sql, view))
