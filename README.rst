dls_backup_bl
===========================

|code_ci| |docs_ci| |coverage| |pypi_version| |license|

A tool for backing up the configuration of the following devices on 
a Beamline:

- Motion Controller
  
  - VME pmacs
  - geobricks
 
- zebras
- Terminal servers

  - ACS
  - Moxa 

============== ==============================================================
Confluence     https://confluence.diamond.ac.uk/x/WoxKBg
PyPI           ``pip install dls_backup_bl``
Source code    https://github.com/dls-controls/dls_backup_bl
Documentation  https://epics-containers.github.io/dls_backup_bl
Releases       https://github.com/dls-controls/dls_backup_bl/releases
============== ==============================================================

How to Use
----------

All examples here use the beamline i16. Substitute i16 with the beamline name you 
are working with.

Run these tools on a beamline workstation or provide the 
beamline name with the command line parameter ``--beamline i16``.

First create a configuration file that describes the devices on the 
beamline. The following command will allow you to view and edit the
list of devices that the backup process will manage::

    dls-backup-gui

This will open a GUI that will allow you to configure the devices.

Once the configuration is complete you can launch the full backup with::

    dls_backup_bl

Note that you can backup a subset of devices like this::

    dls_backup_bl --devices BL16I-MO-STEP-01 BL16I-MO-STEP-02

More Help
---------

Both tools have help which describes the command line options::

    dls-backup-gui --help
    dls_backup_bl --help

This confluence page has much more detailed
https://confluence.diamond.ac.uk/x/WoxKBg

Backup Files
------------

All the backup files are stored in ``/dls_sw/work/motion/Backups/BL16I``

The device description file is 
``/dls_sw/work/motion/Backups/BL16I/BL16I-backup.json``

There are also log files in this directory. Plus a subfolder for each class
of backup device.

The backup folder is a git 
repository and all backups are incremental only. The full history of 
backups can be retrieved with git commands.



.. |code_ci| image:: https://github.com/dls-controls/dls_backup_bl/workflows/Code%20CI/badge.svg?branch=main
    :target: https://github.com/dls-controls/dls_backup_bl/actions?query=workflow%3A%22Code+CI%22
    :alt: Code CI

.. |docs_ci| image:: https://github.com/dls-controls/dls_backup_bl/workflows/Docs%20CI/badge.svg?branch=main
    :target: https://github.com/dls-controls/dls_backup_bl/actions?query=workflow%3A%22Docs+CI%22
    :alt: Docs CI

.. |coverage| image:: https://codecov.io/gh/dls-controls/dls_backup_bl/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/dls-controls/dls_backup_bl
    :alt: Test Coverage

.. |pypi_version| image:: https://img.shields.io/pypi/v/dls_backup_bl.svg
    :target: https://pypi.org/project/dls_backup_bl
    :alt: Latest PyPI version

.. |license| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :target: https://opensource.org/licenses/Apache-2.0
    :alt: Apache License

..
    Anything below this line is used when viewing README.rst and will be replaced
    when included in index.rst

See https://epics-containers.github.io/dls_backup_bl for more detailed documentation.
