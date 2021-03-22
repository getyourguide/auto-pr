from setuptools import find_packages, setup
from autopr import __version__


def get_description() -> str:
    with open("README.md") as fh:
        return fh.read()


setup(
    name="auto-pr",
    version=__version__,
    author="GetYourGuide GmbH",
    description="Perform bulk updates across repositories",
    long_description=get_description(),
    long_description_content_type="text/markdown",
    license="Apache License, Version 2.0",
    license_file="LICENSE",
    url="https://github.com/getyourguide/auto-pr",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "marshmallow",
        "marshmallow-dataclass",
        "click",
        "pygithub",
        "pyyaml",
    ],
    dependency_links=[],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "auto-pr = autopr:main",
        ],
    },
)
