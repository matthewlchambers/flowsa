from typing import Union, List
from collections.abc import Iterable
from pathlib import Path
import appdirs
import esupy.processed_data_mgmt

MODULE_PATH = Path(__file__).resolve().parent
LOCAL_PATH = Path(appdirs.user_data_dir()) / 'flowsa'

esupy_paths = esupy.processed_data_mgmt.Paths()
esupy_paths.local_path = LOCAL_PATH


# # This is for  functions that require a Paths() object from esupy
# def esupy_paths(remote = None, local = None) -> esupy.processed_data_mgmt.Paths:
#     paths = esupy.processed_data_mgmt.Paths()
#     if local is not None:
#         paths.local_path = local
#     else:
#         paths.local_path = LOCAL_PATH
#     if remote is not None:
#         paths.remote_path = remote

class PathList(list):
    def __init__(self, val=None):
        if isinstance(val, Iterable) and not isinstance(val, str):
            super().__init__(Path(p) for p in val)
        elif val is not None:
            super().__init__([Path(val)])
        else:
            super().__init__()

    def __truediv__(self, other) -> 'PathList':
        return PathList(p / other for p in self)

    def __mod__(self, other) -> Path:
        return self.find(other, return_all=False)

    def __add__(self, other) -> 'PathList':
        return PathList(super().__add__(other))

    def append(self, __object) -> None:
        return super().append(Path(__object))

    def extend(self, __iterable: Iterable) -> None:
        return super().extend([Path(x) for x in __iterable])

    def find(
        self, file: str, return_all: bool = False
    ) -> Union[Path, 'PathList']:
        '''
        Checks all folders in the list for a given file name. If return_all
        is False (default), the Path to the first matching file is returned.
        If return_all is True, a PathList of matching files is returned. If the
        file is not found, None is returned.
        '''
        paths_to_file = PathList([p for p in (self / file) if p.is_file()])
        if paths_to_file:
            return paths_to_file if return_all else paths_to_file[0]

    def glob_find(self, glob: str) -> List[Path]:
        '''
        Searches all folders in the list for filenames matching a given glob.
        Return a list of Path objects pointing to these files.
        '''
        return [f for p in self for f in p.glob(glob)]


class PathListValidator:
    def __init__(self) -> None:
        self.val = PathList()

    def __get__(self, instance, objtype) -> PathList:
        return self.val

    def __set__(self, instance, val) -> None:
        self.val = PathList(val)


class InputPaths:
    data = PathListValidator()
    crosswalks = PathListValidator()
    external_data = PathListValidator()
    process_adjustments = PathListValidator()

    methods = PathListValidator()
    fba_methods = PathListValidator()
    fbs_methods = PathListValidator()
    activity_sets = PathListValidator()

    data_source_scripts = PathListValidator()

    scripts = PathListValidator()
    script_fbas = PathListValidator()

    fba = PathListValidator()
    fbs = PathListValidator()


class PathValidator:
    def __init__(self) -> None:
        self.val = None

    def __get__(self, instance, objtype) -> Path:
        return self.val

    def __set__(self, instance, val) -> None:
        if val is None:
            self.val = None
        else:
            self.val = Path(val)


class OutputPaths:
    base = PathValidator()
    fba = PathValidator()
    fbs = PathValidator()
    bibliography = PathValidator()
    log = PathValidator()
    comparison = PathValidator()
    plot = PathValidator()
    table = PathValidator()

    def create_missing(self) -> None:
        for p in [self.base, self.fba, self.fbs, self.bibliography,
                  self.log, self.comparison, self.plot, self.table]:
            if p:
                p.mkdir(parents=True, exist_ok=True)
