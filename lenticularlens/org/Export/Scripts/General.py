
from datetime import datetime, timedelta, timezone
from hashlib import md5, blake2b
from kitchen.text.converters import to_bytes
from os import remove, stat
from os.path import isfile
from rdflib import Dataset
from rdflib import XSD, Literal, Graph
from re import findall, sub
from SPARQLWrapper import SPARQLWrapper, JSON
from lenticularlens.org.Export.Scripts.Variables import LOV
from string import digits
from sys import stdout
from time import time
from unidecode import unidecode


# SCRIPT OVERVIEW #########################################################################################
#                                                                                                         #
#   Generic functions uses in several scripts.                                                            #
#                                                                                                         #
# #########################################################################################################

def ERROR(page, function, location, message):

    return F"\n{'File':15} : {page}.py\n" \
        F"{'Function':15} : {function}\n" \
        F"{'Whereabouts':15} : {location}\n" \
       F"{'Message':15} : {message}\n" \
       F"{'Error Message':15} : {traceback.format_exc()}\n"

# CLEARS THE StringIO GIVEN OBJECT
def clearBuffer(buffer):

    buffer.seek(0)
    buffer.truncate(0)


def printTime(padding=100, message=None, fill: chr = '.', fill_type: chr = ">"):

    message = ' Process started on week: %U/53, %a %d %b %Y at %H:%M:%S %f' if message is None \
        else F" {message.strip()} week: %U/53, %a %d %b %Y %H:%M:%S %f"
    print(F"\n\n{datetime.today().strftime(message):{fill}{fill_type}{padding}}\n{'':{fill}>{padding}}\n")


def getTimestamp():

    # print(datetime.fromtimestamp(datetime.today().timestamp()))
    # return datetime.fromtimestamp(datetime.today().timestamp())
    return Literal(datetime.utcnow())


def getXSDTimestamp():

    # print(Literal(Literal(datetime.utcnow(), datatype=XSD.dateTime)).n3())
    return Literal(Literal(datetime.now(timezone.utc), datatype=XSD.dateTime)).n3(Graph().namespace_manager)


def getDate():

    return F"{datetime.today().strftime('%U/53, %a %d %b %Y at %H:%M:%S %f')}"


def hasher(obj, size=15):

    # h = blake2b(digest_size=10)
    # h.update(bytes(object.__str__(), encoding='utf-8'))
    # print(F"H{h.hexdigest()}")
    h = md5()
    h.update(bytes(obj.__str__(), encoding='utf-8'))
    return F"{h.hexdigest()[:size]}" if size else F"{h.hexdigest()}"


# OFFERS CHOICE TO RANDOMIZE IT OR NOT
def hasherBlake2b(msg, digest_size=8, randomize=False, seed=0):

    h = blake2b(digest_size=digest_size, salt=bytes(seed.__str__(), encoding='utf-8')) \
        if randomize is True else blake2b(digest_size=digest_size)

    h.update(bytes(msg.__str__(), encoding='utf-8'))
    return F"{h.hexdigest()}"


def hashNumber(text):

    # THE NUMBER FROM AN EMPTY STRING   :  418980020
    # THE NUMBER OF A NONE STRING       :  69783645
    numbers = findall(pattern="\\d", string=hasher(text))
    return "".join(x for x in numbers)


def hashIt(text):

    code = hasher(str(text))
    hashed = str(code).replace("-", "N") if str(code).__contains__("-") else "P{}".format(code)
    # print hashed
    return hashed


def deterministicHash(text, digest_size=8):

    code = hasherBlake2b(str(text), digest_size=digest_size)
    # hashed = str(code).replace("-", "N") if str(code).__contains__("-") else "P{}".format(code)
    # print hashed
    return code


def convertBytes(num):

    # file_size = 0
    # if isfile(f_path):
    #     file_size = round(stat(f_path).st_size / (1024 * 1024 * 1024), 3)
    #
    # if file_size > 0:
    #     return "{} MB".format(file_size * 1000)
    #
    # return "{} GB".format(file_size)

    """ this function will convert bytes to MB.... GB... etc """

    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def fileSize(f_path):

    return convertBytes(stat(f_path).st_size)


