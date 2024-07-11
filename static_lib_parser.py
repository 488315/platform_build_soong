import os
import argparse
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from blueprint_parser import parse_module_info_file, check_src_files

# Importing the necessary environment variables
from envsetup import target_obj, clang

def compile_source_file(src, base_path, intermediates_dir, recovery_available, verbose=True):
    """Compiles a single source file into an object file using Clang."""
    src_path = os.path.join(base_path, src)
    obj_file = os.path.join(intermediates_dir, f"{os.path.splitext(src)[0]}.o")
    dep_file = os.path.join(intermediates_dir, f"{os.path.splitext(src)[0]}.d")
    if verbose:
        print(f"Compiling {src_path} to {obj_file} with Clang")
    
    compile_cmd = [
        clang,
        "-c", src_path,
        "-o", obj_file,
        "-MMD", "-MF", dep_file,
        "-I", base_path  # Assuming includes are relative to base_path
    ]

    if recovery_available:
        compile_cmd.append("-D__RECOVERY__")

    result = subprocess.run(compile_cmd, capture_output=True)
    if result.returncode != 0:
        error_message = result.stderr.decode()
        if verbose:
            print(f"Error compiling {src}: {error_message}")
        return False, error_message
    
    return True, obj_file

def compile_cc_library_static(config, base_path, verbose=True):
    """Compiles a cc_library_static block into a static library using Clang."""
    try:
        name = config['name']
        srcs = config.get('srcs', [])
        recovery_available = config.get('recovery_available', False)

        # Define the intermediate and output directories
        intermediates_dir = os.path.join(target_obj, "STATIC_LIBRARIES", f"{name}_intermediates")
        output_file = os.path.join(intermediates_dir, f"{name}.a")

        if verbose:
            print(f"Creating directory {intermediates_dir} if it does not exist.")
        os.makedirs(intermediates_dir, exist_ok=True)

        # Compile each source file using multithreading
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(compile_source_file, src, base_path, intermediates_dir, recovery_available, verbose)
                for src in srcs
            ]
            results = [future.result() for future in as_completed(futures)]

        # Check for compilation errors
        for success, message in results:
            if not success:
                if verbose:
                    print(f"Compilation error: {message}")
                return

        # Archive the object files into a static library
        obj_files = [result[1] for result in results if result[0]]
        archive_cmd = ["ar", "rcs", output_file] + obj_files

        if verbose:
            print(f"Creating static library {output_file}")
        result = subprocess.run(archive_cmd, capture_output=True)
        if result.returncode != 0:
            if verbose:
                print(f"Error creating static library {name}: {result.stderr.decode()}")
            return

        if verbose:
            print(f"Successfully created static library {output_file}")

    except Exception as e:
        if verbose:
            print(f"Error processing cc_library_static {config['name']}: {e}")

def main(verbose=True):
    # Path to the MODULE_INFO file
    module_info_path = "out/.module_paths/MODULE_INFO"

    # Parse the MODULE_INFO file
    all_configs = parse_module_info_file(module_info_path, verbose)

    # Filter and process only cc_library_static blocks
    cc_library_static_configs = [config for config in all_configs if config['type'] == 'cc_library_static']

    # Get the list of module_info.bp file paths
    with open(module_info_path, 'r') as file:
        bp_paths = file.read().splitlines()

    # Print the configurations and compile them
    for bp_path in bp_paths:
        base_path = os.path.dirname(bp_path)
        if verbose:
            print(f"\nProcessing module file: {bp_path}")

        for config in cc_library_static_configs:
            if 'srcs' not in config:
                if verbose:
                    print(f"Skipping {config['name']} as it does not contain 'srcs'.")
                continue

            # Check if the config's source files exist within the current base path
            src_files_exist = all(os.path.exists(os.path.join(base_path, src)) for src in config['srcs'])
            if src_files_exist:
                compile_cc_library_static(config, base_path, verbose)
            else:
                if verbose:
                    print(f"One or more source files for {config['name']} do not exist in {base_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CC Library Static Parser")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    main(verbose=args.verbose)
