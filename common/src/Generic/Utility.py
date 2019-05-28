# -*- coding: utf-8 -*-
# coding=utf-8

import io
import re
import os
import ast
import sys
import time
import gzip
import rdflib
import codecs
import pickle
import shutil
import datetime
import platform
import builtins
import requests
import xmltodict
import subprocess
import collections
import os.path as path
import zipfile as f_zip
import src.Generic.Settings as St
import src.Generic.NameSpace as Ns
import src.Generic.Server_Settings as Svr
import src.DataAccess.Stardog.Query as Stardog

from hashlib import md5  # blake2b,
from unidecode import unidecode
from os import stat, listdir, mkdir
from os.path import isfile, join, splitext
from kitchen.text.converters import to_bytes, to_unicode


# write_to_path = "C:\Users\Al\Dropbox\Linksets\ExactName"


OPE_SYS = platform.system().lower()
mac_weird_name = "darwin"
_format = " It is %a %b %d %Y %H:%M:%S"


#################################################################
""" GENERIC FUNCTIONS """
#################################################################


def print_time(pading=100):
    empty = ""
    print(F"\n{datetime.datetime.today().strftime(_format):.>{pading}}\n{empty:.>{pading}}\n")


def print_heading(text):

    heading = ""
    text = text.split("\n")
    formatted = "{:.^100}\n"
    for text in text:
        if text.strip():
            heading += formatted.format(F" {text} ")

    print("\n{}{}{}".format(formatted.format(""), heading, formatted.format("")))


def date():

    today = datetime.date.isoformat(datetime.date.today()).replace('-', '')
    return F"{today}_{re.findall('..:.*', str(datetime.datetime.now()))[0]}"


def problem(tab="\t", label="PROBLEM", text=None):
    text = text.split('\n')
    temp = ""
    for line in text:
        temp += F"{tab}{line}\n"
    print("\n{0}{1:.^30}\n{0}{2:.^30} \n{3}".format(tab, "", F" {label} ", F"{temp}"))


def completed(started, tab="\t"):

    datetime.timedelta(seconds=time.time() - started)
    print('\n{}{:.^100}'.format(tab, F" COMPLETED IN {datetime.timedelta(seconds=time.time() - started)} "))
    print('{}{:.^100}'.format(tab, F" JOB DONE! "))


def hasher(obj):

    # h = blake2b(digest_size=10)
    # h.update(bytes(object.__str__(), encoding='utf-8'))
    # print(F"H{h.hexdigest()}")
    h = md5()
    h.update(bytes(obj.__str__(), encoding='utf-8'))
    return F"H{h.hexdigest()[:15]}"


def hash_number(text):

    # THE NUMBER FROM AN EMPTY STRING   :  418980020
    # THE NUMBER OF A NONE STRING       :  69783645
    numbers = re.findall(pattern="\\d", string=hasher(text))
    return "".join(x for x in numbers)


def convert_bytes(num):

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


def get_obj_size(obj, seen=None, converted=True):

    def helper(data, seen_set=None):

        # From https://goshippo.com/blog/measure-real-size-any-python-object/
        # Recursively finds size of objects
        size = sys.getsizeof(data)
        if seen_set is None:
            seen_set = set()
        obj_id = id(data)
        if obj_id in seen_set:
            return 0
        # Important mark as seen *before* entering recursion to gracefully handle
        # self-referential objects
        seen_set.add(obj_id)
        if isinstance(data, dict):
            size += sum([helper(v, seen_set) for v in data.values()])
            size += sum([helper(k, seen_set) for k in data.keys()])

        elif hasattr(data, '__dict__'):
            size += helper(data.__dict__, seen_set)

        elif hasattr(data, '__iter__') and not isinstance(data, (str, bytes, bytearray)):
            size += sum([helper(i, seen_set) for i in data])

        return size

    start = time.time()
    if converted is True:
        result = convert_bytes(helper(obj, seen))
        print(F"\tSIZE [{result}] COMPUTED IN {datetime.timedelta(seconds=time.time() - start)}.")
        return result
    else:
        result = helper(obj, seen)
        print(F"\tSIZE [{result}] COMPUTED IN {datetime.timedelta(seconds=time.time() - start)}.")
        return result


def file_size(f_path):

    return convert_bytes(stat(f_path).st_size)


def is_windows():
    return True if OPE_SYS == 'windows' else False


def activation(activated, function, heading):

    if activated is True:
        headings(heading)
        return True
    else:
        print("THE FUNCTION {} IS NOT ACTIVATED".format(function))
        return False


def headings(message, line=True):

    split = message.split("\n")
    if len(split) > 0:
        message = ""
        for data in split:
            message += "\n{:^116}".format(data)

    time_format = "It is %a %b %d %Y %H:%M:%S.%f]"
    date_str = datetime.datetime.today()
    if line is True:
        _line = "--------------------------------------------------------------" \
                "--------------------------------------------------------------"
    else:
        _line = ""
    return "\n{0}\n{2:>116}\n{1:^{3}}\n{0}".format(
        _line, message[1:] if str(message).startswith("\n") is True else message,
        date_str.strftime(time_format), 116)


def zip_dir(file_path, zip_name):

    zip_f = f_zip.ZipFile(zip_name, 'w', f_zip.ZIP_DEFLATED)
    for root, dirs, files in os.walk(file_path):
        for doc in files:
            zip_f.write(os.path.join(root, doc))


def hash_it(text):

    code = hasher(str(text))
    hashed = str(code).replace("-", "N") if str(code).__contains__("-") else "P{}".format(code)
    # print hashed
    return hashed


def from_alignment2singleton(alignment):

    if str(alignment).__contains__(Ns.linkset):
        return str(alignment).replace(Ns.linkset, Ns.singletons)
    elif str(alignment).__contains__(Ns.lens):
        return str(alignment).replace(Ns.lens, Ns.singletons)
    else:
        return alignment


def is_nt_format(resource):
    try:
        temp = resource.strip()
        return temp.startswith("<") and temp.endswith(">")

    except Exception as err:
        print("Exception:", err)
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


def undo_nt_format(resource):
    result = re.findall(pattern="<([^<>]*)>", string=resource)
    if len(result) > 0:
        return result[0].strip()
    return resource


def is_property_path(resource):

    temp = str(to_bytes(resource)).strip()
    check = re.findall("> */ *<", temp)
    return len(check) != 0


