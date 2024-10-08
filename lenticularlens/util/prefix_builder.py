from re import findall

from lenticularlens.util.sparql import SPARQL
from lenticularlens.util.hasher import hash_string

registered_namespaces = dict()


def get_namespace_prefix(uri):
    prefix = get_registered_namespace(uri)
    if not prefix:
        name = get_uri_local_name(uri)
        hash = hash_string(uri.replace(name, ''))[:5]
        prefix = ('N' if name[0] in '0123456789' else '') + name.replace('-', '_').lower() + '_' + hash

    return prefix


def get_uri_local_name(uri):
    local = findall('.*[/#:](.*)$', uri)
    if len(local) > 0 and len(local[0]) > 0:
        return local[0]

    bad_uri = findall('(.*)[/#:]$', uri)
    if len(bad_uri) > 0:
        return get_uri_local_name(bad_uri[0])

    return uri


def get_registered_namespace(namespace):
    if namespace not in registered_namespaces:
        sparql = SPARQL('https://lov.linkeddata.es/dataset/lov/sparql')
        result = sparql.query(f'''
            PREFIX vann: <http://purl.org/vocab/vann/>
            PREFIX voaf: <http://purl.org/vocommons/voaf#>

            SELECT DISTINCT ?output {{
                GRAPH <https://lov.linkeddata.es/dataset/lov> {{
                    ?vocab a voaf:Vocabulary;
                           vann:preferredNamespacePrefix ?output ;
                           vann:preferredNamespaceUri "{namespace}" .
                }}
            }}
        ''', timeout=10)

        if result is not None:
            registered_namespaces[namespace] = result[0]['output']['value'] if result else None

    return registered_namespaces.get(namespace)
