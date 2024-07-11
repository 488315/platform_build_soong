import os
import re
import json
from build_logger import pr_debug, pr_info, pr_warning, pr_error, pr_critical

class BlueprintParseException(Exception):
    pass

def get_error_context(content, pos, context_len=50):
    """Returns a snippet of the context around the error position."""
    start = max(pos - context_len // 2, 0)
    end = min(pos + context_len // 2, len(content))
    return content[start:end]

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
                    pr_info(f"Processed block: {config.get('name', 'unknown')} -> {block_type}, Config: {json.dumps(config)}")
        
        return configs
    except Exception as e:
        pr_error(f"Error parsing file {file_path}: {e}")
        raise

def parse_block(block_type, block_content, base_path, verbose=False):
    """Parses the content of a generic block."""
    try:
        if verbose:
            pr_info(f"Parsing block type: {block_type}")
        block_dict = {"type": block_type}
        
        # Extract key-value pairs and lists, allowing for spaces and newlines
        key_value_pattern = re.compile(r'(\w+)\s*:\s*(\[[^\]]*\]|\{[^\}]*\}|"[^"]*"|true|false|\d+|\w+)', re.DOTALL)
        matches = key_value_pattern.findall(block_content)
        
        if not matches:
            raise BlueprintParseException(f"Invalid block content for block type '{block_type}': {block_content[:50]}...")
        
        if verbose:
            pr_info(f"Found key-value pairs: {matches}")
        
        for key, value in matches:
            try:
                if verbose:
                    pr_debug(f"Processing key: {key}, value: {value}")
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
                elif value.isdigit():
                    # Handle numbers
                    value = int(value)
                
                block_dict[key] = value
                if verbose:
                    pr_debug(f"Processed key: {key}, value: {value}")
            except Exception as e:
                pr_error(f"Error parsing value for key '{key}' in block '{block_type}': {e}")
                raise
        
        if "name" in block_dict:
            check_src_files(block_dict, base_path, verbose)
        
        return block_dict
    except Exception as e:
        pr_error(f"Error parsing block content: {e}")
        raise

def parse_list(value, verbose=False):
    """Parses a list from a string."""
    try:
        if verbose:
            pr_info(f"Parsing list: {value}")
        # Remove comments and extra spaces
        value = re.sub(r'//.*$', '', value, flags=re.MULTILINE).strip()
        value = re.sub(r',\s*}', '}', value)  # Handle trailing commas
        value = re.sub(r',\s*\]', ']', value)  # Handle trailing commas
        
        # Handle variable concatenation
        if '+' in value:
            parts = value.split('+')
            parsed_list = []
            for part in parts:
                part = part.strip()
                if part.startswith('[') and part.endswith(']'):
                    parsed_list.extend(json.loads(part))
                else:
                    parsed_list.append(part)
        else:
            parsed_list = json.loads(value)
        
        if verbose:
            pr_info(f"Parsed list: {parsed_list}")
        return parsed_list
    except json.JSONDecodeError as e:
        error_context = get_error_context(value, e.pos)
        pr_error(f"Error parsing list at line {e.lineno}, column {e.colno}: {e.msg}")
        pr_error(f"Context: {error_context}")
        raise BlueprintParseException(f"Invalid list format: {value}")
    except Exception as e:
        pr_error(f"Error parsing list: {e}")
        raise BlueprintParseException(f"Invalid list format: {value}")

def parse_nested_block(nested_block_content, verbose=False):
    """Parses a nested block."""
    nested_block_dict = {}
    try:
        if verbose:
            pr_info(f"Parsing nested block: {nested_block_content[:50]}...")
        key_value_pattern = re.compile(r'(\w+)\s*:\s*(\[[^\]]*\]|\{[^\}]*\}|"[^"]*"|true|false|\d+|\w+)', re.DOTALL)
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
            elif value.isdigit():
                # Handle numbers
                value = int(value)
            else:
                # Handle variables and single items
                value = value
            
            nested_block_dict[key] = value
            if verbose:
                pr_debug(f"Processed key in nested block: {key}, value: {value}")
    except Exception as e:
        pr_error(f"Error parsing nested block content: {e}")
        raise
    return nested_block_dict

def check_src_files(block_dict, base_path, verbose=False):
    """Checks if source files listed in the block exist."""
    if verbose:
        pr_info(f"Checking source files for block: {block_dict.get('name', 'unknown')}")
    if 'srcs' in block_dict:
        src_files = block_dict['srcs']
        if isinstance(src_files, str):
            src_files = [src_files]
        missing_files = set()
        for src in src_files:
            src_path = os.path.join(base_path, src)
            if not os.path.exists(src_path):
                missing_files.add(src_path)
        for src in missing_files:
            pr_warning(f"Source file does not exist: {src}")

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
            pr_info(f"Final configuration: {json.dumps(config)}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Blueprint Parser")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    main(verbose=args.verbose)
