import os
import json
from blueprint_parser import parse_blueprint_file
from build_logger import pr_info, pr_critical, pr_error, pr_warning
from envsetup import out_dir

# Constants
OWNERSHIP_DIRECTORY = out_dir / "soong" / "ownership"
ALL_TEAMS_FILE = "all_teams.json"

class ModuleTeamInfo:
    def __init__(self, team_name, bp_file):
        self.team_name = team_name
        self.bp_file = bp_file

class AllTeamsSingleton:
    def __init__(self):
        self.output_path = None
        self.teams = {}

    def generate_build_actions(self, modules):
        self.teams = {}

        for module in modules:
            if 'blueprint_file' not in module:
                pr_error(f"Module is missing 'blueprint_file' key: {module}")
                continue

            bp_file = module['blueprint_file']

            if module['type'] == 'team':
                self.teams[module['name']] = module
                continue

        all_teams = self.collect_all_teams()

        os.makedirs(OWNERSHIP_DIRECTORY, exist_ok=True)
        self.output_path = os.path.join(OWNERSHIP_DIRECTORY, ALL_TEAMS_FILE)
        with open(self.output_path, "w") as f:
            json.dump(all_teams, f, indent=4)

    def collect_all_teams(self):
        teams_list = []
        for team_name, team_properties in self.teams.items():
            team_data = {
                "trendy_team_id": team_properties.get('trendy_team_id', ""),
                "name": team_name,
                "path": team_properties.get('blueprint_file', "")
            }
            teams_list.append(team_data)

        return {"teams": teams_list}

def parse_blueprint_modules(module_info_path, verbose=False):
    """Reads the MODULE_INFO file and parses each listed blueprint file."""
    modules = []
    if not os.path.exists(module_info_path):
        pr_critical(f"File not found: {module_info_path}")
        return modules

    try:
        if verbose:
            pr_info(f"Reading MODULE_INFO file: {module_info_path}")
        with open(module_info_path, 'r') as file:
            bp_paths = file.read().splitlines()
        
        if not bp_paths:
            pr_warning(f"No paths found in MODULE_INFO file: {module_info_path}")
            return modules

        for bp_path in bp_paths:
            if os.path.exists(bp_path):
                if verbose:
                    pr_info(f"Parsing module file: {bp_path}")
                configs = parse_blueprint_file(bp_path, verbose)
                for config in configs:
                    config['blueprint_file'] = bp_path
                modules.extend(configs)
            else:
                pr_error(f"File not found: {bp_path}")

    except Exception as e:
        pr_error(f"Error reading MODULE_INFO file: {e}")

    return modules

def main(verbose=False):
    """Main function to parse the MODULE_INFO file and generate all teams JSON."""
    module_info_path = "out/.module_paths/MODULE_INFO"

    # Parse the MODULE_INFO file
    modules = parse_blueprint_modules(module_info_path, verbose)
    if not modules:
        pr_critical("No modules found or parsing failed.")
        return

    singleton = AllTeamsSingleton()
    singleton.generate_build_actions(modules)

    # Output the final path
    if verbose:
        pr_info(f"Generated JSON file at: {singleton.output_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Blueprint Parser")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    main(verbose=args.verbose)
