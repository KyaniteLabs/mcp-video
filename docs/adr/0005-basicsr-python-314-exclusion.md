# BasicSR Python 3.14 Exclusion

`basicsr>=1.4` cannot build from source on Python 3.14 due to Cython compatibility issues. It is excluded via environment marker `python_version < '3.14'` in `pyproject.toml`. The `uv.lock` file cannot be regenerated on Python 3.14; lockfile maintenance must happen on Python 3.12 or 3.13. This is a temporary constraint until `basicsr` publishes a compatible release.
