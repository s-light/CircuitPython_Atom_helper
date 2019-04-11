#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""simple helper script for easier CircuitPython development with Atom."""
##########################################

import sys
import os
import time
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
        "COPY_ARDUINO_AS_UF2": None,
    }

    VERBOSE_DEBUG = 2

    def __init__(
            self,
            *, #noqa
            action=ACTION_DEFAULT,
            path_project=".",
            filename="main.py",
            filename_project="main.py",
            path_arduino="",
            path_uf2="",
            verbose=0,
            path_target=None
    ):
        """Init."""
        super(CPCopy, self).__init__()

        self.path_script = os.path.dirname(os.path.abspath(__file__))

        self.action = action
        self.path_project = path_project
        self.filename = filename
        self.filename_project = filename_project
        self.verbose = verbose
        self.path_target = "/media/$USER/CIRCUITPY/"
        self.path_lib = "lib"
        self.path_arduino = path_arduino
        self.path_uf2 = path_uf2
        if not path_target:
            self.path_target = self.get_UF2_disc()
        else:
            self.path_target = path_target

        # force action for arduino files
        if (
                self.filename.endswith('ino') or
                self.filename_project.endswith('ino')
        ):
            self.action = "COPY_ARDUINO_AS_UF2"
            if self.verbose:
                print(
                    "arduino file found! changed action to: '{}'"
                    "".format(self.action)
                )

        # create action ~ function mapping
        self.ACTIONS["COPY_AS_MAIN"] = self.copy_as_main
        self.ACTIONS["COPY_AS_CODE"] = self.copy_as_code
        self.ACTIONS["COPY"] = self.copy
        self.ACTIONS["COPY_COMPILE"] = self.copy_mpy
        self.ACTIONS["COPY_AS_LIB"] = self.copy_as_lib
        self.ACTIONS["COPY_AS_LIB_COMPILE"] = self.copy_as_lib_mpy
        self.ACTIONS["COPY_ARDUINO_AS_UF2"] = self.copy_arduino_as_uf2

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

        # check for path_target
        if self.path_target:
            self.prepare_paths()
        # elif self.action not "COPY_ARDUINO_AS_UF2":
        else:
            if self.action != "COPY_ARDUINO_AS_UF2":
                raise NotADirectoryError(
                    "no uf2 target disc found. "
                    "is it mounted correctly? "
                )

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
        """Copy with original filename to library folder."""
        if self.verbose > 1:
            print(self.copy_as_lib.__doc__)
        self.copy_w_options(lib=True)

    def copy_as_lib_mpy(self):
        """Compile to mpy and copy with original filename to library folder."""
        if self.verbose > self.VERBOSE_DEBUG:
            print(self.copy_as_lib_mpy.__doc__)
        self.copy_w_options(lib=True, compile_to_mpy=True)

    def copy_arduino_as_uf2(self):
        """Compile Arduino Sketch, then convert to uf2 and copy to disc."""
        filename_root = os.path.splitext(self.filename)[0]
        filename_uf2 = filename_root + ".uf2"
        filename_bin = self.filename + ".bin"
        full_filename_bin = os.path.join("build", filename_bin)
        full_filename_uf2 = os.path.join("build", filename_uf2)

        with cd(self.path_project):
            if self.verbose:
                print("*"*42)
                print("combile arduino sketch")
            self.compile_arduino_sketch(
                self.filename_project,
                path_arduino=self.path_arduino
            )
            if self.verbose:
                print("*"*42)
                print("convert to uf2")
            self.convert_to_uf2(
                full_filename_bin,
                full_filename_uf2,
                path_uf2=self.path_uf2,
                # base_address defaults to 16Byte bootloader (ItsyBitsy M4)
                base_address="0x4000"
            )

        if not self.path_target:
            if self.verbose:
                print("*"*42)
                print("activate bootloader")
            # we need to activate the bootloader before we can copy!!
            self.arduino_reset_board()

        # check for new disc
        timeout_duration = 5
        timeout_start = time.monotonic()
        while (
                (not self.path_target) or
                ((time.monotonic() - timeout_start) > timeout_duration)
        ):
            time.sleep(1)
            self.path_target = self.get_UF2_disc()

        if self.path_target:
            if self.verbose:
                print("*"*42)
                print("copy file")
            source = os.path.join(self.path_project, full_filename_uf2)
            source_abs = os.path.abspath(source)
            destination = os.path.join(self.path_target, filename_uf2)
            destination_abs = os.path.abspath(destination)
            if self.verbose > self.VERBOSE_DEBUG:
                print(source_abs)
                print(destination)
            self.copy_file(source_abs, destination_abs)
        else:
            raise NotADirectoryError(
                "no uf2 target disc found. "
                "is the bootloader active? "
                "is it mounted correctly? "
            )

    ##########################################
    def copy_w_options(
            self,
            *, #noqa
            destination_filename=None,
            compile_to_mpy=False,
            lib=False
    ):
        """Copy with options."""
        source = os.path.join(self.path_project, self.filename_project)
        source_abs = os.path.abspath(source)

        if destination_filename:
            destination = os.path.join(self.path_target, destination_filename)
        else:
            if lib:
                destination = os.path.join(
                    self.path_target, self.path_lib, self.filename_project)
            else:
                destination = os.path.join(self.path_target, self.filename)
        destination_abs = os.path.abspath(destination)

        if self.verbose > self.VERBOSE_DEBUG:
            print(source_abs)
            print(destination_abs)
        self.copy_file(source_abs, destination_abs)

    def copy_file(self, source, destination):
        """Copy file."""
        command = [
            "cp",
            "--verbose",
            source,
            destination,
        ]

        result = None
        result_string = ""
        try:
            if self.verbose:
                print("command:{}".format(" ".join(command)))
            # subprocess.run(command, shell=True)
            # subprocess.run(command)
            result = subprocess.check_output(command)
            result_string = result.decode()
        except subprocess.CalledProcessError as e:
            error_message = "failed: {}".format(e)
            print(error_message)
            result_string += "\n" + error_message
        else:
            if self.verbose:
                print("copy file done.")
            elif self.verbose >= self.VERBOSE_DEBUG:
                print("copy file done:\n" + result_string)
        return result

    ##########################################

    def compile_arduino_sketch(self, source, path_arduino=""):
        """Compile arduino sketch."""
        script = os.path.join(path_arduino, "arduino")
        script = os.path.expanduser(script)
        script = os.path.expandvars(script)
        command = [
            script,
            "--verbose",
            "--pref",
            "build.path=build",
            "--verify",
            "--verbose-build",
            source,
        ]

        result = None
        result_string = ""
        try:
            if self.verbose:
                print("command:{}".format(" ".join(command)))
            # subprocess.run(command, shell=True)
            # subprocess.run(command)
            result = subprocess.check_output(command)
            result_string = result.decode()
        except subprocess.CalledProcessError as e:
            error_message = "failed: {}".format(e)
            print(error_message)
            result_string += "\n" + error_message
        else:
            if self.verbose:
                print("compile done.")
            elif self.verbose >= self.VERBOSE_DEBUG:
                print("compile done:\n" + result_string)
        return result

    def convert_to_uf2(
            self, source, destination, path_uf2="", base_address="0x4000"):
        """Convert to uf2."""
        script = os.path.join(path_uf2, "uf2conv.py")
        script = os.path.expanduser(script)
        script = os.path.expandvars(script)
        command = [
            script,
            "--convert",
            # base_address defaults to 16Byte bootloader (ItsyBitsy M4)
            "--base=" + base_address,
            "--output=" + destination,
            source,
        ]

        result = None
        result_string = ""
        try:
            if self.verbose:
                print("command:{}".format(" ".join(command)))
            # subprocess.run(command, shell=True)
            # subprocess.run(command)
            result = subprocess.check_output(command)
            result_string = result.decode()
        except subprocess.CalledProcessError as e:
            error_message = "failed: {}".format(e)
            print(error_message)
            result_string += "\n" + error_message
        else:
            if self.verbose:
                print("compile done.")
            elif self.verbose >= self.VERBOSE_DEBUG:
                print("compile done:\n" + result_string)
        return result

    def arduino_reset_board(self):
        """Enter bootloader mode."""
        # log from Arduino IDE:
        # Forcing reset using 1200bps open/close on port /dev/ttyACM0
        # PORTS {/dev/ttyACM0, /dev/ttyS4, } / {/dev/ttyACM0, /dev/ttyS4, } =>
        #   {}
        # PORTS {/dev/ttyACM0, /dev/ttyS4, } / {/dev/ttyS4, } =>
        #   {}
        # PORTS {/dev/ttyS4, } / {/dev/ttyACM0, /dev/ttyS4, } =>
        #   {/dev/ttyACM0, }
        # Found upload port: /dev/ttyACM0

        # so we need to know on which port to send the reset command.
        # open the port at 1200bps and closing again.
        # and than wait untill we have a new port.
        import serial
        try:
            arduino_port = serial.Serial(
                port="/dev/ttyACM0",
                baudrate=1200)
            arduino_port.setDTR(True)
            time.sleep(0.1)
            arduino_port.setDTR(False)
        finally:
            arduino_port.close()

    ##########################################

    def get_UF2_disc(self):
        """Find first matching UF2 disc."""
        disc_names = [
            "CIRCUITPY",
            "ITSYM4BOOT",
        ]
        disc_found = False
        disc_names_iter = iter(disc_names)
        media_base = os.path.expanduser("/media/$USER/")
        media_base = os.path.expandvars(media_base)
        result_path = None
        try:
            while not disc_found:
                disc_name = disc_names_iter.__next__()
                temp_path = os.path.join(media_base, disc_name)
                temp_path_exists = os.path.exists(temp_path)
                if temp_path_exists:
                    disc_found = True
                    result_path = temp_path
                # if self.verbose:
                #     print(
                #         "paths:\n"
                #         "* disc_name: {disc_name}\n"
                #         "* temp_path: {temp_path}\n"
                #         "* temp_path_exists: {temp_path_exists}\n"
                #         "".format(
                #             disc_name=disc_name,
                #             temp_path=temp_path,
                #             temp_path_exists=temp_path_exists,
                #         )
                #     )
        except StopIteration:
            # nothing found.
            pass

        return result_path

    def prepare_paths(self):
        """Prepare all paths."""
        self.path_target = os.path.expanduser(self.path_target)
        self.path_target = os.path.expandvars(self.path_target)
        if self.verbose:
            print(
                "paths:\n"
                "* path_script: {path_script}\n"
                "* path_target: {path_target}\n"
                "* path_project: {path_project}\n"
                "* filename: {filename}\n"
                "* filename_project: {filename_project}\n"
                "".format(
                    path_script=self.path_script,
                    path_target=self.path_target,
                    filename=self.filename,
                    filename_project=self.filename_project,
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
    path_arduino_default = ""
    path_uf2_default = ""

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
    parser.add_argument(
        "-pa",
        "--path_arduino",
        help="specify directory with arduino."
        "(defaults to {})"
        "".format(
            path_arduino_default
        ),
        default=path_arduino_default
    )
    parser.add_argument(
        "-pu",
        "--path_uf2",
        help="specify directory with uf2 script."
        "(defaults to {})"
        "".format(
            path_uf2_default
        ),
        default=path_uf2_default
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
        path_arduino=args.path_arduino,
        path_uf2=args.path_uf2,
        verbose=args.verbose
    )
    cp_copy.process()


##########################################

if __name__ == '__main__':
    main()
