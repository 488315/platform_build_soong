# File: blueprint_parser.py
# description: Parses blueprint files and MODULE_INFO file to extract configurations
# copyright: (c) 2024 by 488315
# !/usr/bin/python
import os
import re
import msgspec
from build_logger import pr_debug, pr_info, pr_warning, pr_error, pr_critical


class BlueprintParseException(Exception):
    pass


def parse_blueprint_file(file_path, verbose=False):
    """Parses a single blueprint file for all module blocks."""
    try:
        if verbose:
            pr_info(f"Parsing file: {file_path}")

        with open(file_path, 'r') as file:
            content = file.read()

        # Regular expression to match all blocks, allowing for spaces and comments
        pattern = re.compile(r'(\w+)\s*\{([^{}]*?(?:\{[^{}]*\}[^{}]*)*?)\}', re.DOTALL)
        matches = pattern.findall(content)

        if not matches:
            raise BlueprintParseException(f"No valid blocks found in file: {file_path}")

        configs = []
        for block_type, block_content in matches:
            if verbose:
                pr_info(f"Found block type: {block_type}, Content: {block_content[:50]}...")
            config = parse_block(block_type, block_content, os.path.dirname(file_path), verbose)
            if config:
                configs.append(config)
                if verbose:
                    pr_info(
                        f"Processed block: {config.get('name', 'unknown')} -> {block_type}, Config: {msgspec.json.encode(config).decode()}")

        return configs
    except Exception as e:
        pr_error(f"Error parsing file {file_path}: {e}")
        raise

def parse_block(block_type, block_content, base_path, verbose=False):
    """Parses the content of a generic block."""
    try:
        if verbose:
            pr_info(f"Parsing block type: {block_type}")

        block_dict = initialize_block_dict(block_type, verbose)
        matches = extract_key_value_pairs(block_content, block_type, verbose)

        process_key_value_pairs(matches, block_dict, verbose)

        if "name" in block_dict:
            check_src_files(block_dict, base_path, verbose)

        return block_dict
    except Exception as e:
        pr_error(f"Error parsing block content: {e}")
        raise

def initialize_block_dict(block_type, verbose):
    """Initializes the block dictionary and logs the action if verbose."""
    if verbose:
        pr_info(f"Initializing block dictionary for block type: {block_type}")
    return {"type": block_type}

def extract_key_value_pairs(block_content, block_type, verbose):
    """Extracts key-value pairs from the block content."""
    key_value_pattern = re.compile(r'(\w+)\s*:\s*(\[[^\]]*\]|\{[^\}]*\}|"[^"]*"|true|false|\d+)', re.DOTALL)
    matches = key_value_pattern.findall(block_content)

    if not matches:
        raise BlueprintParseException(
            f"Invalid block content for block type '{block_type}': {block_content[:50]}...")

    if verbose:
        pr_info(f"Found key-value pairs: {matches}")

    return matches

def process_key_value_pairs(matches, block_dict, verbose):
    """Processes key-value pairs and updates the block dictionary."""
    for key, value in matches:
        try:
            if verbose:
                pr_debug(f"Processing key: {key}, value: {value}")

            processed_value = process_value(value, verbose)
            block_dict[key] = processed_value

            if verbose:
                pr_debug(f"Processed key: {key}, value: {processed_value}")
        except Exception as e:
            pr_error(f"Error parsing value for key '{key}' in block '{block_dict['type']}': {e}")
            raise

def process_value(value, verbose):
    """Processes the value based on its type (list, nested block, string, boolean, or number)."""
    if value.startswith('['):
        # Handle lists
        return parse_list(value, verbose)
    elif value.startswith('{'):
        # Handle nested blocks
        return parse_nested_block(value, verbose)
    elif value.startswith('"'):
        # Handle strings
        return value.strip('"')
    elif value in ['true', 'false']:
        # Handle booleans
        return value == 'true'
    else:
        # Handle numbers
        return int(value)


def parse_list(value, verbose=False):
    """Parses a list from a string."""
    try:
        if verbose:
            pr_info(f"Parsing list: {value}")
        # Remove comments and extra spaces, then load as JSON
        value = re.sub(r'//.*$', '', value, flags=re.MULTILINE).strip()
        value = re.sub(r',\s*}', '}', value)  # Handle trailing commas
        value = re.sub(r',\s*\]', ']', value)  # Handle trailing commas
        parsed_list = msgspec.json.decode(value.encode())
        if verbose:
            pr_info(f"Parsed list: {parsed_list}")
        return parsed_list
    except Exception as e:
        pr_error(f"Error parsing list: {e}")
        raise BlueprintParseException(f"Invalid list format: {value}")


