export interface Dataset {
    name: string,
    title: string,
    description: string | null,
    collections: Collections,
}

export interface Collections {
    [collectionId: string]: Collection
}

export interface Collection {
    title: string | null,
    total: number,
    downloaded: boolean,
    properties: Properties,
}

export interface Properties {
    [property: string]: Property
}

export interface Property {
    name: string,
    shortenedUri: string,
    density: number,
    isInverse: boolean,
    isLink: boolean,
    isList: boolean,
    isValueType: boolean,
    referencedCollections: string[],
}

const dataset: Dataset = {
    'collections': {
        'as_OrderedCollectionPage': {
            'downloaded': false,
            'properties': {
                '_inverse_prov_wasDerivedFromList': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': '_inverse_prov_wasDerivedFromList',
                    'referencedCollections': ['pnv_PersonName'],
                    'shortenedUri': 'prov:wasDerivedFrom'
                },
                '_inverse_saa_urlScanList': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': '_inverse_saa_urlScanList',
                    'referencedCollections': ['saa_IndexOpOndertrouwregisters'],
                    'shortenedUri': 'saa:urlScan'
                },
                'rdf_typeList': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': 'rdf_typeList',
                    'referencedCollections': [],
                    'shortenedUri': 'rdf:type'
                },
                'saa_url': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'saa_url',
                    'referencedCollections': [],
                    'shortenedUri': 'saa:url'
                },
                'uri': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': false,
                    'name': 'uri',
                    'referencedCollections': [],
                    'shortenedUri': 'uri'
                }
            },
            'title': null,
            'total': 82366
        },
        'bio_Marriage': {
            'downloaded': false, 'properties': {
                '_inverse_bio_eventList': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': '_inverse_bio_eventList',
                    'referencedCollections': ['saa_Person'],
                    'shortenedUri': 'bio:event'
                },
                'bio_partnerList': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': 'bio_partnerList',
                    'referencedCollections': ['saa_Person'],
                    'shortenedUri': 'bio:partner'
                },
                'rdf_typeList': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': 'rdf_typeList',
                    'referencedCollections': [],
                    'shortenedUri': 'rdf:type'
                },
                'rdfs_comment': {
                    'density': 1,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'rdfs_comment',
                    'referencedCollections': [],
                    'shortenedUri': 'rdfs:comment'
                },
                'rdfs_labelList': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': true,
                    'isValueType': true,
                    'name': 'rdfs_labelList',
                    'referencedCollections': [],
                    'shortenedUri': 'rdfs:label'
                },
                'sem_hasActorList': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': 'sem_hasActorList',
                    'referencedCollections': ['sem_Role'],
                    'shortenedUri': 'sem:hasActor'
                },
                'sem_hasLatestEndTimeStamp': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'sem_hasLatestEndTimeStamp',
                    'referencedCollections': [],
                    'shortenedUri': 'sem:hasLatestEndTimeStamp'
                },
                'sem_hasTimeStamp': {
                    'density': 1,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'sem_hasTimeStamp',
                    'referencedCollections': [],
                    'shortenedUri': 'sem:hasTimeStamp'
                },
                'uri': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': false,
                    'name': 'uri',
                    'referencedCollections': [],
                    'shortenedUri': 'uri'
                }
            }, 'title': null, 'total': 202486
        },
        'pnv_PersonName': {
            'downloaded': false, 'properties': {
                '_inverse_pnv_hasName': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': '_inverse_pnv_hasName',
                    'referencedCollections': ['saa_Person'],
                    'shortenedUri': 'pnv:hasName'
                },
                '_inverse_prov_wasDerivedFrom': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': '_inverse_prov_wasDerivedFrom',
                    'referencedCollections': ['saa_Person'],
                    'shortenedUri': 'prov:wasDerivedFrom'
                },
                '_inverse_saa_mentionsBrideName': {
                    'density': 41,
                    'isInverse': true,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': '_inverse_saa_mentionsBrideName',
                    'referencedCollections': ['saa_IndexOpOndertrouwregisters'],
                    'shortenedUri': 'saa:mentionsBrideName'
                },
                '_inverse_saa_mentionsEarlierHusbandName': {
                    'density': 7,
                    'isInverse': true,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': '_inverse_saa_mentionsEarlierHusbandName',
                    'referencedCollections': ['saa_IndexOpOndertrouwregisters'],
                    'shortenedUri': 'saa:mentionsEarlierHusbandName'
                },
                '_inverse_saa_mentionsEarlierWifeName': {
                    'density': 8,
                    'isInverse': true,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': '_inverse_saa_mentionsEarlierWifeName',
                    'referencedCollections': ['saa_IndexOpOndertrouwregisters'],
                    'shortenedUri': 'saa:mentionsEarlierWifeName'
                },
                '_inverse_saa_mentionsGroomName': {
                    'density': 41,
                    'isInverse': true,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': '_inverse_saa_mentionsGroomName',
                    'referencedCollections': ['saa_IndexOpOndertrouwregisters'],
                    'shortenedUri': 'saa:mentionsGroomName'
                },
                'pnv_baseSurname': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'pnv_baseSurname',
                    'referencedCollections': [],
                    'shortenedUri': 'pnv:baseSurname'
                },
                'pnv_givenName': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'pnv_givenName',
                    'referencedCollections': [],
                    'shortenedUri': 'pnv:givenName'
                },
                'pnv_literalName': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'pnv_literalName',
                    'referencedCollections': [],
                    'shortenedUri': 'pnv:literalName'
                },
                'pnv_surnamePrefix': {
                    'density': 15,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'pnv_surnamePrefix',
                    'referencedCollections': [],
                    'shortenedUri': 'pnv:surnamePrefix'
                },
                'prov_wasDerivedFrom': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'prov_wasDerivedFrom',
                    'referencedCollections': ['saa_Scan', 'as_OrderedCollectionPage'],
                    'shortenedUri': 'prov:wasDerivedFrom'
                },
                'rdf_type': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'rdf_type',
                    'referencedCollections': [],
                    'shortenedUri': 'rdf:type'
                },
                'rdfs_label': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'rdfs_label',
                    'referencedCollections': [],
                    'shortenedUri': 'rdfs:label'
                },
                'saa_isInRecord': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'saa_isInRecord',
                    'referencedCollections': ['saa_IndexOpOndertrouwregisters'],
                    'shortenedUri': 'saa:isInRecord'
                },
                'uri': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': false,
                    'name': 'uri',
                    'referencedCollections': [],
                    'shortenedUri': 'uri'
                }
            }, 'title': null, 'total': 1196810
        },
        'saa_IndexOpOndertrouwregisters': {
            'downloaded': false, 'properties': {
                '_inverse_saa_hasDocument': {
                    'density': 99,
                    'isInverse': true,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': '_inverse_saa_hasDocument',
                    'referencedCollections': ['saa_IntendedMarriage'],
                    'shortenedUri': 'saa:hasDocument'
                },
                '_inverse_saa_isInRecordList': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': '_inverse_saa_isInRecordList',
                    'referencedCollections': ['pnv_PersonName'],
                    'shortenedUri': 'saa:isInRecord'
                },
                'rdf_type': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'rdf_type',
                    'referencedCollections': [],
                    'shortenedUri': 'rdf:type'
                },
                'saa_cancelled': {
                    'density': 1,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'saa_cancelled',
                    'referencedCollections': [],
                    'shortenedUri': 'saa:cancelled'
                },
                'saa_collectionNumber': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'saa_collectionNumber',
                    'referencedCollections': [],
                    'shortenedUri': 'saa:collectionNumber'
                },
                'saa_date': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'saa_date',
                    'referencedCollections': [],
                    'shortenedUri': 'saa:date'
                },
                'saa_description': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'saa_description',
                    'referencedCollections': [],
                    'shortenedUri': 'saa:description'
                },
                'saa_hasEvent': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'saa_hasEvent',
                    'referencedCollections': ['saa_IntendedMarriage'],
                    'shortenedUri': 'saa:hasEvent'
                },
                'saa_identifier': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'saa_identifier',
                    'referencedCollections': [],
                    'shortenedUri': 'saa:identifier'
                },
                'saa_inventoryNumber': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'saa_inventoryNumber',
                    'referencedCollections': [],
                    'shortenedUri': 'saa:inventoryNumber'
                },
                'saa_mentionsBrideName': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'saa_mentionsBrideName',
                    'referencedCollections': ['pnv_PersonName'],
                    'shortenedUri': 'saa:mentionsBrideName'
                },
                'saa_mentionsEarlierHusbandName': {
                    'density': 19,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'saa_mentionsEarlierHusbandName',
                    'referencedCollections': ['pnv_PersonName'],
                    'shortenedUri': 'saa:mentionsEarlierHusbandName'
                },
                'saa_mentionsEarlierWifeName': {
                    'density': 21,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'saa_mentionsEarlierWifeName',
                    'referencedCollections': ['pnv_PersonName'],
                    'shortenedUri': 'saa:mentionsEarlierWifeName'
                },
                'saa_mentionsGroomName': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'saa_mentionsGroomName',
                    'referencedCollections': ['pnv_PersonName'],
                    'shortenedUri': 'saa:mentionsGroomName'
                },
                'saa_registrationDate': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'saa_registrationDate',
                    'referencedCollections': [],
                    'shortenedUri': 'saa:registrationDate'
                },
                'saa_sourceReference': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'saa_sourceReference',
                    'referencedCollections': [],
                    'shortenedUri': 'saa:sourceReference'
                },
                'saa_urlScan': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'saa_urlScan',
                    'referencedCollections': ['saa_Scan', 'as_OrderedCollectionPage'],
                    'shortenedUri': 'saa:urlScan'
                },
                'uri': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': false,
                    'name': 'uri',
                    'referencedCollections': [],
                    'shortenedUri': 'uri'
                }
            }, 'title': null, 'total': 497276
        },
        'saa_IntendedMarriage': {
            'downloaded': false, 'properties': {
                '_inverse_bio_eventList': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': '_inverse_bio_eventList',
                    'referencedCollections': ['saa_Person'],
                    'shortenedUri': 'bio:event'
                },
                '_inverse_saa_hasEvent': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': '_inverse_saa_hasEvent',
                    'referencedCollections': ['saa_IndexOpOndertrouwregisters'],
                    'shortenedUri': 'saa:hasEvent'
                },
                'bio_partnerList': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': 'bio_partnerList',
                    'referencedCollections': ['saa_Person'],
                    'shortenedUri': 'bio:partner'
                },
                'rdf_type': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'rdf_type',
                    'referencedCollections': [],
                    'shortenedUri': 'rdf:type'
                },
                'rdfs_comment': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'rdfs_comment',
                    'referencedCollections': [],
                    'shortenedUri': 'rdfs:comment'
                },
                'rdfs_labelList': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': true,
                    'isValueType': true,
                    'name': 'rdfs_labelList',
                    'referencedCollections': [],
                    'shortenedUri': 'rdfs:label'
                },
                'saa_hasDocument': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'saa_hasDocument',
                    'referencedCollections': ['saa_IndexOpOndertrouwregisters'],
                    'shortenedUri': 'saa:hasDocument'
                },
                'sem_hasActorList': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': 'sem_hasActorList',
                    'referencedCollections': ['sem_Role'],
                    'shortenedUri': 'sem:hasActor'
                },
                'sem_hasTimeStamp': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'sem_hasTimeStamp',
                    'referencedCollections': [],
                    'shortenedUri': 'sem:hasTimeStamp'
                },
                'uri': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': false,
                    'name': 'uri',
                    'referencedCollections': [],
                    'shortenedUri': 'uri'
                }
            }, 'title': null, 'total': 497076
        },
        'saa_Person': {
            'downloaded': false, 'properties': {
                '_inverse_bio_partnerList': {
                    'density': 99,
                    'isInverse': true,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': '_inverse_bio_partnerList',
                    'referencedCollections': ['bio_Marriage', 'sem_Event', 'saa_IntendedMarriage'],
                    'shortenedUri': 'bio:partner'
                },
                '_inverse_rdf_valueList': {
                    'density': 99,
                    'isInverse': true,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': '_inverse_rdf_valueList',
                    'referencedCollections': ['sem_Role'],
                    'shortenedUri': 'rdf:value'
                },
                '_inverse_schema_spouse': {
                    'density': 16,
                    'isInverse': true,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': '_inverse_schema_spouse',
                    'referencedCollections': ['saa_Person'],
                    'shortenedUri': 'schema:spouse'
                },
                'bio_eventList': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': 'bio_eventList',
                    'referencedCollections': ['bio_Marriage', 'sem_Event', 'saa_IntendedMarriage'],
                    'shortenedUri': 'bio:event'
                },
                'pnv_hasName': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'pnv_hasName',
                    'referencedCollections': ['pnv_PersonName'],
                    'shortenedUri': 'pnv:hasName'
                },
                'prov_wasDerivedFrom': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'prov_wasDerivedFrom',
                    'referencedCollections': ['pnv_PersonName'],
                    'shortenedUri': 'prov:wasDerivedFrom'
                },
                'rdf_type': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'rdf_type',
                    'referencedCollections': [],
                    'shortenedUri': 'rdf:type'
                },
                'rdfs_label': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'rdfs_label',
                    'referencedCollections': [],
                    'shortenedUri': 'rdfs:label'
                },
                'schema_spouse': {
                    'density': 16,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'schema_spouse',
                    'referencedCollections': ['saa_Person'],
                    'shortenedUri': 'schema:spouse'
                },
                'uri': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': false,
                    'name': 'uri',
                    'referencedCollections': [],
                    'shortenedUri': 'uri'
                }
            }, 'title': null, 'total': 1196810
        },
        'saa_Scan': {
            'downloaded': false,
            'properties': {
                '_inverse_prov_wasDerivedFromList': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': '_inverse_prov_wasDerivedFromList',
                    'referencedCollections': ['pnv_PersonName'],
                    'shortenedUri': 'prov:wasDerivedFrom'
                },
                '_inverse_saa_urlScanList': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': '_inverse_saa_urlScanList',
                    'referencedCollections': ['saa_IndexOpOndertrouwregisters'],
                    'shortenedUri': 'saa:urlScan'
                },
                'rdf_typeList': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': 'rdf_typeList',
                    'referencedCollections': [],
                    'shortenedUri': 'rdf:type'
                },
                'saa_url': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'saa_url',
                    'referencedCollections': [],
                    'shortenedUri': 'saa:url'
                },
                'uri': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': false,
                    'name': 'uri',
                    'referencedCollections': [],
                    'shortenedUri': 'uri'
                }
            },
            'title': null,
            'total': 82366
        },
        'sem_Event': {
            'downloaded': false, 'properties': {
                '_inverse_bio_eventList': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': '_inverse_bio_eventList',
                    'referencedCollections': ['saa_Person'],
                    'shortenedUri': 'bio:event'
                },
                'bio_partnerList': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': 'bio_partnerList',
                    'referencedCollections': ['saa_Person'],
                    'shortenedUri': 'bio:partner'
                },
                'rdf_typeList': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': 'rdf_typeList',
                    'referencedCollections': [],
                    'shortenedUri': 'rdf:type'
                },
                'rdfs_comment': {
                    'density': 1,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'rdfs_comment',
                    'referencedCollections': [],
                    'shortenedUri': 'rdfs:comment'
                },
                'rdfs_labelList': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': true,
                    'isValueType': true,
                    'name': 'rdfs_labelList',
                    'referencedCollections': [],
                    'shortenedUri': 'rdfs:label'
                },
                'sem_hasActorList': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': 'sem_hasActorList',
                    'referencedCollections': ['sem_Role'],
                    'shortenedUri': 'sem:hasActor'
                },
                'sem_hasLatestEndTimeStamp': {
                    'density': 99,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'sem_hasLatestEndTimeStamp',
                    'referencedCollections': [],
                    'shortenedUri': 'sem:hasLatestEndTimeStamp'
                },
                'sem_hasTimeStamp': {
                    'density': 1,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'sem_hasTimeStamp',
                    'referencedCollections': [],
                    'shortenedUri': 'sem:hasTimeStamp'
                },
                'uri': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': false,
                    'name': 'uri',
                    'referencedCollections': [],
                    'shortenedUri': 'uri'
                }
            }, 'title': null, 'total': 202486
        },
        'sem_Role': {
            'downloaded': false, 'properties': {
                '_inverse_sem_hasActor': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': '_inverse_sem_hasActor',
                    'referencedCollections': ['bio_Marriage', 'sem_Event', 'saa_IntendedMarriage'],
                    'shortenedUri': 'sem:hasActor'
                },
                'rdf_type': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'rdf_type',
                    'referencedCollections': [],
                    'shortenedUri': 'rdf:type'
                },
                'rdf_value': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'rdf_value',
                    'referencedCollections': ['saa_Person'],
                    'shortenedUri': 'rdf:value'
                },
                'rdfs_label': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'rdfs_label',
                    'referencedCollections': [],
                    'shortenedUri': 'rdfs:label'
                },
                'sem_roleType': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'sem_roleType',
                    'referencedCollections': ['sem_RoleType'],
                    'shortenedUri': 'sem:roleType'
                },
                'uri': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': false,
                    'name': 'uri',
                    'referencedCollections': [],
                    'shortenedUri': 'uri'
                }
            }, 'title': null, 'total': 1398680
        },
        'sem_RoleType': {
            'downloaded': false,
            'properties': {
                '_inverse_sem_roleTypeList': {
                    'density': 100,
                    'isInverse': true,
                    'isLink': true,
                    'isList': true,
                    'isValueType': false,
                    'name': '_inverse_sem_roleTypeList',
                    'referencedCollections': ['sem_Role'],
                    'shortenedUri': 'sem:roleType'
                },
                'rdf_type': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'rdf_type',
                    'referencedCollections': [],
                    'shortenedUri': 'rdf:type'
                },
                'rdfs_label': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'rdfs_label',
                    'referencedCollections': [],
                    'shortenedUri': 'rdfs:label'
                },
                'uri': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': false,
                    'name': 'uri',
                    'referencedCollections': [],
                    'shortenedUri': 'uri'
                }
            },
            'title': null,
            'total': 20
        },
        'void_Dataset': {
            'downloaded': false, 'properties': {
                '_inverse_void_inDataset': {
                    'density': 33,
                    'isInverse': true,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': '_inverse_void_inDataset',
                    'referencedCollections': ['void_Dataset'],
                    'shortenedUri': 'void:inDataset'
                },
                '_inverse_void_subset': {
                    'density': 33,
                    'isInverse': true,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': '_inverse_void_subset',
                    'referencedCollections': ['void_Dataset'],
                    'shortenedUri': 'void:subset'
                },
                'dcterms_description': {
                    'density': 66,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'dcterms_description',
                    'referencedCollections': [],
                    'shortenedUri': 'dcterms:description'
                },
                'dcterms_modified': {
                    'density': 66,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'dcterms_modified',
                    'referencedCollections': [],
                    'shortenedUri': 'dcterms:modified'
                },
                'dcterms_title': {
                    'density': 66,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': true,
                    'name': 'dcterms_title',
                    'referencedCollections': [],
                    'shortenedUri': 'dcterms:title'
                },
                'rdf_type': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'rdf_type',
                    'referencedCollections': [],
                    'shortenedUri': 'rdf:type'
                },
                'uri': {
                    'density': 100,
                    'isInverse': false,
                    'isLink': false,
                    'isList': false,
                    'isValueType': false,
                    'name': 'uri',
                    'referencedCollections': [],
                    'shortenedUri': 'uri'
                },
                'void_inDataset': {
                    'density': 33,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'void_inDataset',
                    'referencedCollections': ['void_Dataset'],
                    'shortenedUri': 'void:inDataset'
                },
                'void_subset': {
                    'density': 33,
                    'isInverse': false,
                    'isLink': true,
                    'isList': false,
                    'isValueType': false,
                    'name': 'void_subset',
                    'referencedCollections': ['void_Dataset'],
                    'shortenedUri': 'void:subset'
                }
            }, 'title': null, 'total': 3
        }
    },
    'description': 'Enriched version of the Index op ondertrouwregisters. Enrichment done by Golden Agents. (25-05-2020)',
    'name': 'index_op_ondertrouwregister_enriched_20200525',
    'title': 'Stadsarchief Amsterdam: Index op ondertrouwregisters'
};

export default dataset;