import os
import sys
from ninja_printer import *
from envsetup import build_top
from tqdm import tqdm
from sandbox_build import *

# Define directories based on the build top directory
build_soong_tools = os.path.join(build_top, "out", "soong", "tools")
module_paths_dir = os.path.join(build_top, "out", ".module_paths")
soong_dir = os.path.join(build_top, "out", "soong")
build_tasks_dir = os.path.join(soong_dir, ".build_tasks")
intermediates_dir = os.path.join(soong_dir, ".intermediates")
soong_tmp_dir = os.path.join(soong_dir, ".temp")

def print_newline():
    """Prints a new line."""
    sys.stdout.write("\n")
    sys.stdout.flush()


def prepare_directories(ninja_log):
    """
    Create the necessary directories for the build process.
    """
    for directory in [module_paths_dir, soong_dir, build_tasks_dir, intermediates_dir, soong_tmp_dir]:
        os.makedirs(directory, exist_ok=True)
        ninja_log.display_task("Creating", directory)


def find_include_dirs(build_top, ninja_log):
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
    include_dirs = set()  # Use a set to ensure uniqueness

    # Count the total number of header files (.h) for task tracking
    total = sum([len(files) for r, d, files in os.walk(build_top) if any(file.endswith(".h") for file in files)])

    # Set the total tasks for this function in the log
    ninja_log.total_tasks = total

    # Start tracking tasks
    index = 0
    for root, dirs, files in os.walk(build_top):
        for file in files:
            if file.endswith(".h"):
                include_dirs.add(root)
                index += 1
                ninja_log.display_task("Header Directory", root)  # Display task progress

    export_includes_path = os.path.join(module_paths_dir, 'EXPORT_INCLUDES')
    os.makedirs(os.path.dirname(export_includes_path), exist_ok=True)

    with open(export_includes_path, 'w') as f:
        for dir in sorted(include_dirs):
            ninja_log.display_task("including", dir)
            f.write(dir + '\n')

    print_newline()

    # Reset the task count after completion to avoid affecting future tasks
    ninja_log.current_task = 0
    ninja_log.total_tasks = 0


def find_module_info(ninja_log):
    """
    Find and list all 'module_info.bp' files in the build tree.

    This function performs the following steps:
    1. Traverse the build tree from the root directory.
    2. Identify paths containing 'module_info.bp' files.
    3. Write the full paths of these files to the 'MODULE_INFO' file within the '.module_paths' directory.
    4. Log each found module with an informational message.
    """
    # Count total number of module_info.bp files for progress tracking
    total = sum([len(files) for r, d, files in os.walk(build_top) if 'module_info.bp' in files])

    # Set the total tasks in the ninja log for this function
    ninja_log.total_tasks = total

    # Initialize index for task tracking
    index = 0

    # Display the start of the task
    ninja_log.display_task("Finding", "module_info.bp files")

    # Path where MODULE_INFO will be written
    module_info_path = os.path.join(module_paths_dir, 'MODULE_INFO.list')
    os.makedirs(os.path.dirname(module_info_path), exist_ok=True)

    # Open MODULE_INFO for writing the paths of the found files
    with open(module_info_path, 'w') as f:
        for root, dirs, files in os.walk(build_top):
            if 'module_info.bp' in files:
                # Path of the found module_info.bp file
                module_file_path = os.path.join(root, 'module_info.bp')

                # Write the found file path to MODULE_INFO
                f.write(module_file_path + '\n')

                # Update task progress in ninja log
                ninja_log.display_task("Found module", module_file_path)
                index += 1  # Increment task index for each found file
                ninja_log.display_task("including", root)

    # Print a newline after task completion
    print_newline()

    # Reset the task count after completion to avoid affecting future tasks
    ninja_log.current_task = 0
    ninja_log.total_tasks = 0


def find_owners_files(ninja_log):
    """
    Find and list all 'OWNERS' files in the build tree.
    """
    # Count the total number of OWNERS files for progress tracking
    total = sum([len(files) for r, d, files in os.walk(build_top) if 'OWNERS' in files])

    # Set the total tasks in the ninja log for this function
    ninja_log.total_tasks = total

    # Initialize index for task tracking
    index = 0

    # Display the start of the task
    ninja_log.display_task("Finding", "OWNERS files")

    # Path where OWNERS.list will be written
    owners_list_path = os.path.join(module_paths_dir, 'OWNERS.list')
    os.makedirs(os.path.dirname(owners_list_path), exist_ok=True)

    # Open OWNERS.list for writing the paths of the found files
    with open(owners_list_path, 'w') as f:
        for root, dirs, files in os.walk(build_top):
            if 'OWNERS' in files:
                # Path of the found OWNERS file
                owners_file_path = os.path.join(root, 'OWNERS')

                # Write the found file path to OWNERS.list
                f.write(owners_file_path + '\n')

                # Update task progress in ninja log
                ninja_log.display_task("Found OWNERS file", owners_file_path)
                index += 1  # Increment task index for each found file
                ninja_log.display_task("including", root)

    # Print a newline after task completion
    print_newline()

    # Reset the task count after completion to avoid affecting future tasks
    ninja_log.current_task = 0
    ninja_log.total_tasks = 0


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

    total_tasks = 100  # Estimate the number of tasks for progress tracking (can be adjusted)
    ninja_log = NinjaStyleTqdm(total_tasks)

    prepare_directories(ninja_log)
    find_include_dirs(build_top, ninja_log)
    find_module_info(ninja_log)
    find_owners_files(ninja_log)
    ninja_log.finish()


if __name__ == "__main__":
    soong_main()
