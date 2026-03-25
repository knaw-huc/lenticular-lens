import time
import logging

from SPARQLWrapper import SPARQLWrapper2
from SPARQLWrapper.SmartWrapper import Value

log = logging.getLogger(__name__)


class SPARQL:
    def __init__(self, sparql_url: str):
        self._sparql_url = sparql_url

    def fetch(self, query: str, retry: bool = True, timeout=600) -> list[dict[str, Value]]:
        try:
            sparql = SPARQLWrapper2(self._sparql_url)
            sparql.setMethod('POST')
            sparql.setRequestMethod('postdirectly')
            sparql.setTimeout(timeout)
            sparql.setQuery(query)

            return sparql.query().bindings
        except Exception as e:
            log.info(f'SPARQL query failed on {self._sparql_url}: {e}')
            if retry:
                time.sleep(30)
                return self.fetch(query, retry=False)
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
        property_clause = self.get_class_properties_sparql_clause(class_uri, inverse)

        return self.fetch(f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?property (COUNT(DISTINCT ?entity) AS ?count)
                   (MAX(isLiteral(?value)) AS ?hasLiterals) 
                   (MAX(isIRI(?value)) AS ?hasIRIs) 
                   (MAX(isBlank(?value)) AS ?hasBlankNodes)
            WHERE {{
                {property_clause}
            }}
            GROUP BY ?property
        """)

    def get_class_property_is_list(self, class_uri: str, property_uri: str, inverse: bool) -> list[dict[str, Value]]:
        property_clause = self.get_class_properties_sparql_clause(class_uri, inverse, property_uri)

        return self.fetch(f"""
            SELECT (COUNT(*) > 0 AS ?isList)
            WHERE {{
                {{
                    SELECT ?entity (COUNT(DISTINCT ?value) AS ?numValues)
                    WHERE {{
                        {property_clause}
                    }}
                    GROUP BY ?entity
                    HAVING (COUNT(DISTINCT ?value) > 1)
                }}
            }}
        """)

    def get_class_property_value_classes(self, class_uri: str, property_uri: str, inverse: bool) -> list[dict[str, Value]]:
        property_clause = self.get_class_properties_sparql_clause(class_uri, inverse, property_uri)

        return self.fetch(f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?valueClass
            WHERE {{
                {property_clause}
                
                FILTER(isIRI(?value) || isBlank(?value))
                OPTIONAL {{ ?value a ?valueClassExplicit }}
                
                BIND(COALESCE(?valueClassExplicit, rdfs:Resource) AS ?valueClass)
            }}
        """)

    @staticmethod
    def get_class_properties_sparql_clause(class_uri: str, inverse: bool, property_uri: str | None = None) -> str:
        is_resource_class = class_uri != 'http://www.w3.org/2000/01/rdf-schema#Resource'

        return f"""
            {f"?entity a <{class_uri}> ." if is_resource_class else f"MINUS {{ ?entity a ?type . }}"}
            {('?value ?property ?entity .' if inverse else '?entity ?property ?value .') \
            if property_uri is None else \
            (f'?value <{property_uri}> ?entity .' if inverse else f'?entity <{property_uri}> ?value .')}
        """
