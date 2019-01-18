def convert_link(link):
    uri = link['source_uri'] + '+' + link['target_uri']
    rdf = '<http://lenticular-lenses.di.huc.knaw.nl/job/1/%s> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://lenticular-lenses.di.huc.knaw.nl/job/1/PersonLink> .\n' % uri
    rdf += '<%s> <http://www.w3.org/2002/07/owl#sameAs> <http://lenticular-lenses.di.huc.knaw.nl/job/1/%s> .\n' % (link['source_uri'], uri)
    rdf += '<%s> <http://www.w3.org/2002/07/owl#sameAs> <http://lenticular-lenses.di.huc.knaw.nl/job/1/%s> .\n' % (link['target_uri'], uri)
    for similarity_col, similarity_value in link.items():
        if similarity_col.endswith('_similarity'):
            rdf += '<http://lenticular-lenses.di.huc.knaw.nl/job/1/%s> <http://lenticular-lenses.di.huc.knaw.nl/vocab/%s> "%s" .\n' % (uri, similarity_col, similarity_value)

    return rdf
