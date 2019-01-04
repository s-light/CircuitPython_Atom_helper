#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""simple helper script for easier CircuitPython development with Atom."""
##########################################

import sys
import os
import argparse
import subprocess
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
        "COPY_AS_MAIN": None,
        "COPY_AS_CODE": None,
        "COPY": None,
        "COPY_COMPILE": None,
        "LIB": None,
        "LIB_COMPILE": None,
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

        self.ACTIONS["COPY_AS_MAIN"] = self.copy_as_main
        self.ACTIONS["COPY_AS_CODE"] = self.copy_as_main
        self.ACTIONS["COPY"] = self.copy_as_main
        self.ACTIONS["COPY_COMPILE"] = self.copy_as_main
        self.ACTIONS["LIB"] = self.copy_as_main
        self.ACTIONS["LIB_COMPILE"] = self.copy_as_main

    def process(self):
        """Process Files."""
        if self.verbose > 1:
            # print("action", self.action)
            # print("self.ACTIONS[self.action]", self.ACTIONS[self.action])
            print(
                "ACTIONS['{}']".format(self.action),
                self.ACTIONS[self.action])
        action_function = self.ACTIONS[self.action]
        if self.verbose > 1:
            print("action_function", action_function)
        action_function()

    def copy_as_main(self):
        """Copy as 'main.py'."""
        if self.verbose > 1:
            print(self.copy_as_main.__doc__)
        self.copy_w_options(destination_filename='main.py')

    def copy_as_code(self):
        """Copy as 'code.py'."""
        if self.verbose > 1:
            print(self.copy_as_code.__doc__)
        self.copy_w_options(destination_filename='code.py')

    def copy(self):
        """Copy with original filename."""
        if self.verbose > 1:
            print(self.copy.__doc__)
        self.copy_w_options()

    def copy_mpy(self):
        """Copy with original filename and compile to mpy."""
        if self.verbose > 1:
            print(self.copy_mpy.__doc__)
        self.copy_w_options(compile_to_mpy=True)

    def copy_as_lib(self):
        """Copy with original filename."""
        self.copy_w_options()

    def copy_as_lib_mpy(self):
        """Copy with original filename and compile to mpy."""
        self.copy_w_options(compile_to_mpy=True)

    #####################
    def copy_w_options(
            self,
            destination_filename=None,
            compile_to_mpy=False,
            lib=False
    ):
        """Copy with options."""
        #



        pass

    def copy_file(self, source, destination):
        """Copy file."""
        command = [
            "cp",
            "--verbose",
            source,
            destination,
        ]

        result_string = ""
        try:
            print("command:{}".format(" ".join(command)))
            # subprocess.run(command, shell=True)
            subprocess.run(command)
            # result_string += subprocess.check_output(command).decode()
        except subprocess.CalledProcessError as e:
            error_message = "failed: {}".format(e)
            print(error_message)
            result_string += "\n" + error_message
        else:
            if self.verbose:
                print("copy file done.")
        return result_string

##########################################


def main():
    """Main."""
    print(42*'*')
    print('Python Version: ' + sys.version)
    print(42*'*')

    filename_default = "./main.py"
    projectpath_default = "."

    parser = argparse.ArgumentParser(
        description=CPCopy.__doc__
    )

    parser.add_argument(
        "-a",
        "--action",
        help="what action should i take? (defaults to {})"
        "".format(CPCopy.ACTION_DEFAULT),
        default=CPCopy.ACTION_DEFAULT,
        choices=CPCopy.ACTIONS
    )
    parser.add_argument(
        "-p",
        "--projectpath",
        help="specify the location for the current project (defaults to {})"
        "".format(
            projectpath_default
        ),
        default=projectpath_default
    )
    parser.add_argument(
        "-f",
        "--filename",
        help="specify a location for the input file (defaults to {})"
        "".format(
            filename_default
        ),
        default=filename_default
    )
    # parser.add_argument(
    #     "-c",
    #     "--compile",
    #     help="compile file to 'mpy'? (defaults to False)",
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
        filename=args.filename,
        projectpath=args.projectpath,
        action=args.action,
        verbose=args.verbose
    )
    cp_copy.process()


##########################################

if __name__ == '__main__':
    main()
