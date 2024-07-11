import os
import re
import json

def parse_blueprint_file(file_path, verbose=False):
    """Parses a single blueprint file for all module blocks."""
    try:
        if verbose:
            print(f"\n---\nParsing file: {file_path}")
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Regular expression to match all blocks, allowing for spaces and comments
        pattern = re.compile(r'(\w+)\s*\{([^{}]*?(?:\{[^{}]*\}[^{}]*)*?)\}', re.DOTALL)
        matches = pattern.findall(content)
        
        if not matches:
            if verbose:
                print(f"No matches found in file: {file_path}")
        
        configs = []
        for match in matches:
            block_type, block_content = match
            if verbose:
                print(f"\nFound block type: {block_type}")
                print(f"Block content:\n{block_content}\n")
            config = parse_block(block_type, block_content, os.path.dirname(file_path), verbose)
            if config:
                configs.append(config)
                if verbose:
                    print(f"Processed block: {config.get('name', 'unknown')} -> {block_type}\nConfig: {config}\n")
        
        return configs
    except Exception as e:
        if verbose:
            print(f"Error parsing file {file_path}: {e}")
        return []

def parse_block(block_type, block_content, base_path, verbose=False):
    """Parses the content of a generic block."""
    try:
        if verbose:
            print(f"Parsing block type: {block_type}\nContent: {block_content}")
        block_dict = {"type": block_type}
        
        # Extract key-value pairs and lists, allowing for spaces and newlines
        key_value_pattern = re.compile(r'(\w+)\s*:\s*(\[[^\]]*\]|\{[^\}]*\}|"[^"]*"|true|false|\d+)', re.DOTALL)
        matches = key_value_pattern.findall(block_content)
        
        if verbose:
            print(f"Found key-value pairs: {matches}")
        
        for key, value in matches:
            try:
                if verbose:
                    print(f"\nProcessing key: {key}, value: {value}")
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
                    value = True if value == 'true' else False
                else:
                    # Handle numbers
                    value = int(value)
                
                block_dict[key] = value
                if verbose:
                    print(f"Processed key: {key}, value: {value}")
            except Exception as e:
                if verbose:
                    print(f"Error parsing value for key '{key}' in block '{block_type}': {e}")
        
        if "name" in block_dict:
            check_src_files(block_dict, base_path, verbose)
        
        return block_dict
    except Exception as e:
        if verbose:
            print(f"Error parsing block content: {e}")
        return None

def parse_list(value, verbose=False):
    """Parses a list from a string."""
    try:
        if verbose:
            print(f"Parsing list: {value}")
        # Remove comments and extra spaces, then load as JSON
        value = re.sub(r'//.*$', '', value, flags=re.MULTILINE).strip()
        value = re.sub(r',\s*}', '}', value)  # Handle trailing commas
        value = re.sub(r',\s*\]', ']', value)  # Handle trailing commas
        parsed_list = json.loads(value)
        if verbose:
            print(f"Parsed list: {parsed_list}")
        return parsed_list
    except Exception as e:
        if verbose:
            print(f"Error parsing list: {e}")
        return []

def parse_nested_block(nested_block_content, verbose=False):
    """Parses a nested block."""
    nested_block_dict = {}
    try:
        if verbose:
            print(f"Parsing nested block: {nested_block_content}")
        key_value_pattern = re.compile(r'(\w+)\s*:\s*(\[[^\]]*\]|\{[^\}]*\}|"[^"]*"|true|false|\d+)', re.DOTALL)
        matches = key_value_pattern.findall(nested_block_content)
        
        if verbose:
            print(f"Found key-value pairs in nested block: {matches}")
        
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
                value = True if value == 'true' else False
            else:
                # Handle numbers
                value = int(value)
            
            nested_block_dict[key] = value
            if verbose:
                print(f"Processed key in nested block: {key}, value: {value}")
    except Exception as e:
        if verbose:
            print(f"Error parsing nested block content: {e}")
    return nested_block_dict

def check_src_files(block_dict, base_path, verbose=False):
    """Checks if source files listed in the block exist."""
    if verbose:
        print(f"Checking source files for block: {block_dict.get('name', 'unknown')}")
    if 'srcs' in block_dict:
        src_files = block_dict['srcs']
        if isinstance(src_files, str):
            src_files = [src_files]
        for src in src_files:
            src_path = os.path.join(base_path, src)
            if os.path.exists(src_path):
                if verbose:
                    print(f"File exists for {block_dict['type']} '{block_dict['name']}': {src_path}")
            else:
                if verbose:
                    print(f"File does NOT exist for {block_dict['type']} '{block_dict['name']}': {src_path}")

def parse_module_info_file(module_info_path, verbose=False):
    """Reads the MODULE_INFO file and parses each listed blueprint file."""
    if not os.path.exists(module_info_path):
        if verbose:
            print(f"File not found: {module_info_path}")
        return []
    
    try:
        if verbose:
            print(f"\nReading MODULE_INFO file: {module_info_path}")
        with open(module_info_path, 'r') as file:
            bp_paths = file.read().splitlines()
        
        if not bp_paths:
            if verbose:
                print(f"No paths found in MODULE_INFO file: {module_info_path}")
        
        all_configs = []
        for bp_path in bp_paths:
            if os.path.exists(bp_path):
                if verbose:
                    print(f"\nParsing module file: {bp_path}")
                configs = parse_blueprint_file(bp_path, verbose)
                all_configs.extend(configs)
            else:
                if verbose:
                    print(f"File not found: {bp_path}")
        
        return all_configs
    except Exception as e:
        if verbose:
            print(f"Error reading MODULE_INFO file: {e}")
        return []

def main(verbose=False):
    # Path to the MODULE_INFO file
    module_info_path = "out/.module_paths/MODULE_INFO"

    # Parse the MODULE_INFO file
    all_configs = parse_module_info_file(module_info_path, verbose)

    # Print the configurations
    for config in all_configs:
        if verbose:
            print(f"\nFinal configuration: {config}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Blueprint Parser")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    main(verbose=args.verbose)
