import time
import base64
import logging

from typing import Optional, Union
from SPARQLWrapper import SPARQLWrapper2, QueryResult
from SPARQLWrapper.SmartWrapper import Value, Bindings

log = logging.getLogger(__name__)


class SPARQL:
    def __init__(self, sparql_url: str, graph: Optional[str] = None, authorization: Optional[str] = None):
        self._sparql_url = sparql_url
        self._graph = graph
        self._user, self._password = base64.b64decode(authorization.encode()).decode().split(':', 1) \
            if authorization else (None, None)

    def fetch(self, query: str, retry: bool = True, timeout=600) -> list[dict[str, Value]]:
        return self.fetch_query(query, retry, timeout).bindings

    def ask(self, query: str, retry: bool = True, timeout=600) -> bool:
        result = self.fetch_query(query, retry, timeout).convert()
        return bool(result['boolean'])

    def fetch_query(self, query: str, retry: bool = True, timeout=600) -> Union[Bindings, QueryResult]:
        try:
            sparql = SPARQLWrapper2(self._sparql_url)
            sparql.setMethod('POST')
            sparql.setRequestMethod('postdirectly')
            sparql.setCredentials(self._user, self._password)
            sparql.setTimeout(timeout)
            sparql.setQuery(query.strip())

            if self._graph is not None:
                sparql.addParameter('default' if self._graph == 'default' else 'graph', self._graph)

            return sparql.query()
        except Exception as e:
            log.info(f'SPARQL query failed on {self._sparql_url}: {e}')
            if retry:
                time.sleep(30)
                return self.fetch_query(query, retry=False)
            raise e

    def get_explicit_classes(self, only_classes: bool) -> list[dict[str, Value]]:
        return self.fetch(f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?class {'(SAMPLE(?labels) AS ?label) (COUNT(DISTINCT ?instance) AS ?count)' if not only_classes else ''}
            WHERE {{
              ?instance a ?class .
              FILTER (!isBlank(?class))
              {'OPTIONAL { ?class rdfs:label ?labels }' if not only_classes else ''}
            }}
            GROUP BY ?class
        """)

    def get_class_counts(self, class_uri: str) -> list[dict[str, Value]]:
        return self.fetch(f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT (SAMPLE(?labels) AS ?label) (COUNT(DISTINCT ?instance) AS ?count)
            WHERE {{
              ?instance a <{class_uri}> .
              OPTIONAL {{ <{class_uri}> rdfs:label ?labels }}
            }}
        """)

    def get_untyped_resources(self) -> list[dict[str, Value]]:
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

    def get_class_properties_counts_and_types(self, class_uri: str, inverse: bool) -> list[dict[str, Value]]:
        return self.fetch(f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?property (COUNT(DISTINCT ?entity) AS ?count)
                   (MAX(isLiteral(?value)) AS ?hasLiterals) 
                   (MAX(isIRI(?value)) AS ?hasIRIs) 
                   (MAX(isBlank(?value)) AS ?hasBlankNodes)
            WHERE {{
                {self.get_class_sparql_clause(class_uri)}
                {('?value ?property ?entity .' if inverse else '?entity ?property ?value .')}
            }}
            GROUP BY ?property
        """)

    def get_class_property_is_list(self, class_uri: str, property_uri: str, inverse: bool) -> bool:
        return self.ask(f"""
            ASK {{
                {self.get_class_sparql_clause(class_uri)}
                {f'?value1 <{property_uri}> ?entity .' if inverse else f'?entity <{property_uri}> ?value1 .'}
                {f'?value2 <{property_uri}> ?entity .' if inverse else f'?entity <{property_uri}> ?value2 .'}
                FILTER(?value1 != ?value2)
            }}
        """)

    def get_class_property_value_classes(self, class_uri: str, property_uri: str, inverse: bool) -> list[dict[str, Value]]:
        return self.fetch(f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?valueClass
            WHERE {{
                {self.get_class_sparql_clause(class_uri)}
                {f'?value <{property_uri}> ?entity .' if inverse else f'?entity <{property_uri}> ?value .'}
                
                FILTER(isIRI(?value) || isBlank(?value))
                OPTIONAL {{ ?value a ?valueClassExplicit }}
                
                BIND(COALESCE(?valueClassExplicit, rdfs:Resource) AS ?valueClass)
            }}
        """)

    @staticmethod
    def get_class_sparql_clause(class_uri: str) -> str:
        is_resource_class = class_uri != 'http://www.w3.org/2000/01/rdf-schema#Resource'
        return f"?entity a <{class_uri}> ." if is_resource_class else f"MINUS {{ ?entity a ?type . }}"
