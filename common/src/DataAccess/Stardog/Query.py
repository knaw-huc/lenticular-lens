import time
import xmltodict
import collections
import src.Generic.Utility as Ut
import src.Generic.Settings as St
import src.Generic.NameSpace as Ns
from io import StringIO as Buffer
import src.Generic.Server_Settings as Svr
import urllib.request as request_url
import urllib.parse as parse_url
import urllib.error as error_url
from kitchen.text.converters import to_bytes

DATABASE = Svr.settings[St.database]
HOST = Svr.settings[St.stardog_host_name]

ERROR = "No connection could be made because the target machine actively refused it"
ERROR_2 = 'The query was successfully executed but no feedback was returned'

def endpoint(query):

    """
        param query         : The query that is to be run against the SPARQL endpoint
        param database_name : The name of the database () in with the named-graph resides
        param host          : the host (server) name
        return              : returns the result of the query in the default format of the endpoint.
                            In the case of STARDOG, the sever returns an XML result.
    """

    if type(query) is not str:
        return F"FETCHING DATA FROM AN ENDPOINT REQUIRES A STRING AS QUERY. THE INPUT IS OF TYPE {type(query)}"

    q = to_bytes(query)
    # print query
    # Content-Type: application/json
    # b"Accept": b"text/json"
    # 'output': 'application/sparql-results+json'
    # url = b"http://{}:{}/annex/{}/sparql/query?".format("localhost", "5820", "linkset")
    # headers = {b"Content-Type": b"application/x-www-form-urlencoded",
    #            b"Authorization": b"Basic YWRtaW46YWRtaW5UMzE0YQ=="}

    # THIS SHOULD WORK:
    # The Stardog SPARQL endpoint is http://<server>:<port>/{db}/query.
    # http://145.100.59.152:5820/risis_test#!/query/
    url = "http://{}/annex/{}/sparql/query?".format(HOST, DATABASE)
    # url = b"http://{}/{}#!/query/".format(HOST, DATABASE)
    # print(url)
    params = parse_url.urlencode(
        {b'query': q, b'format': b'application/sparql-results+json',
         b'timeout': b'0', b'debug': b'on', b'should-sponge': b''})
    headers = {b"Content-Type": b"application/x-www-form-urlencoded"}

    """
        Authentication
    """
    user = Svr.settings[St.stardog_user]
    password = Svr.settings[St.stardog_pass]
    passman = request_url.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url, user, password)
    request_url.install_opener(request_url.build_opener(request_url.HTTPBasicAuthHandler(passman)))
    request = request_url.Request(url, data=bytes(params, encoding="utf-8"), headers=headers)

    # print "THE REQUEST'S FULL URI: " + request.get_full_url()
    # print "THE REQUEST'S DATA: {}".format(request.data)

    request.get_method = lambda: "POST"
    try:

        response = request_url.urlopen(request)
        result = response.read()

        # print "NONE", result is None
        # print "EMPTY", len(result)
        return {St.message: "OK", St.result: result}

    except TypeError as err:
        print(F"\t{err}")

    except(error_url.HTTPError, RuntimeError, TypeError, NameError, Exception) as err :
        message = err.read()
        if len(message) == 0:
            message = err

        if str(message).__contains__("Service Unavailable") or str(message).__contains__("Error 503"):
            print("THE SERVER IS NOT ON")
        else:
            print("USING THIS QUERY {}\nERROR CODE {}: {}".format(query, err.code, message))
        return {St.message: message, St.result: None}

    except Exception as err:
        if str(err).__contains__("No connection") is True:
            # logger.warning(err)
            # print ERROR
            return {St.message: ERROR, St.result: None}

        elif str(err).__contains__("timeout") is True:
            print("Query execution cancelled: Execution time exceeded query timeout")
            return {St.message: "Query execution cancelled: Execution time exceeded query timeout.",
                    St.result: None}

        # logger.warning(err)
        message = "\nOR MAYBE THERE IS AN ERROR IN THIS QUERY"
        print(message + "\n" + query)
        return {St.message: err, St.result: None}


