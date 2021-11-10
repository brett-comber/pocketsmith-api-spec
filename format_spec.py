import sys
from collections import OrderedDict
from pathlib import Path
from typing import Union

from ruamel.yaml import CommentToken, YAML
from ruamel.yaml.comments import CommentedBase, CommentedMap, CommentedSeq, CommentedSet
from ruamel.yaml.error import CommentMark

yaml = YAML()
yaml.indent(sequence=4, offset=2)


spec_path = Path(__file__).parent / 'dist/openapi.yaml'


def reorder_map(d: OrderedDict, *keys) -> None:
    """Move the specified keys to the top of the dict, in the order passed

    >>> d = OrderedDict({'a': 1, 'b': 2, 'c': 3, 'd': 4})
    >>> d
    OrderedDict([('a', 1), ('b', 2), ('c', 3), ('d', 4)])
    >>> reorder_map(d, 'c', 'd')
    >>> d
    OrderedDict([('c', 3), ('d', 4), ('a', 1), ('b', 2)])
    """
    for key in keys[::-1]:
        if key in d:
            d.move_to_end(key, last=False)


def load_spec() -> CommentedMap:
    with spec_path.open() as fp:
        return yaml.load(fp)


def dump_spec(spec: CommentedMap) -> None:
    with spec_path.open('w') as fp:
        return yaml.dump(spec, fp)


def clear_newlines(o: CommentedBase) -> None:
    r"""Remove any newline comments in the entirety of the mapping

    >>> d = yaml.load('''
    ... # comment
    ... a:
    ...
    ...   b: 2  # stuff!
    ...
    ...
    ... c: 3
    ... ''')
    >>> yaml.dump(d, sys.stdout)
    # comment
    a:
    <BLANKLINE>
      b: 2  # stuff!
    <BLANKLINE>
    <BLANKLINE>
    c: 3
    >>> clear_newlines(d)
    >>> yaml.dump(d, sys.stdout)
    # comment
    a:
      b: 2  # stuff!
    c: 3
    """
    queue = [o]
    while queue:
        o = queue.pop()

        ca = getattr(o, 'ca', None)
        if ca:
            comm_queue = []

            if ca.comment:
                post, pre, *_ = ca.comment

                if isinstance(pre, (list, tuple)):
                    for item in pre:
                        item.value = item.value.lstrip()

                if isinstance(post, (list, tuple)):
                    comm_queue.extend(post)

            if ca.end:
                ca.end = None

            if ca.items:
                comm_queue.extend(ca.items.values())

            while comm_queue:
                item = comm_queue.pop()
                if isinstance(item, CommentToken):
                    item.value = item.value.strip()
                    if not item.value:
                        item.value = ' '
                elif isinstance(item, (list, tuple)):
                    comm_queue.extend(item)

        if isinstance(o, (list, tuple, set)):
            queue.extend(o)
        elif isinstance(o, dict):
            queue.extend(o.values())


def format_doc(d: CommentedMap, schema) -> None:
    clear_newlines(d)
    _format_container(d, schema)


def _format_container(o: Union[CommentedMap, CommentedSeq, CommentedSet], schema) -> None:
    items = schema.get('items', {})
    if not items:
        return

    defaults = items.get('*', {})
    if isinstance(o, (list, tuple, set)):
        if not defaults:
            return
        children = tuple(enumerate(o))
    elif isinstance(o, dict):
        children = tuple(o.items())
        reorder_map(o, *(key for key in items if key != '*'))
    else:
        return

    last_index = len(children) - 1
    for i, (name, child) in enumerate(children):
        is_first = i == 0
        is_last = i == last_index

        item_schema = items.get(name) or {}
        child_schema = {**defaults, **item_schema}
        _format_container(child, child_schema)

        leading = child_schema.get('leading')
        between = child_schema.get('between')

        if leading:
            set_leading_newlines(o, name, leading)
        elif between and not is_first:
            set_leading_newlines(o, name, between)


def set_leading_newlines(d: CommentedMap, key: str, num: int):
    d.ca.items.setdefault(key, [None, [], None, None])

    c = d.ca.items.get(key)
    if c and c[1] is None:
        c[1] = []

    start_mark = CommentMark(0)
    for i in range(num):
        c[1].append(CommentToken('\n', start_mark, None))


def set_trailing_comment(d: CommentedMap, key: str, s: str):
    d.yaml_set_comment_before_after_key(key, after=s)


FIELD_ITEMS = {}
FIELD_ITEMS.update({
    'items': {
        '*': {
            'items': {
                'type': {},
                'format': {},
                'description': {},
                'example': {},
                'enum': {},
                'properties': {
                    'items': {
                        '*': FIELD_ITEMS,
                    },
                },
            },
        },
    },
})


SCHEMA_ITEMS = {
    'type': {},
    'properties': FIELD_ITEMS,
}

SCHEMA_ATTR = {'schema': {'items': SCHEMA_ITEMS}}


OPENAPI_SCHEMA = {
    'items': {
        'openapi': {},
        'info': {
            'leading': 1,
        },
        'servers': {
            'leading': 1,
        },
        'security': {
            'leading': 1,
        },
        'x-samples-languages': {
            'leading': 1,
        },
        'components': {
            'leading': 2,
            'items': {
                'securitySchemes': {
                    'leading': 1,
                    'items': {
                        '*': {
                            'leading': 1,
                            'items': {
                                'type': {},
                                'name': {},
                                'in': {},
                                'description': {},
                                'flows': {},
                            }
                        },
                    },
                },
                'responses': {
                    'leading': 1,
                    'items': {
                        '*': {
                            'between': 1,
                            'items': {
                                'description': {},
                                'content': {},
                            },
                        },
                    },
                },
                'schemas': {
                    'leading': 1,
                    'items': {
                        '*': {
                            'leading': 1,
                            'items': SCHEMA_ITEMS,
                        },
                    },
                },
            }
        },
        'paths': {
            'leading': 2,
            'items': {
                '*': {
                    'leading': 1,
                    'items': {
                        'post': {},
                        'get': {},
                        'put': {},
                        'delete': {},
                        '*': {
                            'between': 1,
                            'items': {
                                'operationId': {},
                                'summary': {},
                                'description': {},
                                'tags': {},
                                'parameters': {
                                    'items': {
                                        '*': {
                                            'items': {
                                                'name': {},
                                                'in': {},
                                                'required': {},
                                                'description': {},
                                                **SCHEMA_ATTR,
                                            },
                                        },
                                    },
                                },
                                'requestBody': {
                                    'items': {
                                        'content': {
                                            'items': {
                                                '*': {
                                                    'items': SCHEMA_ATTR,
                                                }
                                            }
                                        },
                                    },
                                },
                                'responses': {
                                    'items': {
                                        '*': {
                                            'items': {
                                                'description': {},
                                                'content': {},
                                            }
                                        },
                                    },
                                },
                            },
                        },
                    },
                }
            }
        },
    }
}


def format_spec():
    spec = load_spec()
    format_doc(spec, OPENAPI_SCHEMA)
    dump_spec(spec)


if __name__ == '__main__':
    format_spec()
