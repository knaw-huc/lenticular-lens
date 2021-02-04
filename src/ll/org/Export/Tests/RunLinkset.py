

from ll.org.Export.Scripts.SpecsBuilder import linksetSpecsData
from ll.org.Export.Tests.TestData import DATA_DIR as DIR
from os.path import join

test, chiara, leon = False, False, True
save_in, csv = "/Users/kerim/git/lenticular-lenses/", "Accepted.csv"
chiara_csv = ["ef3849ec51b1aaee68cbca751ddcb652-6.csv"]
n = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]

# SCRIPT OVERVIEW #####################################################################################################
#                                                                                                                     #
#   OBSERVED ISSUES                                                                                                   #
#                                                                                                                     #
# #####################################################################################################################

"""
    #   sem:#Time
    #   sem:#hasLatestEndTimeStamp
    #   __value__

    lstId=6, job=demo

    - property [3]
        1. saa_isInRecord
        2. saa_IndexOpOndertrouwregisters
        3. saa_registrationDate

    - short_properties [3]
        1. saa:isInRecord
        2. ...........
        3. saa:registrationDate

    - uri_properties [3]
        1. None
        2. ...........
        3. None

    LINKSET 18, 17 lstId=0, job=leon_uri_1

    - property [3]
        1. bio_birth
        2. ga_Event
        3. sem_hasEarliestBeginTimeStamp

    - short_properties [3]
        1. bio:birth
        2. 
        3. sem:hasEarliestBeginTimeStamp

    - uri_properties [3]
        1. None
        2. 
        3. None
"""

# SCRIPT OVERVIEW #####################################################################################################
#                                                                                                                     #
#   TESTING THE CODE USING JOBS PRODUCED BY LEON CHIARA AND THE DEMO                                                  #
#                                                                                                                     #
# #####################################################################################################################

if test:
    linksetSpecsData(
        linksetId=15, job='demo', filePath=join(DIR, csv), starReification=False, save_in=save_in, printSpec=False)

if chiara:

    # CHIARA JOBS RESULT OVERVIEW ####################################################################################
    #   01. ac8e16d756d8a901e65b8ca06b55166d : PROBLEM WITH NON EXISTING LONG URI FOR rdaGr2:dateOfBirth
    #   02. ef3849ec51b1aaee68cbca751ddcb652 : NO PROBLEM OBSERVED
    #   03. b402109b65d40e83ca9d4ed500c48f80 : THIS JOB ID APPEARS TO NOT HAVE ANY LINKSET
    #   04. e11534a1baeb545c3d32159b6d9659bf : PROBLEM WITH NON EXISTING LONG URI FOR saa and rdfs
    #   05. a6433528a993389afa2c946ddc860182 : NO PROBLEM OBSERVED
    #   06. 7f63b5e6bea5224c11f7f939d132bf0e : NO PROBLEM OBSERVED
    #   07. e149fc93e2c172d9fc6784f996eb1400 : PROBLEM WITH NON EXISTING LONG URI FOR saa:
    #   08. 8c46acd48ea393c447a7ccb9f0aaea2b :
    #   09. 01492c5d3a4870e63145287108c881cf : PROBLEM WITH NON EXISTING LONG URI FOR schema:
    #   10. c52a1b1d91d541549f23bab5fe94e91b : NO PROBLEM OBSERVED
    # ################################################################################################################

    jobs = [
        "ac8e16d756d8a901e65b8ca06b55166d", "ef3849ec51b1aaee68cbca751ddcb652", "b402109b65d40e83ca9d4ed500c48f80",
        "e11534a1baeb545c3d32159b6d9659bf", "a6433528a993389afa2c946ddc860182", "7f63b5e6bea5224c11f7f939d132bf0e",
        "e149fc93e2c172d9fc6784f996eb1400", "8c46acd48ea393c447a7ccb9f0aaea2b", "01492c5d3a4870e63145287108c881cf",
        "c52a1b1d91d541549f23bab5fe94e91b"]

    for i in [6]:
        linksetSpecsData(linksetId=i, job=jobs[1], filePath=join(DIR, chiara_csv[0]),
                         starReification=True, save_in=save_in, printSpec=False)

if leon:

    # CHIARA JOBS RESULT OVERVIEW ####################################################################################
    #   01. 306ff87eccb2ef66dfe9d4521f90fcc4 : PROBLEM WITH NON EXISTING LONG URI FOR rdaGr2:dateOfBirth
    #   02. fb1cb1d40b5af63fe92fac088e21738f : NO PROBLEM OBSERVED
    # ################################################################################################################

    jobs = ["306ff87eccb2ef66dfe9d4521f90fcc4", "fb1cb1d40b5af63fe92fac088e21738f", ""]

    for i in [20]:
        linksetSpecsData(linksetId=i, job=jobs[1], filePath=join(DIR, csv),
                         starReification=True, save_in=save_in, printSpec=True)