def get_uri_local_name(uri, sep="_"):

    # print "URI: {}".format(uri)
    # print type(uri)

    if uri is None:
        return None

    if len(uri) == 0:
        return None

    if type(uri) is not str:
        print(uri)
        print(type(uri), "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return None

    check = re.findall("<([^<>]*)>/*", uri)

    if is_property_path(uri) or is_nt_format(uri) or len(check) > 0:

        name = ""
        # pro_list = re.findall("<([^<>]*)>/*", uri)
        pro_list = check

        for i in range(len(pro_list)):
            local = get_uri_local_name(pro_list[i])
            if i == 0:
                name = local
            else:
                name = "{}{}{}".format(name, sep, local)
                # print ">>>> name: ", name
        return name

    else:
        pattern = '[ \\w\\.-]'
        non_alphanumeric_str = re.sub(pattern, '', uri)
        if non_alphanumeric_str == "":
            return uri
        else:
            last_char = non_alphanumeric_str[-1]
            index = uri.rindex(last_char)
            name = uri[index + 1:]
            return name


def get_uri_local_name_plus(uri, sep="_"):

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
            local = get_uri_local_name_plus(pro_list[i])
            if i == 0:
                name = local
            else:
                name = "{}{}{}".format(name, sep, local)
                # print ">>>> name: ", name
        return name

    else:

        pattern = ".*[\\/\\#:](.*)$"
        bad_pattern = "(.*)[\\/\\#:]$"
        local = re.findall(pattern, uri)
        if len(local) > 0 and len(local[0]) > 0:
            return local[0]
        else:
            bad_uri = re.findall(bad_pattern, uri)
            if len(bad_uri) > 0:

                # local_name = get_uri_local_name_plus(bad_uri[0])
                # print("BAD:", uri, "LOCAL NAME:", local_name)
                return get_uri_local_name_plus(bad_uri[0])
            else:
                return uri


def split_property_path(property_path):

    # example = """(" <http://www.grid.ac/ontology/hasAddress>  / <http://www.grid.ac/ontology/countryCode>")"""
    if property_path is None:
        return []
    return re.findall("<([^<>]*)>/*", property_path)


def pipe_split(text, sep="_"):

    # print pipe_split("[rembrandt van rijn] aligns with [rembrandt van rijn]")

    altered = ""
    split = str(to_bytes(text)).split("|")

    for i in range(len(split)):
        item = split[i].strip()
        item = get_uri_local_name(item, sep)
        if i == 0:
            altered = item
        else:
            altered += " | {}".format(item)

    if altered is None or len(altered) == 0:
        return text

    return altered


def pipe_split_plus(text, sep="_"):

    # print pipe_split("[rembrandt van rijn] aligns with [rembrandt van rijn]")

    altered = ""
    split = str(to_bytes(text)).split("|")

    for i in range(len(split)):
        item = split[i].strip()
        item = get_uri_local_name_plus(item, sep)
        if i == 0:
            altered = item
        else:
            altered += " | {}".format(item)

    if altered is None or len(altered) == 0:
        return text

    return altered


def get_uri_ns_local_name(uri):

    if (uri is None) or (uri == ""):
        return None

    if is_property_path(uri) or is_nt_format(uri):

        name = ""
        pro_list = re.findall("<([^<>]*)>/*", uri)

        for i in range(len(pro_list)):
            local = get_uri_local_name(pro_list[i])
            if i == 0:
                name = local
            else:
                name = "{}_{}".format(name, local)
                # print ">>>> name: ", name
        return [None, name]

    else:
        non_alphanumeric_str = re.sub('[ \\w]', '', uri)
        if non_alphanumeric_str == "":
            return uri
        else:
            last_char = non_alphanumeric_str[-1]
            index = uri.rindex(last_char)
            name = uri[index + 1:]
            ns = uri[:index+1]
            return [ns, name]


def update_specification(specs):

    # print "Specs update"
    # print specs

    if St.link_old in specs:

        if specs[St.link_old]:
            if is_property_path(specs[St.link_old]) or is_nt_format(specs[St.link_old]):
                pro_list = re.findall("<([^<>]*)>/*", specs[St.link_old])
                name = ""
                for i in range(len(pro_list)):
                    local = get_uri_local_name(pro_list[i])
                    if i == 0:
                        name = local
                    else:
                        name = "{}_{}".format(name, local)
                    # print ">>>> name: ", name
                specs[St.link_old_name] = name
                if len(pro_list) == 1 and St.aligns in specs:
                    specs[St.link_old_ns] = str(specs[St.aligns]).replace(specs[St.link_old_name], '')
                else:
                    specs[St.link_old_ns] = None
            else:
                specs[St.link_old_name] = get_uri_local_name(specs[St.link_old])
                specs[St.link_old_ns] = get_uri_ns_local_name(specs[St.link_old])[0]

    if St.graph in specs:
        if specs[St.graph]:
            specs[St.graph_name] = get_uri_local_name(specs[St.graph])
            specs[St.graph_ns] = get_uri_ns_local_name(specs[St.graph])[0]
            # print specs[St.graph_name]

    if St.entity_type in specs:
        specs[St.entity_name] = get_uri_local_name(specs[St.entity_type])
        specs[St.entity_ns] = str(specs[St.entity_type]).replace(specs[St.entity_name], '')
        # print specs[St.entity_name]

    if St.aligns in specs:

        if specs[St.aligns]:

            if is_property_path(specs[St.aligns]) or is_nt_format(specs[St.aligns]):
                pro_list = re.findall("<([^<>]*)>/*", specs[St.aligns])
                name = ""
                for i in range(len(pro_list)):
                    local = get_uri_local_name(pro_list[i])
                    if i == 0:
                        name = local
                    else:
                        name = "{}_{}".format(name, local)
                    # print ">>>> name: ", name
                specs[St.aligns_name] = name
                if len(pro_list) == 1:
                    specs[St.aligns_ns] = str(specs[St.aligns]).replace(specs[St.aligns_name], '')
                else:
                    specs[St.aligns_ns] = None

            else:
                specs[St.aligns_name] = get_uri_local_name(specs[St.aligns])
                specs[St.aligns_ns] = str(specs[St.aligns]).replace(specs[St.aligns_name], '')
            # print specs[St.aligns_name]

    if St.longitude in specs:

        if specs[St.longitude]:

            if is_property_path(specs[St.longitude]) or is_nt_format(specs[St.longitude]):
                pro_list = re.findall("<([^<>]*)>/*", specs[St.longitude])
                name = ""
                for i in range(len(pro_list)):
                    local = get_uri_local_name(pro_list[i])
                    if i == 0:
                        name = local
                    else:
                        name = "{}_{}".format(name, local)
                        # print ">>>> name: ", name
                specs[St.longitude_name] = name
                if len(pro_list) == 1:
                    specs[St.longitude_ns] = str(specs[St.longitude]).replace(specs[St.longitude_name], '')
                else:
                    specs[St.longitude_ns] = None

            else:
                specs[St.longitude_name] = get_uri_local_name(specs[St.longitude])
                specs[St.longitude_ns] = str(specs[St.longitude]).replace(specs[St.longitude_name], '')
                # print specs[St.aligns_name]

    if St.latitude in specs:

        if specs[St.latitude]:

            if is_property_path(specs[St.latitude]) or is_nt_format(specs[St.latitude]):
                pro_list = re.findall("<([^<>]*)>/*", specs[St.latitude])
                name = ""
                for i in range(len(pro_list)):
                    local = get_uri_local_name(pro_list[i])
                    if i == 0:
                        name = local
                    else:
                        name = "{}_{}".format(name, local)
                        # print ">>>> name: ", name
                specs[St.latitude_name] = name
                if len(pro_list) == 1:
                    specs[St.latitude_ns] = str(specs[St.latitude]).replace(specs[St.latitude_name], '')
                else:
                    specs[St.latitude_ns] = None

            else:
                specs[St.latitude_name] = get_uri_local_name(specs[St.latitude])
                specs[St.latitude_ns] = str(specs[St.latitude]).replace(specs[St.latitude_name], '')
                # print specs[St.aligns_name]

    if St.lens in specs:
        specs[St.lens_name] = get_uri_local_name(specs[St.lens])
        specs[St.lens_ns] = str(specs[St.lens]).replace(specs[St.lens_name], '')

    if St.linkset in specs:
        specs[St.linkset_name] = get_uri_local_name(specs[St.linkset])
        specs[St.linkset_ns] = str(specs[St.linkset]).replace(specs[St.linkset_name], '')

    if St.refined in specs:
        specs[St.refined_name] = get_uri_local_name(specs[St.refined])
        specs[St.refined_ns] = str(specs[St.refined]).replace(specs[St.refined_name], '')

    if St.expands in specs:
        specs[St.expands_name] = get_uri_local_name(specs[St.expands])
        specs[St.expands_ns] = str(specs[St.expands]).replace(specs[St.expands_name], '')

    # print "DONE WITH SPECS UPDATE"


def intersect(a, b):

    if (a is not None) and (b is not None):
        return list(set(a) & set(b))

    return None


def win_bat(file_directory, file_name):

    # NORMALISE THE NAME TO AVOID below
    np = normalise_path(file_directory)
    # print np

    # GET THE DIRECTORY
    directory = os.path.dirname(np) if os.path.isdir(np) is not True else np
    # print dir

    # LOAD ALL FILES
    # file_list = [f for f in os.listdir(dir) if os.path.isfile(join(dir, f))]

    load_builder = io.StringIO()
    load_builder.write("""\n\techo "Loading data\"""")

    if OPE_SYS == 'windows':
        load_builder.write("\n\tstardog data add {} ".format(Svr.settings[St.stardog_uri]))

    # if OPE_SYS.__contains__(mac_weird_name):
    else:
        stardog_path = Svr.settings[St.stardog_path]
        load_builder.write("\n\t{}stardog data add {} ".format(stardog_path, Svr.settings[St.stardog_uri]))

    # LOAD ONLY .TRIG OR .TTL FILES
    print("\nTHESE FILES WILL BE USED FOR GENERATING A BAT FILE:")
    for f in os.listdir(directory):

        full_path = join(directory, f)

        if os.path.isfile(full_path):

            if f.endswith('.trig') or f.endswith('.ttl'):
                # abs =  os.path.abspath(f).replace("\\", "/")

                load_builder.write(" \"{}\"".format(full_path))
                print("  - {}".format(full_path))

    print(load_builder.getvalue())

    # GENERATE THE BAT FILE
    bat_path = "{0}{1}{1}{2}{3}".format(directory, os.path.sep, file_name, batch_extension())
    writer = codecs.open(bat_path, "wb", "utf-8")
    writer.write(to_unicode(load_builder.getvalue()))
    writer.close()

    # print OPE_SYS
    # if OPE_SYS.__contains__(mac_weird_name):
    if OPE_SYS != 'windows':
        os.chmod(bat_path, 0o777)
        print("MAC")

    load_builder.close()

    # RETURN THE BAT FILE
    print("\nTHE BAT FILE IS LOCATED AT:\n  - {}".format(bat_path))
    return bat_path


def batch_extension():

    # print ">>> OPERATING SYSTEM:", OPE_SYS.upper()
    # bat_ext = ""

    if OPE_SYS == "windows":
        bat_ext = ".bat"

    # elif OPE_SYS.__contains__(mac_weird_name):
    else:
        bat_ext = ".sh"

    return bat_ext


def batch_load(batch_load_file):

    if OPE_SYS == "windows":
        return bat_load(batch_load_file)

    # elif OPE_SYS.__contains__(mac_weird_name):
    else:
        return sh_load(batch_load_file)


def bat_load(bat_path):

    try:

        if isfile(bat_path) and bat_path.endswith(batch_extension()):

            # os.system returns 0 if it all went OK and 1 otherwise.
            # BUT IT DOES NOT TELL HOW MANY TRIPLES WHERE ADDED
            # output = os.system("{}".format(bat_path, c_path))

            # SUBPOCESS PRINT THE ENTIRE OUTPUT:
            #   THE FILES THAT WERE ADDED
            #   HOW MANY TRIPLES WHERE ADDED
            output = subprocess.check_output(bat_path, shell=True)
            # print "SUBPROCESS OUTPUT:", output
            # output = re.sub(b'\\(Conversion\\).*\n', '', output)
            output = re.sub('\\(Conversion\\).*\n', '', output)

            # THE OUTPUT CONTAINS FULL PATH THAT IS NOT ADVISABLE TO DISPLAY
            # FIND STRINGS THAT EXHIBIT A FILE PATTERN
            # file_path = re.findall(b" .:.*\\.*\..*", output)
            file_path = re.findall(" .:.*\\.*\\..*", output)
            for f in file_path:

                if f.__contains__("\\"):
                    # print "FILE FOUND: {}".format(f)
                    test = f.split("\\")
                    # EXTRACT THE END OF THAT PATTERN
                    new = test[len(test) - 1]
                    # REPLACE THE PATTERN WITH THAT END FOUNb ABOVE
                    output = output.replace(f, b" " + new)

                elif f.__contains__("/"):
                    # print "FILE FOUND: {}".format(f)
                    test = f.split("/")
                    # EXTRACT THE END OF THAT PATTERN
                    new = test[len(test) - 1]
                    # REPLACE THE PATTERN WITH THAT END FOUNb ABOVE
                    output = output.replace(f, b" " + new)

            print("PROCESS OUTPUT: {}".format(output))
            return {"message": "OK", "result": output}

    except Exception as err:
        print("SUBPROCESS ERROR")
        return {"message": "CHECK THE FILE PATH.\n{}".format(err.__str__()), "result": None}


def sh_load(bat_path):

    try:

        if isfile(bat_path) and bat_path.endswith(batch_extension()):
            print("Executing the batch file from non-windows machine")
            # os.system returns 0 if it all went OK and 1 otherwise.
            # BUT IT DOES NOT TELL HOW MANY TRIPLES WHERE ADDED
            # output = os.system("{}".format(bat_path))

            output = subprocess.check_output(bat_path, shell=True)

            print("PROCESS OUTPUT: {}".format(output))
            return {"message": "OK", "result": output}

    except Exception as err:
        return "CHECK THE FILE PATH.\n{}".format(err.__str__())


def dir_files(directory, extension_list):

    print(directory)

    # print "\nTHESE FILES WILL BE USED FOR GENERATING A BAT FILE:"
    lst = []
    for f in os.listdir(directory):

        full_path = join(directory, f)

        if os.path.isfile(full_path):
            ext = os.path.splitext(f)[1].strip().lower()
            if ext in extension_list:
                lst.append(full_path)

    # print list
    return lst


#######################################################################
"""   USER FRIENDLY PRINTING OF A LIST TUPLE OR DICTIONARY OBJECT   """
#######################################################################


# PRINT/RETURN TUPLES AS A STRING WITH [ | ] AS SEPARATOR
def print_tuple(tuple_list,  comment="", return_print=False, overview=True, tab=0, activated=True):

    if activated is False:
        return

    tabs = ""
    for i in range(0, tab):
        tabs += "\t"

    if tab == 0:
        print("\n\t{}{:.^100}".format(tabs, F" PRINTING A TUPLE OF SIZE {len(tuple_list)} "))
        print("\t{}{:.^100}\n".format(tabs, F" {comment} ")) if comment else print("\t{}{:.^100}\n".format(tabs, F""))

    elif overview is True:
        print(headings("\n>>> {}\n>>TUPLE SIZE : {}".format(comment, len(tuple_list))))

    if return_print is False:
        print(F"{tabs}", " | ".join(x.__str__() for x in tuple_list))
        return ""

    else:
        return F"{tabs}" + " | ".join(x.__str__() for x in tuple_list)


# PRINT/RETURN  A LIST AS A STRING
def print_list(data_list, comment="", return_print=False, overview=True, tab=0, activated=True):

    if activated is False:
        return

    tabs = ""
    builder = io.StringIO()

    for i in range(0, tab):
        tabs += "\t"
    tabs_2 = tabs + "\t"

    if tab == 0:
        print("\n\t{}{:.^100}".format(tabs, F" PRINTING A LIST OF SIZE {len(data_list)} "))
        print("\t{}{:.^100}\n".format(tabs, F" {comment} ")) if comment else print("\t{}{:.^100}\n".format(tabs, F""))

        if return_print is True:
            builder.write("\n\t{}{:.^100}".format(tabs, F" PRINTING A LIST OF SIZE {len(data_list)}\n"))
            builder.write("\t{}{:.^100}\n".format(tabs, F" {comment} ")) if comment else print(
                "\t{}{:.^100}\n".format(tabs, F""))

    if type(data_list) is not list and type(data_list) is not set:

        print(F"\tTHE INPUT DATA STRUCTURE IS NOT A LIST. IT IS OF TYPE: {type(data_list)}")

        if return_print is True:
            builder.write(F"\tTHE INPUT DATA STRUCTURE IS NOT A LIST. IT IS OF TYPE: {type(data_list)}\n")
            return builder.getvalue()

    for item in data_list:

        try:
            if type(item) == tuple:
                print_tuple(item, comment, return_print, overview, tab=tab+1, activated=activated)

                if return_print is True:
                    builder.write(print_tuple(item, comment, return_print, overview, tab=tab+1, activated=activated))

            elif type(item) == list:
                print_list(item, comment, return_print, overview, tab=tab+1, activated=activated)

                if return_print is True:
                    builder.write(print_list(item, comment, return_print, overview, tab=tab+1, activated=activated))

            elif type(item) == dict:
                print_dict(item, overview=False, tab=tab+1)

                if return_print is True:
                    builder.write(print_dict(item, overview=False, tab=tab+1))

            else:
                print(tabs_2 + str(item))

                if return_print is True:
                    builder.write((tabs_2 + str(item) + "\n"))

        except IOError:
            print("PROBLEM!!!")

        if tab == 0:
            print("")

    if len(comment) == 0 and overview is True:
        print("{}\n>>> LIST SIZE : {}".format(comment, len(data_list)))

        if return_print is True:
            builder.write("{}\n>>> LIST SIZE : {}\n".format(comment, len(data_list)))

    elif overview is True:
        print(headings("\n>>> {}\n>>LIST SIZE : {}".format(comment, len(data_list))))

        if return_print is True:
            builder.write(headings("\n>>> {}\n>>LIST SIZE : {}\n".format(comment, len(data_list))))

    if return_print is True:
        return builder.getvalue()


# PRINT/RETURN  A LIST AS A STRING WHERE EACH LINE PRINTS THE DICTIONARY'S KEY ITEM-SIZE AND ITEM
def print_dict(data_dict, comment="", return_print=False, overview=True, tab=0, activated=True):

    if activated is False:
        return

    builder = io.StringIO()
    tabs = ""
    data = []
    keys = dict(data_dict).keys()
    for i in range(0, tab):
        tabs += "\t"
    tabs_2 = tabs + "\t"

    if tab == 0:
        print("\n\t{}{:.^100}".format(tabs, F" PRINTING A DICTIONARY OF SIZE {len(data_dict)} "))
        print("\t{}{:.^100}\n".format(tabs, F" {comment} ")) if comment else print("\t{}{:.^100}\n".format(tabs, F""))
        if return_print is True:
            builder.write("\n\t{}{:.^100}".format(tabs, F" PRINTING A DICTIONARY OF SIZE {len(data_dict)}\n"))
            builder.write(
                "\t{}{:.^100}\n".format(tabs, F" {comment} ")) if comment else print("\t{}{:.^100}\n".format(tabs, F""))

    check = True if isinstance(data_dict, dict) else (True if isinstance(data_dict, collections.defaultdict) else False)
    if check is False:
        print(f"\tTHE INPUT DATA STRUCTURE IS NOT A DICTIONARY. IT IS OF TYPE: {type(data_dict)}")
        if return_print is True:
            builder.write(f"\tTHE INPUT DATA STRUCTURE IS NOT A DICTIONARY. IT IS OF TYPE: {type(data_dict)}")
            return builder.getValue()

        return ""

    for x in keys:
        if type(x) is str:
            data += [len(x)]

    max_length = max(data) if len(data) != 0 else 6

    # ********************************
    # ITERATING THROUGH THE DICTIONARY
    # ********************************
    for key, value in data_dict.items():

        try:

            if type(value) is list:
                line = F"{tabs_2}KEY: {key} \t\t {type(value)} BELOW"
                print(line)
                print_list(value, overview=False, tab=tab+1, return_print=False, activated=True)

                if return_print is True:
                    builder.write(F"{line}\n")
                    builder.write(print_list(value, overview=False, tab=tab+1, return_print=True, activated=True))

            elif type(value) is tuple:
                print(F"{tabs_2}KEY: {key} \t\t {type(value)} BELOW")
                print_tuple(value, overview=False, tab=tab+1)

                if return_print is True:
                    builder.write(F"{tabs_2}KEY: {key} \t\t {type(value)} BELOW\n")
                    builder.write(print_tuple(value, overview=False, tab=tab+1, return_print=True, activated=True))

            elif type(value) is dict:
                print(F"{tabs_2}KEY: {key} \t\t {type(value)} BELOW")
                print_dict(value, comment, return_print, overview, tab=tab+1, activated=True)

                if return_print is True:
                    builder.write(F"{tabs_2}KEY: {key} \t\t {type(value)} BELOW\n")
                    builder.write(print_dict(
                        value, comment, overview=overview, tab=tab+1, return_print=True, activated=True,))

            else:
                try:

                    print("{4}KEY: {1:<{0}} \t\t ITEM (SIZE = {2}): {3}".format(
                        max_length, key,
                        len(value) if type(value) is not int and type(value) is not float
                        and not isinstance(value, type) else 1, str(value), tabs_2))

                    if return_print is True:
                        builder.write("{4}KEY: {1:<{0}} \t\t ITEM (SIZE = {2}): {3}\n".format(
                            max_length, key,
                            len(value) if type(value) is not int and type(value) is not float
                            and not isinstance(value, type) else 1, str(value), tabs_2))

                except TypeError:
                    print("{4}KEY: {1:<{0}} \t\t ITEM (SIZE = {2}): {3}".format(
                        max_length, key, "NA", str(value), tabs_2))

                    if return_print is True:
                        builder.write("{4}KEY: {1:<{0}} \t\t ITEM (SIZE = {2}): {3}\n".format(
                            max_length, key, "NA", str(value), tabs_2))

            if return_print is True:
                return builder.getvalue()

        except IOError:
            print("PROBLEM!!!")

    if tab == 0:
        print("")

    if overview is True:
        print(headings("{}\nDICTIONARY SIZE : {}".format(comment, len(data_dict))))


def print_object(data_structure, comment="", return_print=False, overview=False, tab=0, activated=True):

    if isinstance(data_structure, (dict, collections.OrderedDict, collections.defaultdict)):
        print_dict(data_structure, comment, return_print, overview, tab, activated)

    elif str(type(data_structure)) == "<class 'dict_keys'>":
        print_list(list(data_structure), comment, return_print, overview, tab, activated)

    elif isinstance(data_structure, (list, set)):
        print_list(data_structure, comment, return_print, overview, tab, activated)

    elif isinstance(data_structure, tuple):
        print_tuple(data_structure, comment, return_print, overview, tab, activated)

    else:
        print(data_structure)


###################################################################
"""         ABOUT SERIALISATION AND DE-SERIALISATION            """
###################################################################


safe_builtins = {'range', 'complex', 'set', 'frozenset', 'slice'}


class RestrictedUnpickler(pickle.Unpickler):

    def find_class(self, module, name):

        # Only allow safe classes from builtins.
        if module == "builtins" and name in safe_builtins:
            return getattr(builtins, name)

        # Forbid everything else.
        raise pickle.UnpicklingError("global '%s.%s' is forbidden" %
                                     (module, name))


# def serialize_dict(directory, dictionary, name, cluster_limit=1000):
#
#     print("\tSERIALIZING DICTIONARY OF SIZE: {}...".format(len(dictionary)))
#     start = time.time()
#     file_path = join(directory, name)
#
#     with open(file_path, 'w', encoding="utf-8") as writer:
#         writer.write(F"clusters = {dictionary.__str__()}\n")
#
#     print("\tDONE READING THE FILE IN {}".format(datetime.timedelta(seconds=time.time() - start)),
#           sep=" ")
#     return file_path


# def serialize_dict(directory, dictionary, name, cluster_limit=1000):
#     print("\tSERIALIZING DICTIONARY OF SIZE: {}...".format(len(dictionary)))
#     start = time.time()
#     file_path = join(directory, name)
#     with open(file_path, 'w', encoding="utf-8") as writer:
#
#         counting = 0
#         sub_cluster = {}
#
#         for key, value in dictionary.items():
#             # start_2 = time.time()
#             counting += 1
#
#             # CREATING SUB-DICTIONARIES
#             sub_cluster[key] = value
#
#             # WRITE THE SUB-DICTIONARY WHEN THE LIMIT IS REACHED
#             if counting == cluster_limit:
#                 writer.write(sub_cluster.__str__() + "\n")
#                 sub_cluster = {}
#                 counting = 0
#
#             # print "\n\tFINISH READING LINE {} IN {}".format(
#             #     counting, datetime.timedelta(seconds=time.time() - start_2))
#
#         if counting != 0:
#             writer.write(sub_cluster.__str__() + "\n")
#             sub_cluster = {}
#
#     print("\tDONE READING THE FILE IN {}".format(datetime.timedelta(seconds=time.time() - start)),
#           sep=" ")
#     return file_path


def restricted_loads(data_object):

    """Helper function analogous to pickle.loads()."""
    if isinstance(data_object, (io.BufferedReader, gzip.GzipFile)):
        return RestrictedUnpickler(data_object).load()
    else:
        return RestrictedUnpickler(io.BytesIO(data_object)).load()


def pickle_deserializer(serialised_folder, name, tab="\t"):

    try:
        if serialised_folder is None or name is None:
            return None

        start = time.time()
        file = (join(serialised_folder, name))

        if isfile(file) is False:
            problem(tab="\t", text=F"PICKLE DESERIALIZER: THE FILE DOES NOT EXIST \n\t{file}", label="PROBLEM")
            return None

        if isfile(file)is not True:
            print(F"\tPICKLE DESERIALIZER: THE FILE [{file}] DOES NOT EXITS")
            return None

        name_split = splitext(file)
        unzip_it = False if name_split[1] is None else (True if name_split[1].lower() == ".gz" else False)
        problem(label="DESERIALIZER INFO", text=F"FILE PATH: {file}\nTHE UNZIP OPTION IS NOT CHOSEN FOR THIS FILE.") \
            if unzip_it is False \
            else problem(
            label="DESERIALIZER INFO",
            text=F"FILE PATH: {file}\nTHE DECISION TO UNZIP THE FILE IS SOLELY BASED OF THE FILE'S EXTENSION.")

        try:
            with open(file, 'rb') if unzip_it is False else gzip.open(file, 'rb') as pickle_data:
                de_serialised = restricted_loads(pickle_data)

            print("{}\tDONE READING THE FILE OF AN OBJECT OF SIZE {} IN {}".format(tab,
                  len(de_serialised), datetime.timedelta(seconds=time.time() - start)))

        except OSError as err:

            if err.__str__().lower().__contains__('not a gzipped file'):
                problem(text=F"FILE FILE: [{file}] \nINFO: PROBABLY DUE TO A WRONG EXTENSION, THE FILE WAS BEING UNZIPPED."
                F"\n\t  IT IS NOW BEING CORRECTLY PROCESSED AS A REGULAR UNZIPPED FILE.")
                with open(file, 'rb') as pickle_data:
                    de_serialised = restricted_loads(pickle_data)

        return de_serialised

    except TypeError as err:
        problem(text=F"pickle_deserializer: {err}")


def pickle_serializer(directory, data_object, name, tab="\t", zip_it=True):

    """
    :param directory: THE DIRECTORY OF THE FILE TO SERIALISE
    :param data_object: THE OBJECT TO SERIALISE
    :param name: THE NAME OF THE FILE TO CREATE WITH ITS EXTENSION
    :param tab: SERVES AS JUST AS A PADDING
    :param zip_it: A BOOLEAN ARGUMENT FOR DECIDING TO ZIP THE FILE OF NOT
    :return:
    """

    """
    Protocol version 0
        is the original “human-readable” protocol and is
        backwards compatible with earlier versions of Python.

    Protocol version 1
        is an old binary format which is also compatible with earlier versions of Python.

    Protocol version 2
        was introduced in Python 2.3. It provides much more efficient pickling of new-style classes.
        Refer to PEP 307 for information about improvements brought by protocol 2.

    Protocol version 3
        was added in Python 3.0. It has explicit support for bytes objects and cannot be
        unpickled by Python 2.x. This is the default protocol, and the recommended protocol
        when compatibility with other Python 3 versions is required.

    Protocol version 4 was added in Python 3.4. It adds support for very large objects, pickling more
    kinds of objects, and some data format optimizations. Refer to PEP 3154 for information about
    improvements brought by protocol 4.

    If fix_imports is true and protocol is less than 3, pickle will try to map the new Python 3 names t
    """

    start = time.time()
    if path.isdir(directory) is False:
        mkdir(directory)

    file_path = join(directory, name)

    # IF ZIP IT IS TRUE, CHANGE THE EXTENSION IF IT IS THE WRONG EXTENSION OR DOES NOT HAVE ONE
    if zip_it is True:
        name_split = splitext(file_path)
        # file_path = file_path if name_split[1].lower() == ".gz" else \
        #     (file_path.replace(name_split[1], ".gz") if name_split[1] else F"{file_path}.gz")
        file_path = file_path if name_split[1].lower() == ".gz" else F"{file_path}.gz"

    # MESSAGE
    output = F"SERIALIZING OBJECT OF TYPE {type(data_object)} AND OF SIZE: {len(data_object)}."
    problem(label="SERIALIZER INFO",
            text=F"FILE PATH: {file_path}\nTYPE:{output}\nTHE ZIP OPTION IS NOT CHOSEN FOR THIS FILE.") if zip_it is False \
        else problem(label="SERIALIZER INFO", text=F"FILE PATH: {file_path}\nTYPE: {output}\nYOU HAVE CHOSEN ZIP THE FILE.")

    # PROTOCOL TWO IS CHOSEN FOR COMPATIBILITY ISSUE WITH LENTICULAR LENS 1
    with gzip.open(file_path, 'wb') if zip_it is True else open(file_path, 'wb') as writer:
        pickle.dump(obj=data_object, file=writer, protocol=2, fix_imports=True)

    print(F"{tab}\tDONE WRITING THE FILE {file_path} IN {datetime.timedelta(seconds=time.time() - start)}", sep=" ")

    return file_path


def serialize_dict(directory, dictionary, name, cluster_limit=1000):

    print("\tSERIALIZING DICTIONARY OF SIZE: {}...".format(len(dictionary)))
    start = time.time()

    with open(join(directory, "Serialized_{}".format(name)), 'wb') as writer:

        counting = 0
        sub_cluster = {}

        for key, value in dictionary.items():
            # start_2 = time.time()
            counting += 1
            sub_cluster[key] = value

            if counting == cluster_limit:
                writer.write(sub_cluster.__str__() + "\n")
                sub_cluster = {}
                counting = 0

            # print "\n\tFINISH READING LINE {} IN {}".format(
            #     counting, datetime.timedelta(seconds=time.time() - start_2))

        if counting != 0:
            writer.write(sub_cluster.__str__() + "\n")

    print("\tDONE READING THE FILE IN {}".format(datetime.timedelta(seconds=time.time() - start)))


def de_serialise_dict(serialised_directory_path, name):

    # print "\tREADING FROM SERIALISED FILE..."
    line_count = 0
    reading_start = time.time()
    with open(join(serialised_directory_path, "{}".format(name)), 'r', encoding="utf-8") as s_file_1:
        dictionary = {}
        for line in s_file_1:
            line_count += 1
            # reading_start_2 = time.time()
            dictionary.update(ast.literal_eval(line))
            # print("\t\tFINISH READING LINE {} IN {}".format(
            #     line_count, datetime.timedelta(seconds=time.time() - reading_start_2)), end="\n")

    print("\tDONE READING THE FILE IN {}\n".format(datetime.timedelta(seconds=time.time() - reading_start)))
    return dictionary


def dic_serializer(dic_type_obj, directory, name, mb=30):

    # CREATE THE FOLDER IN WHICH THE SERIALIZED FILES WILL LIVE IN BASED ON A THRESHOLD
    # ITERATE THROUGH THE DICTIONARY

    byte_threshold = 1024 * 1024 * mb
    byte_threshold = 10
    temp = dict()

    for counter, key in enumerate(dic_type_obj.keys()):

        temp[key] = dic_type_obj[key]
        print(get_obj_size(temp, seen=None, converted=False))

        if get_obj_size(dic_type_obj, seen=None, converted=False) >= byte_threshold:
            pickle_serializer(directory=directory, data_object=dic_type_obj, name=F'{counter}_{name}')
            temp = dict()
        # print(counter, key)


# data = {'al': 'uva', 'veruska': 'uva', 'jauco': 'hyugens'}
# dic_serializer(data, '/Users/al/PhD/GA/del', 'test')



###################################################################
"""             ABOUT INSERTING NAMED GRAPHS FILES              """
###################################################################


def insert_graph(dataset_name, f_path, file_count, save=True):

    limit = 70000
    date_str = datetime.date.isoformat(datetime.date.today()).replace('-', '')
    f_path = f_path.replace("\\", "/")
    ds = rdflib.Dataset()
    name = os.path.basename(f_path)

    new_dir = "{}/Inserted_{}_On_{}".format(os.path.dirname(f_path), name, date_str)

    try:
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
    except OSError as err:
        print("\n\t[__init__ in RDF]", err.__str__)
        return

    print("loading : [{}]".format(file_count))
    print("\n\tFile: {}".format(name))
    start_time = time.time()
    ds.parse(source=f_path, format="trig", encoding='utf-8')
    print("\tLoading completed in{:>8} {} seconds".format(":", str(time.time() - start_time)))
    print("\tSize                {:>8} {} triples".format(":", len(ds)))

    count = 1
    # count_chunk = 0
    for graph in ds.graph():
        count_lines = 0

        if len(graph) > 0:
            name = re.findall("<.*>", str(graph))[0]
            if name.__contains__("file:") is not True:
                print("\t>>> Named-graph [{}]{:>15} {}".format(count, ":", name))
                count_chunk = 0
                qrybldr = io.StringIO()
                qrybldr.write("INSERT DATA\n{{\n\tGRAPH {}\n".format(name))
                qrybldr.write("\t{\n")

                for subj, pred, obj in graph:
                    count_lines += 1

                    #  If literal
                    if type(obj) == rdflib.term.Literal:
                        if len(obj) == 1:
                            # obj = to_bytes(obj)
                            obj = obj.replace("\\", "\\\\")
                        obj = "\"\"\"{}\"\"\"".format(to_bytes(obj))
                        # print obj

                    #  if URI
                    elif type(obj) == rdflib.term.URIRef:
                        obj = "<{}>".format(to_bytes(obj))

                    # triple
                    qrybldr.write("\t\t<{}> <{}> {} .\n".format(to_bytes(subj), to_bytes(pred), obj))

                    if count_lines == limit:
                        count_chunk += 1
                        qrybldr.write("\t}\n}\n")
                        query_time = time.time()
                        if save is True:
                            wr = codecs.open("{}/Insert-{}_chunk{}_{}.txt".format(
                                new_dir, dataset_name, count_chunk, date_str), "wb")
                            wr.write(qrybldr.getvalue())
                            wr.close()
                        qres = Stardog.endpoint(qrybldr.getvalue())

                        if qres is not None:
                            doc = xmltodict.parse(qres)
                            print("\t>>> Response of chunk {:<12}: {}".format(count_chunk, doc['sparql']['boolean']))
                            print("\t>>> Inserted in {:>19} {} seconds".format(":", str((time.time() - query_time))))

                        # Reset
                        qrybldr.close()
                        qrybldr = io.StringIO()
                        qrybldr.write("INSERT DATA\n{{\n\tGRAPH {}\n".format(name))
                        qrybldr.write("\t{\n")
                        count_lines = 0
                        # qres = ""

                qrybldr.write("\t}\n}\n")
                query_time = time.time()
                final = qrybldr.getvalue()
                qrybldr.close()
                if len(final) > 0:
                    count_chunk += 1
                    if save is True:
                        wr = codecs.open("{}/Insert-{}_chunk{}_{}.txt".format(
                            new_dir, dataset_name, count_chunk, date_str), "wb")
                        wr.write(final)
                        wr.close()
                    qres = Stardog.endpoint(final)
                    if qres is not None:
                        doc = xmltodict.parse(qres)
                        print("\t>>> Response of chunk {:<12}: {}".format(count_chunk, doc['sparql']['boolean']))
                        print("\t>>> Inserted in {:>19} {} seconds".format(":", str(time.time() - query_time)))
                count += 1

    print("\tProcess completed in {} {} seconds\n".format(":", str(time.time() - start_time)))


def insert_graphs(dataset_name, dir_path):

    format_ = "%a %b %d %H:%M:%S %Y"
    builder = io.StringIO()
    files = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]

    print("\n\n{:>114}".format(datetime.datetime.today().strftime(format_)))
    builder.write("\n--------------------------------------------------------"
                  "----------------------------------------------------------\n")
    builder.write("    Inserting graphs contained in :\n\t\t{}\n".format(dir_path))
    builder.write("    \tThe folder contains [ {} ] files.\n".format(len(files)))
    builder.write("--------------------------------------------------------"
                  "----------------------------------------------------------\n")

    print(builder.getvalue())

    file_count = 1
    for f in listdir(dir_path):
        f_path = join(dir_path, f)
        extension = os.path.splitext(f_path)[1]

        if isfile(f_path) & (extension.lower() == ".trig"):
            # print path
            insert_graph(dataset_name, f_path, file_count)
            file_count += 1


