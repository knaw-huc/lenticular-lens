import logging
from SPARQLWrapper import SPARQLWrapper, JSON

log = logging.getLogger(__name__)


class SPARQL:
    def __init__(self, endpoint):
        self._wrapper = SPARQLWrapper(endpoint)

    def query(self, query, timeout=60):
        try:
            self._wrapper.setQuery(query)
            self._wrapper.setTimeout(timeout)
            self._wrapper.setReturnFormat(JSON)

            result = self._wrapper.query().convert()

            return result['results']['bindings']
        except Exception as e:
            log.error(e, exc_info=True)
