import os

from setuptools.command.develop import develop
from setuptools_dso import setup

import epicscorelibs.path
import epicscorelibs.version


# Add custom develop to add soft link to epicscorelibs in .
class Develop(develop):
    def install_for_development(self):
        develop.install_for_development(self)
        # Make a link here to epicscorelibs so `pip install -e .` works
        # If we don't do this dbCore can't be found when _extension is
        # built into .
        link = os.path.join(self.egg_path, "epicscorelibs")
        if not os.path.exists(link):
            os.symlink(os.path.join(self.install_dir, "epicscorelibs"), link)


setup(
    cmdclass=dict(develop=Develop),
    install_requires=[
        # Dependency version declared in pyproject.toml
        epicscorelibs.version.abi_requires(),
        "numpy",
        "epicsdbbuilder>=1.4",
    ],
    zip_safe=False,  # setuptools_dso is not compatible with eggs!
)