#################################################################
"""
    ABOUT WRITING TO FILE

    REMINDER 1:
    FOR MAC/LINUX REMEMBER TO CHANGE THE FILE PERMISSIONS FOR EXECUTING THE BATCH FILE
        SET: chmod -R 777 Data/
        CHECK: ls -l

    REMINDER 2:
    THE ENVIRONMENT VARIABLES HAVE TO BE SETTLED
        MAKE SURE THE TERMINAL IS RESTARTED AFTER SETTING THE VARIABLES
            in mac
                open ~/.bash_profile
                add to file
                    export STARDOG_HOME=/Users/YOURUSERNAME/Documents/stardog-4.1.3/data
                    export PATH=$PATH:/Users/YOURUSERNAME/Documents/stardog-4.1.3/bin

        TEST THE COMMAND 'STARDOG DATA ADD ...' TO BE SURE
"""
#################################################################


def write_to_file(graph_name, directory, metadata=None, correspondences=None, singletons=None):
    # check_file = False
    # print graph_name
    """
        2. FILE NAME SETTINGS
    """
    try:
        date_str = datetime.date.isoformat(datetime.date.today()).replace('-', '')
        dir_name = directory  # write_to_path os.path.dirname(f_path)
        linkset_file = "{}-Linksets-{}.trig".format(graph_name, date_str)
        metadata_file = "{}-Metadata-{}.trig".format(graph_name, date_str)
        singleton_metadata_file = "{}-SingletonMetadata-{}.trig".format(graph_name, date_str)
        dir_name = dir_name.replace("\\", "/")

        linkset_output = "{}/{}".format(dir_name, linkset_file).replace("//", "/")
        metadata_output = "{}/{}".format(dir_name, metadata_file).replace("//", "/")
        singleton_metadata_output = "{}/{}".format(dir_name, singleton_metadata_file).replace("\\", "/")
        try:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
        except OSError as err:
            print("\n\t[__init__ in RDF]", err.__str__)
            return
        # print "output file is :\n\t{}".format(output_path)

        """
            3. WRITE LINKSET TO FILE
        """
        print("\tDIRECTORY NAME:", path.dirname(metadata_output))
        if metadata is not None:
            document = None
            try:
                print("\t\tMETADATA FILE:", path.basename(metadata_output))
                document = codecs.open(metadata_output, "wb", "utf-8")
                document.write(to_unicode(metadata))
                document.close()
            except Exception as err:
                print(err.__str__())
                if document:
                    document.close()

        if correspondences is not None:
            document = None
            try:
                print("\t\tLINKSET FILE:", path.basename(linkset_output))
                document = codecs.open(linkset_output, "wb", "utf-8")
                document.write(to_unicode(correspondences))
                document.close()
            except Exception as err:
                print(err.__str__())
                if document:
                    document.close()

        if singletons is not None:
            document = None
            try:
                print("\t\tSINGLETON METADATA FILE:", path.basename(singleton_metadata_output))
                document = codecs.open(singleton_metadata_output, "wb", "utf-8")
                document.write(to_unicode(singletons))
                document.close()
            except Exception as err:
                print(err.__str__())
                if document:
                    document.close()

    except Exception as err:
        print(err.__str__())


