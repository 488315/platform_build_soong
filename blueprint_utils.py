import os
import json
from termcolor import colored
from blueprint_parser import parse_and_eval, Scope, ParseError

def parse_module_info_file(module_info_path, verbose):
    with open(module_info_path, 'r') as file:
        paths = file.read().splitlines()

    all_configs = []

    for path in paths:
        if os.path.exists(path):
            with open(path, 'r') as bp_file:
                content = bp_file.read()
                if verbose:
                    print(colored(f"Parsing file: {path}", 'cyan'))
                try:
                    scope = Scope()
                    config, errs = parse_and_eval(path, content, scope)
                    if errs:
                        print(colored(f"Parsing failed for file {path}: {errs}", 'red'))
                    else:
                        all_configs.append(config)
                except ParseError as e:
                    print(colored(f"Parsing failed for file {path}: {e}", 'red'))

    return {'defs': [definition for config in all_configs for definition in config['defs']]}
