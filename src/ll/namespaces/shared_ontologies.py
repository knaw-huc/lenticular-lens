from rdflib import namespace as ns

pref_size = 20


class Namespaces:
    class RDF:
        # rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        rdf = ns.RDF
        prefix = 'rdf'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{rdf}> ."

        type = F"{rdf}type"
        type_ttl = F"{prefix}:type"

        statement = F"{rdf}Statement"
        statement_ttl = F"{prefix}:Statement"

    class RDFS:
        # rdfs = "http://www.w3.org/2000/01/rdf-schema#"
        rdfs = ns.RDFS
        prefix = 'rdfs'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{rdfs}> ."

        resource = F"{rdfs}Resource"
        resource_ttl = F"{prefix}:Resource"

        label = F"{rdfs}label"
        label_ttl = F"{prefix}:label"

        sequence = F"{rdfs}Sequence"
        sequence_ttl = F"{prefix}:Sequence"

    class XSD:
        # xsd = "http://www.w3.org/2001/XMLSchema#"
        xsd = ns.XSD
        prefix = 'xsd'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{xsd}> ."

    class OWL:
        # owl = "http://www.w3.org/2002/07/owl#"
        owl = ns.OWL
        prefix = 'owl'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{owl}> ."

        sameAs = F"{owl}sameAs"
        sameAs_ttl = F"{prefix}:sameAs"

    class Formats:
        # formats = "https://www.w3.org/ns/formats/"
        formats = "http://www.w3.org/ns/formats/"
        prefix = 'formats'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{formats}> ."

        turtle = F"{formats}Turtle"
        turtle_ttl = F"{prefix}:Turtle"

        json_ld = F"{formats}JSON-LD"
        json_ld_ttl = F"{prefix}:JSON-LD"

        n3 = F"{formats}N3"
        n3_ttl = F"{prefix}:N3"

        n_Triples = F"{formats}N-Triples"
        n_Triples_ttl = F"{prefix}:N-Triples"

        n_Quads = F"{formats}N-Quads"
        n_Quads_ttl = F"{prefix}:N-Quads"

        ld_Patch = F"{formats}LD_Patch"
        ld_Patch_ttl = F"{prefix}:LD_Patch"

        microdata = F"{formats}microdata"
        microdata_ttl = F"{prefix}:microdata"

        owl_XML = F"{formats}OWL_XML"
        owl_XML_ttl = F"{prefix}:OWL_XML"

        triG = F"{formats}TriG"
        triG_ttl = "F{prefix}:TriG"

        rdfa = F"{formats}RDFa"
        rdfa_ttl = F"{prefix}:RDFa"

        sparql_results_CSV = "http://www.w3.org/ns/formats/SPARQL_Results_CSV"
        sparql_results_CSV_ttl = F"{prefix}:SPARQL_Results_CSV"

    class VoID:
        # void = "http://rdfs.org/ns/void#"
        void = ns.VOID
        prefix = 'void'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{void}> ."

        # A collection of RDF links between two void:Datasets.
        linkset = F"{void}Linkset"
        linkset_ttl = F"{prefix}:Linkset"

        # The void:Dataset that contains the resources in the subject position of this void:Linkset's triples.
        subTarget = F"{void}subjectsTarget"
        subTarget_ttl = F"{prefix}:subjectsTarget"

        # The void:Dataset that contains the resources in the object position of a void:Linkset's triples.
        objTarget = F"{void}objectsTarget"
        objTarget_ttl = F"{prefix}:objectsTarget"

        # One of the two void:Datasets connected by this void:Linkset.
        target = F"{void}target"
        target_ttl = F"{prefix}:target"

        # A void:TechnicalFeature supported by a void:Datset.
        feature = F"{void}feature"
        feature_ttl = F"{prefix}:feature"

        # Specifies the RDF property of the triples in a void:Linkset.
        linkPredicate = F"{void}linkPredicate"
        linkPredicate_tt = F"{prefix}:linkPredicate"

        # The total number of triples contained in the dataset.
        triples = F"{void}triples"
        triples_ttl = F"{prefix}:triples"

        # The total number of entities that are described in the dataset. To be an entity in a dataset, a
        # resource must have a URI, and the URI must match the dataset's void:uriRegexPattern, if any.
        # Authors of VoID files may impose arbitrary additional requirements, for example, they may consider
        # any foaf:Document resources as not being entities.
        entities = F"{void}entities"
        entities_ttl = F"{prefix}:entities"

        # The total number of distinct subjects in the dataset. In other words, the number of distinct URIs
        # or blank nodes that occur in the subject position of triples in the dataset.
        distinctSubjects = F"{void}distinctSubjects"
        distinctSubjects_ttl = F"{prefix}:distinctSubjects"

        # The total number of distinct objects in the dataset. In other words, the number of distinct URIs,
        # blank nodes, or literals that occur in the object position of triples in the dataset.
        distinctObjects = F"{void}distinctObjects"
        distinctObjects_ttl = F"{prefix}:distinctObjects"

        dataset = F"{void}Dataset"
        dataset_ttl = F"{prefix}:Dataset"

        subset = F"{void}subset"
        subset_ttl = F"{prefix}:subset"

        classPartition = F"{void}classPartition"
        classPartition_ttl = F"{prefix}:classPartition"

        propertyPartition = F"{void}propertyPartition"
        propertyPartition_ttl = F"{prefix}:propertyPartition"

        property = F"{void}property"
        property_ttl = F"{prefix}:property"

        voidClass = F"{void}class"
        voidClass_ttl = F"{prefix}:class"

    class SKOS:
        # SKOS Simple Knowledge Organization System Namespace
        # https://www.w3.org/TR/2008/WD-skos-reference-20080829/skos.html

        # skos = "http://www.w3.org/2004/02/skos/core#"
        skos = ns.SKOS
        prefix = 'skos'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{skos}> ."

        broadMatch = F"{skos}broadMatch"
        broadMatch_ttl = F"{prefix}:broadMatch"

        closeMatch = F"{skos}closeMatch"
        closeMatch_ttl = F"{prefix}:closeMatch"

        exactMatch = F"{skos}exactMatch"
        exactMatch_ttl = F"{prefix}:exactMatch"

        narrowMatch = F"{skos}narrowMatch"
        narrowMatch_ttl = F"{prefix}:narrowMatch"

        relatedMatch = F"{skos}relatedMatch"
        relatedMatch_ttl = F"{prefix}:relatedMatch"

    class PROV:
        # prov = "http://www.w3.org/ns/prov#"
        prov = ns.PROV
        prefix = 'prov'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{prov}> ."

        wasDerivedFrom = F"{prov}wasDerivedFrom"
        wasDerivedFrom_ttl = F"{prefix}:wasDerivedFrom"

    class BDB:
        # bdb = "http://vocabularies.bridgedb.org/ops#"
        bdb = 'http://vocabularies.bridgedb.org/ops#'
        prefix = 'bdb'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{bdb}> ."

        lens = F"{bdb}Lens"
        lens_ttl = F"{prefix}:Lens"

    class DCterms:
        # dcterms = "http://purl.org/dc/terms"
        dcterms = ns.DCTERMS
        prefix = 'dcterms'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{dcterms}> ."

        description = F"{dcterms}description"
        description_ttl = F"{prefix}:description"

        license = F"{dcterms}license"
        license_ttl = F"{prefix}:license"

        rights = F"{dcterms}rights"
        rights_ttl = F"{prefix}:rights"

        subject = F"{dcterms}subject"
        subject_ttl = F"{prefix}:subject"

        created = F"{dcterms}created"
        created_ttl = F"{prefix}:created"

        creator = F"{dcterms}creator"
        creator_ttl = F"{prefix}:creator"

        publisher = F"{dcterms}publisher"
        publisher_ttl = F"{prefix}:publisher"

        identifier = F"{dcterms}identifier"
        identifier_ttl = F"{prefix}:identifier"

    class FOAF:
        # foaf = "http://xmlns.com/foaf/0.1/"
        foaf = ns.FOAF
        prefix = 'foaf'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{foaf}> ."

    class Units:
        # units = "http://qudt.org/vocab/unit#"
        units = "http://qudt.org/vocab/unit#"
        prefix = 'units'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{units}> ."

        kilometer = F"{units}Kilometer"
        kilometer_ttl = F"{prefix}:Kilometer ."

        meter = F"{units}Meter"
        meter_ttl = F"{prefix}:meter ."

        centimeter = F"{units}Centimeter"
        centimeter_ttl = F"{prefix}:centimeter ."

        mileUSStatute = F"{units}MileUSStatute"
        mileUSStatute_ttl = F"{prefix}:mileUSStatute ."

        yard = F"{units}Yard"
        yard_ttl = F"{prefix}:yard ."

        inch = F"{units}Inch"
        inch_ttl = F"{prefix}:nch> ."

        foot = F"{units}Foot"
        foot_ttl = F"{prefix}:foot ."

    class PAV:
        # pav = "http://purl.org/pav/"
        pav = "http://purl.org/pav/"
        prefix = 'pav'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{pav}> ."

        importedFromSource = F"{pav}importedFromSource"
        importedFromSource_ttl = F"{prefix}:importedFromSource"

        authors = F"{pav}authors"
        authors_ttl = F"{prefix}:authors"

        contributors = F"{pav}importedFromSource"
        contributors_ttl = F"{prefix}:contributors"

        createdBy = F"{pav}createdBy"
        createdBy_ttl = F"{prefix}:createdBy"

    class SIM:
        # sim = "http://purl.org/ontology/similarity/"
        sim = "http://purl.org/ontology/similarity/"
        prefix = 'sim'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{sim}> ."

        # weight - A weighting value bound to a sim:Association where a value of 0 implies two elements are not at all
        # associated and a higher value implies a closer association.
        weight = F"{sim}weight"
        weight_ttl = F"{prefix}:weight"

        # distance - A weighting value for an Association where a value of 0 implies two elements are the same individual.
        distance = F"{sim}distance"
        distance_ttl = F"{prefix}:distance"

        # method - Specifies the sim:AssociationMethod used to derive a particular Association statement. This should be
        # used when the process for deriving association statements can be described further.
        method = F"{sim}method"
        method_ttl = F"{prefix}:method"

        # description - Specifies some description that discloses the process or set of processes used to derive asso-
        # ciation statements for the given AssociationMethod. This property is depricated in favor of the more appro-
        # priately named sim:workflow property.
        # workflow - Specifies a workflow that discloses the process or set of processes used to derive association
        # statements for the given sim:AssociationMethod
        workflow = F"{sim}workflow"
        workflow_ttl = F"{prefix}:workflow"

        # Network - A network is a grouping of sim:Associations. The associations that comprise a network are specified
        # using a series of sim:edge predicates.
        Network = F"{sim}Network"
        Network_ttl = F"{prefix}:Network"

    class CC:
        # https://labs.creativecommons.org/2011/ccrel-guide/
        # https://creativecommons.org/ns
        # Creative Commons (CC) is an internationally active non-profit organisation that provides free licences for
        # creators to use when making their work available to the public. These licences help the creator to give
        # permission for others to use the work in advance under certain conditions.

        # cc = "http://creativecommons.org/ns#"
        cc = "http://creativecommons.org/ns#"
        prefix = 'cc'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{cc}> ."

        # A License prohibits a Prohibition.
        license = F"{cc}license"
        license_ttl = F"{prefix}:license"

        # A License requires a Requirement.
        requires = F"{cc}requires"
        requires_ttl = F"{prefix}:requires"

        # A License prohibits a Prohibition.
        prohibits = F"{cc}prohibits"
        prohibits_ttl = F"{prefix}:prohibits"

        # The URL of the legal text of a License.
        legalcode = F"{cc}legalcode"
        legalcode_ttl = F"{prefix}:legalcode"

        # A License may be deprecated; provides the date deprecated on.
        deprecatedOn = F"{cc}deprecatedOn"
        deprecatedOn_ttl = F"{prefix}:deprecatedOn"

        # The URL the creator of a Work would like used when attributing re-use.
        attributionName = F"{cc}attributionName"
        attributionName_ttl = F"{prefix}:attributionName"

        # The URL the creator of a Work would like used when attributing re-use.
        attributionURL = F"{cc}attributionURL"
        attributionURL_ttl = F"{prefix}:attributionURL"

    class Time:
        # time = "http://www.w3.org/2006/time#"
        time = "http://www.w3.org/2006/time#"
        prefix = 'time'
        prefix_ttl = F"@prefix {prefix:>{pref_size}}: <{time}> ."

        day = F"{time}unitDay"
        day_ttl = F"{prefix}:unitDay"

        hour = F"{time}unitHour"
        hour_ttl = F"{prefix}:unitHour"

        minute = F"{time}unitMinute"
        minute_ttl = F"{prefix}:unitMinute"

        month = F"{time}unitMonth"
        month_ttl = F"{prefix}:unitMonth"

        second = F"{time}unitSecond"
        second_ttl = F"{prefix}:unitSecond"

        week = F"{time}unitWeek"
        week_ttl = F"{prefix}:unitWeek"

        year = F"{time}unitYear"
        year_ttl = F"{prefix}:unitYear"

        unitType = F"{time}unitType"
        unitType_ttl = F"{prefix}:unitType"

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
            "day": F"{prefix}:unitDay",
            "days": F"{prefix}:unitDay",

            "hour": F"{prefix}:unitHour",
            "hours": F"{prefix}:unitHour",

            "minute": F"{prefix}:unitMinute",
            "minutes": F"{prefix}:unitMinute",

            "month": F"{prefix}:unitMonth",
            "months": F"{prefix}:unitMonth",

            "second": F"{prefix}:unitSecond",
            "seconds": F"{prefix}:unitSecond",

            "week": F"{prefix}:unitWeek",
            "weeks": F"{prefix}:unitWeek",

            "year": F"{prefix}:unitYear",
            "years": F"{prefix}:unitYear",

            "unitType": F"{prefix}:unitType",
            "unitTypes": F"{prefix}:unitType",
        }

        @staticmethod
        def get_uri(time_unit):
            return Namespaces.Time.converter[time_unit.lower()]

        @staticmethod
        def get_uri_ttl(time_unit):
            return Namespaces.Time.converter_ttl[time_unit.lower()]
