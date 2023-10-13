from . import path_tools
import subprocess
import os
from importlib.metadata import version
from esupy.util import get_git_hash

# Set default paths for inputs and outputs
input_paths = path_tools.InputPaths()

input_paths.data = path_tools.MODULE_PATH / 'data'
input_paths.crosswalks = input_paths.data / 'activitytosectormapping'
input_paths.external_data = input_paths.data / 'external_data'
input_paths.process_adjustments = input_paths.data / 'process_adjustments'

input_paths.methods = path_tools.MODULE_PATH / 'methods'
input_paths.fba_methods = input_paths.methods / 'flowbyactivitymethods'
input_paths.fbs_methods = input_paths.methods / 'flowbysectormethods'
input_paths.activity_sets = input_paths.methods / 'flowbysectoractivitysets'

input_paths.data_source_scripts = path_tools.MODULE_PATH / 'data_source_scripts'

input_paths.scripts = path_tools.MODULE_PATH.parent / 'scripts'
input_paths.script_fbas = input_paths.scripts / 'FlowByActivity_Datasets'

input_paths.fba = path_tools.LOCAL_PATH / 'FlowByActivity'
input_paths.fbs = path_tools.LOCAL_PATH / 'FlowBySector'

output_paths = path_tools.OutputPaths()

output_paths.base = path_tools.LOCAL_PATH
output_paths.fba = output_paths.base / 'FlowByActivity'
output_paths.fbs = output_paths.base / 'FlowBySector'
output_paths.bibliography = output_paths.base / 'Bibliography'
output_paths.log = output_paths.base / 'Log'
output_paths.comparison = output_paths.base / 'FBSComparisons'
output_paths.plot = output_paths.base / 'Plots'
output_paths.table = output_paths.base / 'DisplayTables'

output_paths.create_missing()

DEFAULT_DOWNLOAD_IF_MISSING = False


def return_pkg_version():
    # return version with git describe
    try:
        # set path to flowsa repository, necessary if running method files
        # outside the flowsa repo
        tags = subprocess.check_output(
            ["git", "describe", "--tags", "--always"],
            cwd=path_tools.MODULE_PATH).decode().strip()
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