def queryEndpoint(query="select * {?s ?p ?o.} LIMIT 10", endpoint=LOV):

    # Query an endpoint and return the result as JSON
    try:
        sparql = SPARQLWrapper(endpoint)
        sparql.setQuery(query)
        # print(query)
        # print(sparql)
        # exit()
        sparql.setReturnFormat(JSON)
        # print(sparql.query().convert())
        return sparql.query().convert()

    except Exception as er:
        return None


def correctStr(input_text):
    return len(input_text.strip() if input_text else "") > 0


def isNumber(text: str):

    # Returns False if it contains letters
    if text:
        return False not in [char in list(digits) for char in text]
    return False


def isDecimalLike(text: str):

    result = findall(pattern="^\\d*[.]?\\d+$", string=str(text))
    return True if result else False


def isNtFormat(resource):
    try:
        temp = resource.strip()
        return temp.startswith("<") and temp.endswith(">")

    except Exception as err:
        print("Exception:", err)
        return False


def undoNtFormat(resource):
    result = findall(pattern="<([^<>]*)>", string=resource)
    if len(result) > 0:
        return result[0].strip()
    return resource


def isPropertyPath(resource):

    temp = str(to_bytes(resource)).strip()
    check = findall("> */ *<", temp)
    return len(check) != 0


def prep4Iri(input_text, spacing="_"):

    # With unidecode, super-schwüler gewählt für becomes super-schwuler gewahlt fur
    # Only alpha numeric
    return sub('[\\W]', spacing, unidecode(input_text.__str__().strip() if input_text else ""))


def getUriLocalNamePlus(uri, sep="_"):

    # This      : http://www.vondel.humanities.uva.nl/ecartico/lod/vocab/#religiousName
    # RETURNS   : religiousName

    if uri is None:
        return None

    if len(uri) == 0:
        return None

    check = findall("<([^<>]*)>/*", uri)

    if isPropertyPath(uri) or isNtFormat(uri) or len(check) > 0:

        name = ""
        pro_list = check

        for i in range(len(pro_list)):
            local = getUriLocalNamePlus(pro_list[i])
            if i == 0:
                name = local
            else:
                name = "{}{}{}".format(name, sep, local)
                # print ">>>> name: ", name
        return name

    else:

        pattern = ".*[\\/\\#:](.*)$"
        bad_pattern = "(.*)[\\/\\#:]$"
        local = findall(pattern, uri)
        if len(local) > 0 and len(local[0]) > 0:
            return local[0]
        else:
            bad_uri = findall(bad_pattern, uri)
            if len(bad_uri) > 0:

                # local_name = get_uri_local_name_plus(bad_uri[0])
                # print("BAD:", uri, "LOCAL NAME:", local_name)
                return getUriLocalNamePlus(bad_uri[0])
            else:
                return uri


def progressOut(i, total, start=None, bars=50):

    increment = 100/float(bars)
    ratio = i * bars / total if total > 0 else 0
    dif = "" if start is None else str(timedelta(seconds=time() - start))
    progressed = u"\u2588" * int(round(ratio, 0))
    # from time import sleep
    # sleep(1)
    return F"| {progressed:{bars}} | {str(round(ratio * increment, 0)):>3}% in {dif}"


def inLinePrint(data, tab='\t'):

    """To print things to stdout on one line dynamically, simply use
    ANSI code escapes to move back to the beginning of the line  and
    then clear that entire line before printing the current status output."""

    stdout.write(F"\r\x1b[K {tab}{data.__str__()}")
    stdout.flush()
    # sleep(1)


