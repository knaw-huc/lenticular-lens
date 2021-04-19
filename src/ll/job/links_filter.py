from psycopg2 import sql

from ll.job.validation import Validation


class LinksFilter:
    def __init__(self):
        self._alias = None
        self._uri = None
        self._source_uri = None
        self._target_uri = None
        self._min = 0
        self._max = 1
        self._cluster_id = None
        self._validation_filter = Validation.ALL

    def set_alias(self, alias):
        self._alias = alias

    def filter_on_uri(self, uri):
        self._uri = uri

    def filter_on_link(self, source_uri, target_uri):
        self._source_uri = source_uri
        self._target_uri = target_uri

    def filter_on_min_max_strength(self, min=0, max=1):
        self._min = min
        self._max = max

    def filter_on_cluster(self, cluster_id):
        self._cluster_id = cluster_id

    def filter_on_validation(self, validation_filter):
        self._validation_filter = validation_filter

    def sql(self, include_where=True, default=sql.SQL('')):
        filters = []

        if self._uri_sql:
            filters.append(self._uri_sql)
        if self._link_sql:
            filters.append(self._link_sql)
        if self._cluster_sql:
            filters.append(self._cluster_sql)
        if self._validation_sql:
            filters.append(self._validation_sql)
        if self._min_max_sql:
            filters.append(self._min_max_sql)

        if filters and include_where:
            return sql.SQL('WHERE {}').format(sql.SQL(' AND ').join(filters))

        if filters:
            return sql.SQL(' AND ').join(filters)

        return default

    @property
    def _alias_sql(self):
        return sql.SQL('{}.').format(sql.Identifier(self._alias)) if self._alias else sql.SQL('')

    @property
    def _uri_sql(self):
        if self._uri:
            return sql.SQL('({alias}source_uri = {uri} OR {alias}target_uri = {uri})').format(
                alias=self._alias_sql,
                uri=sql.Literal(self._uri)
            )

        return None

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
        min_sql = sql.SQL('{alias}computed_similarity > {min}').format(
            alias=self._alias_sql,
            min=sql.Literal(self._min),
        ) if self._min is not None and self._min > 0 else None

        max_sql = sql.SQL('{alias}computed_similarity < {max}').format(
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
    def _cluster_sql(self):
        if self._cluster_id:
            return sql.SQL('{alias}cluster_id = {cluster_id}').format(
                alias=self._alias_sql,
                cluster_id=sql.Literal(self._cluster_id)
            )

        return None

    @property
    def _validation_sql(self):
        if self._validation_filter < Validation.ALL:
            validation_filter_sqls = []

            if Validation.ACCEPTED in self._validation_filter:
                validation_filter_sqls.append(sql.SQL('{alias}valid = {valid}').format(
                    alias=self._alias_sql,
                    valid=sql.Literal('accepted'))
                )
            if Validation.REJECTED in self._validation_filter:
                validation_filter_sqls.append(sql.SQL('{alias}valid = {valid}').format(
                    alias=self._alias_sql,
                    valid=sql.Literal('rejected'))
                )
            if Validation.NOT_SURE in self._validation_filter:
                validation_filter_sqls.append(sql.SQL('{alias}valid = {valid}').format(
                    alias=self._alias_sql,
                    valid=sql.Literal('not_sure'))
                )
            if Validation.NOT_VALIDATED in self._validation_filter:
                validation_filter_sqls.append(sql.SQL('{alias}valid = {valid}').format(
                    alias=self._alias_sql,
                    valid=sql.Literal('not_validated'))
                )
            if Validation.MIXED in self._validation_filter:
                validation_filter_sqls.append(sql.SQL('{alias}valid = {valid}').format(
                    alias=self._alias_sql,
                    valid=sql.Literal('mixed'))
                )

            return sql.SQL(' OR ').join(validation_filter_sqls)

        return None