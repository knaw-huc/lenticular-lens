from psycopg2 import sql


class ClustersFilter:
    def __init__(self):
        self._min_size = 0
        self._max_size = None
        self._min_count = 0
        self._max_count = None

    def filter_on_min_max_size(self, min=0, max=1):
        self._min_size = min
        self._max_size = max

    def filter_on_min_max_count(self, min=0, max=1):
        self._min_count = min
        self._max_count = max

    def sql(self):
        filters = []

        if self._min_max_size_sql:
            filters.append(self._min_max_size_sql)
        if self._min_max_links_sql:
            filters.append(self._min_max_links_sql)

        if filters:
            return sql.SQL('HAVING {}').format(sql.SQL(' AND ').join(filters))

        return sql.SQL('')

    @property
    def _min_max_size_sql(self):
        min_sql = sql.SQL('count(DISTINCT nodes) >= {}').format(sql.Literal(self._min_size)) \
            if self._min_size is not None and self._min_size > 0 else None

        max_sql = sql.SQL('count(DISTINCT nodes) <= {}').format(sql.Literal(self._max_size)) \
            if self._max_size is not None else None

        if min_sql and max_sql:
            return sql.Composed([min_sql, sql.SQL(' AND '), max_sql])
        if min_sql:
            return min_sql
        if max_sql:
            return max_sql
        return None

    @property
    def _min_max_links_sql(self):
        min_sql = sql.SQL('count(valid) / 2 >= {}').format(sql.Literal(self._min_count)) \
            if self._min_count is not None and self._min_count > 0 else None

        max_sql = sql.SQL('count(valid) / 2 <= {}').format(sql.Literal(self._max_count)) \
            if self._max_count is not None else None

        if min_sql and max_sql:
            return sql.Composed([min_sql, sql.SQL(' AND '), max_sql])
        if min_sql:
            return min_sql
        if max_sql:
            return max_sql
        return None

    @staticmethod
    def create(min_size=None, max_size=None, min_count=None, max_count=None):
        clusters_filter = ClustersFilter()

        if min_size and max_size:
            clusters_filter.filter_on_min_max_size(min_size, max_size)
        if min_count and max_count:
            clusters_filter.filter_on_min_max_count(min_count, max_count)

        return clusters_filter
