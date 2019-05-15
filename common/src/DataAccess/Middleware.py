# import src.Generic.Utility as Ut
import src.Generic.Settings as St
import src.DataAccess.Stardog.Query as Stardog
import src.DataAccess.PostgreSQL.Query as Postgre


# RETURNS A QUERY STRING TO RUN OVER THE DATA STORE OF CHOICE
node_labels_switcher = {
    St.Stardog: Stardog.get_resource_value,
    St.Postgre: Postgre.get_resource_value}


# RETURNS THE RESULT OF A QUERY IN AN XML FORMAT
run_query_xml_switcher = {
    St.Stardog: Stardog.endpoint}


# RETURNS THE RESULT OF A QUERY IN A TABLE (A MATRIX)
run_query_matrix_switcher = {
    # St.Stardog: Stardog.sparql_xml_to_matrix,
    St.Postgre: Postgre.execute_query
}


# from src.DataAccess.Stardog.Query import investigate_resources
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
# investigate_resources(data_example, ["resource_1", "resource_2", "resource_3"])