def write_2_disc(file_directory, file_name, data, extension="txt"):

    date_str = datetime.date.isoformat(datetime.date.today()).replace('-', '')
    file_path = join(file_directory, file_name)
    file_path = "{}_{}.{}".format(file_path, date_str, extension)
    if file_name is not None and data:
        document = None
        try:
            if not os.path.exists(file_directory):
                os.makedirs(file_directory)
            document = codecs.open(file_path, "wb", "utf-8")
            document.write(to_unicode(data))
            document.close()
        except Exception as err:
            print(err.__str__())
            if document:
                document.close()


def get_writers(graph_name, directory, expands=False, is_source=True):

    # expands: A BOOLEAN PARAMETER TO SPECIFIED WHETHER THE LINKSET IS BEING EXPANDED
    # is_source: TO SPECIFY IF THIS ES BEING EXPANDED FROM THE SOURCE OR THE TARGET.
    if expands is True and is_source is True:
        unique = "_expands_source_"
    elif expands is True and is_source is False:
        unique = "_expands_target_"
    else:
        unique = ""

    #  print graph_name
    """ 2. FILE NAME SETTINGS """
    date_str = datetime.date.isoformat(datetime.date.today()).replace('-', '')
    dir_name = directory  # write_to_path  # os.path.dirname(f_path)
    batch_file = "{}_batch{}_{}{}".format(graph_name, unique, date_str, batch_extension())
    linkset_file = "{}(Linksets){}-{}.trig".format(graph_name, unique, date_str)
    metadata_file = "{}{}(Metadata)-{}.sparql".format(graph_name, unique, date_str)
    singleton_metadata_file = "{}{}(SingletonMetadata)-{}.trig".format(graph_name, unique, date_str)
    dir_name = dir_name.replace("\\", "/")
    dir_name = dir_name.replace("//", "/")

    batch_output = "{}/{}".format(dir_name, batch_file)
    linkset_output = "{}/{}".format(dir_name, linkset_file)
    metadata_output = "{}/{}".format(dir_name, metadata_file)
    singleton_metadata_output = "{}/{}".format(dir_name, singleton_metadata_file)

    try:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    except OSError as err:
        print("\n\t[__init__ in RDF]", err.__str__)
        return
    # print "output file is :\n\t{}".format(output_path)

    """
        3. WRITE LINKSET TO FILE
    """
    writers = dict()
    writers[St.meta_writer] = codecs.open(metadata_output, "wb", "utf-8")
    writers[St.crpdce_writer] = codecs.open(linkset_output, "wb", "utf-8")
    writers[St.singletons_writer] = codecs.open(singleton_metadata_output, "wb", "utf-8")
    writers[St.batch_writer] = codecs.open(batch_output, "wb", "utf-8")

    writers[St.meta_writer_path] = metadata_output
    writers[St.crpdce_writer_path] = linkset_output
    writers[St.singletons_writer_path] = singleton_metadata_output
    writers[St.batch_output_path] = batch_output

    return writers


