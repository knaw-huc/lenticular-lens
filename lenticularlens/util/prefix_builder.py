from re import findall
from rdflib import Graph

from lenticularlens.util.hasher import hash_string

graph = Graph()


def qname(uri: str) -> tuple[str, str | None, str | None]:
    try:
        ns_manager = graph.namespace_manager
        prefix, namespace, name = ns_manager.compute_qname(uri, generate=False)
        shortened_uri = ':'.join((prefix, name))
    except (KeyError, ValueError):
        prefix, name = None, None
        shortened_uri = uri

    return shortened_uri, prefix, name


def get_namespace_prefix(uri):
    _shortened_uri, prefix, _name = qname(uri)
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
