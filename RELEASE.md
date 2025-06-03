# Release process

1. In `CHANGELOG.md` replace `_Unreleased_` with the release version.
2. In `pyproject.toml` update `version`.
3. Create a release via the GitHub UI.
    -   Set the tag to match the version
    -   Set the title to match the version
    -   Copy the contents of the release changelog to the description field

Publishing the package is handled automatically.
