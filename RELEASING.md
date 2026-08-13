# Releasing

## PyPI setup

The `trueform` distribution name is owned by an unrelated project. This SDK publishes as
`trueform-cloud` and imports as `trueform_cloud`.

Trusted publishing is configured with these values:

- PyPI project name: `trueform-cloud`
- GitHub owner: `True-Form-Cloud`
- GitHub repository: `trueform-python-sdk`
- Workflow filename: `release.yml`
- Environment: `release`

The protected GitHub environment is named `release`. Trusted publishing uses short-lived OIDC
credentials, so the repository does not need a PyPI API token. Recreate the publisher at
[pypi.org/manage/project/trueform-cloud/settings/publishing/](https://pypi.org/manage/project/trueform-cloud/settings/publishing/)
only if this configuration changes.

## Prepare a release

1. Start from a clean `main` branch with passing CI.
2. Update `CHANGELOG.md`.
3. Set `__version__` in `src/trueform_cloud/_version.py`.
4. Run the complete check from `CONTRIBUTING.md`.
5. Merge the version and changelog update into `main`.
6. Create and push a tag that exactly matches `v<package version>`.
7. After PyPI publishing succeeds, create a GitHub Release from the tag using the changelog entry.

Pushing the tag runs the release workflow. It verifies the tag, builds and checks the wheel and
source distribution in an unprivileged job, then publishes those exact artifacts to PyPI from a
separate trusted-publishing job.
