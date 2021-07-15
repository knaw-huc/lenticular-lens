
from ll.org.Export.Scripts.General import isNtFormat, undoNtFormat
from ll.org.Export.Scripts.Variables import PREF_SIZE, LL
from rdflib import URIRef, Literal, Graph
MANAGER = Graph().namespace_manager

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

    linkset = F"{resource_ns}linkset#"
    linkset_prefix = F"@prefix {'linkset':>{PREF_SIZE}}: <{resource_ns}linkset#> ."

    lens = F"{resource_ns}lens#"
    lens_prefix = F"@prefix {'lens':>{PREF_SIZE}}: <{resource_ns}lens#> ."

    operator = F"{resource_ns}lensOperator#"
    operator_prefix = F"@prefix {'operator':>{PREF_SIZE}}: <{resource_ns}lensOperator#> ."

    validationset = F"{resource_ns}validationset#"
    validationset_prefix = F"@prefix {'validationset':>{PREF_SIZE}}: <{resource_ns}validationset#> ."

    validation = F"{resource_ns}validation#"
    validation_prefix = F"@prefix {'validationset':>{PREF_SIZE}}: <{resource_ns}validation#> ."

    clusterset = F"{resource_ns}clusterset#"
    clusterset_prefix = F"@prefix {'clusterset':>{PREF_SIZE}}: <{resource_ns}clusterset#> ."

    cluster = F"{resource_ns}clusterset#"
    cluster_prefix = F"@prefix {'clusterset':>{PREF_SIZE}}: <{resource_ns}cluster#> ."

    singleton = F"{resource_ns}singleton#"
    singleton_prefix = F"@prefix {'singleton':>{PREF_SIZE}}: <{resource_ns}singleton#> ."

    dataset = F"{resource_ns}dataset#"
    dataset_prefix = F"@prefix {'dataset':>{PREF_SIZE}}: <{resource_ns}dataset#> ."

    project = F"{resource_ns}singleton#"
    project_prefix = F"@prefix {'singleton':>{PREF_SIZE}}: <{resource_ns}project#> ."

    researchQ = F"{resource_ns}research-question#"
    researchQ_prefix = F"@prefix {'researchQ':>{PREF_SIZE}}: <{resource_ns}research-question#> ."

    @staticmethod
    def uri_resource(uri: str):
        if isNtFormat(uri):
            uri = undoNtFormat(uri)
        return URIRef(uri.strip()).n3()

    @staticmethod
    def literal_resource(text: str, lang: str = None):
        return Literal(text).n3(MANAGER, lang=lang) if lang else Literal(text).n3(MANAGER)

    @staticmethod
    def ga_resource(local_name):
        if isNtFormat(local_name):
            local_name = undoNtFormat(local_name)
        return URIRef(F"{resource_ns}{local_name}").n3()

    @staticmethod
    def ga_resource_ttl(local_name: str):

        if local_name.__contains__("\n"):
            return local_name

        # IF THE LOCAL NAME IS IN A turtle or n3 FORMAT, RETURN THE LOCAL NAME
        elif isNtFormat(local_name) or (local_name.__contains__(":") and local_name.__contains__("://") is False):
            return local_name

        # IF LOCAL NAME IS AN IRI, RETURN IT IN AN n3 FORMAT
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
    def clusterset_ttl(name: str):
        return F"clusterset:{name}"

    @staticmethod
    def cluster_ttl(name: str):
        return F"cluster:{name}"

    @staticmethod
    def validationset_ttl(name: str):
        return F"validationset:{name}"

    @staticmethod
    def validation_ttl(name: str):
        return F"validation:{name}"

    @staticmethod
    def operator_ttl(name: str):
        return F"operator:{name}"

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



