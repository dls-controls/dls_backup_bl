#!/usr/bin/env python3
# coding: utf8

# a wrapper script to launch dls_backup_bl with correct module name

from dls_backup_bl import BackupBeamline

if __name__ == '__main__':
    BackupBeamline().main()

