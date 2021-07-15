

from ll.org.Export.Scripts.SpecsBuilder import linksetSpecsData, lensSpecsDataItr, linksetSpecsDataItr, getLinks
from ll.org.Export.Tests.TestData import DATA_DIR as DIR
from csv import reader as csv_reader
from ll.org.Export.Tests.TestData import DATA_DIR as DIR
from os.path import join

# PREFIX.CC
# LEON: https://recon.diginfra.net/?job_id=fb1cb1d40b5af63fe92fac088e21738f
save_in = "/Users/al/Downloads/"
csv = ['demo_linkset_14.csv', "Accepted.csv", 'leon-38.txt']
jobs = ['demo', 'a7a63e74db5ffc0ff3d487a55e4ef89c']
# a7a63e74db5ffc0ff3d487a55e4ef89c


# SCRIPT OVERVIEW #####################################################################################################
#                                                                                                                     #
#   OBSERVED ISSUES                                                                                                   #
#                                                                                                                     #
# #####################################################################################################################

"""
==> EXACT SHOULD NOT HAVE A COMBINATION THRESHOLD 
==> CONFIGURE FUZZY LOGIC SHOULD NOT POPUP UNLESS SOURCE OR TARGET HAVE MORE THAN ONE PREDICATE    
==> DEFAULT SIMILARITY THRESHOLD OF TRIGRAM IS O.3???


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

# Apply list configuration
#     It is no longer possible to set the values of "minimum match" and "unique value"
#     once the page is saved without proper assignment (values are set to 0)

# Embedded

# intermediate
# #     It does not check for bad configuration

# TeAM

# New methods
#   TRIGRAM
#   METAPHONE
#   DOUBLE METAPHONE
#   bloothooftReduct

# THRESHOLDS
#   Levenshtein Distance    :   'max_distance'
#   Levenshtein Normalised  :   'threshold'
#   Jaro                    :   'threshold'
#   Trigram                 :   'threshold'
#   Jaro Winkler            :   'threshold' 'prefix_weight'
#   Soundex                 :   'size'
#   Bloothooft              :   'name_type'
#   Word Intersection       :   'approximate': True, 'ordered': False, 'stop_symbols': ".-,+'?;()–", 'threshold': 0.7
#   Metaphone               :   'max'
#   DOUBLE METAPHONE        :


# SCRIPT OVERVIEW #####################################################################################################
#                                                                                                                     #
#   TESTING THE CODE USING JOBS PRODUCED BY LEON CHIARA AND THE DEMO                                                  #
#                                                                                                                     #
# #####################################################################################################################

# USING CSV FILE
# linksetSpecsData(
#     linksetId=14, job='demo', filePath=join(DIR, csv), starReification=False, save_in=save_in, printSpec=False)

# USING ITERATOR
used_csv = 0
used_job = 0
loop = 12


LINKSET = True

if LINKSET:

    linkset = 15
    links = getLinks(job_id=jobs[used_job], set_id=linkset, isLinkset=True)

    for line in links:
        for key, item in line.items():
            print("\t", key, item)
        break

    linksetSpecsDataItr(
        linksetId=linkset, job=jobs[used_job], lst_result=links,
        starReification=True, save_in=save_in, printSpec=False
    )

else:
    lens_id = 4
    csv_links = getLinks(job_id=jobs[used_job], set_id=lens_id, isLinkset=False)

    for line in csv_links:
        for key, item in line.items():
            print("\t", key, item)
        break

    lensSpecsDataItr(
        lensId=lens_id, job=jobs[used_job], lens_result=csv_links,
        starReification=True, save_in=save_in, printSpec=False)

# from ll.org.Export.Scripts.AnnotatedLinkset_Generic import standardLinkGenerator2
#
# with open(join(DIR, csv[used_csv])) as file_data:
#     data = csv_reader(file_data)
#
#     for item in standardLinkGenerator2("http:testing/voila/owl", data, {}):
#         print(item)
#         continue
