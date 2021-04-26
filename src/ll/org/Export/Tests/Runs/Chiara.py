from ll.org.Export.Scripts.SpecsBuilder import linksetSpecsData, linksetSpecsDataItr
from ll.org.Export.Tests.TestData import DATA_DIR as DIR
from csv import reader as csv_reader
from os.path import join

save_in = "/Users/al/Downloads/"
chiara_csv = ["ef3849ec51b1aaee68cbca751ddcb652-6.csv", "Accepted.csv", 'linkset_4.csv']


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

jobs = [("8c46acd48ea393c447a7ccb9f0aaea2b", [7]), ("01492c5d3a4870e63145287108c881cf", [5]),
        ("d37dcb8ab91c197600d6462bdedda307", [4]),
    "ac8e16d756d8a901e65b8ca06b55166d", "ef3849ec51b1aaee68cbca751ddcb652", "b402109b65d40e83ca9d4ed500c48f80",
    "e11534a1baeb545c3d32159b6d9659bf", "a6433528a993389afa2c946ddc860182", "7f63b5e6bea5224c11f7f939d132bf0e",
    "e149fc93e2c172d9fc6784f996eb1400", "8c46acd48ea393c447a7ccb9f0aaea2b", "01492c5d3a4870e63145287108c881cf",
    "c52a1b1d91d541549f23bab5fe94e91b"]

idx = 2
used_csv = 2
used_job = jobs[idx][0]
linkset = jobs[idx][1]

for i in linkset:
    # USING CSV FILE
    # linksetSpecsData(linksetId=i, job=jobs[1], filePath=join(DIR, chiara_csv[0]),
    #                  starReification=True, save_in=save_in, printSpec=False)

    # USING ITERATOR
    with open(join(DIR, chiara_csv[used_csv])) as file_data:
        data = csv_reader(file_data)
        linksetSpecsDataItr(
            linksetId=i, job=used_job, lst_result=data, starReification=True, save_in=save_in, printSpec=False)
