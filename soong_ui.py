import os
import shutil
from build_logger import pr_info
from envsetup import build_top
from sandbox_build import *

# Define directories based on the build top directory
build_soong_tools = os.path.join(build_top, "out", "soong", "tools")
module_paths_dir = os.path.join(build_top, "out", ".module_paths")
soong_dir = os.path.join(build_top, "out", "soong")
build_tasks_dir = os.path.join(soong_dir, ".build_tasks")
intermediates_dir = os.path.join(soong_dir, ".intermediates")
soong_tmp_dir = os.path.join(soong_dir, ".temp")

def prepare_directories():
    """
    Create the necessary directories for the build process.

    This function iterates through a list of directories and creates each one if it does not already exist.
    It also logs the creation of each directory with an informational message.
    """
    for directory in [module_paths_dir, soong_dir, build_tasks_dir, intermediates_dir, soong_tmp_dir]:
        os.makedirs(directory, exist_ok=True)
        pr_info(f"Created directory: {directory}", log_tag="DIRECTORY_SETUP")

def find_include_dirs(build_top):
    """
    Find and list all directories containing header files in the build tree.

    Parameters:
    build_top (str): The root directory of the build tree.

    This function performs the following steps:
    1. Traverse the build tree from the root directory.
    2. Identify directories containing header files (.h files).
    3. Write the list of these directories to the 'EXPORT_INCLUDES' file within the '.module_paths' directory.
    4. Log each found directory with an informational message.
    """
    include_dirs = set()
    for root, dirs, files in os.walk(build_top):
        for file in files:
            if file.endswith(".h"):
                include_dirs.add(root)
    
    export_includes_path = os.path.join(module_paths_dir, 'EXPORT_INCLUDES')
    os.makedirs(os.path.dirname(export_includes_path), exist_ok=True)
    
    with open(export_includes_path, 'w') as f:
        for dir in include_dirs:
            pr_info(f"Found include directory: {dir}", log_tag="INCLUDE_DIRS")
            f.write(dir + '\n')

def find_module_info():
    """
    Find and list all 'module_info.bp' files in the build tree.

    This function performs the following steps:
    1. Traverse the build tree from the root directory.
    2. Identify paths containing 'module_info.bp' files.
    3. Write the full paths of these files to the 'MODULE_INFO' file within the '.module_paths' directory.
    4. Log each found module with an informational message.
    """
    pr_info("Finding module information", log_tag="MODULE_INFO")
    module_info_path = os.path.join(module_paths_dir, 'MODULE_INFO')
    os.makedirs(os.path.dirname(module_info_path), exist_ok=True)
    
    with open(module_info_path, 'w') as f:
        for root, dirs, files in os.walk(build_top):
            if 'module_info.bp' in files:
                module_file_path = os.path.join(root, 'module_info.bp')
                f.write(module_file_path + '\n')
                pr_info(f"Found module: {module_file_path}", log_tag="MODULE_INFO")

def soong_main():
    """
    Main function to set up the sandboxed build environment.

    This function performs the following steps:
    1. Set up the temporary directory for the build process.
    2. Create the necessary directories for the build process.
    3. Find and list all directories containing header files in the build tree.
    4. Find and list all 'module_info.bp' files in the build tree.
    5. Log the completion of the sandboxed build environment setup.
    """
    sandbox_setup()
    prepare_directories()
    find_include_dirs(build_top)
    find_module_info()

    pr_info("Sandboxed build environment setup complete", log_tag="SANDBOX_SETUP")

if __name__ == "__main__":
    soong_main()