def normalise_path(file_path):

    file_path = re.sub('[\']', "\\\\", file_path)
    file_path = re.sub('[\"]', "\\\\", file_path)
    file_path = re.sub('[\1]', "\\\\1", file_path)
    file_path = re.sub('[\2]', "\\\\2", file_path)
    file_path = re.sub('[\3]', "\\\\3", file_path)
    file_path = re.sub('[\4]', "\\\\4", file_path)
    file_path = re.sub('[\5]', "\\\\5", file_path)
    file_path = re.sub('[\6]', "\\\\6", file_path)
    file_path = re.sub('[\7]', "\\\\7", file_path)
    file_path = re.sub('[\0]', "\\\\0", file_path)
    file_path = re.sub('[\a]', "\\\\a", file_path)
    file_path = re.sub('[\b]', "\\\\b", file_path)
    file_path = re.sub('[\f]', "\\\\f", file_path)
    file_path = re.sub('[\n]', "\\\\n", file_path)
    file_path = re.sub('[\r]', "\\\\r", file_path)
    file_path = re.sub('[\t]', "\\\\t", file_path)
    file_path = re.sub('[\v]', "\\\\v", file_path)
    return file_path


def load_triple_store(graph_uri, directory, data):

    #  print graph_name
    """ 2. FILE NAME SETTINGS """
    graph_name = get_uri_local_name(graph_uri)
    date_str = datetime.date.isoformat(datetime.date.today()).replace('-', '')
    dir_name = directory
    np = normalise_path(dir_name)
    dir_name = os.path.dirname(np) if os.path.isdir(np) is not True else np
    dir_name = dir_name.replace("\\", "/")

    # FILE NAME
    batch_file = "{}_batch_{}{}".format(graph_name, date_str, batch_extension())
    insert_file = "{}-{}.trig".format(graph_name, date_str)

    # FILE PATH
    batch_output = "{}/{}".format(dir_name, batch_file)
    insert_output = "{}/{}".format(dir_name, insert_file)

    # MAKE SURE THE FOLDER EXISTS
    try:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    except OSError as err:
        print("\n\t[utility_LOAD_TRIPLE_STORE:]", err.__str__)
        return

    # WRITERS
    b_writer = codecs.open(insert_output, "wb", "utf-8")
    i_writer = codecs.open(batch_output, "wb", "utf-8")

    # WRITE DATA TO FILE
    i_writer.write(data.getvalue)
    i_writer.close()

    # GENERATE THE BATCH FILE
    if OPE_SYS == 'windows':
        b_writer.write("\n\tstardog data add {} {}".format(Svr.settings[St.stardog_uri], insert_output))
    else:
        stardog_path = Svr.settings[St.stardog_path]
        b_writer.write("\n\t{}stardog data add {} {}".format(stardog_path, Svr.settings[St.stardog_uri], insert_output))
    b_writer.close()

    # SET ACCESS RIGHT
    if OPE_SYS != 'windows':
        print("MAC BATCH: {}".format(batch_output))
        os.chmod(batch_output, 0o777)

    # RUN THE BATCH FILE
    batch_load(batch_output)
    if os.path.exists(batch_output) is True:
        os.remove(batch_output)

    triples = Stardog.get_namedgraph_size(graph_uri)
    print(triples)

    return {"result": triples, "message": "{} inserted".format(triples)}


def listening(directory, sleep_time=10):

    # run indefinitely
    print(directory)
    t_start = time.time()
    try:
        while True:
            # get the directory listing
            lock_file = [name for name in os.listdir(directory)
                         if name.endswith('.lock')]

            # print the most recent listing
            for lock in lock_file:
                print("\t>>> {} is active".format(lock))

            try:
                response = requests.get("http://{}".format(Svr.settings[St.stardog_host_name]))
            except Exception as err:
                response = str(err)

            # print "LISTENER RESPONSE:", response
            diff = time.time() - t_start
            if str(response).__contains__("10061") or str(response).__contains__("61"):
                print("\t>>> The connection has not been established yet with the stardog server...\n" \
                      "\t>>> It has been {} so far...".format(datetime.timedelta(seconds=diff)))

            else:
                if len(lock_file) > 0 and str(response).__contains__("401"):
                    print("\t>>> THE STARDOG SERVER IS ON AND REQUIRES PASSWORD.")
                    return "THE STARDOG SERVER IS ON AND REQUIRES PASSWORD."

                if len(lock_file) > 0 and \
                        (str(response).__contains__("200") or str(response).__contains__("No connection") is False):
                    print("\t>>> THE SERVER IS ON.")
                    return "THE SERVER IS ON."

            print("\nListening for \"system.lock\" file and checking whether " \
                  "a connection to the server is established every {} seconds...".format(str(sleep_time)))
            # wait a little bit before getting the next listing
            # if you want near instantaneous updates, make the sleep value small.
            time.sleep(sleep_time)

    except Exception as err:
        print(err.__str__())


