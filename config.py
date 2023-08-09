#!/usr/bin/env python3

"""
Configure the target architecture of the current build.

In order to build for Android, the location of the NDK must be defined in one of the following
environment variables:

    $NDK_HOME,
    $ANDROID_NDK_HOME,
    $ANDROID_NDK
"""

import os
import platform
import subprocess
import sys
import traceback


# Map "our target" to the Rust target
rust_target_map = {
    "ios": "aarch64-apple-ios",
    "ios-sim-arm64": "aarch64-apple-ios-sim",
    "ios-sim-x64": "x86_64-apple-ios",
    "android": "aarch64-linux-android",
    "android32": "armv7-linux-androideabi",
    "native": None
}

android_api_level = 24


root_dir = os.path.dirname(os.path.realpath(__file__))

# Xcode cannot see our user-local $PATH, so we need the full path
rustup = os.path.join(os.environ["HOME"], ".cargo", "bin", "rustup")
cargo = os.path.join(os.environ["HOME"], ".cargo", "bin", "cargo")


def configure(target):
    if target not in rust_target_map:
        raise RuntimeError(f"Invalid target {target}")

    rust_target = rust_target_map[target]

    setup_rust_toolchain("stable", rust_target)

    envvars = generate_android_envvars(rust_target) if target.startswith("android") else None

    cargo_dir = os.path.join(root_dir, ".cargo")
    config_toml = os.path.join(cargo_dir, "config.toml")
    if rust_target is None:
        # Native target
        os.remove(config_toml)
    else:
        if not os.path.exists(cargo_dir):
            os.makedirs(cargo_dir)
        with open(config_toml, "w") as f:
            f.write('[build]\n')
            f.write(f'target = "{rust_target}"\n')
            f.write('\n')

            if envvars:
                linker = envvars["LINKER"]
                f.write(f'[target.{rust_target}]\n')
                f.write(f'linker = "{linker}"\n')
                f.write('\n')

                f.write('[env]\n')
                for envvar in envvars:
                    if envvar != "LINKER":
                        f.write(f'{envvar} = "{envvars[envvar]}"\n')


def setup_rust_toolchain(rust_toolchain, rust_target):
    run(f"Install rust {rust_toolchain}", [rustup, "install", rust_toolchain])
    if rust_target is not None:
        run(
            "Add rust target",
            [rustup, "target", "add", rust_target, "--toolchain", rust_toolchain],
        )
    run(f"Update rust {rust_toolchain}", [rustup, "update", rust_toolchain])


def generate_android_envvars(rust_target):
    host_os = platform.system().lower()
    dot_cmd = ".cmd" if host_os == "windows" else ""
    dot_exe = ".exe" if host_os == "windows" else ""

    android_ndk_dir = None
    for envvar in ["NDK_HOME", "ANDROID_NDK_HOME", "ANDROID_NDK"]:
        if envvar in os.environ:
            android_ndk_dir = os.environ[envvar]
            break
    if android_ndk_dir is None:
        raise RuntimeError("No Android NDK env-var set!")

    envvars = {"CMAKE_TOOLCHAIN_FILE": find_file(android_ndk_dir, "build", "cmake", "android.toolchain.cmake")}

    # Note on macOS with Apple Silicon the toolchain uses x86_64, at least as of NDK 25.2
    toolchain = find_dir(android_ndk_dir, "toolchains", "llvm", "prebuilt", f"{host_os}-x86_64")

    envvars["SYSROOT"] = find_dir(toolchain, "sysroot")

    bin_dir = find_dir(toolchain, "bin")

    envvars["AR"] = find_file(bin_dir, f"llvm-ar{dot_exe}")
    envvars["AS"] = find_file(bin_dir, f"llvm-as{dot_exe}")
    envvars["CC"] = find_file(bin_dir, f"clang{dot_exe}")
    envvars["CXX"] = find_file(bin_dir, f"clang++{dot_exe}")
    envvars["LD"] = find_file(bin_dir, f"ld{dot_exe}")

    # This is a nice gotcha...
    bin_name_arch = "armv7a-linux-androideabi" if rust_target == "armv7-linux-androideabi" else rust_target
    envvars["LINKER"] = find_file(bin_dir, f"{bin_name_arch}{android_api_level}-clang{dot_cmd}")

    return envvars


def run(purpose, cmdline):
    print_now(f"{purpose}: " + " ".join(cmdline))
    rc = subprocess.call(cmdline)
    if rc != 0:
        raise RuntimeError(f"Failed to {purpose.lower()}")


def find_file(*path_elements):
    candidate = os.path.join(*path_elements)
    if not os.path.exists(candidate):
        raise RuntimeError(f"Cannot find {candidate}")
    if not os.path.isfile(candidate):
        raise RuntimeError(f"Found {candidate} but it's not a file")
    return candidate


def find_dir(*path_elements):
    candidate = os.path.join(*path_elements)
    if not os.path.exists(candidate):
        raise RuntimeError(f"Cannot find {candidate}")
    if not os.path.isdir(candidate):
        raise RuntimeError(f"Found {candidate} but it's not a directory")
    return candidate


def print_now(message):
    print(message)
    sys.stdout.flush()


if __name__ == "__main__":
    exitcode = 0
    try:
        if len(sys.argv) == 2:
            configure(sys.argv[1])
        else:
            print("Usage: config.py target")
            print("Where target is one of:")
            for name in rust_target_map:
                print(f"    {name}")
            exitcode = 1
    except Exception as e:
        print(traceback.format_exc())
        exitcode = 99
    sys.exit(exitcode)
