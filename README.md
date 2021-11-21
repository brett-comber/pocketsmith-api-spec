# yak's aftermarket PocketSmith API spec

PocketSmith released an [OpenAPI spec of their public API](https://github.com/pocketsmith/api), but I wanted it to look prettier (and be in YAML format), include `operationId` values for sane method names during API client generation, and correct a few things. So, here we are.

This spec now includes Data Feeds, which are not included in PocketSmith's official spec, yet. Just note that many fields are without descriptions, many enums are likely incomplete, and new fields on existing schemas may be missing.


# Python Client

The spec in this repo is used to generate a Python API client for PocketSmith: [theY4Kman/python-pocketsmith-api](https://github.com/theY4Kman/python-pocketsmith-api)

```shell
pip install pocketsmith-api
```
```python
>>> import pocketsmith
>>> client = pocketsmith.PocketsmithClient('my-api-key')
>>> client.users.get_me()
{'email': 'yak@y4k.dev',
 'id': 1234565,
 'login': 'yamsandwich',
 'name': 'Yam S Andwich',
 'time_zone': 'Eastern Time (US & Canada)',
 # fields omitted for brevity
}
```

If you want real-time events, plus better searching of transactions, a web-based client is also available: [theY4Kman/python-pocketsmith-web-client](https://github.com/theY4Kman/python-pocketsmith-web-client)


# Contributing

If you see anything missing, I'd be happy to do some reverse-engineering and improve the spec. Just open an issue, and I'll see what I can do.

If you want to open a pull request yourself, there's a few things to note.


## Split Spec Format
Due to the sheer size of the full spec, and the sheer inadequacy of PyCharm/IDEA to edit the full spec, I have split it into multiple files.

Schemas live under `spec/schemas`, with their filenames matching their schema names, and must be listed in `spec/schemas/_index.yaml` to be included in the full spec.

Endpoints live under `spec/paths`, in sub-folders matching their API path (with `{var}` transmuted to `_var_`), and each endpoint must be listed in `spec/paths/_index.yaml` to be included in the full spec.

When referencing schemas or endpoints in `spec/schemas/_index.yaml` or `spec/paths/_index.yaml`, always use file references (e.g. `$ref: './MySchema.yaml'`). But when referencing them from other files (e.g. within endpoint operation responses), use JSON Schema references (e.g. `#/components/schemas/MySchema`). This prevents duplication of values in the final bundled spec.

## Bundling the Spec
Unsatisfied with the state of the current Python-based OpenAPI split spec bundlers, I wrote my own. To use it, you'll first need [Poetry](https://python-poetry.org/) to install the dependencies. There are many ways to install it, but the easiest (in my opinion) is
```shell
pip install poetry
# or, if that has permissions issues
pip install --user poetry
```

Then, install dependencies with
```shell
poetry install
```

Finally, bundle the spec with
```shell
python bundle_spec.py
```

This will dereference any file-based `$ref` values, and plonk the bundled spec into `dist/openapi.yaml`.

## Formatting the Spec
In addition to bundling the split spec, some formatting is also applied to the resulting YAML, to make things more human-readable (hopefully). Why a human would want to read it, I'm not sure; but I've been that human before, and the original spec so irked me that I wrote a formatter to place some things in specific order (and put properties into alphabetical order).

To format the spec, first ensure the dependencies have been installed (per the Bundling section), then run:
```shell
python format_spec.py
```

This will format `dist/openapi.yaml` in-place.

## Changelog
Since this manicured spec has now diverged a bit from the official spec, I've started keeping a changelog. When opening a pull request, please include your changes under the `# [Unreleased]` section, categorized into one or more of these subsections:

 - `### Added`
 - `### Changed`
 - `### Fixed`

## Updating Authors
If this is your first time contributing, please add yourself to the `authors` list in `pyproject.toml`! Get some street cred, yo!

## Versioning
At the moment, this manicured spec is all over the place in terms of stability. As such, I hesitate to use version numbers over 1.0.0. However, I instead use [semantic versioning](https://semver.org/) with a leading `0.` — as in `0.MAJOR.MINOR.PATCH`.

Breaking changes should increment `MAJOR`, non-breaking additions should increment `MINOR`, and fixes should increment `PATCH`.

However, please refrain from touching the version numbers in a pull request. This allows me to pull in multiple changes into a single release, and do other maintainery things before releasing.
