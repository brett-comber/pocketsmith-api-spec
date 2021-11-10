from collections import defaultdict
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple, Union
from urllib.parse import urlparse

from ruamel.yaml import RoundTripRepresenter, YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq, CommentedSet

CommentedContainer = Union[CommentedMap, CommentedSeq, CommentedSet]


class NonAliasingRTRepresenter(RoundTripRepresenter):
    def ignore_aliases(self, data):
        return True


yaml = YAML()
yaml.indent(sequence=4, offset=2)

# Disable automatic aliases/anchoring of reused/copied specs
yaml.Representer = NonAliasingRTRepresenter

script_dir = Path(__file__).parent
spec_dir = script_dir / 'spec'
spec_root = spec_dir / '_index.yaml'
out_path = script_dir / 'dist' / 'openapi.yaml'


class MergeQueueItem(NamedTuple):
    node: CommentedContainer
    key: Optional[Union[str, int]]
    parent: Optional[CommentedContainer]
    working_dir: Path


@dataclass
class Reference:
    node: CommentedContainer
    grandparent: CommentedContainer
    parent_key: Union[str, int]
    working_dir: Path
    loc: str = None
    fragment: str = None

    @property
    def is_local(self) -> bool:
        return not self.loc

    @property
    def is_file(self) -> bool:
        return bool(self.loc)

    @cached_property
    def absolute(self) -> Path:
        return (self.working_dir / self.loc).absolute()

    @cached_property
    def fragment_path(self) -> Tuple[str, ...]:
        return tuple(self.fragment.lstrip('/').split('/'))


def merge_spec(root: Union[str, Path]) -> CommentedMap:
    if isinstance(root, str):
        root = Path(root)
    root_spec = load_spec(root)

    unresolved_refs: Dict[Path, List[Reference]] = defaultdict(list)
    resolved_refs: Dict[Tuple[Path, Optional[str]], CommentedContainer] = {}

    queue = [MergeQueueItem(root_spec, None, None, root.parent)]
    while queue:
        item = queue.pop(0)

        if isinstance(item.node, CommentedMap):
            if '$ref' in item.node:
                ref = parse_reference(item.node, item.parent, item.key, item.working_dir)
                if ref.is_file:
                    unresolved_refs[ref.absolute].append(ref)

                    if (ref.absolute, None) not in resolved_refs:
                        ref_spec = load_spec(ref.absolute)
                        resolved_refs[ref.absolute, None] = ref_spec
                        queue.insert(0, MergeQueueItem(ref_spec, None, None, ref.absolute.parent))

            else:
                queue.extend(
                    MergeQueueItem(child, key, item.node, item.working_dir)
                    for key, child in item.node.items()
                )

        elif isinstance(item.node, (CommentedSet, CommentedSeq)):
            queue.extend(
                MergeQueueItem(child, i, item.node, item.working_dir)
                for i, child in enumerate(item.node)
            )

    for path, refs in unresolved_refs.items():
        for ref in refs:
            print('Dereferencing', ref.loc, ref.fragment, 'from', ref.absolute)

            try:
                deref = resolved_refs[ref.absolute, ref.fragment]
            except KeyError:
                deref = resolved_refs[ref.absolute, None]
                if ref.fragment:
                    deref = deref.mlget(ref.fragment_path)
                resolved_refs[ref.absolute, ref.fragment] = deref

            ref.grandparent[ref.parent_key] = deref

    return root_spec


def parse_reference(
    node: CommentedMap, grandparent: CommentedContainer, key: Union[str, int], working_dir: Path
) -> Reference:
    value = node['$ref']
    parsed = urlparse(value)
    return Reference(
        node=node,
        grandparent=grandparent,
        parent_key=key,
        working_dir=working_dir,
        loc=parsed.path,
        fragment=parsed.fragment,
    )


def load_spec(path: Path) -> CommentedMap:
    with path.open() as fp:
        return yaml.load(fp)


def dump_spec(spec: CommentedMap, path: Path) -> None:
    with path.open('w') as fp:
        return yaml.dump(spec, fp)


if __name__ == '__main__':
    bundle = merge_spec(spec_root)
    dump_spec(bundle, out_path)
    # yaml.dump(bundle, sys.stdout)
