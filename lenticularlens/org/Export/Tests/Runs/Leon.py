
from lenticularlens.org.Export.Scripts.SpecsBuilder import linksetSpecsData, linksetSpecsDataItr, getLinks, lensSpecsDataItr
from lenticularlens.org.Export.Tests.TestData import DATA_DIR as DIR
from os.path import join
from csv import reader as csv_reader

test, chiara, leon = True, False, False
save_in, csv, leon = "/Users/al/Downloads/", "Accepted.csv", "Leon-38.txt"


# CHIARA JOBS RESULT OVERVIEW ####################################################################################
#   01. 306ff87eccb2ef66dfe9d4521f90fcc4 : PROBLEM WITH NON EXISTING LONG URI FOR rdaGr2:dateOfBirth
#   02. fb1cb1d40b5af63fe92fac088e21738f : NO PROBLEM OBSERVED
# ################################################################################################################

jobs = ["306ff87eccb2ef66dfe9d4521f90fcc4", "fb1cb1d40b5af63fe92fac088e21738f", "261f2367696e8d2c01656ca2711bd51d"]
USED_JOB = 2
LIST_1 = [0, 1, 2, 5, 6, 7, 17, 18]
LIST_2 = [0, 1, 2, 4, 5, 10, 12, 14, 15, 18, 20, 21, 22, 24, 25, 24,  28, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 47]


LINKSET = True

if LINKSET:
    for i in [35]:
        # with open(join(DIR, leon)) as file_data:
        #     data = csv_reader(file_data)
        csv = getLinks(job_id=jobs[USED_JOB], set_id=i, isLinkset=True)
        linksetSpecsDataItr(linksetId=i, job=jobs[USED_JOB], lst_result=csv,
                                starReification=False, save_in=save_in, printSpec=False)

else:
    lens = 0
    csv = getLinks(job_id=jobs[USED_JOB], set_id=lens, isLinkset=False)
    lensSpecsDataItr(lensId=lens, job=jobs[USED_JOB], lens_result=csv,
                     starReification=True, save_in=save_in, printSpec=False)
