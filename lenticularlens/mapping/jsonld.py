from typing import Union, Optional
from pyld.jsonld import requests_document_loader


def create_mapping(doc: dict) -> dict[str, str]:
    ctx = doc.get('@context', {})
    terms, _ = resolve_context(ctx)
    return {uri: label for label, uri in terms.items() if not uri.startswith('@')}


def resolve_context(ctx: Union[str, list, dict], seen: Optional[set] = None):
    if seen is None:
        seen = set()

    loader = requests_document_loader()
    merged = {}
    prefixes = {}

    if isinstance(ctx, str):
        if ctx in seen:
            return {}, {}

        seen.add(ctx)
        remote_doc = loader(ctx)['document']
        remote_context = remote_doc.get('@context', {})

        terms, prefs = resolve_context(remote_context, seen)
        merged.update(terms)
        prefixes.update(prefs)

    elif isinstance(ctx, list):
        for c in ctx:
            terms, prefs = resolve_context(c, seen)
            merged.update(terms)
            prefixes.update(prefs)

    elif isinstance(ctx, dict):
        for k, v in ctx.items():
            if isinstance(v, str) and v.endswith(('#', '/')):
                prefixes[k] = v
            elif isinstance(v, str):
                merged[k] = v
            elif isinstance(v, dict) and '@id' in v:
                merged[k] = v['@id']
            if isinstance(v, dict) and '@context' in v:
                terms, prefs = resolve_context(v['@context'], seen)
                merged.update(terms)
                prefixes.update(prefs)

    for label, uri in merged.items():
        if ':' in uri:
            prefix, suffix = uri.split(':', 1)
            if prefix in prefixes:
                merged[label] = prefixes[prefix] + suffix

    return merged, prefixes
