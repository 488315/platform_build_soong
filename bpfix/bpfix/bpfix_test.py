import unittest
from unittest.mock import patch, MagicMock
from bpfix import run_bpfix, Fixer, runPatchListMod, parser

def print_list_of_strings(items):
    if len(items) == 0:
        return "[]"
    return f"[\"{'\", \"'.join(items)}\"]"


def build_tree(local_include_dirs, export_include_dirs):
    input_str = f"""cc_library_shared {{
        name: "iAmAModule",
        local_include_dirs: {print_list_of_strings(local_include_dirs)},
        export_include_dirs: {print_list_of_strings(export_include_dirs)},
    }}"""
    tree, errs = parser.parse("<testcase>", input_str)
    if errs:
        raise Exception(f"Failed to parse: {errs}")
    return tree


def impl_filter_list_test(local_include_dirs, export_include_dirs, expected_result):
    tree = build_tree(local_include_dirs, export_include_dirs)
    fixer = Fixer(tree)
    runPatchListMod(simplify_known_properties_duplicating_each_other)(fixer)

    mod = fixer.tree['defs'][0]
    result = mod.get("properties", {}).get("local_include_dirs")

    if expected_result is None:
        assert result is None, "Expected 'local_include_dirs' to be unset, but it was found."
    else:
        assert result == expected_result, f"Expected {expected_result} but got {result}"


class TestBpfix(unittest.TestCase):

    def test_simplify_known_variables_duplicating_each_other(self):
        impl_filter_list_test(["include"], ["include"], None)
        impl_filter_list_test(["include1"], ["include2"], ["include1"])
        impl_filter_list_test(["include1", "include2", "include3", "include4"], ["include2"], ["include1", "include3", "include4"])
        impl_filter_list_test([], ["include"], [])
        impl_filter_list_test([], [], [])

    def check_error(self, in_str, expected_err, inner_test):
        expected = self.pre_process_out_err(expected_err)
        self.run_test_once(in_str, expected, inner_test)

    def run_test_once(self, in_str, expected, inner_test):
        fixer = self.pre_process_in(in_str)
        out, err = self.run_fixer_once(fixer, inner_test)
        if err:
            out = str(err)
        compare_result = self.compare_out_expected(in_str, out, expected)
        if compare_result:
            self.fail(compare_result)

    def pre_process_out_err(self, expected_err):
        return expected_err.strip()

    def pre_process_in(self, in_str):
        in_str, err = self.pre_process_out(in_str)
        if err:
            raise Exception(err)
        tree, errs = parser.parse("<testcase>", in_str)
        if errs:
            raise Exception(f"Parse error: {errs}")
        return Fixer(tree)

    def run_fixer_once(self, fixer, inner_test):
        err = inner_test(fixer)
        if err:
            return "", err
        out, err = parser.print(fixer.tree)
        return out, err

    def compare_out_expected(self, in_str, out, expected):
        if out != expected:
            return f"Output didn't match:\ninput:\n{in_str}\n\nexpected:\n{expected}\ngot:\n{out}\n"
        return None

    def run_pass_once(self, in_str, out_str, inner_test):
        expected, err = self.pre_process_out(out_str)
        if err:
            raise Exception(err)
        self.run_test_once(in_str, expected, inner_test)

    def run_pass(self, in_str, out_str, inner_test):
        expected, err = self.pre_process_out(out_str)
        if err:
            raise Exception(err)
        fixer = self.pre_process_in(in_str)

        got = ""
        prev = "foo"
        passes = 0
        while got != prev and passes < 10:
            out, err = self.run_fixer_once(fixer, inner_test)
            if err:
                raise Exception(err)
            prev = got
            got = out
            passes += 1

        compare_result = self.compare_out_expected(in_str, out, expected)
        if compare_result:
            self.fail(compare_result)

    # Example of a conversion for one of the test cases (TestMergeMatchingProperties in Go)
    def test_merge_matching_properties(self):
        test_cases = [
            {
                "name": "empty",
                "in": """
                    java_library {
                        name: "foo",
                        static_libs: [],
                        static_libs: [],
                    }
                """,
                "out": """
                    java_library {
                        name: "foo",
                        static_libs: [],
                    }
                """
            },
            {
                "name": "single line into multiline",
                "in": """
                    java_library {
                        name: "foo",
                        static_libs: [
                            "a",
                            "b",
                        ],
                        //c1
                        static_libs: ["c" /*c2*/],
                    }
                """,
                "out": """
                    java_library {
                        name: "foo",
                        static_libs: [
                            "a",
                            "b",
                            "c", /*c2*/
                        ],
                        //c1
                    }
                """
            },
        ]
        for case in test_cases:
            with self.subTest(case["name"]):
                self.run_pass(case["in"], case["out"], lambda fixer: runPatchListMod(mergeMatchingModuleProperties)(fixer))

    # Additional tests following the same pattern as above for other test functions

if __name__ == '__main__':
    unittest.main()
