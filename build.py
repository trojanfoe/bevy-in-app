#!/usr/bin/env python3

"""
Build the game library and copy it into the relevant app build directory.

This script is designed to executed from Xcode or Android Studio.

"""

# Our sister script
from config import *

import os
import shutil
import sys
import traceback


def build(args):
    if "ACTION" in os.environ:
        release = True if os.environ["CONFIGURATION"] == "Release" else False

        platform_name = os.environ["PLATFORM_NAME"]
        if platform_name == "iphoneos":
            build_ios(release)
        elif platform_name == "iphonesimulator":
            build_ios_sim(release)
        else:
            raise RuntimeError(f"Unsupported platform {platform_name}")
    else:
        raise RuntimeError("TODO")


# Build for iOS and copy it into the intermediate build dir
def build_ios(release):
    target = "ios"
    configure(target)
    cmdline = [cargo, "build", "--lib"]
    if release:
        cmdline.append("--release")
    run(f"Build for {target}", cmdline)

    src_path = os.path.join(root_dir, "target", rust_target_map[target], "release" if release else "debug",
                            "libgame.dylib")
    dest_dir = os.path.join(root_dir, "iOS", "libs")
    dest_path = os.path.join(dest_dir, "libgame.dylib")
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    shutil.copyfile(src_path, dest_path)


# Build for iOS Simulator (two architectures) and create a fat binary in the intermediate build dir
def build_ios_sim(release):
    dest_dir = os.path.join(root_dir, "iOS", "libs")
    dest_path = os.path.join(dest_dir, "libgame.dylib")
    lipo_cmdline = ["lipo", "-create", "-output", dest_path]
    for target in ["ios-sim-arm64", "ios-sim-x64"]:
        configure(target)
        cmdline = [cargo, "build", "--lib"]
        if release:
            cmdline.append("--release")
        run(f"Build for {target}", cmdline)

        lipo_cmdline.append(os.path.join(root_dir, "target", rust_target_map[target], "release" if release else "debug",
                                         "libgame.dylib"))

    run("Create fat ios-sim binary", lipo_cmdline)

    # We must fix the install name of the fat binary, in order to avoid confusing copy_dylibs.py
    cmdline = ["install_name_tool", "-id", dest_path, dest_path]
    run("Fix fat ios-sim binary install name", cmdline)


# Build for Android
def build_android(release):
    for target in ["android", "android32"]:
        configure(target)
        cmdline = [cargo, "build", "--lib"]
        if release:
            cmdline.append("--release")
        run(f"Build for target {target}", cmdline)

        src_path = os.path.join("target", rust_target_map[target], "release" if release else "debug",
                                "libgame.so")

        # TBC


if __name__ == "__main__":
    exitcode = 0
    try:
        build(sys.argv)
    except Exception as e:
        print(traceback.format_exc())
        exitcode = 99
    sys.exit(exitcode)
