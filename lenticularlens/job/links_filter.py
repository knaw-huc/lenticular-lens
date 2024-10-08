from psycopg import sql

from lenticularlens.job.validation import Validation


class LinksFilter:
    def __init__(self):
        self._alias = None
        self._source_uri = None
        self._target_uri = None
        self._min = 0
        self._max = 1
        self._uris = []
        self._cluster_ids = []
        self._validation_filter = Validation.ALL

    def set_alias(self, alias):
        self._alias = alias

    def filter_on_uris(self, uris):
        self._uris.extend(uris)

    def filter_on_link(self, source_uri, target_uri):
        self._source_uri = source_uri
        self._target_uri = target_uri

    def filter_on_min_max_strength(self, min=0, max=1):
        self._min = min
        self._max = max

    def filter_on_clusters(self, cluster_ids):
        self._cluster_ids.extend(cluster_ids)

    def filter_on_validation(self, validation_filter):
        self._validation_filter = validation_filter

    def sql(self, include_where=True, additional_filter=None, default=sql.SQL('')):
        filters = []

        if self._link_sql:
            filters.append(self._link_sql)
        if self._uris_sql:
            filters.append(self._uris_sql)
        if self._cluster_sql:
            filters.append(self._cluster_sql)
        if self._validation_sql:
            filters.append(self._validation_sql)
        if self._min_max_sql:
            filters.append(self._min_max_sql)
        if additional_filter:
            filters.append(additional_filter)

        if filters and include_where:
            return sql.SQL('WHERE {}').format(sql.SQL(' AND ').join(filters))

        if filters:
            return sql.SQL(' AND ').join(filters)

        return default

    @property
    def _alias_sql(self):
        return sql.SQL('{}.').format(sql.Identifier(self._alias)) if self._alias else sql.SQL('')

    @property
    def _link_sql(self):
        if self._source_uri and self._target_uri:
            return sql.SQL('{alias}source_uri = {source_uri} AND {alias}target_uri = {target_uri}').format(
                alias=self._alias_sql,
                source_uri=sql.Literal(self._source_uri),
                target_uri=sql.Literal(self._target_uri)
            )

        return None

    @property
    def _min_max_sql(self):
        min_sql = sql.SQL('{alias}similarity >= {min}').format(
            alias=self._alias_sql,
            min=sql.Literal(self._min),
        ) if self._min is not None and self._min > 0 else None

        max_sql = sql.SQL('{alias}similarity <= {max}').format(
            alias=self._alias_sql,
            max=sql.Literal(self._max),
        ) if self._max is not None and self._max < 1 else None

        if min_sql and max_sql:
            return sql.Composed([min_sql, sql.SQL(' AND '), max_sql])
        if min_sql:
            return min_sql
        if max_sql:
            return max_sql
        return None

    @property
    def _uris_sql(self):
        if self._uris and len(self._uris) == 1:
            return sql.SQL('({alias}source_uri = {uri} OR {alias}target_uri = {uri})').format(
                alias=self._alias_sql,
                uri=sql.Literal(self._uris[0])
            )
        elif self._uris and len(self._uris) > 1:
            return sql.SQL('({alias}source_uri IN ({uris}) OR {alias}target_uri IN ({uris}))').format(
                alias=self._alias_sql,
                uris=sql.SQL(', ').join([sql.Literal(uri) for uri in self._uris])
            )

        return None

    @property
    def _cluster_sql(self):
        if self._cluster_ids and len(self._cluster_ids) == 1:
            return sql.SQL('{alias}cluster_id = {cluster_id}').format(
                alias=self._alias_sql,
                cluster_id=sql.Literal(self._cluster_ids[0])
            )
        elif self._cluster_ids and len(self._cluster_ids) > 1:
            return sql.SQL('{alias}cluster_id IN ({cluster_ids})').format(
                alias=self._alias_sql,
                cluster_ids=sql.SQL(', ').join([sql.Literal(cluster_id) for cluster_id in self._cluster_ids])
            )

        return None

    @property
    def _validation_sql(self):
        if self._validation_filter < Validation.ALL:
            validation_filter_sqls = []

            if Validation.ACCEPTED in self._validation_filter:
                validation_filter_sqls.append(sql.Literal('accepted'))
            if Validation.REJECTED in self._validation_filter:
                validation_filter_sqls.append(sql.Literal('rejected'))
            if Validation.UNCERTAIN in self._validation_filter:
                validation_filter_sqls.append(sql.Literal('uncertain'))
            if Validation.UNCHECKED in self._validation_filter:
                validation_filter_sqls.append(sql.Literal('unchecked'))
            if Validation.DISPUTED in self._validation_filter:
                validation_filter_sqls.append(sql.Literal('disputed'))

            return sql.SQL('{alias}valid IN ({states})').format(
                alias=self._alias_sql,
                states=sql.SQL(', ').join(validation_filter_sqls)
            )

        return None

    @staticmethod
    def create(uris=None, link=(None, None), min_strength=None, max_strength=None,
               cluster_ids=None, validation_filter=Validation.ALL):
        links_filter = LinksFilter()

        if uris:
            links_filter.filter_on_uris(uris)
        if link:
            links_filter.filter_on_link(link[0], link[1])
        if min_strength or max_strength:
            links_filter.filter_on_min_max_strength(min_strength, max_strength)
        if cluster_ids:
            links_filter.filter_on_clusters(cluster_ids)
        if validation_filter:
            links_filter.filter_on_validation(validation_filter)

        return links_filter