def validate_RDFStar_(file):

    temp = file.replace('.ttl', '_rdf_check.ttl')
    start = time()

    try:
        with open(temp, 'w') as transformer:

            with open(file, "r") as reader:

                for index, line in enumerate(reader):
                    # print('Size of file is', reader.tell(), 'bytes')
                    pgs = progressOut(i=index + 1, total=500, start=start, bars=10)
                    star_subject = findall(pattern="<<(.*)>>", string=line)
                    if star_subject:
                        transformer.write(F"\t{star_subject[0]} . \n\t<http://{hash(star_subject[0])}>")
                    else:
                        transformer.write(line)
                    inLinePrint(F"{pgs}")

        g = Dataset().parse(temp, format="trig")
        print(F"The file [{file}] \nis in a valid RDFStar format!")

    except Exception as err:
        print("Invalid RDFStar\n")
        print(err)

    finally:
        # if isfile(temp):
        #     remove(temp)
        print("Done!!!!!!!")


def validateRDFStar(file, removeIt=True):

    center, line = 66, 70
    print(F"\n{'':>16}{'-' * line:^{center}}\n{'|':>16}\t{F'VALIDATING RDFStar FILE {fileSize(file)}':^{center}}|\n{'':>16}{'-' * line:^{center}}\n")
    if 'trig' in file:
        temp = file.replace('.trig', '_rdf_check.trig')
    elif 'ttl' in file:
        temp = file.replace('.ttl', '_rdf_check.ttl')
    start = time()
    from pathlib import Path
    size = Path(file).stat().st_size

    try:

        print("\t1. Converting the file to RDFStar")
        with open(temp, 'w') as transformer:

            with open(file, "r") as reader:
                line = reader.readline()
                while line:
                    line, pos = reader.readline(), reader.tell()
                    star_subject = findall(pattern="<<(.*)>>", string=line)

                    if star_subject:
                        transformer.write(F"{line.rstrip().replace(F'<<{star_subject[0]}>>', star_subject[0])} ."
                                          F"\n\t<http://{deterministicHash(star_subject[0])}>\n")
                    else:
                        transformer.write(line)

                    inLinePrint(progressOut(i=pos, total=size, start=start, bars=10), tab='\t\t')

        print("\n\n\t2. Checking the converted file.")
        start = time()
        Dataset().parse(temp, format="trig")
        print(F"\n\t\t>>> ✅ The converted file \n\t\t[{temp}] \n\t\tis in a valid RDFStar format! "
              F"\n\n\t\t>>> We therefore can highly ascertain that the original file "
              F"\n\t\t[{file}]\n\t\tis in a valid RDFStar format")
        print("" if start is None else F"""\n\t{'3. Parsing time':.<50} {str(timedelta(seconds=time() - start))}""")

    except Exception as err:
        print("\t\t>>> ❌ Invalid RDFStar")
        print(F"\t\t>>> [DETAIL ERROR FROM validate_RDFStar] {err}")

    finally:
        print(F"\n\t3. Removing the converted file from disc..\n\t{temp}")
        if isfile(temp) and removeIt is True:
            remove(temp)
        print(F"\n\t{'4. Done in':.<53} {str(timedelta(seconds=time() - start))}")


def validateRDF(file):

    center, line = 66, 70
    print(F"\n{'':>16}{'-' * line:^{center}}\n{'|':>16}\t{F'VALIDATING RDF FILE {fileSize(file)}':^{center}}|\n{'':>16}{'-' * line:^{center}}\n")

    start = time()
    from pathlib import Path
    size = Path(file).stat().st_size

    try:

        print("\n\t1. Checking the RDF file.")
        start = time()
        Dataset().parse(file, format="trig")
        print(F"\n\t\t>>> ✅ The converted file \n\t\t[{file}] \n\t\tis in a valid RDF format! "
              F"\n\n\t\t>>> We therefore can highly ascertain that the original file "
              F"\n\t\t[{file}]\n\t\tis in a valid RDF format.")
        print("" if start is None else F"""\n\t2. {'Parsing time':.<50} {str(timedelta(seconds=time() - start))}""")

    except Exception as err:
        print("\t\t\t>>> ❌ Invalid RDF")
        print(F"\t\t\t>>> [DETAIL ERROR FROM validate_RDF] {err}")

    finally:
        print(F"\n\t{'2. Done in':.<53} {str(timedelta(seconds=time() - start))}")
