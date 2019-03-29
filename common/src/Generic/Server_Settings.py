import os
import src.Generic.Settings as St

# UPLOAD_FOLDER = os.getcwd()
SEP = os.path.sep
SRC_DIR = "{0}{1}{1}".format(os.getcwd(), SEP)
DIR = "{0}{1}{1}Alignments{1}{1}Data".format(os.getcwd(), SEP)
UPLOAD_FOLDER = "{0}{1}{1}UploadedFiles".format(os.getcwd(), SEP)
UPLOAD_ARCHIVE = "{0}{1}{1}UploadedArchive".format(os.getcwd(), SEP)
# "http://stardog.risis.d2s.labs.vu.nl/annex/risis/sparql/query"

# EXAMPLE 1
# SERVER_MAC = "localhost:5820"
# STARDOG_PATH_MAC = '/Applications/stardog-5.0.2/bin/'
# STARDOG_DATA_PATH_MAC = "/Users/userX/data/"

# EXAMPLE 2
# SERVER_LINUX = "stardog.server.d2s.labs.vu.nl"
# STARDOG_PATH_LINUX = '/scratch/risis/data/stardog/stardog-5.0/stardog-5.0/bin/'
# STARDOG_DATA_PATH_LINUX = '/scratch/risis/data/stardog/stardog-5.0/stardog-5.0/data/'

# EXAMPLE 3 IS CURRENTLY ACTIVATED
# SERVER_WIN = "localhost:5820"
# STARDOG_PATH_WIN = 'C:\\Program Files\\stardog-5.3.0\\bin\\'
# STARDOG_DATA_PATH_WIN = "C:\\Productivity\\data\\stardog"

DEFAULT_SERVER = "localhost:5820"
LENTICULAR_LENS_PORT = int(os.getenv("LL_PORT", 5077))
SERVER = os.getenv("LL_STARDOG_SERVER", DEFAULT_SERVER)
DEFAULT_DATABASE = os.getenv("LL_STARDOG_DATABASE", "gadb")
DEFAULT_DOMAIN = os.getenv("LL_DEFAULT_DOMAIN", "goldenagents.org")
STARDOG_PATH = os.getenv("LL_STARDOG_PATH", "C:\\Program Files\\stardog-5.0.5.1\\bin\\")
STARDOG_DATA = os.getenv("LL_STARDOG_DATA", "C:\\Disambiguation\\data\\stardog")

# IN stardog-5.0.5.1\bin\
# IN [stardog-server]       THE [STARDOG_HOME] CAN BE SET FOR THE [DATA PATH] AS WELL AS THE [BIN] PATH
# IN [stardog]              [STARDOG_JAVA_ARGS="-Xmx2g"]                                    CAN BE SET
# IN [stardog.bat]          [STARDOG_JAVA_ARGS=-Xmx2g] -Xms2g]                              CAN BE SET
# IN [stardog-admin.bat]    [STARDOG_JAVA_ARGS=-Xmx2g -Xms2g -XX:MaxDirectMemorySize=2g]    CAN BE SET


settings = {

    St.database: DEFAULT_DATABASE,
    St.stardog_user: "admin",
    St.stardog_pass: "admin",

    St.ll_port: LENTICULAR_LENS_PORT,

    # TRUE MEANS THE PYTHON SERVER AND THE STARDOG
    # SERVER ARE NOT ON THE SAME LOCAL HOST
    # St.split_sys: True,
    St.split_sys: False,

    # DOMAIN NAME
    St.domain_name: DEFAULT_DOMAIN,

    # STARDOG SERVER LOCAL HOST NAME
    St.stardog_host_name: SERVER,

    # STARDOG PATH
    St.stardog_path: STARDOG_PATH,

    # STARDOG DATA PATH
    St.stardog_data_path: STARDOG_DATA,

    # STARDOG 4 IS COMPATIBLE
    # STARDOG 5 IS NOT COMPATIBLE
    St.stardog_version: "NOT COMPATIBLE",
    # St.stardog_version: "COMPATIBLE",

    # MAIN DATA FOLDER
    St.data_dir: DIR,

    # LINKSET FOLDER
    St.linkset_dir: '{0}{1}{1}Linkset'.format(DIR, SEP),
    St.linkset_Exact_dir: '{0}{1}{1}Linkset{1}{1}Exact'.format(DIR, SEP),
    St.linkset_Subset_dir: '{0}{1}{1}Linkset{1}{1}Subset'.format(DIR, SEP),
    St.linkset_Approx_dir: '{0}{1}{1}Linkset{1}{1}Approx'.format(DIR, SEP),
    St.linkset_Emb_dir: '{0}{1}{1}Linkset{1}{1}Embedded'.format(DIR, SEP),
    St.linkset_ID_dir: '{0}{1}{1}Linkset{1}{1}Identifier'.format(DIR, SEP),
    St.linkset_Refined_dir: '{0}{1}{1}Linkset{1}{1}Refined'.format(DIR, SEP),
    St.lens_Refined_dir: '{0}{1}{1}Lens{1}{1}Refined'.format(DIR, SEP),

    # LENS FOLDER
    St.lens_dir: '{0}{1}{1}Lens'.format(DIR, SEP),
    St.lens_Diff_dir: '{0}{1}{1}Lens{1}{1}Diff'.format(DIR, SEP),
    St.lens_transitive__dir: '{0}{1}{1}Lens{1}{1}Transitive'.format(DIR, SEP),
    St.lens_Union__dir: '{0}{1}{1}Lens{1}{1}Union'.format(DIR, SEP),

    # FOLDER FOR DATASET FILES UPLOADED FOR  CONVERSION
    St.uploaded_dataset_dir: '{0}{1}{1}Dataset'.format(DIR, SEP),

    # UPLOADED ALIGNMENTS
    St.uploaded_alignments: '{0}{1}{1}Alignments'.format(DIR, SEP),
}

# STARDOG URI STANDING FOR STARDOG DATABASE
settings[St.stardog_uri] = "http://{}/{}".format(settings[St.stardog_host_name], settings[St.database])

# print DIR
