# cc_binary_parser.py
import os
from termcolor import colored
from blueprint_parser import parse_module_info_file
from envsetup import target_obj
from cc_library import compile_cc_binary, compile_library
from defaults_parser import apply_defaults
from meta_lic_gen import generate_meta_lic
from device_info import target_arch, target_2nd_arch

def list_available_modules(verbose=True):
    # Path to the MODULE_INFO file
    module_info_path = "out/.module_paths/MODULE_INFO"

    # Parse the MODULE_INFO file
    all_configs = parse_module_info_file(module_info_path, verbose)

    # Collect available modules
    available_modules = [config['name'] for config in all_configs if config['type'] in {'cc_binary', 'cc_library_static', 'cc_library_shared', 'cc_library_headers', 'cc_library'}]
    
    print("Available modules:")
    for module in available_modules:
        print(module)

    return available_modules

def find_base_path_and_compile(configs, library_type, packages, bp_paths, header_include_dirs, verbose):
    for config in configs:
        if config['name'] not in packages:
            continue
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
            compile_library(config, base_path, library_type, header_include_dirs, verbose)
        else:
            print(colored(f"One or more source files for {config['name']} do not exist in any module path:", 'red'))
            for missing_src in missing_sources:
                print(colored(f"  - {missing_src}", 'red'))

def process_header_libraries(cc_library_headers_configs, verbose=True):
    header_include_dirs = []
    for config in cc_library_headers_configs:
        intermediates_dir = os.path.join(target_obj, "HEADER_LIBRARIES", f"{config['name']}_intermediates")
        include_dirs = [os.path.join(target_obj, inc) for inc in config.get('export_include_dirs', [])]
        header_include_dirs.extend(include_dirs)
        generate_meta_lic(config, intermediates_dir, verbose)
    return header_include_dirs

def compile_cc_binaries(packages, module_info_path, bp_paths, verbose=True):
    # Parse the MODULE_INFO file
    all_configs = parse_module_info_file(module_info_path, verbose)

    # Separate configurations based on the type
    defaults_map = {}
    cc_defaults_map = {}
    cc_binary_configs = []
    cc_library_headers_configs = []

    for config in all_configs:
        if config['type'] == 'defaults':
            defaults_map[config['name']] = config
        elif config['type'] == 'cc_defaults':
            cc_defaults_map[config['name']] = config
        elif config['type'] == 'cc_binary':
            cc_binary_configs.append(config)
        elif config['type'] == 'cc_library_headers':
            cc_library_headers_configs.append(config)

    # Apply defaults to configurations
    all_defaults_map = {**defaults_map, **cc_defaults_map}
    cc_binary_configs = [apply_defaults(config, all_defaults_map) for config in cc_binary_configs]

    # Process header libraries first and collect include directories
    header_include_dirs = process_header_libraries(cc_library_headers_configs, verbose)

    # Compile cc_binary configs with the correct shared and static libraries
    for config in cc_binary_configs:
        if config['name'] not in packages:
            continue
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
            shared_libs = config.get('shared_libs', [])
            static_libs = config.get('static_libs', [])
            cflags = config.get('cflags', [])
            include_dirs = config.get('export_include_dirs', []) + header_include_dirs
            if verbose:
                print(colored(f"\nFinal configuration: {config}", 'yellow'))
            compile_cc_binary(config, base_path, shared_libs, static_libs, include_dirs, verbose, cflags)
        else:
            print(colored(f"One or more source files for {config['name']} do not exist in any module path:", 'red'))
            for missing_src in missing_sources:
                print(colored(f"  - {missing_src}", 'red'))
