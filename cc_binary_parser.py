import os
import argparse
from concurrent.futures import ThreadPoolExecutor
from envsetup import target_obj
from termcolor import colored
from blueprint_parser import parse_module_info_file
from cc_library import compile_cc_binary, compile_library
from defaults_parser import apply_defaults

def generate_meta_lic(config, target_product_out, verbose=True):
    """Generates meta_lic file in the target_product_out directory."""
    try:
        meta_lic_dir = os.path.join(target_obj, "HEADER_LIBRARIES", f"{config['name']}_intermediates")
        if not os.path.exists(meta_lic_dir):
            os.makedirs(meta_lic_dir)
        meta_lic_file = os.path.join(meta_lic_dir, "meta_lic")
        with open(meta_lic_file, 'w') as f:
            licenses = config.get('license_kinds', [])
            for license in licenses:
                f.write(f"{license}\n")
            if verbose:
                print(colored(f"Generated meta_lic file at {meta_lic_file}", 'green'))
    except Exception as e:
        print(colored(f"\nError generating meta_lic for {config['name']}: {e}", 'red'))

def main(verbose=True):
    # Path to the MODULE_INFO file
    module_info_path = "out/.module_paths/MODULE_INFO"

    # Parse the MODULE_INFO file
    all_configs = parse_module_info_file(module_info_path, verbose)

    # Separate defaults, cc_binary, cc_library_static, cc_library_shared, cc_library_headers, and cc_defaults blocks
    defaults_map = {}
    cc_defaults_map = {}
    cc_binary_configs = []
    cc_library_static_configs = []
    cc_library_shared_configs = []
    cc_library_headers_configs = []

    for config in all_configs:
        if config['type'] == 'defaults':
            defaults_map[config['name']] = config
        elif config['type'] == 'cc_defaults':
            cc_defaults_map[config['name']] = config
        elif config['type'] == 'cc_binary':
            cc_binary_configs.append(config)
        elif config['type'] == 'cc_library_static':
            cc_library_static_configs.append(config)
        elif config['type'] == 'cc_library_shared':
            cc_library_shared_configs.append(config)
        elif config['type'] == 'cc_library_headers':
            cc_library_headers_configs.append(config)

    # Apply defaults to configurations
    all_defaults_map = {**defaults_map, **cc_defaults_map}
    cc_binary_configs = [apply_defaults(config, all_defaults_map) for config in cc_binary_configs]
    cc_library_static_configs = [apply_defaults(config, all_defaults_map) for config in cc_library_static_configs]
    cc_library_shared_configs = [apply_defaults(config, all_defaults_map) for config in cc_library_shared_configs]
    cc_library_headers_configs = [apply_defaults(config, all_defaults_map) for config in cc_library_headers_configs]

    # Get the list of module_info.bp file paths
    with open(module_info_path, 'r') as file:
        bp_paths = file.read().splitlines()

    header_include_dirs = []

    # Process header libraries first and collect include directories
    for config in cc_library_headers_configs:
        for bp_path in bp_paths:
            base_path = os.path.dirname(bp_path)
            intermediates_dir = os.path.join(base_path, "obj/HEADER_LIBRARIES", f"{config['name']}_intermediates")
            if not os.path.exists(intermediates_dir):
                os.makedirs(intermediates_dir)
            include_dirs = [os.path.join(base_path, inc) for inc in config.get('export_include_dirs', [])]
            header_include_dirs.extend(include_dirs)
            generate_meta_lic(config, intermediates_dir, verbose)

    def find_base_path_and_compile(configs, library_type):
        for config in configs:
            missing_sources = []
            valid_sources = False
            for bp_path in bp_paths:
                base_path = os.path.dirname(bp_path)
                srcs = config.get('srcs', [])
                src = config.get('src', None)
                if src:
                    if isinstance(src, list):
                        srcs.extend(src)
                    else:
                        srcs.append(src)
                src_files_exist = all(os.path.exists(os.path.join(base_path, src)) for src in srcs)
                if src_files_exist:
                    config['base_path'] = base_path
                    valid_sources = True
                    break
                else:
                    for src in srcs:
                        if not os.path.exists(os.path.join(base_path, src)):
                            missing_sources.append(src)

            if valid_sources:
                base_path = config.pop('base_path', None)
                if base_path:
                    compile_library(config, base_path, library_type, header_include_dirs, verbose)
            else:
                print(colored(f"One or more source files for {config['name']} do not exist in any module path:", 'red'))
                for missing_src in missing_sources:
                    print(colored(f"  - {missing_src}", 'red'))

    # Compile static and shared libraries
    find_base_path_and_compile(cc_library_static_configs, 'static')
    find_base_path_and_compile(cc_library_shared_configs, 'shared')

    # Compile cc_binary configs with the correct shared and static libraries
    for config in cc_binary_configs:
        missing_sources = []
        valid_sources = False
        for bp_path in bp_paths:
            base_path = os.path.dirname(bp_path)
            srcs = config.get('srcs', [])
            src = config.get('src', None)
            if src:
                if isinstance(src, list):
                    srcs.extend(src)
                else:
                    srcs.append(src)
            src_files_exist = all(os.path.exists(os.path.join(base_path, src)) for src in srcs)
            if src_files_exist:
                config['base_path'] = base_path
                valid_sources = True
                break
            else:
                for src in srcs:
                    if not os.path.exists(os.path.join(base_path, src)):
                        missing_sources.append(src)

        if valid_sources:
            base_path = config.pop('base_path', None)
            if base_path:
                shared_libs = config.get('shared_libs', [])
                static_libs = config.get('static_libs', [])
                cflags = config.get('cflags', [])
                include_dirs = config.get('export_include_dirs', []) + header_include_dirs
                if verbose:
                    print(colored(f"\nFinal configuration: {config}", 'yellow'))
                compile_cc_binary(config, base_path, shared_libs, static_libs, include_dirs, verbose, cflags)
            else:
                print(colored(f"Base path is missing for configuration: {config['name']}", 'red'))
        else:
            print(colored(f"One or more source files for {config['name']} do not exist in any module path:", 'red'))
            for missing_src in missing_sources:
                print(colored(f"  - {missing_src}", 'red'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CC Binary Parser")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    main(verbose=args.verbose)
