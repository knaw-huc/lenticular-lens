from re import findall
from rdflib import Graph

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
        g = Graph()
        g.parse('https://lov.linkeddata.es/dataset/lov')

        query = f"""
            PREFIX vann: <http://purl.org/vocab/vann/>
            PREFIX voaf: <http://purl.org/vocommons/voaf#>

            SELECT DISTINCT ?output {{
                GRAPH <https://lov.linkeddata.es/dataset/lov> {{
                    ?vocab a voaf:Vocabulary;
                           vann:preferredNamespacePrefix ?output ;
                           vann:preferredNamespaceUri "{namespace}" .
                }}
        """

        result = list(g.query(query))
        if result:
            registered_namespaces[namespace] = str(result[0][0])
        else:
            registered_namespaces[namespace] = None

    return registered_namespaces.get(namespace)
