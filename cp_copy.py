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
        "COPY_AS_LIB": None,
        "COPY_AS_LIB_COMPILE": None,
    }

    VERBOSE_DEBUG = 2

    def __init__(
            self,
            *, #noqa
            action=ACTION_DEFAULT,
            path_project=".",
            filename="main.py",
            filename_project="main.py",
            verbose=0,
            path_target=None
    ):
        """Init."""
        super(CPCopy, self).__init__()

        self.action = action
        self.path_project = path_project
        self.filename = filename
        self.filename_project = filename_project
        self.verbose = verbose
        self.path_target = "/media/$USER/CIRCUITPY/"
        if path_target:
            self.path_target = path_target

        # create action ~ function mapping
        self.ACTIONS["COPY_AS_MAIN"] = self.copy_as_main
        self.ACTIONS["COPY_AS_CODE"] = self.copy_as_code
        self.ACTIONS["COPY"] = self.copy
        self.ACTIONS["COPY_COMPILE"] = self.copy_mpy
        self.ACTIONS["COPY_AS_LIB"] = self.copy_as_lib
        self.ACTIONS["COPY_AS_LIB_COMPILE"] = self.copy_as_lib_mpy

        self.prepare_paths()

    ##########################################
    def process(self):
        """Process Files."""
        if self.verbose:
            print("action: '{}'".format(self.action))
        if self.verbose >= self.VERBOSE_DEBUG:
            print(
                "ACTIONS['{}']".format(self.action),
                self.ACTIONS[self.action]
            )
        action_function = self.ACTIONS[self.action]

        if self.verbose >= self.VERBOSE_DEBUG:
            print("action_function", action_function)

        # do action
        action_function() #noqa

        # force sync all things to disk
        if self.verbose:
            print("sync to disk...")
        os.sync()

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
        if self.verbose > 1:
            print(self.copy_as_lib.__doc__)
        self.copy_w_options(lib=True)

    def copy_as_lib_mpy(self):
        """Copy with original filename and compile to mpy."""
        if self.verbose > self.VERBOSE_DEBUG:
            print(self.copy_as_lib_mpy.__doc__)
        self.copy_w_options(lib=True, compile_to_mpy=True)

    ##########################################
    def copy_w_options(
            self,
            *, #noqa
            destination_filename=None,
            compile_to_mpy=False,
            lib=False
    ):
        """Copy with options."""
        #
        source = os.path.join(self.path_project, self.filename)
        source_abs = os.path.abspath(source)

        destination = os.path.join(self.path_target, self.filename)
        destination_abs = os.path.abspath(destination)

        if self.verbose > self.VERBOSE_DEBUG:
            print(source_abs)
        self.copy_file(source_abs, destination_abs)

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
            if self.verbose:
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

    def prepare_paths(self):
        """Prepare all paths."""
        self.path_script = os.path.dirname(os.path.abspath(__file__))
        self.path_target = os.path.expanduser(self.path_target)
        self.path_target = os.path.expandvars(self.path_target)
        if self.verbose:
            print(
                "paths:\n"
                "* path_script: {path_script}\n"
                "* path_target: {path_target}\n"
                "* path_project: {path_project}\n"
                "* filename: {filename}\n"
                "".format(
                    path_script=self.path_script,
                    path_target=self.path_target,
                    filename=self.filename,
                    path_project=self.path_project,
                )
            )
##########################################


def main():
    """Main."""
    print(42*'*')
    print('Python Version: ' + sys.version)
    print(42*'*')

    filename_default = "./main.py"
    path_project_default = "."

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
        "--path_project",
        help="specify the location for the current project (defaults to {})"
        "".format(
            path_project_default
        ),
        default=path_project_default
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
    parser.add_argument(
        "-fp",
        "--filename_project",
        help="specify a location for the input file relative to project."
        "(defaults to {})"
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
        action=args.action,
        path_project=args.path_project,
        filename=args.filename,
        filename_project=args.filename_project,
        verbose=args.verbose
    )
    cp_copy.process()


##########################################

if __name__ == '__main__':
    main()