def stardog_on(bat_path):

    # print "\nSTARTING THE STARDOG SERVER"
    directory = Svr.settings[St.stardog_data_path]
    lock_file = [name for name in os.listdir(directory) if name.endswith('.lock')]

    # 1. SEND A REQUEST TO CHECK WHETHER THE SERVER IS ON OR NOT
    try:
        response = requests.get("http://{}".format(Svr.settings[St.stardog_host_name]))
    except Exception as err:
        response = str(err)
    # print response

    # 2. NO NEED FOR TURNING THE SERVER ON AS IT IS ALREADY ON
    if len(lock_file) > 0 and (str(response).__contains__("200") or str(response).__contains__("401")):
        print("\t>>> THE SERVER WAS ALREADY ON.")

    # 3. NEED TO TURN ON THE TRIPLE STORE
    else:

        # REMOVE THE LOCK FILE IF IT EXISTS
        if len(lock_file) > 0 and path.exists(join(directory, lock_file[0])):
            os.remove(join(directory, lock_file[0]))

        # CREATE THE BATCH FILE FOR STARTING THE STARDOG SERVER
        if path.exists(bat_path) is False:
            # START stardog-admin.bat server start --disable-security
            if batch_extension() == ".bat":
                cmd = """
    @echo -------------------------------------------------------------------------------------------------------------
    @echo STARTING STARDOG FROM {}...
    @echo ------------------------------------------------------------------------------------------------------------
    cd "{}"
    START stardog-admin.bat server start
                """.format(bat_path, Svr.settings[St.stardog_path])

            else:
                cmd = """
    echo STARTING STARDOG...
    "{0}"stardog-admin server start
                """.format(Svr.settings[St.stardog_path])

            writer = open(bat_path, "wb")
            writer.write(cmd)
            writer.close()
            os.chmod(bat_path, 0o777)

        if batch_extension() == ".bat":
            # os.system(bat_path)
            subprocess.call(bat_path, shell=False)
        else:
            os.system("OPEN -a Terminal.app {}".format(bat_path))
        # time.sleep(waiting_time)

        while True:

            try:
                try:
                    response = requests.get("http://{}".format(Svr.settings[St.stardog_host_name]))
                except Exception as err:
                    response = str(err)

                if str(response).__contains__("200"):
                    print(">>> THE SERVER IS ON.")
                return "THE SERVER IS ON"

            except Exception as err:
                "ERROR: {}".format(str(err))
                "THE SERVER IS STILL STARTING UP..."
                pass

        # listening(Svr.settings[St.stardog_data_path]) TEST_SERVER


def stardog_off(bat_path):

    print("\nSTOPPING THE STARDOG SERVER")

    directory = Svr.settings[St.stardog_data_path]

    # IF THE STARDOG-STOP FILE DOES NOT EXIST, CREATE IT
    if path.exists(bat_path) is False:

        if batch_extension() == ".bat":

            cmd = """
    @echo -------------------------------------------------------------------------------------------------
    @echo STOPPING STARDOG FROM{}...
    @echo -------------------------------------------------------------------------------------------------
    cls
    cd "{}"
    call stardog-admin server stop
            """.format(bat_path, Svr.settings[St.stardog_path])

        else:

            cmd = """
            echo STOPPING STARDOG...
            "{}"stardog-admin server stop
            """.format(Svr.settings[St.stardog_path])

        writer = open(bat_path, "wb")
        writer.write(cmd)
        writer.close()
        os.chmod(bat_path, 0o777)

    # GETTING THE .LOCK FILE. THIS FILES DETERMINES WHETHER STARDOG IS ON OR OFF
    lock_file = [name for name in os.listdir(directory) if name.endswith('.lock')]

    if len(lock_file) > 0:

        # STARDOG IS ON SO... RUN THE STOP CODE
        off = batch_load(bat_path)

        if off is not None and type(off) is dict:
            # print "IS DICTIONARY"
            print(">>> RESPONSE: {}".format(off['result']))
            # lock_file = [name for name in os.listdir(Svr.settings[St.stardog_data_path]) if name.endswith('.lock')]
            if off['result'] is not None and off['result'].lower().__contains__("successfully") and len(lock_file) > 0:
                # MAKE SURE AS SOMETIMES IT TAKES TIME FOR THE LOCK FILE TO BE REMOVED BY STARDOG
                if path.exists(join(directory, lock_file[0])):
                    os.remove(join(directory, lock_file[0]))
        else:
            print(">>> RESPONSE: {}".format(off))
            lock_file = [name for name in os.listdir(directory) if name.endswith('.lock')]
            if off.lower().__contains__("successfully") and len(lock_file) > 0:
                if path.exists(join(directory, lock_file[0])):
                    os.remove(join(directory, lock_file[0]))

    else:
        print(">>> THE SERVER WAS NOT ON.")


def run_cdm(cmd, batch_path, delete_after=True, output=False):

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    # CREATE THE BATCH FILE FOR CHECKING PIP PYTHON AND VIRTUALENV
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    try:
        with open(name=batch_path, mode="wb") as writer:
            writer.write(cmd)

        # FILE ACCESS WRIGHT
        # if OPE_SYS != 'windows':
        os.chmod(batch_path, 0o777)

        # EXECUTE THE COMMAND

        if output is True:
            output = subprocess.check_output(batch_path, shell=True)
            if delete_after is True:
                os.remove(batch_path)
            return str(output)
        else:
            # RUNS IN A NEW SHELL
            output = subprocess.call(batch_path, shell=True)

            if delete_after is True:
                os.remove(batch_path)

            return output

        # RUNNING THE BATCH COMMANDS
        # if platform.system().lower() == "windows":
        #     os.system(batch_path)
        # else:
        #     os.system("OPEN -a Terminal.app {}".format(batch_path))

        # DELETE THE BATCH COMMAND AFTER EXECUTION

    except Exception as err:
        return err.__str__()


def create_database(stardog_bin_path, db_bat_path, db_name):

    if check_db_exists(db_name) is True:
        return False

    endpoint = Svr.settings[St.stardog_uri].replace("/{}".format(Svr.settings[St.database]), "")

    # CREATING THE DATABASE IN STARDOG
    create_db = " \"{0}{2}stardog-admin\" --server {3} db create -o " \
                "spatial.enabled=true search.enabled=true strict.parsing=false -n {1}".format(stardog_bin_path, db_name, os.path.sep, endpoint)

    print(create_db)

    writer = open(db_bat_path, "w")
    writer.write(create_db)
    writer.close()
    os.chmod(db_bat_path, 0o777)

    # subprocess.call(bat_path, shell=True)
    print("   >>> CREATING THE {} DATABASE".format(db_name))
    if platform.system().lower() == "windows":
        os.system(db_bat_path)
    else:
        os.system("OPEN -a Terminal.app {}".format(db_bat_path))

    return True

    # os.remove(db_bat_path)


def export_database(stardog_bin_path, db_name, save_in):

    # MAKE SURE THE DIRECTORY END WITH A SEPARATOR
    date_str = datetime.date.isoformat(datetime.date.today()).replace('-', '')
    file_path = join(save_in, "{}__backup_{}.ttl".format(db_name, date_str))

    # MAKE SURE THE BIN PATH ENDS WIT A SEPARATOR
    stardog_bin_path = stardog_bin_path if str(stardog_bin_path).endswith(os.path.sep) \
        else "{0}{1}{1}".format(stardog_bin_path, os.path.sep)

    cmd = "\"{0}stardog\" data export --named-graph ALL --format TRIG {1} {2}".format(
        stardog_bin_path, db_name, file_path)

    batch_path = join(save_in, "{}__backup_{}{}".format(db_name, date_str, batch_extension()))
    run_cdm(cmd, batch_path, delete_after=True)

    export_database(Svr.settings[St.stardog_path], db_name, save_in)


def check_db_exists(database):

    response = Stardog.sparql_xml_to_matrix_db(
        query="SELECT DISTINCT ?s WHERE { ?s ?p ?o } LIMIT 10", database=database)
    # print "DB CREATION CHECK:", response

    # if response["result"] is not None:
    if "justification" in response:
        justification = response["justification"]
        if justification.__contains__("UnknownDatabase") is True:
            print("\n\tDATABASE [{}] DOES NOT EXIST: ".format(database))
            return False
        else:
            # THE DB EXISTS BUT NOT POPULATED
            print("\n\tDATABASE [{}] ALREADY EXISTS: ".format(database))
            return True
    else:
        # THE DB EXISTS AND IT IS POPULATED
        print("\n\tDATABASE [{}] ALREADY EXISTS".format(database))
        return True
    # else:
    #     return False


def extract_ref(text):

    # example = """(" <http://www.grid.ac/ontology/yfshvbsuov_code>")"""
    if text is None:
        return []
    result = re.findall(".*/([^_]*)_.*", text)
    if len(result) == 0:
        local = get_uri_local_name(text)
        return local
    return result[0]


#######################################################################
"""                         MAPPING LETTERS                         """
#######################################################################


