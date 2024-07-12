import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from termcolor import colored
from defaults_parser import apply_defaults
from envsetup import target_obj, clang, clangxx, target_vendor_out_bin, target_system_out_bin, target_recovery_out_usr_bin, target_product_out, build_top

def compile_source_file(src, base_path, intermediates_dir, recovery_available, index, total, cflags, include_dirs, library_type=None, rtti=False, verbose=True):
    """Compiles a single source file into an object file using Clang or Clang++."""
    src_path = os.path.join(base_path, src)
    obj_file = os.path.join(intermediates_dir, f"{os.path.splitext(src)[0]}.o")
    dep_file = os.path.join(intermediates_dir, f"{os.path.splitext(src)[0]}.d")

    # Determine the compiler based on the file extension
    compiler = clangxx if src.endswith(('.cpp', '.cc', '.cxx')) else clang

    compile_cmd = [
        compiler,
        "-c", src_path,
        "-o", obj_file,
        "-MMD", "-MF", dep_file,
        "-fcolor-diagnostics"  # Enable color diagnostics
    ]

    # Add include directories
    for include_dir in include_dirs:
        compile_cmd.extend(["-I", os.path.join(build_top, include_dir)])

    if recovery_available:
        compile_cmd.append("-D__RECOVERY__")

    # Add custom flags if provided
    if cflags:
        compile_cmd.extend(cflags)

    # Add -fPIC for shared libraries
    if library_type == 'shared':
        compile_cmd.append("-fPIC")

    # Add RTTI support if required
    if rtti:
        compile_cmd.append("-frtti")

    # Display the compilation message in the desired format
    clear_line = '\033[K'
    status_line = f"[{index}/{total}] //{os.path.relpath(base_path, start='/run/media/kjones/build/android/minimal_linux')} {compiler} {os.path.basename(src)}{clear_line}\r"
    print(colored(status_line, 'blue'), end='')

    result = subprocess.run(compile_cmd, capture_output=True)
    if result.returncode != 0:
        error_message = result.stderr.decode()
        print(colored(f"\nError compiling {src}: {error_message}", 'red'))
        return False, error_message

    return True, obj_file

def get_library_path(lib_name, lib_type):
    """Generates the correct path for static or shared libraries."""
    if lib_type == 'static':
        lib_path = os.path.join(target_product_out, "obj/STATIC_LIBRARIES", f"{lib_name}_intermediates", f"{lib_name}.a")
    else:
        lib_path = os.path.join(target_product_out, "obj/SHARED_LIBRARIES", f"{lib_name}_intermediates", f"{lib_name}.so")
    return lib_path

def link_executable(name, obj_files, shared_libs, static_libs, output_file, verbose=True):
    """Links object files into an executable using Clang with mold linker."""
    link_cmd = [clangxx, "-fuse-ld=mold", "-o", output_file] + obj_files

    # Add static libraries
    for lib in static_libs:
        lib_path = get_library_path(lib, 'static')
        if os.path.exists(lib_path):
            link_cmd.append(lib_path)
        else:
            print(colored(f"Static library {lib_path} does not exist", 'red'))

    # Add shared libraries
    for lib in shared_libs:
        lib_path = get_library_path(lib, 'shared')
        if os.path.exists(lib_path):
            link_cmd.append(lib_path)
        else:
            print(colored(f"Shared library {lib_path} does not exist", 'red'))

    # Add flag to treat missing symbols as errors
    link_cmd.append("-Wl,--no-undefined")
    link_cmd.append("-Wl,--as-needed")

    if verbose:
        print(colored(f"Linking executable {output_file}", 'yellow'))
    result = subprocess.run(link_cmd, capture_output=True)
    if result.returncode != 0:
        print(colored(f"Error linking executable {name}: {result.stderr.decode()}", 'red'))
        return False

    return True