def parse_nested_block(nested_block_content, verbose=False):
    """Parses a nested block."""
    nested_block_dict = {}
    try:
        if verbose:
            pr_info(f"Parsing nested block: {nested_block_content[:50]}...")
        key_value_pattern = re.compile(r'(\w+)\s*:\s*(\[[^\]]*\]|\{[^\}]*\}|"[^"]*"|true|false|\d+)', re.DOTALL)
        matches = key_value_pattern.findall(nested_block_content)

        if not matches:
            raise BlueprintParseException(f"Invalid nested block content: {nested_block_content[:50]}...")

        if verbose:
            pr_info(f"Found key-value pairs in nested block: {matches}")

        for key, value in matches:
            if value.startswith('['):
                # Handle lists
                value = parse_list(value, verbose)
            elif value.startswith('{'):
                # Handle nested blocks
                value = parse_nested_block(value, verbose)
            elif value.startswith('"'):
                # Handle strings
                value = value.strip('"')
            elif value in ['true', 'false']:
                # Handle booleans
                value = value == 'true'
            else:
                # Handle numbers
                value = int(value)

            nested_block_dict[key] = value
            if verbose:
                pr_debug(f"Processed key in nested block: {key}, value: {value}")
    except Exception as e:
        pr_error(f"Error parsing nested block content: {e}")
        raise
    return nested_block_dict


import os


def check_src_files(block_dict, base_path, verbose=False):
    """Checks if source files listed in the block exist."""
    if verbose:
        log_block_info(block_dict)

    src_files = get_src_files(block_dict)
    for src in src_files:
        check_file_existence(src, block_dict, base_path, verbose)


def log_block_info(block_dict):
    """Logs information about the block if verbose mode is enabled."""
    pr_info(f"Checking source files for block: {block_dict.get('name', 'unknown')}")


def get_src_files(block_dict):
    """Returns a list of source files from the block dictionary."""
    src_files = block_dict.get('srcs', [])
    if isinstance(src_files, str):
        src_files = [src_files]
    return src_files


def check_file_existence(src, block_dict, base_path, verbose):
    """Checks if a source file exists and logs the result if verbose mode is enabled."""
    src_path = os.path.join(base_path, src)
    if os.path.exists(src_path):
        if verbose:
            pr_debug(f"File exists for {block_dict['type']} '{block_dict['name']}': {src_path}")
    else:
        if verbose:
            pr_warning(f"File does NOT exist for {block_dict['type']} '{block_dict['name']}': {src_path}")


def parse_module_info_file(module_info_path, verbose=False):
    """Reads the MODULE_INFO file and parses each listed blueprint file."""
    if not os.path.exists(module_info_path):
        pr_error(f"File not found: {module_info_path}")
        raise BlueprintParseException(f"File not found: {module_info_path}")

    try:
        if verbose:
            pr_info(f"Reading MODULE_INFO file: {module_info_path}")
        with open(module_info_path, 'r') as file:
            bp_paths = file.read().splitlines()

        if not bp_paths:
            pr_warning(f"No paths found in MODULE_INFO file: {module_info_path}")
            raise BlueprintParseException(f"No paths found in MODULE_INFO file: {module_info_path}")

        all_configs = []
        for bp_path in bp_paths:
            if os.path.exists(bp_path):
                if verbose:
                    pr_info(f"Parsing module file: {bp_path}")
                configs = parse_blueprint_file(bp_path, verbose)
                all_configs.extend(configs)
            else:
                pr_error(f"File not found: {bp_path}")
                raise BlueprintParseException(f"File not found: {bp_path}")

        return all_configs
    except Exception as e:
        pr_error(f"Error reading MODULE_INFO file: {e}")
        raise


def main(verbose=False):
    """Main function to parse the MODULE_INFO file and print configurations."""
    module_info_path = "out/.module_paths/MODULE_INFO"

    # Parse the MODULE_INFO file
    try:
        all_configs = parse_module_info_file(module_info_path, verbose)
    except BlueprintParseException as e:
        pr_critical(f"Parsing failed: {e}")
        return

    # Print the configurations
    for config in all_configs:
        if verbose:
            pr_info(f"Final configuration: {msgspec.json.encode(config).decode()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Blueprint Parser")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    main(verbose=args.verbose)
