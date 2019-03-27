import re


# **************************************************************************************
# THIS FUNCTION BUILDS CONTEXTUAL INFORMATION ON A [SET OF PROVIDED RESOURCES]
# BASED ON [DATASETS] AND [MANDATORY PROPERTIES] OR [OPTIONAL PROPERTIES] OF INTEREST
# **************************************************************************************
def investigate_resources(data, resources):

    # DATASET AND THE PROPERTIES OF INTEREST. EACH PROPERTY CAN BE PROVIDED WITH AN ALTERNATIVE NAME
    # data_example = {
    #     'dataset-1': [
    #         {
    #             'entity_type': 'Person',
    #             'mandatory': [('property-1', 'name'), ('property-10', ""), ('property-15', '')],
    #             'optional': [('property-00', 'country'), ('property-00', 'country_name'), ('property-00', 'address')]
    #         }
    #     ],
    #     'dataset-2': [
    #         {
    #             'entity_type': 'Person',
    #             'mandatory': [('property-2', 'name'), ('property-23', ""), ('property-30', "")],
    #             'optional': []
    #         },
    #         {
    #             'entity_type': 'Human',
    #             'mandatory': [('property-2', 'name'), ('property-20', ""), ('property-25', "")],
    #             'optional': []
    #         }
    #     ],
    #     'dataset-3': [
    #         {
    #             'entity_type': 'Person',
    #             'mandatory': [('property-3', 'name'), ('property-36', ""), ('property-33', "")],
    #             'optional': []
    #         }
    #     ]
    # }

    # THE LIST OF RESOURCES TO INVESTIGATE
    # resource = ['resource-1', 'resource-2', 'resource-3']

    # QUERY TEMPLE EXAMPLE
    """
    SELECT *
    {
        # LIST OR RESOURCES TO INVESTIGATE
        VALUES ?resource { resource-1 resource-2 resource-3 }

        {
            GRAPH <dataset-2>
            {
                BIND( <dataset-2> as ?dataset)
                ?resource <property-2> ?name .
                ?resource <property-23> ?dataset-2_property-23 .
                ?resource <property-30> ?dataset-2_property-30 .
            }
        }	UNION

        {
            GRAPH <dataset-3>
            {
                BIND( <dataset-3> as ?dataset)
                ?resource <property-3> ?name .
                ?resource <property-36> ?dataset-3_property-36 .
                ?resource <property-33> ?dataset-3_property-33 .
            }
        }	UNION

        {
            GRAPH <dataset-1>
            {
                BIND( <dataset-1> as ?dataset)
                ?resource <property-1> ?name .
                ?resource <property-10> ?dataset-1_property-10 .
                ?resource <property-15> ?dataset-1_property-15 .
                OPTIONAL { ?resource <property-00> ?country . }
            }
        }
    }
    """

    count_union = 0
    sub_query = ""

    template_1 = """\t{}
        {{
            # RESOURCE DATA ON DATASET {}
            GRAPH {}
            {{ \n\t\t\t\t{}\n{}{}
            }}
        }}"""

    template_2 = """
    SELECT DISTINCT *
    {{
        # LIST OR RESOURCES TO INVESTIGATE
        VALUES ?resource
        {{ {}
        }}
        {}
    }} ORDER BY ?dataset ?resource

    """

    # CONVERTING THE LIST INTO A SPACE SEPARATED LIST
    resource_enumeration = "\n\t\t\t{}".format("\n\t\t\t".join(to_nt_format(item) for item in resources))

    for dataset, values in data.items():

        for dictionary in values:

            e_type = dictionary['entity_type']
            mandatory = dictionary['mandatory']
            optional = dictionary['optional']

            # GENERATE THE SUB-QUERY FOR MANDATORY PROPERTIES
            sub_mandatory = "\t\t\t\t?resource a <{}> .\n".format(e_type)
            sub_mandatory += "\n".join(
                "\t\t\t\t?resource {0} ?{1} .".format(
                    to_nt_format(uri), alternative if len(alternative) > 0 else
                    "{}_{}".format(
                        local_name(dataset),
                        local_name(uri))) for uri, alternative in mandatory)

            # GENERATE THE SUB-QUERY FOR OPTIONAL PROPERTIES
            if len(optional) > 0:
                sub_optional = "\n".join(
                    "\t\t\t\tOPTIONAL {{ ?resource {0} ?{1} . }}".format(
                        to_nt_format(uri), alternative if len(alternative) > 0 else
                        "{}_{}".format(
                            local_name(dataset),
                            local_name(uri))) for uri, alternative in optional)
            else:
                sub_optional = ""

            sub_optional = "\n{}".format(sub_optional) if (len(sub_optional) > 0) else sub_optional

            # BIND THE DATASET TO HAVE IT IN THE SELECT
            bind = "BIND( {} as ?dataset)".format(to_nt_format(dataset))

            # ACCUMULATE THE SUB-QUERIES
            sub_query += template_1.format(
                "UNION\n" if count_union > 0 else "", dataset, to_nt_format(dataset), bind, sub_mandatory,
                sub_optional)
            count_union += 1


    # THE FINAL QUERY
    query = template_2.format(resource_enumeration, sub_query)
    return query


# **************************************************************************************
# HELPER FUNCTIONS
# **************************************************************************************

def is_property_path(resource):

    temp = str(resource).strip()
    check = re.findall("> */ *<", temp)
    return len(check) != 0


def is_nt_format(resource):
    try:
        temp = resource.strip()
        return temp.startswith("<") and temp.endswith(">")

    except Exception as err:
        print ("Exception:", err)
        return False


def to_nt_format(resource):

    try:
        if is_nt_format(resource) is True:
            return resource
        else:
            return "<{}>".format(resource)

    except Exception as err:
        print("Exception:", err.__str__())
        return resource


def local_name(uri, sep="_"):

    # print "URI: {}".format(uri)
    # print type(uri)

    if uri is None:
        return None

    if len(uri) == 0:
        return None

    # if type(uri) is not str:
    #     return None

    check = re.findall("<([^<>]*)>/*", uri)

    if is_property_path(uri) or is_nt_format(uri) or len(check) > 0:

        name = ""
        pro_list = check

        for i in range(len(pro_list)):
            local = local_name(pro_list[i])
            if i == 0:
                name = local
            else:
                name = "{}{}{}".format(name, sep, local)
                # print ">>>> name: ", name
        return name

    else:
        pattern = ".*[\/\#](.*)$"
        local = re.findall(pattern, uri)
        if len(local) > 0 and len(local[0]) > 0:
            return local[0]
        else:
            return uri


if __name__ == "__main__":

    data_example = {
        'dataset-1': [
            {
                'entity_type': 'Person',
                'mandatory': [('property-1', 'name'), ('property-10', ""), ('property-15', '')],
                'optional': [('property-00', 'country'), ('property-00', 'country_name'), ('property-00', 'address')]
            }
        ],
        'dataset-2': [
            {
                'entity_type': 'Person',
                'mandatory': [('property-2', 'name'), ('property-23', ""), ('property-30', "")],
                'optional': []
            },
            {
                'entity_type': 'Human',
                'mandatory': [('property-2', 'name'), ('property-20', ""), ('property-25', "")],
                'optional': []
            }
        ],
        'dataset-3': [
            {
                'entity_type': 'Person',
                'mandatory': [('property-3', 'name'), ('property-36', ""), ('property-33', "")],
                'optional': []
            }
        ]
    }

    query = investigate_resources(data_example, ["resource_1", "resource_2", "resource_3"])

    print(query)