def compile_cc_binary(config, base_path, shared_libs, static_libs, verbose=True, cflags=None, include_dirs=None):
    """Compiles a cc_binary block into an executable using Clang."""
    try:
        name = config['name']
        srcs = config.get('srcs', [])
        src = config.get('src', None)
        if src:
            if isinstance(src, list):
                srcs.extend(src)
            else:
                srcs.append(src)
        cflags = config.get('cflags', []) if cflags is None else cflags
        recovery_available = config.get('recovery_available', False)
        is_vendor = config.get('vendor', False)
        include_dirs = config.get('export_include_dirs', []) if include_dirs is None else include_dirs
        rtti = config.get('rtti', False)

        # Define the intermediate and output directories
        intermediates_dir = os.path.join(target_obj, "EXECUTABLES", f"{name}_intermediates")
        if recovery_available:
            output_dir = target_recovery_out_usr_bin
        elif is_vendor:
            output_dir = target_vendor_out_bin
        else:
            output_dir = target_system_out_bin
        output_file = os.path.join(output_dir, name)

        os.makedirs(intermediates_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        total_files = len(srcs)
        # Compile each source file using multithreading
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(compile_source_file, src, base_path, intermediates_dir, recovery_available, index + 1, total_files, cflags, include_dirs, verbose, rtti)
                for index, src in enumerate(srcs)
            ]
            results = [future.result() for future in as_completed(futures)]

        # Check for compilation errors
        obj_files = []
        for success, obj_file in results:
            if not success:
                print(colored(f"\nCompilation error: {obj_file}", 'red'))
                return
            obj_files.append(obj_file)

        # Link object files into an executable
        if not link_executable(name, obj_files, shared_libs, static_libs, output_file, verbose):
            print(colored(f"\nFailed to link executable {name}", 'red'))
            return

        print(colored(f"\nSuccessfully created executable {output_file}", 'green'))

    except Exception as e:
        print(colored(f"\nError processing cc_binary {config['name']}: {e}", 'red'))

def compile_library(config, base_path, library_type, verbose=True):
    """Compiles a cc_library_static or cc_library_shared block using Clang."""
    try:
        name = config['name']
        srcs = config.get('srcs', [])
        src = config.get('src', None)
        if src:
            if isinstance(src, list):
                srcs.extend(src)
            else:
                srcs.append(src)
        cflags = config.get('cflags', [])
        include_dirs = config.get('export_include_dirs', [])
        shared_libs = config.get('shared_libs', [])
        static_libs = config.get('static_libs', [])
        rtti = config.get('rtti', False)
        intermediates_dir = os.path.join(target_obj, f"{library_type.upper()}_LIBRARIES", f"{name}_intermediates")

        os.makedirs(intermediates_dir, exist_ok=True)

        total_files = len(srcs)
        # Compile each source file using multithreading
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(compile_source_file, src, base_path, intermediates_dir, False, index + 1, total_files, cflags, include_dirs, library_type, rtti, verbose)
                for index, src in enumerate(srcs)
            ]
            results = [future.result() for future in as_completed(futures)]

        # Check for compilation errors
        obj_files = []
        for success, obj_file in results:
            if not success:
                print(colored(f"\nCompilation error: {obj_file}", 'red'))
                return False
            obj_files.append(obj_file)

        # Archive object files into a static library or link into a shared library
        if library_type == 'static':
            archive_cmd = ["ar", "rcs", os.path.join(intermediates_dir, f"{name}.a")] + obj_files
            if verbose:
                print(colored(f"\nCreating static library {name}", 'yellow'))
            result = subprocess.run(archive_cmd, capture_output=True)
        else:
            link_cmd = [clangxx, "-shared", "-Wl,--no-undefined", "-o", os.path.join(intermediates_dir, f"{name}.so")] + obj_files

            # Add shared libraries specified in the config
            for lib in shared_libs:
                lib_path = get_library_path(lib, 'shared')
                if os.path.exists(lib_path):
                    link_cmd.append(lib_path)
                else:
                    print(colored(f"Shared library {lib_path} does not exist", 'red'))

            # Add static libraries specified in the config
            for lib in static_libs:
                lib_path = get_library_path(lib, 'static')
                if os.path.exists(lib_path):
                    link_cmd.append(lib_path)
                else:
                    print(colored(f"Static library {lib_path} does not exist", 'red'))

            if verbose:
                print(colored(f"\nCreating shared library {name}", 'yellow'))
            result = subprocess.run(link_cmd, capture_output=True)

        if result.returncode != 0:
            print(colored(f"\nError creating library {name}: {result.stderr.decode()}", 'red'))
            return False

        print(colored(f"\nSuccessfully created library {name}", 'green'))
        return True

    except Exception as e:
        print(colored(f"\nError processing {library_type}_library {config['name']}: {e}", 'red'))
        return False

def main(configs, base_path, verbose=True):
    shared_libs = []
    static_libs = []
    binaries = []

    # Separate shared libraries, static libraries, and binaries from configs
    for config in configs:
        if config.get('library_type') == 'shared':
            shared_libs.append(config)
        elif config.get('library_type') == 'static':
            static_libs.append(config)
        else:
            binaries.append(config)

    # Compile shared libraries first
    for config in shared_libs:
        compile_library(config, base_path, 'shared', verbose)

    # Compile static libraries next
    for config in static_libs:
        compile_library(config, base_path, 'static', verbose)

    # Compile binaries last
    for config in binaries:
        compile_cc_binary(config, base_path, shared_libs, static_libs, verbose)
