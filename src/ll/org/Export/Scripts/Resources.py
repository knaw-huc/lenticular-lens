
from ll.org.Export.Scripts.General import isNtFormat, undoNtFormat
from ll.org.Export.Scripts.Variables import PREF_SIZE, LL
from rdflib import URIRef, Literal

# SCRIPT OVERVIEW ######################################################################################################
#                                                                                                                      #
#   This script allows mainly for the formatting of RDF resources such as                                              #
#       - Linkset                                                                                                      #
#       - Lens                                                                                                         #
#       - Singleton                                                                                                    #
#       - dataset                                                                                                      #
#       - Research Question                                                                                            #
#   into turtle format                                                                                                 #
#                                                                                                                      #
# ######################################################################################################################
resource_ns = F"{LL}resource/"


class Resource:

    global resource_ns

    resource = resource_ns
    resource_prefix = F"@prefix {'resource':>{PREF_SIZE}}: <{resource_ns}> ."

    linkset = F"{resource_ns}linkset/"
    linkset_prefix = F"@prefix {'linkset':>{PREF_SIZE}}: <{resource_ns}linkset/> ."

    lens = F"{resource_ns}lens/"
    lens_prefix = F"@prefix {'lens':>{PREF_SIZE}}: <{resource_ns}lens> ."

    singleton = F"{resource_ns}singleton/"
    singleton_prefix = F"@prefix {'singleton':>{PREF_SIZE}}: <{resource_ns}singleton/> ."

    dataset = F"{resource_ns}dataset/"
    dataset_prefix = F"@prefix {'dataset':>{PREF_SIZE}}: <{resource_ns}dataset/> ."

    project = F"{resource_ns}singleton/"
    project_prefix = F"@prefix {'singleton':>{PREF_SIZE}}: <{resource_ns}project/> ."

    researchQ = F"{resource_ns}research-question/"
    researchQ_prefix = F"@prefix {'reserachQ':>{PREF_SIZE}}: <{resource_ns}reserach-question/> ."

    @staticmethod
    def uri_resource(uri: str):
        if isNtFormat(uri):
            uri = undoNtFormat(uri)
        return URIRef(uri.strip()).n3()

    @staticmethod
    def literal_resource(text: str, lang: str = None):
        return Literal(text).n3() if lang else Literal(text, lang=lang).n3()

    @staticmethod
    def ga_resource(local_name):
        if isNtFormat(local_name):
            local_name = undoNtFormat(local_name)
        return URIRef(F"{resource_ns}{local_name}").n3()

    @staticmethod
    def ga_resource_ttl(local_name: str):

        # IF THE LOCAL NAME IS IN A turtle or n3 FORMAT, RETURN THE LOCAL NAME
        if isNtFormat(local_name) or (local_name.__contains__(":") and local_name.__contains__("://") is False):
            return local_name

        # IF LOCAL NAME IS AN IRI, RETURN IN IN AN n3 FORMAT
        elif local_name.__contains__("://"):
            return F"<{local_name}>"

        # IF IS IS JUST A LOCAL NAME, RETURN IT AS A GA RESOURCE IN AN n3 FORMAT.
        return F"resource:{local_name}"

    @staticmethod
    def linkset_ttl(name: str):
        return F"linkset:{name}"

    @staticmethod
    def lens_ttl(name: str):
        return F"lens:{name}"

    @staticmethod
    def singleton_ttl(name: str):
        return F"singleton:{name}"

    @staticmethod
    def dataset_ttl(name: str):
        return F"dataset:{name}"

    @staticmethod
    def project_ttl(name: str):
        return F"project:{name}"

    @staticmethod
    def researchQ_ttl(name: str):
        return F"reserachQ:{name}"



