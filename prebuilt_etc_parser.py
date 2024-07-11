import os
import argparse
import shutil
from blueprint_parser import parse_module_info_file

# Importing the necessary environment variables
from envsetup import target_vendor_out_etc, target_system_out_etc, target_recovery_out_etc, target_ramdisk_out, target_container_out

def apply_defaults(config, defaults_map):
    """Applies defaults to the config based on the defaults_map."""
    if 'defaults' in config:
        defaults_name = config['defaults']
        if defaults_name in defaults_map:
            defaults = defaults_map[defaults_name]
            # Apply each default value if the config doesn't already define it
            for key, value in defaults.items():
                if key not in config:
                    config[key] = value
    return config

def copy_prebuilt_etc_files(config, base_path, verbose=True):
    """Copies prebuilt_etc files to the appropriate output directory."""
    try:
        src_path = os.path.join(base_path, config['src'])
        sub_dir = config.get('sub_dir', '')
        name = config['name']
        is_vendor = config.get('vendor', False)
        is_recovery = config.get('recovery', False)
        is_ramdisk = config.get('ramdisk', False)
        is_container = config.get('container', False)

        if is_vendor:
            dest_dir = os.path.join(target_vendor_out_etc, sub_dir)
        else:
            dest_dir = os.path.join(target_system_out_etc, sub_dir)

        if is_recovery:
            dest_dir = os.path.join(target_recovery_out_etc, sub_dir)
        if is_ramdisk:
            dest_dir = os.path.join(target_ramdisk_out, sub_dir)


        dest_path = os.path.join(dest_dir, name)

        # Create destination directory if it does not exist
        if verbose:
            print(f"Creating directory {dest_dir} if it does not exist.")
        os.makedirs(dest_dir, exist_ok=True)

        # Copy the file
        if verbose:
            print(f"Copying from {src_path} to {dest_path}")
        shutil.copy(src_path, dest_path)
        if verbose:
            print(f"Copied {src_path} to {dest_path}")
    except Exception as e:
        if verbose:
            print(f"Error copying file {config['name']}: {e}")

def main(verbose=True):
    # Path to the MODULE_INFO file
    module_info_path = "out/.module_paths/MODULE_INFO"

    # Parse the MODULE_INFO file
    all_configs = parse_module_info_file(module_info_path, verbose)

    # Separate defaults and prebuilt_etc blocks
    defaults_map = {}
    prebuilt_etc_configs = []

    for config in all_configs:
        if config['type'] == 'defaults':
            defaults_map[config['name']] = config
        elif config['type'] == 'prebuilt_etc':
            prebuilt_etc_configs.append(config)

    # Apply defaults to prebuilt_etc configs
    prebuilt_etc_configs = [apply_defaults(config, defaults_map) for config in prebuilt_etc_configs]

    # Filter out configs with non-existent source files
    valid_prebuilt_etc_configs = []
    for config in prebuilt_etc_configs:
        # Get the list of module_info.bp file paths
        with open(module_info_path, 'r') as file:
            bp_paths = file.read().splitlines()

        valid_sources = False
        for bp_path in bp_paths:
            base_path = os.path.dirname(bp_path)
            src_path = os.path.join(base_path, config.get('src', ''))
            if os.path.exists(src_path):
                config['base_path'] = base_path
                valid_sources = True
                break

        if valid_sources:
            valid_prebuilt_etc_configs.append(config)
        else:
            if verbose:
                print(f"Source file {config.get('src', 'undefined')} does not exist in any module path for config: {config['name']}")

    # Print the configurations and copy them to the output directory
    for config in valid_prebuilt_etc_configs:
        base_path = config.pop('base_path', None)
        if base_path:
            if verbose:
                print(f"\nFinal configuration: {config}")
            copy_prebuilt_etc_files(config, base_path, verbose)
        else:
            if verbose:
                print(f"Base path is missing for configuration: {config['name']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prebuilt ETC Parser")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    main(verbose=args.verbose)