def diacritic_character_mapping(input_text):
    temp = str(input_text, "utf-8")
    # print temp
    builder = io.StringIO()
    "http://www.fileformat.info/info/unicode/char/0189/index.htm"
    "http://www.jarte.com/help_new/accent_marks_diacriticals_and_special_characters.html"
    # Diacritical Character to ASCII Character Mapping
    "https://docs.oracle.com/cd/E29584_01/webhelp/mdex_basicDev/src/rbdv_chars_mapping.html"
    convert = {

        u"a": u"a", u"á": u"a", u"ä": u"a", u"ã": u"a", u"â": u"a", u"à": u"a", u"å": u"a", u"æ": u"ae", u"ā": u"a",
        u"ă": u"a", u"ą": u"a",
        u"À": u"A", u"Á": u"A", u"Â": u"A", u"Ã": u"A", u"Ä": u"A", u"Å": u"A", u"Æ": u"AE",  u"Ā": u"A", u"Ą": u"A",

        u"b": u"b", u"ƀ": u"b", u"ɓ": u"b", u"ƃ": u"b",
        u"Ƀ": u"B", u"Ɓ": u"B", u"Ƃ": u"B", u"Ƅ": u"B",

        u"c": u"c", u"ç": u"c", u"č": u"c", u"ć": u"c", u"¢": u"c", u"ĉ": u"c",
        u"Ç": u"C", u"Ć": u"C", u"Ĉ": u"C", u"Ċ": u"C", u"Č": u"C", u"ċ": u"C",
        u"ƈ": u"C",
        u"Ƈ": u"C",

        u"d": u"d", u"ď": u"d",  u"đ": u"d", u"ð": u"d", u"ɖ": u"ɖ",
        u"Ď": u"D", u"Đ": u"D", u"Ɖ": u"d",
        u"e": u"e", u"é": u"e", u"ë": u"e", u"ê": u"e", u"è": u"e", u"ē": u"e", u"ĕ": u"e", u"ė": u"e", u"ę": u"e",
        u"ě": u"e",
        u"È": u"E", u"É": u"E", u"Ê": u"E", u"Ë": u"E", u"Ē": u"E", u"Ĕ": u"E", u"Ė": u"E", u"Ę": u"E", u"Ě": u"E",

        u"f": u"f",
        u"g": u"g", u"ġ": u"g", u"ĝ": u"g", u"ģ": u"g",
        u"Ĝ": u"G", u"Ğ": u"G", u"Ġ": u"G", u"Ģ": u"G",

        u"h": u"h", u"ħ": u"h",  u"ĥ": u"h",
        u"Ħ": u"H", u"Ĥ": u"H",

        u"i": u"i", u"í": u"i", u"ï": u"i", u"ì": u"i", u"î": u"i", u"ĭ": u"i", u"ĩ": u"i", u"ī": u"i", u"Į": u"I",
        u"ı": u"i",
        u"Ì": u"I", u"Í": u"I", u"Î": u"I", u"Ï": u"I", u"Ĩ": u"I", u"Ī": u"I", u"Ĭ": u"I", u"į": u"i", u"I": u"I",

        u"Ĳ": u"IJ",
        u"ĳ": u"ij",

        u"ß": u"ss",

        u"j": u"j", u"ĵ": u"j",
        u"Ĵ": u"J",

        u"k": u"k", u"Ķ": u"K", u"ķ": u"k", u"ĸ": u"K",

        u"l": u"l", u"ļ": u"l", u"ľ": u"l", u"ĺ": u"l", u"ŀ": u"l", u"ł": u"l",
        u"Ĺ": u"L", u"Ļ": u"L", u"Ľ": u"L", u"Ŀ": u"L", u"Ł": u"L",

        u"m": u"m", u"µ": u"m",

        u"n": u"n", u"ñ": u"n", u"ń": u"n", u"ņ": u"n", u"ň": u"n", u"ŋ": u"n",
        u"Ñ": u"N", u"Ń": u"N", u"Ņ": u"N", u"Ň": u"N", u"ʼN": u"n", u"Ŋ": u"N",

        u"o": u"o", u"ó": u"o", u"ö": u"o", u"ô": u"o", u"ø": u"o", u"õ": u"o", u"œ": u"oe", u"ò": u"o", u"ɔ": u"o",
        u"Ò": u"O", u"Ó": u"O", u"Ô": u"O", u"Õ": u"O", u"Ö": u"O",  u"Ø": u"O", u"Ɔ": u"O",

        u"Ō": u"O", u"Ŏ": u"O", u"Ő": u"o",
        u"ō": u"o", u"ŏ": u"o", u"ő": u"o",

        u"Œ": u"oe",
        u"p": u"p",
        u"q": u"q",

        u"r": u"r", u"ŕ": u"r", u"ŗ": u"t", u"ř": u"r",
        u"Ŕ": u"R", u"Ŗ": u"R", u"Ř": u"R",

        u"s": u"s", u"ş": u"s", u"š": u"s", u"ś": u"s", u"ŝ": u"s", u"S": u"S", u"ſ": u"s",
        u"Ś": u"S", u"Ŝ": u"S", u"Ş": u"S", u"Š": u"S",

        u"t": u"t", u"ţ": u"t", u"ť": u"t", u"ŧ": u"t", u"Ţ": u"T", u"Ť": u"T",
        u"Ŧ": u"T",

        u"u": u"u", u"ü": u"u", u"û": u"u", u"ù": u"u", u"ú": u"u", u"ũ": u"u", u"ū": u"u", u"ŭ": u"u", u"ů": u"u",
        u"ű": u"u", u"ų": u"u",
        u"Ù": u"U", u"Ú": u"U", u"Ü": u"U", u"Û": u"U", u"Ũ": u"U", u"Ū": u"U", u"Ŭ": u"U", u"Ů": u"U", u"Ű": u"U",
        u"Ų": u"U",

        u"v": u"v",
        u"w": u"w",
        u"ŵ": u"w", u"Ŵ": u"W",
        u"x": u"x",

        u"y": u"y", u"ÿ": u"y", u"ý": u"y", u"ŷ": u"y",
        u"Ÿ": u"Y", u"¥": u"Y", u"Ý": u"Y", u"Ŷ": u"Y",

        u"z": u"z", u"ź": u"z", u"ž": u"z", u"ż": u"z",
        u"Ź": u"Z", u"Ż": u"Z", u"Ž": u"Z",
    }

    # for x, y in convert.items():
    #     print x, y

    for x in temp:
        # print x
        if x in convert:
            # print "yes", x
            builder.write(convert[x])
        else:
            # print "no", x
            if type(x) == str:
                builder.write(to_bytes(x))
            else:
                builder.write(str(x, "utf-8"))
    return builder.getvalue()


def character_mapping(input_text):
    print(input_text)
    if type(input_text) is str:
        return unidecode(input_text)
    print(unidecode("""super-schwüler gewählt für."""))


def to_alphanumeric(input_text, spacing="_"):
    print(input_text)
    # if type(input_text) is not str:
    #     input_text = (str(input_text, "utf-8"))
    return re.sub('[\\W]', spacing, input_text)

# print(to_alphanumeric("Встре́ча с медве́дем мо́жет быть о́чень опа́сна. Ру́сские лю́ди лю́бят ходи́ть в лес и собира́ть грибы́ и я́годы. Они́ де́лают э́то с осторо́жностью, так как медве́ди то́же о́чень лю́бят я́годы и мо́гут напа́сть на челове́ка. Медве́дь ест всё: я́годы, ры́бу, мя́со и да́же насеко́мых. Осо́бенно он лю́бит мёд."))
# print(character_mapping("Встре́ча с медве́дем мо́жет быть о́чень опа́сна. Ру́сские лю́ди лю́бят ходи́ть в лес и собира́ть грибы́ и я́годы. Они́ де́лают э́то с осторо́жностью, так как медве́ди то́же о́чень лю́бят я́годы и мо́гут напа́сть на челове́ка. Медве́дь ест всё: я́годы, ры́бу, мя́со и да́же насеко́мых. Осо́бенно он лю́бит мёд."))
# print(character_mapping("Bénin"))
# print(to_alphanumeric("Bénin"))


def prep_4_uri(input_text):

    # map diacritic characters
    mapping = character_mapping(input_text)

    # Only alpha numeric
    return to_alphanumeric(mapping)


def zip_folder(input_folder_path, output_file_path=None):

    """
    Zip the contents of an entire folder (with that folder included
    in the archive). Empty sub-folders will be included in the archive
    as well.
    """

    if output_file_path is not None:
        print("output_file_path:", output_file_path)
        print("output_file_path directory:", path.dirname(output_file_path))

    if output_file_path is None or path.isdir(path.dirname(output_file_path)) is False:
        print("CREATING THE DIRECTORY")
        output_file_path = os.path.join(os.path.abspath(
            os.path.join(input_folder_path, os.pardir)), "exportResearch.zip")

    # parent_dir = os.path.abspath(os.path.join(input_folder_path, os.pardir))

    file_name = os.path.basename(output_file_path)
    (short_name, extension) = os.path.splitext(file_name)

    # Retrieve the paths of the folder contents.
    contents = os.walk(input_folder_path)
    zip_f = None

    try:

        zip_f = f_zip.ZipFile(output_file_path, 'w', f_zip.ZIP_DEFLATED)

        for root, folders, files in contents:

            # Include all sub-folders, including empty ones.
            for folder_name in folders:
                absolute_path = os.path.join(root, folder_name)
                # print "Adding '%s' to archive." % absolute_path
                zip_f.write(absolute_path, "{0}{0}{1}{0}{0}{2}".format(os.path.sep, short_name, file_name))

            for file_name in files:
                absolute_path = os.path.join(root, file_name)
                # print "Adding '%s' to archive." % absolute_path
                zip_f.write(absolute_path, "{0}{0}{1}{0}{0}{2}".format(os.path.sep, short_name, file_name))

        print("\n\t'%s' created successfully." % output_file_path)
        return output_file_path

    except IOError as err:
        print(err.__str__)
        sys.exit(1)
    # except OSError as err:
    #     print(err.__str__)
    #     sys.exit(1)
    except f_zip.BadZipfile as err:
        print(err.__str__)
        sys.exit(1)
    finally:
        if zip_f is not None:
            zip_f.close()


def zip_file(file_path):

    with open(file_path, 'rb') as f_in:
        with gzip.open(F'{file_path}.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


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
            graph           : THE DATASET URI
            data =
                [
                    entity_type : THE ENTITY TYPE OF INTEREST
                    properties  : THE PROPERTIES SELECTED BY THE USER FOR THE ABOVE TYPE
                ]
        },
        ...
    ]
    """

    rsc_builder = io.StringIO()
    if type(resources) is str:
        rsc_builder.write("\t\t{}\n".format(to_nt_format(resources)))
    else:
        for i in range(0, len(resources)):
            rsc_builder.write("\t{}\n".format(to_nt_format(resources[i]))) if i == 0 \
                else rsc_builder.write("\t\t\t{}\n".format(to_nt_format(resources[i])))

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
    query = io.StringIO()
    empty = True
    for dictionary in targets:
        graph = dictionary[St.graph]
        data = dictionary[St.data]
        for types in data:
            data_type = types[St.entity_type]
            properties = types[St.properties]
            for i_property in properties:
                p_formatted = to_nt_format(i_property)
                if empty is True:
                    query.write("\t\tVALUES ?resource \n\t\t{{\n\t\t {} \t\t}}".format(rsc_builder.getvalue()))
                    query.write(i_format.format(graph, data_type, p_formatted))
                    empty = False
                else:
                    query.write("\tUNION" + i_format.format(graph, data_type, p_formatted))

    return query.getvalue()
#
# # THIS NEED TO BE A STRING OTHERWISE IT DOES NOT WORK IN STARDOG
#                 BIND("{2}" AS ?property)
#                 # WE BIND THE DATASET TO EXTRACT IT IN THE SELECT
#                 BIND(<{0}> AS ?dataset)
#                 ?resource a <{1}> .
#                 ?resource {2} ?value


def confusion_matrix(true_p=0, false_p=0, true_n=0, false_n=0,
                     positive_ground_truth=0, observations=0, latex=False, zero_rule=True, code=True):

    # CODE IS JUST FOR THE ZERO RULE. zero_rule=False ==> code=False
    # OBSERVATIONS IS THE TOTAL OF ITEMS IN THE GROUND TRUTH
    confusion_zero = []

    if zero_rule is True:

        if positive_ground_truth > observations - positive_ground_truth:
            confusion_zero += confusion_matrix(
                true_p=positive_ground_truth, false_p=observations - positive_ground_truth, true_n=0, false_n=0,
                positive_ground_truth=positive_ground_truth, observations=observations, latex=latex, zero_rule=False,
                code=False)

        else:
            confusion_zero += confusion_matrix(
                true_p=0, false_p=0, true_n=observations - positive_ground_truth, false_n=positive_ground_truth,
                positive_ground_truth=positive_ground_truth, observations=observations, latex=latex, zero_rule=False,
                code=False)

    # else:
    #     confusion_zero = [("-", "-", "-", "-")]
    # confusion_matrix(true_p=231, false_p=58, ground_truth_p=272, false_n=41, true_n=61, observations=391)

    # PREDICT
    confusion = io.StringIO()

    recall = "-"
    precision = "-"
    ground_truth_n = "-"
    fall_out = "-"
    omission = "-"
    f_disc_rate = "-"
    n_pred_value = "-"
    likelihood_ratio = "-"
    f_1 = "-"

    positives = true_p + false_p
    negatives = false_n + true_n

    if positives > 0:
        recall = true_p / float(positives)
        f_disc_rate = round(false_p / float(positives), 3)

    if negatives > 0:
        omission = round(false_n / float(negatives), 3)
        n_pred_value = round(true_n / float(negatives), 3)

    if positive_ground_truth > 0:
        precision = true_p / float(positive_ground_truth)

    if observations >= positive_ground_truth:
        ground_truth_n = observations - positive_ground_truth
        if ground_truth_n > 0:
            fall_out = round(false_p / float(ground_truth_n), 3)

    if fall_out != "-" and fall_out > 0:
        likelihood_ratio = round(recall/fall_out, 3)

    if precision != "-" and recall != "-" and recall * precision > 0:
        f_1 = round(2 * (precision * recall)/(recall + precision), 3)

    long_line = "{:->105}\n".format("")
    short_line = "{:19}{:->35}\n".format("", "")
    end_line = "{:19}{:->86}\n".format("", "")
    short_line_base = "{:^19}{:->35}\n".format("*** BASE LINE ***" if zero_rule is True else "", "")

    base = "\\tiny *** BASE" if zero_rule is False else ""
    base_line = "\\tiny LINE ***" if zero_rule is False else ""

    # LINE 1
    confusion.write(short_line)
    confusion.write("{:>19}|{:^32} |\n".format("", "{} GROUND TRUTHS".format(observations)))

    # LINE 2
    bae_1 = "*** ZERO RULE ***" if code is False else ""
    bae_2 = "*** BASE LINE ***" if code is False else ""

    # if zero_rule is True:
    #     print confusion_zero[0]
    #     f1_0 = 0 if confusion_zero[0][2].rstrip() == "-" else confusion_zero[0][2]
    #     f1_1 = 0 if confusion_zero[1][2] == "-" else confusion_zero[1][2]
    #     print f1_0,"---" , f1_1, "---", confusion_zero[0][2].rstrip()
    #     bae_1 = "BETTER  THAN" if f1_1 > f1_0 else "WORST THAN"
    #     bae_2 = "THE BASELINE"

    confusion.write(short_line_base) if zero_rule is False else confusion.write(short_line)
    confusion.write("{:^19}| {:^14} | {:^14} |\n".format(bae_1, "GT Positive", "GT Negative"))
    confusion.write("{:^19}| {:^14} | {:^14} |\n".format(bae_2, positive_ground_truth, ground_truth_n))

    # LINE 3
    confusion.write(long_line)
    confusion.write("{:8}| Positive | {:^14} | {:^14} | {:^19} | {:^25} |\n".format(
        "", "True Positive", "False Positive", "Precision", "False discovery rate (FDR)"))

    if recall != "-":
        confusion.write("{:8}| {:^8} | {:^14} | {:^14} | {:^19} | {:^26} |\n".format(
            "", positives, true_p, false_p, round(recall, 3), f_disc_rate))
    else:
        confusion.write("{:8}| {:^8} | {:^14} | {:^14} | {:^19} | {:^26} |\n".format(
            "", positives, true_p, false_p, "-", f_disc_rate))

    # LINE 4
    confusion.write("{:7} {:->97}\n".format("PREDICT", ""))
    confusion.write("{:^8}| Negative | {:^14} | {:^14} | {:^19} | {:^25} |\n".format(
        str(positives + negatives),
        "False Negative", "True Negative", "False omission rate", "Negative predictive value "))
    confusion.write("{:8}| {:^8} | {:^14} | {:^14} | {:^19} | {:^26} |\n".format(
        "", negatives, false_n, true_n, omission, n_pred_value))

    # LINE 5
    confusion.write(long_line)
    confusion.write("{:8}           | {:^14} | {:^14} |{:^20} | {:^13}{:^13} |\n".format(
        "", "Recall", "Fall-out", " P. Likelihood Ratio", "F1 score", "Accuracy"))

    accuracy = round((true_p + true_n) / float(observations), 3) if observations > 0 else 0

    if precision != "-":
        confusion.write("{:8}           | {:^14} | {:^14} |{:^20} | {:^13}{:^13} |\n".format(
            "", round(precision, 3), fall_out, likelihood_ratio, f_1, accuracy))
    else:
        confusion.write("{:8}           | {:^14} | {:^14} |{:^20} | {:^13} {:^13}|\n".format(
            "", precision, fall_out, likelihood_ratio, f_1, accuracy))

    # LINE 6
    confusion.write(end_line)

    if zero_rule is True:
        confusion.write("\nPrecision                  PPV   = Positive Predicted Value  = TP / (TP + FP)\n")
        confusion.write("Recall                     TPR   = True Positive Rate        = TP / GT\n")
        confusion.write("False discovery rate       FDR   = Σ False positive / Σ Predicted condition positive\n")
        confusion.write("Negative predictive value  NPV   = Σ True negative / Σ Predicted condition negative\n")
        confusion.write("False omission rate        FOR   = Σ False negative / Σ Predicted condition negative\n")
        confusion.write("Positive likelihood ratio  LR+   = TPR / FPR\n")
        confusion.write("False positive rate        FPR   = Σ False positive / Σ Condition negative\n")
        confusion.write("FPR a.k.a Fall-out, probability of false alarm")

    latex_cmd = """