def endpoint_db(query, database):

    """
        param query         : The query that is to be run against the SPARQL endpoint
        param database_name : The name of the database () in with the named-graph resides
        param host          : the host (server) name
        return              : returns the result of the query in the default format of the endpoint.
                            In the case of STARDOG, the sever returns an XML result.
    """

    q = to_bytes(query)
    # print query
    # Content-Type: application/json
    # b"Accept": b"text/json"
    # 'output': 'application/sparql-results+json'
    # url = b"http://{}:{}/annex/{}/sparql/query?".format("localhost", "5820", "linkset")
    # headers = {b"Content-Type": b"application/x-www-form-urlencoded",
    #            b"Authorization": b"Basic YWRtaW46YWRtaW5UMzE0YQ=="}

    # THIS SHOULD WORK:
    # The Stardog SPARQL endpoint is http://<server>:<port>/{db}/query.
    # http://145.100.59.152:5820/risis_test#!/query/
    url = "http://{}/annex/{}/sparql/query?".format(HOST, database)
    # url = b"http://{}/{}#!/query/".format(HOST, DATABASE)
    # print url
    params = parse_url.urlencode(
        {b'query': q, b'format': b'application/sparql-results+json',
         b'timeout': b'0', b'debug': b'on', b'should-sponge': b''})
    headers = {b"Content-Type": b"application/x-www-form-urlencoded"}

    """
        Authentication
    """
    user = Svr.settings[St.stardog_user]
    password = Svr.settings[St.stardog_pass]
    passman = request_url.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url, user, password)
    request_url.install_opener(request_url.build_opener(request_url.HTTPBasicAuthHandler(passman)))
    request = request_url.Request(url, data=bytes(params, encoding="utf-8"), headers=headers)

    # print "THE REQUEST'S FULL URI: " + request.get_full_url()
    # print "THE REQUEST'S DATA: {}".format(request.data)

    request.get_method = lambda: "POST"
    try:
        response = request_url.urlopen(request)
        result = response.read()
        # print result
        # print "NONE", result is None
        # print "EMPTY", len(result)
        return {St.message: "OK", St.result: result}

    except TypeError as err:
        print(F"\t{err}")

    except error_url.HTTPError as err:
        message = err.read()
        if len(message) == 0:
            message = err

        if str(message).__contains__("Service Unavailable") or str(message).__contains__("Error 503"):
            print("THE SERVER IS NOT ON")
        else:
            print("USING THIS QUERY {}\nERROR CODE {}: {}".format(query, err.code, message))
        return {St.message: message, St.result: None}

    except Exception as err:

        if str(err).__contains__("No connection") is True:
            # logger.warning(err)
            # print ERROR
            return {St.message: ERROR, St.result: None}

        elif str(err).__contains__("timeout") is True:
            print("Query execution cancelled: Execution time exceeded query timeout")
            return {St.message: "Query execution cancelled: Execution time exceeded query timeout.",
                    St.result: None}

        # logger.warning(err)
        message = "\nOR MAYBE THERE IS AN ERROR IN THIS QUERY"
        print(message + "\n" + query)
        return {St.message: err, St.result: None}


def boolean_endpoint_response(query, display=False):

    # if query.lower().__contains__('ask') is False:
    #     print "THE QUERY IS NOT OF TYPE [ASK]"
    #     return None

    # print query
    drop_start = time.time()
    response = endpoint(query)
    drop_end = time.time()
    result = None
    # print response
    if response[St.result] is not None:
        if len(response[St.result]) == 0:
            return ERROR_2
        drops_doc = xmltodict.parse(response[St.result])
        result = drops_doc['sparql']['boolean']
        # print "BOOLEAN QUERY RESULT: {}".format(result)
        if display is True:
            print(">>> Query executed : {:<14}".format(result))
            print(">>> Executed in    : {:<14} minute(s)".format(str((drop_end - drop_start) / 60)))
            print(">>> Query details  : {}\n".format(query))
            print("")
    else:
        print(query)

    return result


def delete_serialised_clusters(graph):
    # DELETE THE NAME AND CLUSTER SIZE OF THE ALIGNMENT CLUSTERED
    query = """
    delete
    {{
        <{0}> <{1}serialisedClusters> ?serialised .
        <{0}> <{1}numberOfClusters> ?numberOfClusters .
    }}

    where
    {{
        <{0}> <{1}serialisedClusters> ?serialised .
        <{0}> <{1}numberOfClusters> ?numberOfClusters .
    }}
    """.format(graph, Ns.alivocab)
    endpoint(query=query)
    print("DONE1!!")


