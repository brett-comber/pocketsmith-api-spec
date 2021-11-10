import functools
from copy import deepcopy
from io import StringIO
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

from ruamel.yaml import YAML

from bundle_spec import merge_spec

FileStructure = Dict[str, Union[str, 'FileStructure']]


class StringDumpYAML(YAML):
    def dump(self, data, stream=None, **kw):
        return_string = False
        if stream is None:
            return_string = True
            stream = StringIO()
        super().dump(data, stream, **kw)
        if return_string:
            return stream.getvalue()


yaml = StringDumpYAML()


def write_file_structure(path: Path, structure: FileStructure) -> None:
    queue: List[Tuple[Path, FileStructure]] = [(path, structure)]
    while queue:
        path, structure = queue.pop()
        path.mkdir(exist_ok=True)

        for name, value in structure.items():
            child_path = path / name
            if isinstance(value, dict):
                queue.append((child_path, value))
            else:
                child_path.write_text(value)


def extract_ref(spec: dict, path: Union[str, Sequence[str]], ref: str) -> Tuple[dict, dict]:
    """Return a copy of spec with an item replaced by a $ref"""
    if isinstance(path, str):
        path = path.split('.')

    spec = deepcopy(spec)

    ref_parent = functools.reduce(lambda d, key: d[key], path[:-1], spec)
    ref_key = path[-1]

    extracted = ref_parent[ref_key]
    ref_parent[ref_key] = {'$ref': ref}

    return spec, extracted


class DescribeMergeSpec:
    def it_resolves_file_ref_in_same_folder(self, tmp_path):
        bundled = {
            'reference': {
                'stuff': 'things',
            },
        }
        split_index, split_other = extract_ref(bundled, 'reference', 'other.yaml')

        write_file_structure(tmp_path, {
            'index.yaml': yaml.dump(split_index),
            'other.yaml': yaml.dump(split_other),
        })

        expected = bundled
        actual = merge_spec(tmp_path / 'index.yaml')
        assert expected == actual

    def it_resolves_file_ref_in_child_folder(self, tmp_path):
        bundled = {
            'reference': {
                'stuff': 'things',
            },
        }
        split_index, split_other = extract_ref(bundled, 'reference', 'child/other.yaml')

        write_file_structure(tmp_path, {
            'index.yaml': yaml.dump(split_index),
            'child': {
                'other.yaml': yaml.dump(split_other),
            },
        })

        expected = bundled
        actual = merge_spec(tmp_path / 'index.yaml')
        assert expected == actual

    def it_resolves_nested_file_refs_relatively(self, tmp_path):
        bundled = {
            'components': {
                'schemas': {
                    'Account': {
                        'type': 'object',
                        'properties': {
                            'stuff': {'type': 'string', 'example': 'things'},
                        },
                    },
                    'Error': {
                        'type': 'object',
                        'properties': {
                            'error': {'type': 'string', 'example': 'OH NO AN ERROR'},
                        },
                    },
                },
            },
        }
        split_index, split_schemas = extract_ref(
            bundled, 'components.schemas', 'schemas/_index.yaml'
        )
        split_schemas, split_account = extract_ref(split_schemas, 'Account', 'Account.yaml')
        split_schemas, split_error = extract_ref(split_schemas, 'Error', 'Error.yaml')

        write_file_structure(tmp_path, {
            'index.yaml': yaml.dump(split_index),
            'schemas': {
                '_index.yaml': yaml.dump(split_schemas),
                'Account.yaml': yaml.dump(split_account),
                'Error.yaml': yaml.dump(split_error),
            },
        })

        expected = bundled
        actual = merge_spec(tmp_path / 'index.yaml')
        assert expected == actual
