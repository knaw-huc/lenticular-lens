import logging

from rdflib import Graph, query
from functools import partial
from cachetools import cachedmethod, TTLCache
from cachetools.keys import methodkey
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

    @cachedmethod(lambda self: self.cache, key=partial(methodkey, method='classes'))
    def get_classes(self) -> query.Result | None:
        return self.fetch("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX dct: <http://purl.org/dc/terms/>
            
            SELECT ?class (SAMPLE(?label) AS ?label) (COUNT(DISTINCT ?instance) AS ?count)
            WHERE {
                {
                    ?instance a ?class .
                    FILTER (!isBlank(?class))
                    OPTIONAL { ?class rdfs:label ?label }
                }
                UNION
                {
                    ?instance ?p ?o .
                    MINUS { ?instance a ?class }
                    BIND(rdfs:Resource AS ?class)
                }
                UNION
                {
                    ?s ?p ?instance .
                    MINUS { ?instance a ?class }
                    FILTER (isURI(?instance))
                    BIND(rdfs:Resource AS ?class)
                }
            }
            GROUP BY ?class
        """)

    @cachedmethod(lambda self: self.cache, key=partial(methodkey, method='properties'))
    def get_class_properties(self, class_uri: str) -> query.Result | None:
        return self.fetch(f"""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?property ?isInverse ?isLiteral ?isIRI
                   (SUM(IF(?numValues > 1, 1, 0)) > 0 AS ?isList)
                   (COUNT(DISTINCT ?entity) AS ?count)
                   (GROUP_CONCAT(DISTINCT COALESCE(?valueClass, rdfs:Resource); SEPARATOR=" | ") AS ?valueClasses)
            WHERE {{
                {{
                    ?entity rdf:type <{class_uri}> .
                    ?entity ?property ?value .
            
                    BIND(FALSE AS ?isInverse)
                    BIND(isLiteral(?value) AS ?isLiteral)
                    BIND(isIRI(?value) AS ?isIRI)
            
                    OPTIONAL {{ ?value rdf:type ?valueClass }}
                    
                    {{
                        SELECT ?entity ?property (COUNT(DISTINCT ?value) AS ?numValues)
                        WHERE {{
                            ?entity a <{class_uri}> .
                            ?entity ?property ?value .
                        }}
                        GROUP BY ?entity ?property
                    }}
                }}
                UNION
                {{
                    ?entity rdf:type <{class_uri}> .
                    ?value ?property ?entity .
            
                    BIND(TRUE AS ?isInverse)
                    BIND(isLiteral(?value) AS ?isLiteral)
                    BIND(isIRI(?value) AS ?isIRI)
            
                    OPTIONAL {{ ?value rdf:type ?valueClass }}
                    
                    {{
                         SELECT ?entity ?property (COUNT(DISTINCT ?value) AS ?numValues)
                         WHERE {{
                            ?entity a <{class_uri}> .
                            ?value ?property ?entity .
                        }}
                        GROUP BY ?entity ?property
                    }}
                }}
            }}
            GROUP BY ?property ?isInverse ?isLiteral ?isIRI
        """)


# sparql = SPARQL('https://sparql2.goldenagents.org/rijksmuseum')
# dataset = sparql.dataset
# if dataset:
#     print(f"Dataset title: {dataset.title}")
#     print(f"Number of entity types: {len(dataset.entity_types)}")
#     for entity_type in dataset.entity_types.values():
#         print(f"Entity type: {entity_type.label} ({entity_type.id})")
#         for property in entity_type.properties.values():
#             print(f"  Property: {property.label} ({property.id})")
