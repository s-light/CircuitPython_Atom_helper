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


class CPCopy:
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
        *,  # noqa
        action=ACTION_DEFAULT,
        path_project=".",
        filename=None,
        filename_project=None,
        path_arduino="",
        path_uf2="",
        verbose=0,
        path_target=None
    ):
        """Init."""
        super()

        self.path_script = os.path.dirname(os.path.abspath(__file__))

        self.action = action
        self.path_project = path_project
        self.filename = filename
        self.filename_project = filename_project
        if self.filename_project:
            self.filename = os.path.basename(self.filename_project)
        self.verbose = verbose
        if self.verbose:
            print("verbose level:", self.verbose)
        self.path_target = "/media/$USER/CIRCUITPY/"
        self.path_lib = "lib"
        self.path_arduino = path_arduino
        self.path_uf2 = path_uf2
        if not path_target:
            self.path_target = self.get_UF2_disc()
        else:
            self.path_target = path_target

        # force action for arduino files
        if self.check_for_arduino_file():
            self.action = "COPY_ARDUINO_AS_UF2"
            if self.verbose:
                print("arduino file found! changed action to: '{}'".format(self.action))

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
        if self.verbose and self.verbose >= self.VERBOSE_DEBUG:
            print("ACTIONS['{}']".format(self.action), self.ACTIONS[self.action])
        action_function = self.ACTIONS[self.action]

        if self.verbose and self.verbose >= self.VERBOSE_DEBUG:
            print("action_function", action_function)

        # check for path_target
        if self.path_target:
            self.prepare_paths()
        # elif self.action not "COPY_ARDUINO_AS_UF2":
        else:
            if self.action != "COPY_ARDUINO_AS_UF2":
                raise NotADirectoryError(
                    "no uf2 target disc found. " "is it mounted correctly? "
                )

        # do action
        action_function()  # noqa

        # force sync all things to disk
        if self.verbose:
            print("sync to disk...")
            os.sync()
        print("done.")

    def copy_as_main(self):
        """Copy as 'main.py'."""
        if self.verbose > 1:
            print(self.copy_as_main.__doc__)
        self.copy_w_options(destination_filename="main.py")

    def copy_as_code(self):
        """Copy as 'code.py'."""
        if self.verbose > 1:
            print(self.copy_as_code.__doc__)
        self.copy_w_options(destination_filename="code.py")

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
        filenames = self.arduino_prepare_filenames()
        # if self.verbose > 1:
        #     print("sketch_base_dir", filenames.sketch_base_dir)
        #     print("sketch_filename", filenames.sketch_filename)

        try:
            self.arduino_compile_to_uf2(filenames)
        except ValueError as error:
            print(error)
        else:
            board_found = False
            if not self.path_target:
                if self.verbose:
                    print("*" * 42)
                    print("activate bootloader")
                # we need to activate the bootloader before we can copy!!
                board_found = self.arduino_reset_board()
                if board_found:
                    self.wait_for_new_uf2_disc()
            else:
                board_found = True

            if board_found:
                if self.path_target:
                    self.copy_uf2_file(
                        filenames["sketch_base_dir"],
                        filenames["full_filename_uf2"],
                        filenames["filename_uf2"],
                    )
                else:
                    raise NotADirectoryError(
                        "no uf2 target disc found. "
                        "is the bootloader active? "
                        "is it mounted correctly? "
                    )
            else:
                print("No Board found.")

    ##########################################
    def copy_w_options(
        self, *, destination_filename=None, compile_to_mpy=False, lib=False  # noqa
    ):
        """Copy with options."""
        source = os.path.join(self.path_project, self.filename_project)
        source_abs = os.path.abspath(source)

        if destination_filename:
            destination = os.path.join(self.path_target, destination_filename)
        else:
            if lib:
                destination = os.path.join(
                    self.path_target, self.path_lib, self.filename_project
                )
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
                if self.verbose >= self.VERBOSE_DEBUG:
                    print("details:")
                    print(result_string)
                print("copy file done.")
        return result

    ##########################################

    def check_for_arduino_file(self):
        """Check for Arduino File and search main project file."""
        result = False
        filename = self.filename
        filename_prj = self.filename_project
        if filename and filename_prj:
            if filename.endswith("ino") or filename_prj.endswith("ino"):
                result = True
            elif (filename.endswith("h") or filename_prj.endswith("h")) or (
                filename.endswith("cpp") or filename_prj.endswith("cpp")
            ):
                result = "subfile"
        return result

    def arduino_prepare_filenames(self):
        sketch_base_dir = os.path.dirname(self.filename_project)
        if sketch_base_dir == "":
            sketch_base_dir = "."

        sketch_filename = os.path.basename(self.filename_project)
        print("sketch_filename", sketch_filename)
        if sketch_filename.endswith("h") or sketch_filename.endswith("cpp"):
            print("searching for main arduino sketch entry point...")
            # sketch_filename
            # sketch_base_dir
            head, tail = os.path.split(sketch_base_dir)
            if not tail:
                head, tail = os.path.split(head)
            # hopefully tail now contains the project folder name
            prj_folder_name = tail
            if prj_folder_name:
                sketch_filename = prj_folder_name + ".ino"
            else:
                print("error: not able to find arduino sketch entry point.")
            print(
                "done. we have the main entry point found: '{}'".format(sketch_filename)
            )

        filename_root = os.path.splitext(sketch_filename)[0]
        filename_uf2 = filename_root + ".uf2"
        filename_bin = sketch_filename + ".bin"
        full_filename_bin = os.path.join("build", filename_bin)
        full_filename_uf2 = os.path.join("build", filename_uf2)
        return {
            "sketch_base_dir": sketch_base_dir,
            "sketch_filename": sketch_filename,
            "filename_root": filename_root,
            "filename_uf2": filename_uf2,
            "filename_bin": filename_bin,
            "full_filename_bin": full_filename_bin,
            "full_filename_uf2": full_filename_uf2,
        }

    def arduino_compile_to_uf2(self, filenames):
        """Compile arduino sketch and convert to uf2."""
        with cd(filenames["sketch_base_dir"]):
            if self.verbose:
                print("*" * 42)
                print("compile arduino sketch")
            compile_result = self.compile_arduino_sketch(
                filenames["sketch_filename"], path_arduino=self.path_arduino
            )
            # print(compile_result)
            if compile_result:
                raise ValueError("arduino compilation failed!")

            if self.verbose:
                print("*" * 42)
                print("convert to uf2")
            self.convert_to_uf2(
                filenames["full_filename_bin"],
                filenames["full_filename_uf2"],
                path_uf2=self.path_uf2,
                # base_address defaults to 16Byte bootloader (ItsyBitsy M4)
                base_address="0x4000",
            )

    def compile_arduino_sketch(self, source, path_arduino=""):
        """Compile arduino sketch."""
        script = os.path.join(path_arduino, "arduino")
        script = os.path.expanduser(script)
        script = os.path.expandvars(script)
        command = [
            script,
            "--pref",
            "build.path=build",
            "--verify",
            "--verbose",
            source,
        ]

        result = None
        try:
            # if self.verbose:
            if self.verbose and self.verbose >= self.VERBOSE_DEBUG:
                print("command:{}".format(" ".join(command)))
            print("", flush=True)
            result = subprocess.check_output(command, universal_newlines=True)
        except subprocess.CalledProcessError as error:
            # print("error handling...")
            print("*" * 42)
            print("failed: {}".format(error))
            if self.verbose and self.verbose >= self.VERBOSE_DEBUG:
                print("detailed output")
                print(error.output)
            result = error
            print("*" * 42)
        else:
            if self.verbose:
                if self.verbose == 1:
                    # print 'Sketch uses' line.
                    print(result.splitlines()[-1])
                elif self.verbose >= self.VERBOSE_DEBUG:
                    print("detailed output:")
                    print(result)
                print("compile done.")
            result = None
        return result

    def convert_to_uf2(self, source, destination, path_uf2="", base_address="0x4000"):
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
                if self.verbose >= self.VERBOSE_DEBUG:
                    print("details:")
                    print(result_string)
                print("convert done.")
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

        board_found = False

        # so we need to know on which port to send the reset command.
        # open the port at 1200bps and closing again.
        # and than wait untill we have a new port.
        import serial

        arduino_port = serial.Serial(baudrate=1200)
        try:
            arduino_port.port = "/dev/ttyACM0"
            arduino_port.open()
            arduino_port.setDTR(True)
            time.sleep(0.1)
            arduino_port.setDTR(False)
            board_found = True
        except serial.serialutil.SerialException as e:
            if self.verbose:
                print("SerialException: ", e)
            board_found = False
        finally:
            arduino_port.close()

        return board_found

    def wait_for_new_uf2_disc(self):
        """Wait for new uf2 disc to appear."""
        # check for new disc
        timeout_duration = 10
        timeout_start = time.monotonic()
        wait_flag = True
        while wait_flag:
            if self.path_target:
                wait_flag = False
            if self.verbose and self.verbose > self.VERBOSE_DEBUG:
                print(
                    "\n" "time:",
                    time.monotonic() - timeout_start,
                    "timeout:",
                    timeout_duration,
                )
            if (time.monotonic() - timeout_start) > timeout_duration:
                wait_flag = False
            try:
                time.sleep(1)
                if self.verbose:
                    print(".", end="", flush=True)
            except KeyboardInterrupt as e:
                print()
                print("wait_for_new_uf2_disc stoped by KeyboardInterrupt.", e)
                wait_flag = False

            if wait_flag:
                self.path_target = self.get_UF2_disc()
                if self.verbose and self.verbose > self.VERBOSE_DEBUG:
                    print()
                    print("self.path_target:\n", self.path_target)
        print()

    def copy_uf2_file(self, sketch_base_dir, full_filename_uf2, filename_uf2):
        """Copy uf2 file."""
        if self.verbose:
            print("*" * 42)
            print("copy file")
        source = os.path.join(sketch_base_dir, full_filename_uf2)
        source_abs = os.path.abspath(source)
        destination = os.path.join(self.path_target, filename_uf2)
        destination_abs = os.path.abspath(destination)
        if self.verbose and self.verbose > self.VERBOSE_DEBUG:
            print(source_abs)
            print(destination)
        self.copy_file(source_abs, destination_abs)

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
    """Handle main."""
    print(42 * "*")
    print("Python Version: " + sys.version)
    print(42 * "*")

    print(" ".join(sys.argv))

    filename_default = "./main.py"
    filename_project_default = "./main.py"
    path_project_default = "."
    path_arduino_default = ""
    path_uf2_default = ""

    parser = argparse.ArgumentParser(description=CPCopy.__doc__)

    parser.add_argument(
        "-a",
        "--action",
        help="what action should i take? (defaults to {})"
        "".format(CPCopy.ACTION_DEFAULT),
        default=CPCopy.ACTION_DEFAULT,
        choices=CPCopy.ACTIONS,
    )
    parser.add_argument(
        "-p",
        "--path_project",
        help="specify the location for the current project (defaults to {})"
        "".format(path_project_default),
        default=path_project_default,
    )
    parser.add_argument(
        "-f",
        "--filename",
        help="specify a location for the input file (defaults to {})"
        "".format(filename_default),
        default=filename_default,
    )
    parser.add_argument(
        "-fp",
        "--filename_project",
        help="specify a location for the input file relative to project."
        "(defaults to {})"
        "".format(filename_project_default),
        default=filename_project_default,
    )
    parser.add_argument(
        "-pa",
        "--path_arduino",
        help="specify directory with arduino."
        "(defaults to {})"
        "".format(path_arduino_default),
        default=path_arduino_default,
    )
    parser.add_argument(
        "-pu",
        "--path_uf2",
        help="specify directory with uf2 script."
        "(defaults to {})"
        "".format(path_uf2_default),
        default=path_uf2_default,
    )
    # parser.add_argument(
    #     "-c",
    #     "--compile",
    #     help="compile file to 'mpy'? (defaults to False)",
    #     action='store_true'
    # )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    parser.add_argument("-v", "--verbose", action="count")
    args = parser.parse_args()

    cp_copy = CPCopy(
        action=args.action,
        path_project=args.path_project,
        filename=args.filename,
        filename_project=args.filename_project,
        path_arduino=args.path_arduino,
        path_uf2=args.path_uf2,
        verbose=args.verbose,
    )
    cp_copy.process()


##########################################

if __name__ == "__main__":
    main()
