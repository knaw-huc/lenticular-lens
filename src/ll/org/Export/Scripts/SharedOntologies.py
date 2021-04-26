from rdflib import namespace as ns
from ll.org.Export.Scripts.Variables import PREF_SIZE
from ll.org.Export.Scripts.CountryCode import iso_639_1

# SCRIPT OVERVIEW ######################################################################################################--
#                                                                                                                      #
#   List of the URL of Ontologies of importance to the Lenticular Lens Tool                                            #
#   THis includes:                                                                                                     #
#       1. RDF                                                                                                         #
#       2, RDFS                                                                                                        #
#       3. XSD                                                                                                         #
#       4. OWL                                                                                                         #
#       5. FORMAT                                                                                                      #
#       6. VoID                                                                                                        #
#       7. SKOS                                                                                                        #
#       8. PROV                                                                                                        #
#       9. BDB                                                                                                         #
#       10. DCterms                                                                                                    #
#       11. FOAF                                                                                                       #
#       12. Units                                                                                                      #
#       13. SIM                                                                                                        #
#       14. CC                                                                                                         #
#       15. Time                                                                                                       #
#                                                                                                                      #
# ######################################################################################################################


class Namespaces:

    class RDF:

        # rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        rdf = ns.RDF
        prefix = F"@prefix {'rdf':>{PREF_SIZE}}: <{rdf}> ."

        type = F"{rdf}type"
        type_ttl = F"rdf:type"

        statement = F"{rdf}Statement"
        statement_ttl = F"rdf:Statement"

    class RDFS:

        # rdfs = "http://www.w3.org/2000/01/rdf-schema#"
        rdfs = ns.RDFS
        prefix = F"@prefix {'rdfs':>{PREF_SIZE}}: <{rdfs}> ."

        resource = F"{rdfs}Resource"
        resource_ttl = F"rdfs:Resource"

        label = F"{rdfs}label"
        label_ttl = F"rdfs:label"

        sequence = F"{rdfs}Sequence"
        sequence_ttl = F"rdfs:Sequence"

        comment = F"{rdfs}comment"
        comment_ttl = F"rdfs:comment"

    class XSD:

        # xsd = 'http://www.w3.org/2001/XMLSchema#'
        xsd = ns.XSD
        prefix = F"@prefix {'xsd':>{PREF_SIZE}}: <{xsd}> ."

    class OWL:

        # owl = "http://www.w3.org/2002/07/owl#"
        owl = ns.OWL
        prefix = F"@prefix {'owl':>{PREF_SIZE}}: <{owl}> ."

        sameAs = F"{owl}sameAs"
        sameAs_ttl = F"owl:sameAs"

    class Formats:

        # https://www.w3.org/ns/formats/

        formats = "http://www.w3.org/ns/formats/"
        prefix = F"@prefix {'formats':>{PREF_SIZE}}: <{formats}> ."

        turtle = F"{formats}Turtle"
        turtle_ttl = F"formats:Turtle"

        json_ld = F"{formats}JSON-LD"
        json_ld_ttl = "formats:JSON-LD"

        n3 = F"{formats}N3"
        n3_ttl = "formats:N3"

        n_Triples = F"{formats}N-Triples"
        n_Triples_ttl = "formats:N-Triples"

        n_Quads = F"{formats}N-Quads"
        n_Quads_ttl = "formats:N-Quads"

        ld_Patch = F"{formats}LD_Patch"
        ld_Patch_ttl = "formats:LD_Patch"

        microdata = F"{formats}microdata"
        microdata_ttl = "formats:microdata"

        owl_XML = F"{formats}OWL_XML"
        owl_XML_ttl = "formats:OWL_XML"

        triG = F"{formats}TriG"
        triG_ttl = "formats:TriG"

        rdfa = F"{formats}RDFa"
        rdfa_ttl = "formats:RDFa"

        sparql_results_CSV = "http://www.w3.org/ns/formats/SPARQL_Results_CSV"
        sparql_results_CSV_ttl = "formats:SPARQL_Results_CSV"

    class VoID:

        # void = "http://rdfs.org/ns/void#"
        void = ns.VOID
        prefix = F"@prefix {'void':>{PREF_SIZE}}: <{void}> ."

        # A collection of RDF links between two void:Datasets.
        linkset = F"{void}Linkset"
        linkset_ttl = F"void:Linkset"

        # The void:Dataset that contains the resources in the subject position of this void:Linkset's triples.
        subTarget = F"{void}subjectsTarget"
        subTarget_ttl = F"void:subjectsTarget"

        # The void:Dataset that contains the resources in the object position of a void:Linkset's triples.
        objTarget = F"{void}objectsTarget"
        objTarget_ttl = F"void:objectsTarget"

        # One of the two void:Datasets connected by this void:Linkset.
        target = F"{void}target"
        target_ttl = F"void:target"

        # A void:TechnicalFeature supported by a void:Datset.
        feature = F"{void}feature"
        feature_ttl = F"void:feature"

        # Specifies the RDF property of the triples in a void:Linkset.
        linkPredicate = F"{void}linkPredicate"
        linkPredicate_tt = F"void:linkPredicate"

        # The total number of triples contained in the dataset.
        triples = F"{void}triples"
        triples_ttl = F"void:triples"

        # The total number of entities that are described in the dataset. To be an entity in a dataset, a
        # resource must have a URI, and the URI must match the dataset's void:uriRegexPattern, if any.
        # Authors of VoID files may impose arbitrary additional requirements, for example, they may consider
        # any foaf:Document resources as not being entities.
        entities = F"{void}entities"
        entities_ttl = F"void:entities"

        # The total number of distinct subjects in the dataset. In other words, the number of distinct URIs
        # or blank nodes that occur in the subject position of triples in the dataset.
        distinctSubjects = F"{void}distinctSubjects"
        distinctSubjects_ttl = F"void:distinctSubjects"

        # The total number of distinct objects in the dataset. In other words, the number of distinct URIs,
        # blank nodes, or literals that occur in the object position of triples in the dataset.
        distinctObjects = F"{void}distinctObjects"
        distinctObjects_ttl = F"void:distinctObjects"

        dataset = F"{void}Dataset"
        dataset_ttl = F"void:Dataset"

        subset = F"{void}subset"
        subset_ttl = F"void:subset"

        classPartition = F"{void}classPartition"
        classPartition_ttl = F"void:classPartition"

        propertyPartition = F"{void}propertyPartition"
        propertyPartition_ttl = F"void:propertyPartition"

        property = F"{void}property"
        property_ttl = F"void:property"

        voidClass = F"{void}class"
        voidClass_ttl = F"void:class"

    class SKOS:

        # SKOS Simple Knowledge Organization System Namespace
        # https://www.w3.org/TR/2008/WD-skos-reference-20080829/skos.html

        # skos = "http://www.w3.org/2004/02/skos/core#"
        skos = ns.SKOS
        prefix = F"@prefix {'skos':>{PREF_SIZE}}: <{skos}> ."

        # -------------------------------------------------- #
        #     IDENTITY AND LIKES FROM SHARED VOCABULARIES    #
        # -------------------------------------------------- #

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

    class PROV:

        # prov = "http://www.w3.org/ns/prov#"
        prov = ns.PROV
        prefix = F"@prefix {'prov':>{PREF_SIZE}}: <{prov}> ."

        wasDerivedFrom = F"{prov}wasDerivedFrom"
        wasDerivedFrom_ttl = "prov:wasDerivedFrom"

    class BDB:

        bdb = 'http://vocabularies.bridgedb.org/ops#'
        prefix = F"@prefix {'bdb':>{PREF_SIZE}}: <{bdb}> ."

        lens = F"{bdb}Lens"
        lens_ttl = "bdb:Lens"

    class DC:

        dc = ns.DC
        prefix = F"@prefix {'dc':>{PREF_SIZE}}: <{dc}> ."

        language = F"{dc}language"
        language_ttl = F"dc:language"

    class DCterms:

        # dcterms = "http://purl.org/dc/terms"
        dcterms = ns.DCTERMS
        prefix = F"@prefix {'dcterms':>{PREF_SIZE}}: <{dcterms}> ."

        description = F"{dcterms}description"
        description_ttl = F"dcterms:description"

        license = F"{dcterms}license"
        license_ttl = F"dcterms:license"

        rights = F"{dcterms}rights"
        rights_ttl = F"dcterms:rights"

        subject = F"{dcterms}subject"
        subject_ttl = F"dcterms:subject"

        created = F"{dcterms}created"
        created_ttl = F"dcterms:created"

        creator = F"{dcterms}creator"
        creator_ttl = F"dcterms:creator"

        publisher = F"{dcterms}publisher"
        publisher_ttl = F"dcterms:publisher"

        identifier = F"{dcterms}identifier"
        identifier_ttl = F"dcterms:identifier"

        identifier = F"{dcterms}identifier"
        identifier_ttl = F"dcterms:identifier"

    class FOAF:

        # foaf = "http://xmlns.com/foaf/0.1/"
        foaf = ns.FOAF
        prefix = F"@prefix {'foaf':>{PREF_SIZE}}: <{foaf}> ."

    class Units:

        units = "http://qudt.org/vocab/unit#"
        prefix = F"@prefix {'units':>{PREF_SIZE}}: <{units}> ."

        kilometer = F"{units}Kilometer"
        kilometer_ttl = F"units:Kilometer ."

        meter = F"{units}Meter"
        meter_ttl = F"units:meter ."

        centimeter = F"{units}Centimeter"
        centimeter_ttl = F"units:centimeter ."

        mileUSStatute = F"{units}MileUSStatute"
        mileUSStatute_ttl = F"units:mileUSStatute ."

        yard = F"{units}Yard"
        yard_ttl = F"units:yard ."

        inch = F"{units}Inch"
        inch_ttl = F"units:nch> ."

        foot = F"{units}Foot"
        foot_ttl = F"units:foot ."

    class PAV:

        pav = "http://purl.org/pav/"
        prefix = F"@prefix {'pav':>{PREF_SIZE}}: <{pav}> ."

        importedFromSource = F"{pav}importedFromSource"
        importedFromSource_ttl = "pav:importedFromSource"

        authors = F"{pav}authors"
        authors_ttl = "pav:authors"

        contributors = F"{pav}importedFromSource"
        contributors_ttl = "pav:contributors"

        createdBy = F"{pav}createdBy"
        createdBy_ttl = "pav:createdBy"

    class SIM:

        sim = "http://purl.org/ontology/similarity/"
        prefix = F"@prefix {'pav':>{PREF_SIZE}}: <{sim}> ."

        # weight - A weighting value bound to a sim:Association where a value of 0 implies two elements are not at all
        # associated and a higher value implies a closer association.
        weight = F"{sim}weight"
        weight_ttl = "sim:weight"

        # distance - A weighting value for an Association where a value of 0 implies two elements are the same individual.
        distance = F"{sim}distance"
        distance_ttl = "sim:distance"

        # method - Specifies the sim:AssociationMethod used to derive a particular Association statement. This should be
        # used when the process for deriving association statements can be described further.
        method = F"{sim}method"
        method_ttl = "sim:method"

        # description - Specifies some description that discloses the process or set of processes used to derive asso-
        # ciation statements for the given AssociationMethod. This property is depricated in favor of the more appro-
        # priately named sim:workflow property.
        # workflow - Specifies a workflow that discloses the process or set of processes used to derive association
        # statements for the given sim:AssociationMethod
        workflow = F"{sim}workflow"
        workflow_ttl = "sim:workflow"

        # Network - A network is a grouping of sim:Associations. The associations that comprise a network are specified
        # using a series of sim:edge predicates.
        Network = F"{sim}Network"
        Network_ttl = "sim:Network"

    class CC:

        # https://labs.creativecommons.org/2011/ccrel-guide/
        # https://creativecommons.org/ns
        # Creative Commons (CC) is an internationally active non-profit organisation that provides free licences for
        # creators to use when making their work available to the public. These licences help the creator to give
        # permission for others to use the work in advance under certain conditions.

        cc = "http://creativecommons.org/ns#"
        prefix = F"@prefix {'cc':>{PREF_SIZE}}: <{cc}> ."

        # A License prohibits a Prohibition.
        license = F"{cc}license"
        license_ttl = "cc:license"

        # A License requires a Requirement.
        requires = F"{cc}requires"
        requires_ttl = "cc:requires"

        # A License prohibits a Prohibition.
        prohibits = F"{cc}prohibits"
        prohibits_ttl = "cc:prohibits"

        # The URL of the legal text of a License.
        legalcode = F"{cc}legalcode"
        legalcode_ttl = "cc:legalcode"

        # A License may be deprecated; provides the date deprecated on.
        deprecatedOn = F"{cc}deprecatedOn"
        deprecatedOn_ttl = "cc:deprecatedOn"

        # The URL the creator of a Work would like used when attributing re-use.
        attributionName = F"{cc}attributionName"
        attributionName_ttl = "cc:attributionName"

        # The URL the creator of a Work would like used when attributing re-use.
        attributionURL = F"{cc}attributionURL"
        attributionURL_ttl = "cc:attributionURL"

    class Time:

        # https://www.w3.org/TR/owl-time/#time:unitType

        time = "http://www.w3.org/2006/time#"
        prefix = F"@prefix {'time':>{PREF_SIZE}}: <{time}> ."

        unitType = F"{time}unitType"
        unitType_ttl = "time:unitType"

        day = F"{time}unitDay"
        day_ttl = "time:unitDay"

        hour = F"{time}unitHour"
        hour_ttl = "time:unitHour"

        minute = F"{time}unitMinute"
        minute_ttl = "time:unitMinute"

        month = F"{time}unitMonth"
        month_ttl = "time:unitMonth"

        second = F"{time}unitSecond"
        second_ttl = "time:unitSecond"

        week = F"{time}unitWeek"
        week_ttl = "time:unitWeek"

        year = F"{time}unitYear"
        year_ttl = "time:unitYear"

        unitType = F"{time}unitType"
        unitType_ttl = "time:unitType"

        global converter
        global converter_ttl

        converter = {

            "day": F"{time}unitDay",
            "days": F"{time}unitDay",

            "hour": F"{time}unitHour",
            "hours": F"{time}unitHour",

            "minute": F"{time}unitMinute",
            "minutes": F"{time}unitMinute",

            "month": F"{time}unitMonth",
            "months": F"{time}unitMonth",

            "second": F"{time}unitSecond",
            "seconds": F"{time}unitSecond",

            "week": F"{time}unitWeek",
            "weeks": F"{time}unitWeek",

            "year": F"{time}unitYear",
            "years": F"{time}unitYear",

            "unitType": F"{time}unitType",
            "unitTypes": F"{time}unitType"
        }

        converter_ttl = {

            "day": "time:unitDay",
            "days": "time:unitDay",

            "hour": "time:unitHour",
            "hours": "time:unitHour",

            "minute": "time:unitMinute",
            "minutes": "time:unitMinute",

            "month": "time:unitMonth",
            "months": "time:unitMonth",

            "second": "time:unitSecond",
            "seconds": "time:unitSecond",

            "week": "time:unitWeek",
            "weeks": "time:unitWeek",

            "year": "time:unitYear",
            "years": "time:unitYear",

            "unitType": "time:unitType",
            "unitTypes": "time:unitType",
        }

        @staticmethod
        def get_uri(time_unit):
            return converter[time_unit.lower()]

        @staticmethod
        def get_uri_ttl(time_unit):
            return converter_ttl[time_unit.lower()]

    class ISO:

        prefix_code = "iso_369_1"
        iso3166_1 = "https://id.loc.gov/vocabulary/iso639-1/"
        prefix = F"@prefix {prefix_code:>{PREF_SIZE}}: <{iso3166_1}> ."

        def get_iso369_1_uri(self, iso_369_1_code):
            return F"{self.iso3166_1}{iso_369_1_code}" if len(iso_369_1_code) == 2 else None

        def get_iso369_1_ttl_uri(self, iso_369_1_code):
            return F"{self.prefix_code}:{iso_369_1_code}" if len(iso_369_1_code) == 2 else None