def sparql_xml_to_matrix(query):

    # query = bytes(F"{query}", encoding="utf-8")

    name_index = dict()

    if type(query) is not str and type(query) is not bytes:
        message = "THE QUERY NEEDS TO BE OF TYPE STRING. {} WAS GIVEN".format(type(query))
        print(message)
        return {St.message: message, St.result: None}

    if (query is None) or (query == ""):
        message = "Empty query"
        print(message)
        return {St.message: message, St.result: None}

    # start_time = time.time()
    matrix = None
    # logger.info("XML RESULT TO TABLE")
    # print query

    # if query.lower().__contains__("optional") is True:
    #     message = "MATRIX DOES NOT YET DEAL WITH OPTIONAL"
    #     return {St.message: message, St.result: None}

    response = endpoint(query)
    # logger.info("1. RESPONSE OBTAINED")
    # print response[St.result]

    # DISPLAYING THE RESULT

    if response and response[St.message] == "OK":

        # print "response:", response[St.result]
        # print "response length:", len(response[St.result])

        if len(response[St.result]) == 0:
            message = "NO RESULT FOR THE QUERY"
            return {St.message: message, St.result: None}

        # logger.info("2. RESPONSE IS NOT ''NONE''")

        if True:
            # print response[St.result]
            xml_doc = xmltodict.parse(response[St.result])
            # print "3. FROM XML TO DOC IN {}".format(str(time.time() - start_time))

            # VARIABLES
            # print "4. GETTING VARIABLE'S LIST FROM XML_DOC"
            variables_list = xml_doc['sparql']['head']['variable']
            # print "Variable List", variables_list
            # print "5. EXTRACTED IN {} SECONDS".format(str(time.time() - start_time))

            variables_size = len(variables_list)
            # print "6. VARIABLE SIZE:", variables_size

            # RESULTS
            # print "7. GETTING RESULT'S LIST FROM XML_DOC"
            results = xml_doc['sparql']['results']
            # print "8. IN {}".format(str(time.time() - start_time))

            if results is not None:
                # print "9. RESULT LIST IS NOT NONE"
                results = results['result']
                # print results
                # print type(results)
            else:
                message = "NO RESULT FOR THE QUERY"
                return {St.message: message, St.result: None}
                # print query

            """ >>> SINGLE RESULT """
            if type(results) is collections.OrderedDict:
                # print "SINGLE RESULT"
                # Creates a list containing h lists, each of w items, all set to 0
                # INITIALIZING THE MATRIX
                w, h = variables_size, 2
                # print "Creating matrix with size {} by {}".format(w, h)
                # x*y*0 to avoid weak error say x and y where not used
                matrix = [[str(x*y*0).replace("0", "") for x in range(w)] for y in range(h)]
                # print matrix
                col = -1

                if variables_size == 1:
                    for name, variable in variables_list.items():
                        # HEADER
                        col += 1
                        # print variable
                        matrix[0][col] = variable
                        # print matrix

                    # RECORDS
                    for key, value in results.items():
                        # print type(value)
                        if type(value) is collections.OrderedDict:
                            item_value = list(value.items())[1][1]
                            if "#text" in item_value:
                                # print to_bytes(item_value["#text"])
                                matrix[1][0] = to_bytes(item_value["#text"])
                            else:
                                # matrix[1][0] = to_bytes(item_value)
                                matrix[1][0] = item_value
                        else:
                            # matrix[1][0] = to_bytes(value.items()[1][1])
                            matrix[1][0] = value.items()[1][1]

                else:
                    # print "Variable greater than 1"
                    # HEADER
                    for variable in variables_list:
                        for key, value in variable.items():
                            col += 1
                            # matrix[0][col] = to_bytes(value)
                            matrix[0][col] = value
                            # name_index[to_bytes(value)] = col
                            name_index[value] = col
                            # print "{} was inserted".format(value)
                            # print matrix

                    # RECORDS
                    # print results.items()
                    for key, value in results.items():
                        # COLUMNS
                        # print "Key: ", key
                        # print "Value: ", value
                        for data in value:
                            # print "value Items: ", value.items()[i][1]
                            # print "Length:", len(value.items())
                            if type(data) is list:
                                # print "value:", value
                                # data = value[i]

                                # get_property = data['@name']
                                # print "get_property:", get_property
                                # index = name_index[get_property]
                                # print "index", index
                                index = name_index[data['@name']]
                                item = data.items()[1][1]
                                # print data['@name'], name_index[data['@name']]
                                matrix[1][index.encode()] = to_bytes(item)

                            elif type(data) is collections.OrderedDict:
                                data = list(data.items())
                                # print(name_index)
                                index = name_index[data[0][1]]
                                matrix[1][index] = data[1][1]
                                # if data.items()[1][0] != '@name':
                                #     item = data.items()[1][1]
                                #     matrix[1][index] = to_bytes(item)
                                #     # print "Collection:", value.items()[i][0]
                                # else:
                                #     item = ""

                            # if type(item) is collections.OrderedDict:
                            #     # print "Data is a collection"
                            #     # print "{} was inserted".format(data.items()[1][1])
                            #     matrix[1][index] = to_bytes(item.items()[1][1])
                            else:
                                # print "data is regular"
                                # print "{} was inserted".format(data)
                                # matrix[1][index] = to_bytes(item)
                                # matrix[1][index] = item
                                # matrix[1][index] = data
                                # print matrix
                                print("PROBLEM!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

                    # print "The matrix is: {}".format(matrix)

            """ >>> MORE THAN ONE RESULT """
            if type(results) is list:
                # print "THE LIST CONTAINS MORE THAN ONE RESULTS"
                row = 0
                columns = -1
                row_size = len(results)

                # Creates a list containing h lists, each of w items, all set to 0
                w, h = variables_size, row_size + 1

                # print "INITIALIZING THE MATRIX FOR: [{}][{}]".format(h, w)
                matrix = [[str(x*y*0).replace("0", "") for x in range(w)] for y in range(h)]

                # HEADER
                # print "UPDATING MATRIX'S HEADER"

                if type(variables_list) is collections.OrderedDict:
                    variables_list = list(variables_list.items())
                    for i in range(0, len(variables_list)):
                        matrix[0][i] = str(variables_list[i][1])

                else:
                    for variable in variables_list:

                        if type(variable) is collections.OrderedDict:
                            for key, value in variable.items():
                                columns += 1
                                # print "COLUMN: ", columns, value
                                # print value
                                # matrix[0][columns] = to_bytes(value)
                                matrix[0][columns] = value
                                name_index[to_bytes(value)] = columns
                        else:
                            # print "TYPE", type(variables_list)
                            # print "value:", variables_list.items()[0][1]
                            columns += 1
                            # print "COLUMN: ", columns
                            # matrix[0][columns] = to_bytes(variables_list.items()[0][1])
                            # print(variable)
                            matrix[0][columns] = variables_list.items()[0][1]

                # RECORDS
                # print "UPDATING MATRIX WITH VARIABLES' VALUES"
                for result in results:

                    # ROWS
                    if variables_size == 1:
                        # result = list(result)

                        for key, value in result.items():
                            row += 1

                            for c in range(variables_size):
                                # print value.items()[1][1]

                                # if type(c) is collections.OrderedDict:
                                # data = value.items()[1][1]
                                data = list(value.items())
                                matrix[row][0] = data[1][1]

                                # if type(data) is collections.OrderedDict:
                                #     item = data.items()[1][1]
                                #     matrix[row][0] = F"{item}"
                                #
                                # else:
                                #     # matrix[row][0] = to_bytes(data)
                                #     matrix[row][0] = F"{data}"
                    else:
                        for key, value in result.items():
                            # COLUMNS
                            # print type(value)
                            row += 1
                            # value is a list
                            # for c in range(variables_size):
                            for data in value:

                                if type(data) is collections.OrderedDict:

                                    # print row
                                    # print value[c].items()[1][1]
                                    # data = value[c]
                                    # print data['@name'], name_index[data['@name']]
                                    get_index = data['@name']
                                    # print(name_index)
                                    index = name_index[get_index.encode()]
                                    # print "index:", index, "TYPE:", type(data)
                                    parameters, value = data.items()
                                    item = value[1]
                                    # print index, item
                                    if type(item) is collections.OrderedDict:
                                        parameters_2, value_2 = item.items()
                                        item_value = value_2[1]
                                        # matrix[row][index] = to_bytes(item_value)
                                        matrix[row][index] = F"{item_value}"
                                        # print to_bytes(item_value)
                                        # print item.items()
                                        # print "r{} c{} v{}".format(row, c, data.items()[1][1])
                                    else:
                                        # matrix[row][index] = to_bytes(item)
                                        matrix[row][index] = F"{item}"
                                        # print to_bytes(item)
                                        # print "r:{} c:{} {}={}".format(row, c, matrix[0][c], to_bytes(item))
                                else:
                                    index = name_index[value['@name']]
                                    if data != '@name':
                                        # matrix[row][index] = to_bytes(value[data])
                                        matrix[row][index] = F"{value[data]}"
                                        # print "data:", data, value[data], name_index[value['@name']]

            # print "DONE"
            # print "out with: {}".format(matrix)
            return {St.message: "OK", St.result: matrix}

        # except Exception as err:
        #     message = "\nUNACCEPTED ERROR IN THE RESPONSE."
        #     print message
        #     return {St.message: err, St.result: None}

    else:
        # logger.warning("NO RESPONSE")
        # print response[St.message]
        if response:
            return {St.message: "NO RESPONSE", St.result: response[St.result], "justification": response[St.message]}

        return {St.message: "NO RESPONSE", St.result: None, "justification": "THE TRIPLE STORE IS NOT ONLINE"}


def sparql_xml_to_matrix_db(query, database):

    name_index = dict()

    if type(query) is not str and type(query) is not bytes:
        message = "THE QUERY NEEDS TO BE OF TYPE STRING. {} WAS GIVEN".format(type(query))
        print(message)
        return {St.message: message, St.result: None}

    if (query is None) or (query == ""):
        message = "Empty query"
        print(message)
        return {St.message: message, St.result: None}

    # start_time = time.time()
    matrix = None
    # logger.info("XML RESULT TO TABLE")
    # print query

    # if query.lower().__contains__("optional") is True:
    #     message = "MATRIX DOES NOT YET DEAL WITH OPTIONAL"
    #     return {St.message: message, St.result: None}

    response = endpoint_db(query, database)
    # logger.info("1. RESPONSE OBTAINED")
    # print response[St.result]

    # DISPLAYING THE RESULT

    if response and response[St.message] == "OK":

        # print "response:", response[St.result]
        # print "response length:", len(response[St.result])

        if len(response[St.result]) == 0:
            message = "NO RESULT FOR THE QUERY"
            return {St.message: message, St.result: None}

        # logger.info("2. RESPONSE IS NOT ''NONE''")

        if True:
            # print response[St.result]
            xml_doc = xmltodict.parse(response[St.result])
            # print "3. FROM XML TO DOC IN {}".format(str(time.time() - start_time))

            # VARIABLES
            # print "4. GETTING VARIABLE'S LIST FROM XML_DOC"
            variables_list = xml_doc['sparql']['head']['variable']
            # print "Variable List", variables_list
            # print "5. EXTRACTED IN {} SECONDS".format(str(time.time() - start_time))

            variables_size = len(variables_list)
            # print "6. VARIABLE SIZE:", variables_size

            # RESULTS
            # print "7. GETTING RESULT'S LIST FROM XML_DOC"
            results = xml_doc['sparql']['results']
            # print "8. IN {}".format(str(time.time() - start_time))

            if results is not None:
                # print "9. RESULT LIST IS NOT NONE"
                results = results['result']
                # print results
                # print type(results)
            else:
                message = "NO RESULT FOR THE QUERY"
                return {St.message: message, St.result: None}
                # print query

            """ >>> SINGLE RESULT """
            if type(results) is collections.OrderedDict:
                # print "SINGLE RESULT"
                # Creates a list containing h lists, each of w items, all set to 0
                # INITIALIZING THE MATRIX
                w, h = variables_size, 2
                # print "Creating matrix with size {} by {}".format(w, h)
                # x*y*0 to avoid weak error say x and y where not used
                matrix = [[str(x * y * 0).replace("0", "") for x in range(w)] for y in range(h)]
                # print matrix
                col = -1

                if variables_size == 1:
                    for name, variable in variables_list.items():
                        # HEADER
                        col += 1
                        # print variable
                        matrix[0][col] = variable
                        # print matrix

                    # RECORDS
                    for key, value in results.items():
                        # print type(value)
                        if type(value) is collections.OrderedDict:
                            item_value = list(value.items())[1][1]
                            if "#text" in item_value:
                                # print to_bytes(item_value["#text"])
                                matrix[1][0] = to_bytes(item_value["#text"])
                            else:
                                # matrix[1][0] = to_bytes(item_value)
                                matrix[1][0] = item_value
                        else:
                            # matrix[1][0] = to_bytes(value.items()[1][1])
                            matrix[1][0] = value.items()[1][1]

                else:
                    # print "Variable greater than 1"
                    # HEADER
                    for variable in variables_list:
                        for key, value in variable.items():
                            col += 1
                            # matrix[0][col] = to_bytes(value)
                            matrix[0][col] = value
                            # name_index[to_bytes(value)] = col
                            name_index[value] = col
                            # print "{} was inserted".format(value)
                            # print matrix

                    # RECORDS
                    # print results.items()
                    for key, value in results.items():
                        # COLUMNS
                        # print "Key: ", key
                        # print "Value: ", value
                        for data in value:
                            # print "value Items: ", value.items()[i][1]
                            # print "Length:", len(value.items())
                            if type(data) is list:
                                # print "value:", value
                                # data = value[i]

                                # get_property = data['@name']
                                # print "get_property:", get_property
                                # index = name_index[get_property]
                                # print "index", index
                                index = name_index[data['@name']]
                                item = data.items()[1][1]
                                # print data['@name'], name_index[data['@name']]
                                matrix[1][index.encode()] = to_bytes(item)

                            elif type(data) is collections.OrderedDict:
                                data = list(data.items())
                                # print(name_index)
                                index = name_index[data[0][1]]
                                matrix[1][index] = data[1][1]
                                # if data.items()[1][0] != '@name':
                                #     item = data.items()[1][1]
                                #     matrix[1][index] = to_bytes(item)
                                #     # print "Collection:", value.items()[i][0]
                                # else:
                                #     item = ""

                            # if type(item) is collections.OrderedDict:
                            #     # print "Data is a collection"
                            #     # print "{} was inserted".format(data.items()[1][1])
                            #     matrix[1][index] = to_bytes(item.items()[1][1])
                            else:
                                # print "data is regular"
                                # print "{} was inserted".format(data)
                                # matrix[1][index] = to_bytes(item)
                                # matrix[1][index] = item
                                # matrix[1][index] = data
                                # print matrix
                                print("PROBLEM!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

                                # print "The matrix is: {}".format(matrix)

            """ >>> MORE THAN ONE RESULT """
            if type(results) is list:
                # print "THE LIST CONTAINS MORE THAN ONE RESULTS"
                row = 0
                columns = -1
                row_size = len(results)

                # Creates a list containing h lists, each of w items, all set to 0
                w, h = variables_size, row_size + 1

                # print "INITIALIZING THE MATRIX FOR: [{}][{}]".format(h, w)
                matrix = [[str(x * y * 0).replace("0", "") for x in range(w)] for y in range(h)]

                # HEADER
                # print "UPDATING MATRIX'S HEADER"

                if type(variables_list) is collections.OrderedDict:
                    variables_list = list(variables_list.items())
                    for i in range(0, len(variables_list)):
                        matrix[0][i] = str(variables_list[i][1])

                else:
                    for variable in variables_list:

                        if type(variable) is collections.OrderedDict:
                            for key, value in variable.items():
                                columns += 1
                                # print "COLUMN: ", columns, value
                                # print value
                                # matrix[0][columns] = to_bytes(value)
                                matrix[0][columns] = value
                                name_index[to_bytes(value)] = columns
                        else:
                            # print "TYPE", type(variables_list)
                            # print "value:", variables_list.items()[0][1]
                            columns += 1
                            # print "COLUMN: ", columns
                            # matrix[0][columns] = to_bytes(variables_list.items()[0][1])
                            # print(variable)
                            matrix[0][columns] = variables_list.items()[0][1]

                # RECORDS
                # print "UPDATING MATRIX WITH VARIABLES' VALUES"
                for result in results:

                    # ROWS
                    if variables_size == 1:
                        # result = list(result)

                        for key, value in result.items():
                            row += 1

                            for c in range(variables_size):
                                # print value.items()[1][1]

                                # if type(c) is collections.OrderedDict:
                                # data = value.items()[1][1]
                                data = list(value.items())
                                matrix[row][0] = data[1][1]

                                # if type(data) is collections.OrderedDict:
                                #     item = data.items()[1][1]
                                #     matrix[row][0] = F"{item}"
                                #
                                # else:
                                #     # matrix[row][0] = to_bytes(data)
                                #     matrix[row][0] = F"{data}"
                    else:
                        for key, value in result.items():
                            # COLUMNS
                            # print type(value)
                            row += 1
                            # value is a list
                            # for c in range(variables_size):
                            for data in value:

                                if type(data) is collections.OrderedDict:

                                    # print row
                                    # print value[c].items()[1][1]
                                    # data = value[c]
                                    # print data['@name'], name_index[data['@name']]
                                    get_index = data['@name']
                                    # print(name_index)
                                    index = name_index[get_index.encode()]
                                    # print "index:", index, "TYPE:", type(data)
                                    parameters, value = data.items()
                                    item = value[1]
                                    # print index, item
                                    if type(item) is collections.OrderedDict:
                                        parameters_2, value_2 = item.items()
                                        item_value = value_2[1]
                                        # matrix[row][index] = to_bytes(item_value)
                                        matrix[row][index] = F"{item_value}"
                                        # print to_bytes(item_value)
                                        # print item.items()
                                        # print "r{} c{} v{}".format(row, c, data.items()[1][1])
                                    else:
                                        # matrix[row][index] = to_bytes(item)
                                        matrix[row][index] = F"{item}"
                                        # print to_bytes(item)
                                        # print "r:{} c:{} {}={}".format(row, c, matrix[0][c], to_bytes(item))
                                else:
                                    index = name_index[value['@name']]
                                    if data != '@name':
                                        # matrix[row][index] = to_bytes(value[data])
                                        matrix[row][index] = F"{value[data]}"
                                        # print "data:", data, value[data], name_index[value['@name']]

            # print "DONE"
            # print "out with: {}".format(matrix)
            return {St.message: "OK", St.result: matrix}

            # except Exception as err:
            #     message = "\nUNACCEPTED ERROR IN THE RESPONSE."
            #     print message
            #     return {St.message: err, St.result: None}

    else:
        # logger.warning("NO RESPONSE")
        # print response[St.message]
        if response:
            return {St.message: "NO RESPONSE", St.result: response[St.result], "justification": response[St.message]}

        return {St.message: "NO RESPONSE", St.result: None, "justification": "THE TRIPLE STORE IS NOT ONLINE"}


def display_matrix(matrix, spacing=50, limit=100, output=False, line_feed='.', is_activated=False):

    limit = limit
    table = Buffer()
    message = """
    ####################################################################################
    TABLE OF {} Row(S) AND {} Columns LIMIT={}
    ####################################################################################
         """.format(0, 0, limit)

    if is_activated is True:

        line = ""
        for space in range(spacing):
            line += "#"

        # logger.info(display_result)
        my_format = "{{:{}<{}}}".format(line_feed, spacing)
        my_format2 = "{{:<{}}}".format(spacing)

        if matrix[St.message] == "NO RESPONSE":
            # print(Ec.ERROR_CODE_1)
            return message

        if matrix[St.result] is None:
            # logger.warning("\nTHE MATRIX IS EMPTY\n")
            print(message)
            return message

        message = """
    ####################################################################################
    TABLE OF {} Row(S) AND {} Columns LIMIT={}
    ####################################################################################
         """.format(len(matrix[St.result]) - 1, len(matrix[St.result][0]), limit)

        table.write(message)

        count = 0
        for r in range(len(matrix[St.result])):

            count += 1

            row = ""

            # SUBJECT
            if r == 0:
                for c in range(len(matrix[St.result][0])):
                    # formatted = my_format2.format(to_bytes(matrix[St.result][r][c]))
                    formatted = my_format2.format(matrix[St.result][r][c])
                    row = "{}{} ".format(row, formatted)

            # SUBJECT LINE
            elif r == 1:
                for c in range(len(matrix[St.result][0])):
                    formatted = my_format2.format(line)
                    row = "{}{} ".format(row, formatted)
                row += "\n\t"

            if r >= 1:
                for c in range(len(matrix[St.result][0])):
                    # formatted = my_format.format(to_bytes(matrix[St.result][r][c]))
                    formatted = my_format.format(str(matrix[St.result][r][c]))
                    row = "{}{} ".format(row, formatted)

            table.write("\n\t{}".format(row))

            if count == limit + 1:
                # if output is False:
                #     print table.getvalue()
                # else:
                #     return table.getvalue()
                break

    if output is False:
        print(table.getvalue())
    else:
        return table.getvalue()


def to_nt_format(resource):

    try:
        if Ut.is_nt_format(resource) is True:
            return resource
        else:
            return "<{}>".format(resource)

    except Exception as err:
        print("Exception:", err.__str__())
        return resource


def get_namedgraph_size(linkset_uri, isdistinct=False):

    distinct = ""

    if isdistinct is True:
        distinct = "DISTINCT "

    check_query = "\n{}\n{}\n{}\n{}\n{}\n{}\n{}".format(
        # "PREFIX linkset: <http://risis.eu/linkset/>",
        # "PREFIX lsMetadata: <http://risis.eu/linkset/metadata/>",
        # "PREFIX predicate: <http://risis.eu/linkset/predicate/>",
        # "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>",
        "    ##### GETTING THE LINKSET SIZE",
        "    select(count({}?source) as ?triples)".format(distinct),
        "    WHERE ",
        "    {",
        "       GRAPH <{}>".format(linkset_uri),
        "       { ?source ?predicate ?target }",
        "    }"
    )

    # print check_query

    result = endpoint(check_query)

    # print result

    if result[St.result] is not None:
        # """
        # EXAMPLE OF THE RESULT
        # <?xml version='1.0' encoding='UTF-8'?>
        # <sparql xmlns='http://www.w3.org/2005/sparql-results#'>
        #     <head>
        #         <variable name='triples'/>
        #     </head>
        #     <results>
        #         <result>
        #             <binding name='triples'>
        #                 <literal datatype='http://www.w3.org/2001/XMLSchema#integer'>13164</literal>
        #             </binding>
        #         </result>
        #     </results>
        # </sparql>
        # """
        dropload_doc = xmltodict.parse(result[St.result])
        return dropload_doc['sparql']['results']['result']['binding']['literal']['#text']
    else:
        return None


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
    resource_enumeration = "\n\t\t\t{}".format("\n\t\t\t".join(Ut.to_nt_format(item) for item in resources))

    for dataset, values in data.items():

        for dictionary in values:

            e_type = dictionary['entity_type']
            mandatory = dictionary['mandatory']
            optional = dictionary['optional']

            # GENERATE THE SUB-QUERY FOR MANDATORY PROPERTIES
            sub_mandatory = "\t\t\t\t?resource a <{}> .\n".format(e_type)
            sub_mandatory += "\n".join(
                "\t\t\t\t?resource {0} ?{1} .".format(
                    Ut.to_nt_format(uri), alternative if len(alternative) > 0 else
                    "{}_{}".format(
                        Ut.get_uri_local_name_plus(dataset),
                        Ut.get_uri_local_name_plus(uri))) for uri, alternative in mandatory)

            # GENERATE THE SUB-QUERY FOR OPTIONAL PROPERTIES
            if len(optional) > 0:
                sub_optional = "\n".join(
                    "\t\t\t\tOPTIONAL {{ ?resource {0} ?{1} . }}".format(
                        Ut.to_nt_format(uri), alternative if len(alternative) > 0 else
                        "{}_{}".format(
                            Ut.get_uri_local_name_plus(dataset),
                            Ut.get_uri_local_name_plus(uri))) for uri, alternative in optional)
            else:
                sub_optional = ""

            sub_optional = "\n{}".format(sub_optional) if (len(sub_optional) > 0) else sub_optional

            # BIND THE DATASET TO HAVE IT IN THE SELECT
            bind = "BIND( {} as ?dataset)".format(Ut.to_nt_format(dataset))

            # ACCUMULATE THE SUB-QUERIES
            sub_query += template_1.format(
                "UNION\n" if count_union > 0 else "", dataset, Ut.to_nt_format(dataset), bind, sub_mandatory,
                sub_optional)
            count_union += 1


    # THE FINAL QUERY
    query = template_2.format(resource_enumeration, sub_query)
    print(query)
    # Qry.display_result(query, is_activated=True)

    # response = Qry.sparql_xml_to_matrix(query)

    # if response is None:
    #     return None
    # else:
    #     return response['result']


def get_resource_value(resources, targets):

    """
    :param resources    : LIST OF RESOURCE URI FOR WHICH DATA NEEDS TO BE EXTRACTED
    :param targets      : A DICTIONARY WITH THE FOLLOWING KEYS
    :return             :

    DESCRIPTION OF THE PROPERTIES FOR NODE'S LABEL VISUALISATION OBJECT
    ------------------------------------------------------------------
    targets =
    [
        {
            graph               : THE DATASET URI
            data =
                [
                    {
                        entity_type : THE ENTITY TYPE OF INTEREST
                        properties  : THE PROPERTIES SELECTED BY THE USER FOR THE ABOVE TYPE
                    }
                ]
        },
        ...
    ]
    """

    rsc_builder = Buffer()
    if type(resources) is str:
        rsc_builder.write("\t\t{}\n".format(Ut.to_nt_format(resources)))
    else:
        for i in range(0, len(resources)):
            rsc_builder.write("\t{}\n".format(Ut.to_nt_format(resources[i]))) if i == 0 \
                else rsc_builder.write("\t\t\t{}\n".format(Ut.to_nt_format(resources[i])))

    i_format = """
        {{
            GRAPH <{0}>
            {{
                BIND("{2}" AS ?property)
                BIND(<{0}> AS ?dataset)
                ?resource a <{1}> .
                ?resource {2} ?value .
            }}
        }}
    """

    query = Buffer()
    empty = True
    for dictionary in targets:
        graph = dictionary[St.graph]
        data = dictionary[St.data]
        for types in data:
            data_type = types[St.entity_type]
            properties = types[St.properties]
            for i_property in properties:
                p_formatted = Ut.to_nt_format(i_property)
                if empty is True:
                    query.write("\t\tVALUES ?resource \n\t\t{{\n\t\t {} \t\t}}".format(rsc_builder.getvalue()))
                    query.write(i_format.format(graph, data_type, p_formatted))
                    empty = False
                else:
                    query.write("\tUNION" + i_format.format(graph, data_type, p_formatted))

    end_format = F"""
    SELECT ?resource ?dataset ?property ?value
    {{\n{query.getvalue()}}}
    """
    return end_format
