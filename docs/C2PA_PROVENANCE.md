# C2PA Provenance Signing

Kinocut can optionally add a C2PA manifest to final MP4 exports on the existing path-based `export` / `video_export` / `Client.export()` flow.

Signing is off by default. Kinocut only reports `c2pa.status == "signed"` after `c2patool` signs the rendered MP4 and a follow-up `c2patool <asset>` verification read succeeds without validation errors. If `c2patool`, the manifest, a signer, or credentials are unavailable, the export does not claim signing.

## Requirements

- `c2patool` installed and executable.
- A C2PA manifest definition JSON compatible with the installed `c2patool`.
- Signing material available to `c2patool`, either in the manifest definition or through an external signer passed with `--c2pa-signer-path`.

Current upstream `c2patool` docs describe adding a manifest with:

```bash
c2patool input.mp4 --manifest manifest.json --output signed.mp4 --force
```

They also state that current signing validates after signing by default. Kinocut still performs a separate verification read before returning a signed status.

## CLI

```bash
kino export input.mp4 \
  --output final.mp4 \
  --format mp4 \
  --c2pa-manifest manifest.json \
  --c2pa-tool /path/to/c2patool \
  --c2pa-signer-path /path/to/signer
```

`--c2pa-tool` is optional when `c2patool` is on `PATH`, or when `KINOCUT_C2PATOOL` / `MCP_VIDEO_C2PATOOL` points to an executable. `--c2pa-signer-path` is optional when the manifest itself contains the signing configuration expected by `c2patool`.

## Python

```python
from kinocut import Client

result = Client().export(
    "input.mp4",
    output="final.mp4",
    format="mp4",
    c2pa_manifest_path="manifest.json",
    c2pa_tool_path="/path/to/c2patool",
    c2pa_signer_path="/path/to/signer",
)

assert result.c2pa["status"] == "signed"
assert result.c2pa["verified"] is True
```

## MCP

`video_export` accepts the same optional fields:

- `c2pa_manifest_path`
- `c2pa_tool_path`
- `c2pa_signer_path`

## Failure Contract

- Default exports remain unsigned and return `c2pa: null`.
- C2PA signing is currently limited to final MP4 exports.
- Missing or non-executable `c2patool` raises `c2patool_not_found`.
- `c2patool` signing failures raise `c2pa_signing_failed` or `c2pa_timeout`.
- Verification output with validation problems raises `c2pa_verification_failed`.

Run the focused fake-provider tests with:

```bash
python3 -m pytest tests/test_c2pa_provenance.py -q
```

The real-tool integration test is skipped unless `c2patool` is installed and `KINOCUT_C2PA_TEST_MANIFEST` points to a usable signing manifest.
