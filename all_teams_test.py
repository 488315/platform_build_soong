import unittest
import json
import os
from all_teams import AllTeamsSingleton, parse_blueprint_modules  # Import the necessary functions and classes

class TestAllTeams(unittest.TestCase):

    def setUp(self):
        # Setup code to initialize test context and environment
        self.module_info_path = "test_module_info.bp"
        self.create_test_files()

    def tearDown(self):
        # Clean up the test files
        if os.path.exists(self.module_info_path):
            os.remove(self.module_info_path)
        for dirpath, _, filenames in os.walk("test_dir"):
            for f in filenames:
                os.remove(os.path.join(dirpath, f))
        os.rmdir("test_dir")

    def create_test_files(self):
        # Create the necessary test files
        if not os.path.exists("test_dir"):
            os.makedirs("test_dir")
        
        blueprint_content = """
            fake {
                name: "main_test",
                team: "someteam",
            }
            team {
                name: "someteam",
                trendy_team_id: "cool_team",
            }

            team {
                name: "team2",
                trendy_team_id: "22222",
            }

            fake {
                name: "tool",
                team: "team2",
            }

            fake {
                name: "noteam",
            }
        """
        with open(os.path.join("test_dir", "module_info.bp"), "w") as file:
            file.write(blueprint_content)
        
        module_info_content = "test_dir/module_info.bp\n"
        with open(self.module_info_path, "w") as file:
            file.write(module_info_content)

    def test_all_teams(self):
        singleton = AllTeamsSingleton()
        modules = parse_blueprint_modules(self.module_info_path, verbose=False)
        singleton.generate_build_actions(modules)

        with open(singleton.output_path, "r") as file:
            teams = json.load(file)

        actual_teams = {team["target_name"]: team.get("trendy_team_id") for team in teams["teams"]}
        expected_teams = {
            "main_test": "cool_team",
            "tool": "22222",
            "noteam": None,
        }

        self.assertEqual(expected_teams, actual_teams)

    def test_package_lookup(self):
        singleton = AllTeamsSingleton()
        # Create the necessary test files for this test case
        self.create_package_lookup_files()
        modules = parse_blueprint_modules(self.module_info_path, verbose=False)
        singleton.generate_build_actions(modules)

        with open(singleton.output_path, "r") as file:
            teams = json.load(file)

        actual_teams = {team["target_name"]: team.get("trendy_team_id") for team in teams["teams"]}
        expected_teams = {
            "module_with_team1": "111",
            "module2_with_team1": "111",
            "modulepd2": "trendy://team_top",
            "modulepd3": "trendy://team_top",
            "modulepd3b": "111",
            "module_dir1": None,
            "module_dir123": None,
        }

        self.assertEqual(expected_teams, actual_teams)

    def create_package_lookup_files(self):
        if not os.path.exists("package_defaults"):
            os.makedirs("package_defaults/pd2/pd3")
        
        rootBp = """
            team {
                name: "team_top",
                trendy_team_id: "trendy://team_top",
            }
        """
        dir1Bp = """
            fake {
                name: "module_dir1",
            }
        """
        dir3Bp = """
            package {}
            fake {
                name: "module_dir123",
            }
        """
        teamsDirBp = """
            fake {
                name: "module_with_team1",
                team: "team1"
            }
            team {
                name: "team1",
                trendy_team_id: "111",
            }
        """
        teamsDirDeeper = """
            fake {
                name: "module2_with_team1",
                team: "team1"
            }
        """
        packageDefaultsBp = ""
        packageDefaultspd2 = """
            package { default_team: "team_top"}
            fake {
                name: "modulepd2",
            }
        """
        packageDefaultspd3 = """
            fake {
                name: "modulepd3",
            }
            fake {
                name: "modulepd3b",
                team: "team1"
            }
        """

        with open("module_info.bp", "w") as file:
            file.write(rootBp)
        with open("dir1/module_info.bp", "w") as file:
            file.write(dir1Bp)
        if not os.path.exists("dir1/dir2/dir3"):
            os.makedirs("dir1/dir2/dir3")
        with open("dir1/dir2/dir3/module_info.bp", "w") as file:
            file.write(dir3Bp)
        with open("teams_dir/module_info.bp", "w") as file:
            file.write(teamsDirBp)
        if not os.path.exists("teams_dir/deeper"):
            os.makedirs("teams_dir/deeper")
        with open("teams_dir/deeper/module_info.bp", "w") as file:
            file.write(teamsDirDeeper)
        with open("package_defaults/module_info.bp", "w") as file:
            file.write(packageDefaultsBp)
        with open("package_defaults/pd2/module_info.bp", "w") as file:
            file.write(packageDefaultspd2)
        with open("package_defaults/pd2/pd3/module_info.bp", "w") as file:
            file.write(packageDefaultspd3)

if __name__ == "__main__":
    unittest.main()
