class Namespaces:
    class RDF:
        rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        prefix = 'rdf'

        type = F"{prefix}:type"
        statement = F"{prefix}:Statement"

    class RDFS:
        rdfs = "http://www.w3.org/2000/01/rdf-schema#"
        prefix = 'rdfs'

        resource = F"{prefix}:Resource"
        label = F"{prefix}:label"
        sequence = F"{prefix}:Sequence"
        comment = F"rdfs:comment"
        seeAlso = F"rdfs:seeAlso"

    class XSD:
        xsd = "http://www.w3.org/2001/XMLSchema#"
        prefix = 'xsd'

    class OWL:
        owl = "http://www.w3.org/2002/07/owl#"
        prefix = 'owl'

        sameAs = F"{prefix}:sameAs"

    class Formats:
        formats = "http://www.w3.org/ns/formats/"
        prefix = 'formats'

        turtle = F"{prefix}:Turtle"
        json_ld = F"{prefix}:JSON-LD"
        n3 = F"{prefix}:N3"
        n_triples = F"{prefix}:N-Triples"
        n_quads = F"{prefix}:N-Quads"
        ld_patch = F"{prefix}:LD_Patch"
        microdata = F"{prefix}:microdata"
        owl_xml = F"{prefix}:OWL_XML"
        trig = F"{prefix}:TriG"
        rdfa = F"{prefix}:RDFa"
        sparql_results_csv = F"{prefix}:SPARQL_Results_CSV"

    class VoID:
        void = "http://rdfs.org/ns/void#"
        prefix = 'void'

        linkset = F"{prefix}:Linkset"
        sub_target = F"{prefix}:subjectsTarget"
        obj_target = F"{prefix}:objectsTarget"
        target = F"{prefix}:target"
        feature = F"{prefix}:feature"
        link_predicate_tt = F"{prefix}:linkPredicate"
        triples = F"{prefix}:triples"
        entities = F"{prefix}:entities"
        distinct_subjects = F"{prefix}:distinctSubjects"
        distinct_objects = F"{prefix}:distinctObjects"
        dataset = F"{prefix}:Dataset"
        subset = F"{prefix}:subset"
        class_partition = F"{prefix}:classPartition"
        property_partition = F"{prefix}:propertyPartition"
        property = F"{prefix}:property"
        void_class = F"{prefix}:class"

    class SKOS:
        skos = "http://www.w3.org/2004/02/skos/core#"
        prefix = 'skos'

        broad_match = F"{prefix}:broadMatch"
        close_match = F"{prefix}:closeMatch"
        exact_match = F"{prefix}:exactMatch"
        narrow_match = F"{prefix}:narrowMatch"
        related_match = F"{prefix}:relatedMatch"

    class PROV:
        prov = "http://www.w3.org/ns/prov#"
        prefix = 'prov'

        was_derived_from = F"{prefix}:wasDerivedFrom"

    class DC:
        dc = "http://purl.org/dc/elements/1.1/"
        prefix = 'dc'

        language = F"{prefix}:language"

    class DCterms:
        dcterms = "http://purl.org/dc/terms"
        prefix = 'dcterms'

        description = F"{prefix}:description"
        license = F"{prefix}:license"
        rights = F"{prefix}:rights"
        subject = F"{prefix}:subject"
        created = F"{prefix}:created"
        creator = F"{prefix}:creator"
        publisher = F"{prefix}:publisher"
        identifier = F"{prefix}:identifier"

    class Units:
        units = "http://qudt.org/vocab/unit#"
        prefix = 'units'

        kilometer = F"{prefix}:Kilometer ."
        meter = F"{prefix}:meter ."
        centimeter = F"{prefix}:centimeter ."
        mile_us_statute = F"{prefix}:mileUSStatute ."
        yard = F"{prefix}:yard ."
        inch = F"{prefix}:nch> ."
        foot = F"{prefix}:foot ."

    class PAV:
        pav = "http://purl.org/pav/"
        prefix = 'pav'

        imported_from_source = F"{prefix}:importedFromSource"
        authors = F"{prefix}:authors"
        contributors = F"{prefix}:contributors"
        created_by = F"{prefix}:createdBy"

    class SIM:
        sim = "http://purl.org/void_plus/similarity/"
        prefix = 'sim'

        weight = F"{prefix}:weight"
        distance = F"{prefix}:distance"
        method = F"{prefix}:method"
        workflow = F"{prefix}:workflow"
        network = F"{prefix}:Network"

    class CC:
        cc = "http://creativecommons.org/ns#"
        prefix = 'cc'

        license = F"{prefix}:license"
        requires = F"{prefix}:requires"
        prohibits = F"{prefix}:prohibits"
        legalcode = F"{prefix}:legalcode"
        deprecated_on = F"{prefix}:deprecatedOn"
        attribution_name = F"{prefix}:attributionName"
        attribution_url = F"{prefix}:attributionURL"

    class ISO:
        iso = "https://id.loc.gov/vocabulary/iso639-1/"
        prefix = "iso_369_1"

    class Time:
        time = "http://www.w3.org/2006/time#"
        prefix = 'time'

        day = F"{prefix}:unitDay"
        hour = F"{prefix}:unitHour"
        minute = F"{prefix}:unitMinute"
        month = F"{prefix}:unitMonth"
        second = F"{prefix}:unitSecond"
        week = F"{prefix}:unitWeek"
        year = F"{prefix}:unitYear"
        unit_type = F"{prefix}:unitType"
