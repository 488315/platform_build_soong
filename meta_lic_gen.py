import os
from termcolor import colored

def generate_meta_lic(config, intermediates_dir, verbose=True):
    """Generates meta_lic file in the specified intermediates directory."""
    try:
        meta_lic_file = os.path.join(intermediates_dir, "meta_lic")
        if not os.path.exists(intermediates_dir):
            os.makedirs(intermediates_dir)
        with open(meta_lic_file, 'w') as f:
            f.write(f'package_name:  ""\n')
            f.write(f'module_name:  "{config["name"]}"\n')
            f.write(f'module_types:  "{config["type"]}"\n')
            f.write(f'module_classes:  "UNKNOWN"\n')
            f.write(f'projects:  "{config.get("projects", "unknown")}"\n')
            for license_kind in config.get('license_kinds', []):
                f.write(f'license_kinds:  "{license_kind}"\n')
            for license_condition in config.get('license_conditions', []):
                f.write(f'license_conditions:  "{license_condition}"\n')
            for license_text in config.get('license_texts', []):
                f.write(f'license_texts:  "{license_text}"\n')
            f.write(f'is_container:  false\n')
            f.write(f'built:  "{config.get("built", "unknown")}"\n')
            for source in config.get('sources', []):
                f.write(f'sources:  "{source}"\n')
            for dep in config.get('deps', []):
                f.write('deps:  {\n')
                f.write(f'  file:  "{dep["file"]}"\n')
                for annotation in dep.get('annotations', []):
                    f.write(f'  annotations:  "{annotation}"\n')
                f.write('}\n')
        if verbose:
            print(colored(f"Generated meta_lic file at {meta_lic_file}", 'green'))
    except Exception as e:
        print(colored(f"\nError generating meta_lic for {config['name']}: {e}", 'red'))
