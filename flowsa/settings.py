import sys
import os
import logging
import subprocess
from importlib.metadata import version
from pathlib import Path
from esupy.processed_data_mgmt import Paths, mkdir_if_missing
from esupy.util import get_git_hash

try:
    MODULEPATH = \
        os.path.dirname(os.path.realpath(__file__)).replace('\\', '/') + '/'
except NameError:
    MODULEPATH = 'flowsa/'

datapath = MODULEPATH + 'data/'
crosswalkpath = datapath + 'activitytosectormapping/'
externaldatapath = datapath + 'external_data/'
process_adjustmentpath = datapath + 'process_adjustments/'

methodpath = MODULEPATH + 'methods/'
sourceconfigpath = methodpath + 'flowbyactivitymethods/'
flowbysectormethodpath = methodpath + 'flowbysectormethods/'
flowbysectoractivitysetspath = methodpath + 'flowbysectoractivitysets/'

datasourcescriptspath = MODULEPATH + 'data_source_scripts/'

# "Paths()" are a class defined in esupy
paths = Paths()
paths.local_path = paths.local_path / 'flowsa'
outputpath = paths.local_path
fbaoutputpath = outputpath / 'FlowByActivity'
fbsoutputpath = outputpath / 'FlowBySector'
biboutputpath = outputpath / 'Bibliography'
logoutputpath = outputpath / 'Log'
diffpath = outputpath / 'FBSComparisons'
plotoutputpath = outputpath / 'Plots'

# ensure directories exist
mkdir_if_missing(logoutputpath)
mkdir_if_missing(plotoutputpath)

DEFAULT_DOWNLOAD_IF_MISSING = False

# paths to scripts
scriptpath = \
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))
                    ).replace('\\', '/') + '/scripts/'
scriptsFBApath = scriptpath + 'FlowByActivity_Datasets/'

# define 4 logs, one for general information, one for major validation
# logs that are also included in the general info log, one for very specific
# validation that is only included in the validation log, and a console
# printout that includes general and validation, but not detailed validation


# format for logging .txt generated
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')

# create loggers
# general logger
log = logging.getLogger('allLog')
log.setLevel(logging.DEBUG)
log.propagate = False
# log.propagate=False
# general validation logger
vLog = logging.getLogger('validationLog')
vLog.setLevel(logging.DEBUG)
vLog.propagate = False
# detailed validation logger
vLogDetailed = logging.getLogger('validationLogDetailed')
vLogDetailed.setLevel(logging.DEBUG)
vLogDetailed.propagate = False

# create handlers
# create handler for overall logger
log_fh = logging.FileHandler(logoutputpath / 'flowsa.log',
                             mode='w', encoding='utf-8')
log_fh.setFormatter(formatter)
# create handler for general validation information
vLog_fh = logging.FileHandler(logoutputpath / 'validation_flowsa.log',
                              mode='w', encoding='utf-8')
vLog_fh.setFormatter(formatter)
# create console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

# add handlers to various loggers
# general logger
log.addHandler(ch)  # print to console
log.addHandler(log_fh)
vLog.addHandler(log_fh)
# validation logger
vLog.addHandler(ch)  # print to console
vLog.addHandler(vLog_fh)
vLogDetailed.addHandler(vLog_fh)


def return_pkg_version():
    # return version with git describe
    try:
        # set path to flowsa repository, necessary if running method files
        # outside the flowsa repo
        tags = subprocess.check_output(
            ["git", "describe", "--tags", "--always"],
            cwd=MODULEPATH).decode().strip()
        pkg_version = tags.split("-", 1)[0].replace('v', "")
    except subprocess.CalledProcessError:
        pkg_version = version('flowsa')

    return pkg_version


# https://stackoverflow.com/a/41125461
def memory_limit(percentage=.93):
    # Placed here becuase older versions of Python do not have this
    import resource
    # noinspection PyBroadException
    try:
        max_memory = get_memory()
        print(f"Max Memory: {max_memory}")
    except Exception:
        print("Could not determine max memory")
    else:
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (int(max_memory * 1024 * percentage), hard))


def get_memory():
    with open('/proc/meminfo', 'r') as mem:
        free_memory = 0
        for i in mem:
            sline = i.split()
            if str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:', 'SwapFree:'):
                free_memory += int(sline[1])
    return free_memory


# metadata
PKG = "flowsa"
PKG_VERSION_NUMBER = return_pkg_version()
GIT_HASH_LONG = os.environ.get('GITHUB_SHA') or get_git_hash('long')
if GIT_HASH_LONG:
    GIT_HASH = GIT_HASH_LONG[0:7]
else:
    GIT_HASH = None

# Common declaration of write format for package data products
WRITE_FORMAT = "parquet"
