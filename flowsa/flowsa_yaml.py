from typing import IO, Callable
import yaml
from flowsa.settings import input_paths
from flowsa.path_tools import PathList
from os import path
import sys
import csv
import importlib


class FlowsaLoader(yaml.SafeLoader):
    '''
    Custom YAML loader implementing !include: tag to allow inheriting
    arbitrary nodes from other yaml files.
    '''
    def __init__(self, stream: IO) -> None:
        super().__init__(stream)
        self.add_multi_constructor('!include:', self.include)
        self.add_multi_constructor('!from_index:', self.from_index)
        self.add_multi_constructor('!script_function:', self.script_function)
        self.add_multi_constructor('!clean_function:', self.clean_function)
        self.add_constructor('!external_config', self.external_config)
        self.external_paths_to_search = PathList()
        self.external_path_to_pass = None

    @staticmethod
    def include(loader: 'FlowsaLoader', suffix: str, node: yaml.Node) -> dict:
        file, *keys = suffix.split(':')
        search_path = (loader.external_paths_to_search
                       + input_paths.fba_methods
                       + input_paths.fbs_methods
                       + input_paths.data)
        file = search_path % file

        if file is None:
            raise FileNotFoundError(f'{file} not found')

        with open(file) as f:
            branch = load(f, loader.external_path_to_pass)

        while keys:
            branch = branch[keys.pop(0)]

        if isinstance(node, yaml.MappingNode):
            if isinstance(branch, dict):
                context = loader.construct_mapping(node)
                branch.update(context)
            else:
                raise TypeError(f'{suffix} is not a mapping/dict')

        elif isinstance(node, yaml.SequenceNode):
            if isinstance(branch, list):
                context = loader.construct_sequence(node)
                branch.extend(context)
            else:
                raise TypeError(f'{suffix} is not a sequence/list')

        return branch

    @staticmethod
    def external_config(
        loader: 'FlowsaLoader',
        node: yaml.Node
    ) -> str or list:
        if isinstance(node, yaml.SequenceNode):
            paths = loader.construct_sequence(node)
            loader.external_paths_to_search.extend(paths)
            return paths
        elif isinstance(node, yaml.ScalarNode):
            path = loader.construct_scalar(node)
            loader.external_paths_to_search.append(path)
            return path
        else:
            raise TypeError('Cannot tag a mapping node with !external_config')

    @staticmethod
    def from_index(
        loader: 'FlowsaLoader',
        file: str,
        node: yaml.ScalarNode
    ) -> list:
        if not isinstance(node, yaml.ScalarNode):
            raise TypeError('Can only tag a scalar node with !from_index:')
        search_path = loader.external_paths_to_search + input_paths.activity_sets
        file = search_path % file
        if file is None:
            raise FileNotFoundError(f'{file} not found')

        activity_set = loader.construct_scalar(node)

        with open(file, 'r', encoding='utf-8-sig', newline='') as f:
            index = csv.DictReader(f)
            return [
                row['name'] for row in index
                if row['activity_set'] == activity_set
            ]

    @staticmethod
    def script_function(
        loader: 'FlowsaLoader',
        module_name: str,
        node: yaml.ScalarNode
    ) -> Callable:
        if not isinstance(node, yaml.ScalarNode):
            raise TypeError('Can only tag scalar node with !script_function:')

        # For security, this constructor ONLY searches data_source_scripts
        # paths from flowsa.settings.input_paths
        # If someone who understands security concerns better than I do feels
        # it is safe to change this behavior, then go ahead.
        sys.path.extend(str(p) for p in input_paths.data_source_scripts
                        if str(p) not in sys.path)
        module = importlib.import_module(module_name)
        return getattr(module, loader.construct_scalar(node))

    @staticmethod
    def clean_function(
        loader: 'FlowsaLoader',
        module_name: str,
        node: yaml.ScalarNode
    ) -> Callable:
        if not isinstance(node, yaml.ScalarNode):
            raise TypeError('Can only tag scalar node with !clean_function:')

        # For security, this constructor does NOT search external config paths.
        # If someone who understands security concerns better than I do feels
        # it is safe to change this behavior, then go ahead.
        module = importlib.import_module(f'flowsa.{module_name}')
        return getattr(module, loader.construct_scalar(node))


def load(stream: IO, external_path: str = None) -> dict:
    loader = FlowsaLoader(stream)
    if external_path:
        loader.external_paths_to_search.append(external_path)
        loader.external_paths_to_search.append(
            f'{external_path}flowbysectormethods/')
        loader.external_paths_to_search.append(
            path.dirname(external_path))
        loader.external_path_to_pass = external_path
        # TODO: With improved handling of paths in flowsa.settings, this should
        #       posibly be considered unnecessary
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()
