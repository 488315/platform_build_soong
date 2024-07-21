# main_build.py
import os
import argparse
from concurrent.futures import ThreadPoolExecutor
from termcolor import colored
from envsetup import target_product_out
from device_info import product_packages, target_arch, target_2nd_arch
from cc_binary_parser import list_available_modules, compile_cc_binaries, find_base_path_and_compile, process_header_libraries
from xml_parser import prebuilt_etc_xml_factory
from blueprint_parser import parse_module_info_file
from defaults_parser import apply_defaults
from meta_lic_gen import generate_meta_lic

def generate_product_packages_file(packages):
    """Generates a product_packages.txt file in the target_out directory."""
    target_out_dir = os.path.join(target_product_out, "product_packages.txt")
    with open(target_out_dir, 'w') as f:
        for package in packages:
            f.write(f"{package}\n")
    print(colored(f"Generated product_packages.txt at {target_out_dir}", 'green'))

def generate_all_modules_file(modules):
    """Generates an all_modules.txt file in the target_out directory."""
    target_out_dir = os.path.join(target_product_out, "all_modules.txt")
    with open(target_out_dir, 'w') as f:
        for module in modules:
            f.write(f"{module}\n")
    print(colored(f"Generated all_modules.txt at {target_out_dir}", 'green'))

def compile_modules_for_packages(packages, verbose=True):
    # Path to the MODULE_INFO file
    module_info_path = "out/.module_paths/MODULE_INFO"

    # Get the list of module_info.bp file paths
    with open(module_info_path, 'r') as file:
        bp_paths = file.read().splitlines()

    # Parse the MODULE_INFO file
    all_configs = parse_module_info_file(module_info_path, verbose)

    # Separate configurations based on the type
    defaults_map = {}
    cc_defaults_map = {}
    cc_library_static_configs = []
    cc_library_shared_configs = []
    cc_library_headers_configs = []
    cc_library_configs = []
    cc_binary_configs = []
    prebuilt_etc_xml_configs = []

    for config in all_configs:
        if config['type'] == 'defaults':
            defaults_map[config['name']] = config
        elif config['type'] == 'cc_defaults':
            cc_defaults_map[config['name']] = config
        elif config['type'] == 'cc_library_static':
            cc_library_static_configs.append(config)
        elif config['type'] == 'cc_library_shared':
            cc_library_shared_configs.append(config)
        elif config['type'] == 'cc_library_headers':
            cc_library_headers_configs.append(config)
        elif config['type'] == 'cc_library':
            cc_library_configs.append(config)
        elif config['type'] == 'cc_binary':
            cc_binary_configs.append(config)
        elif config['type'] == 'prebuilt_etc_xml':
            prebuilt_etc_xml_configs.append(config)

    # Apply defaults to configurations
    all_defaults_map = {**defaults_map, **cc_defaults_map}
    cc_library_static_configs = [apply_defaults(config, all_defaults_map) for config in cc_library_static_configs]
    cc_library_shared_configs = [apply_defaults(config, all_defaults_map) for config in cc_library_shared_configs]
    cc_library_headers_configs = [apply_defaults(config, all_defaults_map) for config in cc_library_headers_configs]
    cc_library_configs = [apply_defaults(config, all_defaults_map) for config in cc_library_configs]
    cc_binary_configs = [apply_defaults(config, all_defaults_map) for config in cc_binary_configs]

    # Process header libraries first and collect include directories
    header_include_dirs = process_header_libraries(cc_library_headers_configs, verbose)

    # Compile static and shared libraries first
    find_base_path_and_compile(cc_library_static_configs, 'static', packages, bp_paths, header_include_dirs, verbose)
    find_base_path_and_compile(cc_library_shared_configs, 'shared', packages, bp_paths, header_include_dirs, verbose)
    find_base_path_and_compile(cc_library_configs, 'library', packages, bp_paths, header_include_dirs, verbose)

    # Compile cc_binary configs with the correct shared and static libraries
    compile_cc_binaries(packages, module_info_path, bp_paths, verbose)

    # Process prebuilt_etc_xml configs
    for config in prebuilt_etc_xml_configs:
        source_file = config.get('srcs', [None])[0]
        schema = config.get('schema', None)
        if source_file:
            prebuilt_etc_xml_factory(source_file, schema)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CC Module Compiler")
    parser.add_argument("--module", type=str, help="Specify a single module to compile")
    parser.add_argument("--get-modules", action="store_true", help="List all available modules")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    if args.get_modules:
        available_modules = list_available_modules(verbose=args.verbose)
        generate_all_modules_file(available_modules)
    elif args.module:
        compile_modules_for_packages([args.module], verbose=args.verbose)
    else:
        compile_modules_for_packages(product_packages, verbose=args.verbose)
        generate_product_packages_file(product_packages)
