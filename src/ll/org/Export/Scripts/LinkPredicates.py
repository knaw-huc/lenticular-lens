from rdflib import URIRef, Literal, namespace as ns


# SCRIPT OVERVIEW ###########################################################################################
#                                                                                                           #
#   We provide here a list of possible link predicates to use for a set of identity matching result in the  #
#   lenticular lens. This includes:                                                                         #
#       1. owl:sameAs                                                                                       #
#       2. skos:broadMatch                                                                                  #
#       3. skos:closeMatch                                                                                  #
#       4. skos:exactMatch                                                                                  #
#       5. skos:narrowMatch                                                                                 #
#       6. skos:relatedMatch                                                                                #
#                                                                                                           #
# ###########################################################################################################


class LinkPredicates:

    skos = ns.SKOS
    owl = ns.OWL

    sameAs = F"{owl}sameAs"
    sameAs_tt = F"owl:sameAs"

    broadMatch = F"{skos}broadMatch"
    broadMatch_ttl = "skos:broadMatch"

    closeMatch = F"{skos}closeMatch"
    closeMatch_ttl = "skos:closeMatch"

    exactMatch = F"{skos}exactMatch"
    exactMatch_ttl = "skos:exactMatch"

    narrowMatch = F"{skos}narrowMatch"
    narrowMatch_ttl = "skos:narrowMatch"

    relatedMatch = F"{skos}relatedMatch"
    relatedMatch_ttl = "skos:relatedMatch"
