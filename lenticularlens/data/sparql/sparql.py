import logging

from rdflib import Graph, query
from cachetools import cachedmethod, TTLCache
from rdflib.plugins.stores.sparqlstore import SPARQLStore

log = logging.getLogger(__name__)


class SPARQL:
    cache = TTLCache(maxsize=500, ttl=24 * 60 * 60)  # One day cache

    def __init__(self, sparql_url: str):
        self._sparql_url = sparql_url
        self._graph = Graph(bind_namespaces='none', store=SPARQLStore(sparql_url))
        self._graph.store.method = 'POST_FORM'

    def fetch(self, query) -> query.Result:
        result = self._graph.query(query)
        if isinstance(result, tuple):
            raise Exception(f'SPARQL endpoint returned error {result[0]}: {result[1]}')

        return result

    @cachedmethod(lambda self: self.cache, key=lambda self: (self._sparql_url, 'explicit_classes'))
    def get_explicit_classes(self) -> query.Result | None:
        return self.fetch("""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?class (SAMPLE(?label) AS ?label) (COUNT(DISTINCT ?instance) AS ?count)
            WHERE {
              ?instance a ?class .
              FILTER (!isBlank(?class))
              OPTIONAL { ?class rdfs:label ?label }
            }
            GROUP BY ?class
        """)

    @cachedmethod(lambda self: self.cache, key=lambda self: (self._sparql_url, 'untyped_resources'))
    def get_untyped_resources(self) -> query.Result | None:
        return self.fetch("""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT (rdfs:Resource AS ?class) (COUNT(DISTINCT ?instance) AS ?count)
            WHERE {
              {
                ?instance ?p ?o .
              }
              UNION
              {
                ?s ?p ?instance .
                FILTER(isURI(?instance))
              }
              MINUS { ?instance a ?anyClass }
            }
        """)

    @cachedmethod(lambda self: self.cache,
                  key=lambda self, class_uri, inverse: (self._sparql_url, 'class_properties', class_uri, inverse))
    def get_class_properties(self, class_uri: str, inverse: bool) -> query.Result | None:
        match_type_clause = f"?entity a <{class_uri}> ." \
            if class_uri != 'http://www.w3.org/2000/01/rdf-schema#Resource' else \
            f"MINUS {{ ?entity a ?type . }}"

        match_clause = '?value ?property ?entity .' if inverse else '?entity ?property ?value .'

        return self.fetch(f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?property
                   (MAX(?isLiteral) AS ?hasLiterals)
                   (MAX(?isIRI) AS ?hasIRIs)
                   (SUM(IF(?numValues > 1, 1, 0)) > 0 AS ?isList)
                   (COUNT(DISTINCT ?entity) AS ?count)
                   (GROUP_CONCAT(DISTINCT ?valueClassIRIs; SEPARATOR=" | ") AS ?valueClasses)
            WHERE {{
                {match_type_clause}
                {match_clause}
        
                BIND(isLiteral(?value) AS ?isLiteral)
                BIND(isIRI(?value) AS ?isIRI)
        
                OPTIONAL {{ ?value a ?valueClass }}
                BIND(IF(?isIRI, COALESCE(?valueClass, rdfs:Resource), "") AS ?valueClassIRIs)
                
                {{
                    SELECT ?entity ?property (COUNT(DISTINCT ?value) AS ?numValues)
                    WHERE {{
                        {match_type_clause}
                        {match_clause}
                    }}
                    GROUP BY ?entity ?property
                }}
            }}
            GROUP BY ?property
        """)
