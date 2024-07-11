import os
from envsetup import *
from blueprint_parser import *

def process_license_block(block_dict):
    """Processes a license block and generates notice file content."""
    print(f"Processing license block: {block_dict['name']}")
    license_name = block_dict['name']
    license_kinds = block_dict.get('license_kinds', [])
    license_text = block_dict.get('license_text', [])
    
    print(f"License Name: {license_name}")
    print(f"License Kinds: {license_kinds}")
    print(f"License Text: {license_text}")

    # Generate notice file content
    notice_content = f"License Name: {license_name}\n"
    notice_content += f"License Kinds: {', '.join(license_kinds)}\n"
    notice_content += f"License Text:\n"
    for text in license_text:
        notice_content += f"{text}\n"
    
    notice_file_dir = os.path.join(target_obj, "NOTICES")
    notice_file_path = os.path.join(notice_file_dir, f"{license_name}_NOTICE.txt")
    
    # Ensure the directory exists
    os.makedirs(notice_file_dir, exist_ok=True)
    
    # Write the notice file
    with open(notice_file_path, 'w') as notice_file:
        notice_file.write(notice_content)
    
    print(f"Generated notice file: {notice_file_path}")

# Example usage, assuming you have the required functions to parse the MODULE_INFO file:
def main():
    # Path to the MODULE_INFO file
    module_info_path = "out/.module_paths/MODULE_INFO"

    # Parse the MODULE_INFO file
    all_configs = parse_module_info_file(module_info_path)

    # Process the license blocks
    for config in all_configs:
        if config["type"] == "license":
            process_license_block(config)

if __name__ == "__main__":
    main()
