#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""simple helper script for easier CircuitPython development with Atom."""
##########################################

import sys
import os
import argparse
# import subprocess
from contextlib import contextmanager


##########################################
# functions

@contextmanager
def cd(newdir):
    """
    Change directory.

    found at:
    http://stackoverflow.com/questions/431684/how-do-i-cd-in-python/24176022#24176022
    """
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


##########################################

class CPCopy(object):
    u"""
    Copy CircuitPython scripts or libraries.

    can copy files as
    - 'main' or 'code' → renames files!
    - as is (preserve script name)
    - libraries (with sub directory preservation)
    """

    ACTION_DEFAULT = "COPY_AS_MAIN"
    ACTIONS = {
        "COPY_AS_MAIN",
        "COPY_AS_CODE",
        "COPY",
        "COPY_COMPILE",
        "LIB",
        "LIB_COMPILE",
    }

    def __init__(
            self,
            # *, #noqa
            action=ACTION_DEFAULT,
            projectpath=".",
            filename="main.py",
            verbose=0
    ):
        """Init."""
        super(CPCopy, self).__init__()

        self.action = action
        self.projectpath = projectpath
        self.filename = filename
        self.verbose = verbose

##########################################


def main(args):
    """Main."""
    print(42*'*')
    print('Python Version: ' + sys.version)
    print(42*'*')

    input_filename_default = "./main.py"
    input_projectpath_default = "."

    parser = argparse.ArgumentParser(
        description="adds watermark to image file."
    )

    parser.add_argument(
        "-a",
        "--action",
        help="what action should i take? (defaults to {})"
        "".format(CPCopy.ACTION_DEFAULT),
        metavar='COMPILE',
        default=CPCopy.ACTION_DEFAULT,
        choices=CPCopy.ACTIONS
    )
    parser.add_argument(
        "-i",
        "--input_projectpath",
        help="specify the location for the current project (defaults to {})"
        "".format(
            input_projectpath_default
        ),
        metavar='INPUT_PROJECTPATH',
        default=input_projectpath_default
    )
    parser.add_argument(
        "-i",
        "--input_filename",
        help="specify a location for the input file (defaults to {})"
        "".format(
            input_filename_default
        ),
        metavar='INPUT_FILENAME',
        default=input_filename_default
    )
    # parser.add_argument(
    #     "-c",
    #     "--compile",
    #     help="compile file to 'mpy'? (defaults to False)",
    #     metavar='COMPILE',
    #     action='store_true'
    # )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='count'
    )
    args = parser.parse_args()

    cp_copy = CPCopy(
        filename=args.input_filename,
        projectpath=args.input_projectpath,
        action=args.action,
        verbose=args.verbose
    )
    cp_copy.process()


##########################################

if __name__ == '__main__':
    main()