\\newcolumntype{{s}}{{>{{\columncolor[HTML]{{AAACED}}}} p{{3cm}}}}
\\renewcommand{{\\arraystretch}}{{1.2}}
\\begin{{table}}[h!]
    \\vspace{{-0.5cm}}
    \centering
    {{\scriptsize
    \\begin{{tabular}}{{
    >{{\centering\\arraybackslash}}p{{0.5cm}}
    >{{\centering\\arraybackslash}}p{{1.5cm}} |
    >{{\centering\\arraybackslash}}p{{1.6cm}} |
    >{{\centering\\arraybackslash}}p{{1.6cm}} |
    >{{\centering\\arraybackslash}}p{{2.2cm}}
    >{{\centering\\arraybackslash}}p{{2.3cm}} }} \cline{{3-4}}
     % RAW 1 ************************************
     \cline{{3-4}}
    &
    & \multicolumn{{2}}{{ c| }}{{\cellcolor{{gray!10}} \\tiny {0} GROUND TRUTHS}}
    &
    & \\\\
    % RAW 2 ************************************
    \cline{{3-4}} \cline{{3-4}}
    \cline{{3-4}}
    & {18}
    & GT. Pos.
    & GT. neg.
    &
    & \\\\
    % RAW 3 ************************************
    & {19}
    & {1}
    & {2}
    &
    & \\\\
    % RAW 4 ************************************
    \cline{{1-6}}
     \multicolumn{{1}}{{ |c| }}{{\cellcolor{{gray!10}}}}
    &  \\tiny POSITIVE
    & True Pos.
    & False Pos.
    & {{\cellcolor{{green!10}} Precision}}
    & \multicolumn{{1}}{{ |c| }}{{False Discovery Rate}} \\\\
    % RAW 5 ************************************
    \multicolumn{{1}}{{ |c| }}{{\cellcolor{{gray!10}}}}
    & {15}
    & {3}
    & {4}
    & {{\cellcolor{{green!10}} {5}}}
    & \multicolumn{{1}}{{ |c| }}{{{6}}} \\\\
    % RAW 6 ************************************
     \cline{{2-6}}\multicolumn{{1}}{{ |c| }}{{\cellcolor{{gray!10}}}}
    & \\tiny NEGATIVE
    & False Neg.
    & True Neg.
    & F. Omission Rate
    & \multicolumn{{1}}{{ |c| }}{{Neg. Predictive Value}} \\\\
     % RAW 7 ************************************
    \multicolumn{{1}}{{ |c| }}{{\multirow{{-4}}{{*}}{{\\rotatebox[origin=c]{{90}}
    {{\cellcolor{{gray!10}} \\tiny  \\textbf{{PREDICT}}}}}}}}
    & {16}
    & {7}
    & {8}
    & {9}
    & \multicolumn{{1}}{{ |c| }}{{{10}}} \\\\
    % RAW 8 ************************************
    \cline{{1-6}}\multicolumn{{1}}{{  c  }}{{       }}
    &
    & {{ \cellcolor{{green!10}} Recall}}
    & Fall-out
    & Positive L. Ratio
    & \multicolumn{{1}}{{ |c| }}{{\cellcolor{{green!10}} F1 score | Accuracy}} \\\\
    % RAW 9 ************************************
    \multicolumn{{1}}{{  c  }}{{       }}
    &
    & {{ \cellcolor{{green!10}} {11}  }}
    & {12}
    & {13}
    & \multicolumn{{1}}{{ |c| }}{{\cellcolor{{green!10}} {14} | {17}}}  \\\\
    \cline{{3-6}}
    \end{{tabular}}
    \\vspace{{5pt}}
    \caption{{Confusion matrix for link-networks of size 8.}}
    \label{{table_confusion_matrix}}
    }}
    \\vspace{{-1cm}}
\end{{table}}
    """.format(observations, positive_ground_truth, ground_truth_n, true_p, false_p,
               round(recall, 3) if recall != "-" else "-", f_disc_rate,
               false_n, true_n, omission, n_pred_value, round(precision, 3) if precision != "-" else "-",
               fall_out, likelihood_ratio, f_1, positives, negatives, accuracy, base, base_line)

    print("\n{}".format(confusion.getvalue()))
    if latex is True:
        print(latex_cmd)

    # if code == 1:
    #     return confusion_zero, "".format(confusion.getvalue()), latex_cmd, f_1, accuracy
    # print "\n\n>>> CONFUSION", ("".format(confusion.getvalue()), f_1, accuracy)

    confusion_zero += [(confusion.getvalue(), latex_cmd, f_1, accuracy)]
    return confusion_zero


def combinations(paths):

    # RETURN ALL POSSIBLE COMBINATIONS OF TWO ITEM REGARDLESS OF THE DIRECTION
    combined = []
    size = len(paths)
    for i in range(0, size):
        # print paths[i]

        for j in range(i+1, size):
            # print "\t", paths[i], paths[j]
            combined += [(paths[i], paths[j])]

    return combined


def ordered_combinations(paths):

    # RETURN ALL POSSIBLE COMBINATIONS OF TWO ITEM REGARDLESS OF THE DIRECTION
    combined = []
    size = len(paths)
    for i in range(0, size):
        for j in range(i+1, size):
            combined += [(paths[i], paths[j])] if paths[i] < paths[j] else [(paths[j], paths[i])]
    return combined


def full_combinations(paths):

    # RETURN ALL POSSIBLE COMBINATIONS OF TWO ITEM REGARDLESS OF THE DIRECTION
    combined = []
    size = len(paths)
    for i in range(0, size):
        for j in range(i+1, size):
            combined += [(paths[i], paths[j])]
            combined += [(paths[j], paths[i])]
    return combined


# def sample_size(population_size, confidence_level=0.05, degree_freedom=1):
#
#     # CHI SQUARE WITH 1 DEGREE OF FREEDOM (0.10) = 2.71
#     # CHI SQUARE WITH 1 DEGREE OF FREEDOM ( (0.05) = 3.84
#     # CHI SQUARE WITH 1 DEGREE OF FREEDOM ( (0.01) = 6.64
#     # CHI SQUARE WITH 1 DEGREE OF FREEDOM ( (0.001) = 10.83
#     # https: // www.surveysystem.com / sscalc.htm
#     # https://www.surveymonkey.com/mp/sample-size-calculator/
#     from math import pow
#     from scipy.stats import chi2
#     chi = chi2.isf(q=confidence_level, df=degree_freedom)
#
#     # R.V. Krejcie and D.W. Morgan,
#     # Determining sample size for research activities,
#     # Educational and Psychological Measurement 30 (1970), 607–610
#
#     n = population_size     # POPULATION SIZE
#     p = 0.50                # POPULATION PROPORTION
#     d = confidence_level    # DEGREE OF ACCURACY
#     return round((chi * n * p * (1 - p)) / (pow(d, 2) * (n - 1) + chi * p * (1 - p)), 0)


def get_key(node_1, node_2):
    strength_key = "key_{}".format(str(hasher((node_1, node_2))).replace("-", "N")) if node_1 < node_2 \
        else "key_{}".format(str(hasher((node_2, node_1))).replace("-", "N"))
    return strength_key
