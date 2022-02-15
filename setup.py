from setuptools import setup, find_packages


def _requires_from_file(filename):
    return open(filename).read().splitlines()


setup(
    name="tileget",
    version="0.0.2",
    description="Tile download utility - easily download xyz-tile data",
    author="Kanahiro Iguchi",
    license="MIT",
    url="https://github.com/Kanahiro/tileget",
    packages=find_packages(),
    install_requires=_requires_from_file('requirements.txt'),
    entry_points={
        "console_scripts": [
            "tileget=tileget.__main__:main",
        ]
    }
)
