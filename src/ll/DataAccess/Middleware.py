import ll.Generic.Settings as St
import ll.DataAccess.Stardog.Query as Stardog

# from ll.data.query import get_property_values_queries, get_property_values

# RETURNS A QUERY STRING TO RUN OVER THE DATA STORE OF CHOICE
node_labels_switcher = {
    St.Stardog: Stardog.get_resource_value,
    # St.Postgre: lambda targets, resources: get_property_values_queries(targets, uris=resources)
    St.Postgre: lambda targets, resources: None
}

# RETURNS THE RESULT OF A QUERY IN AN XML FORMAT
run_query_xml_switcher = {
    St.Stardog: Stardog.endpoint
}

# RETURNS THE RESULT OF A QUERY IN A TABLE (A MATRIX)
run_query_matrix_switcher = {
    # St.Stardog: Stardog.sparql_xml_to_matrix,
    # St.Postgre: get_property_values
    St.Postgre: None
}
