def apply_defaults(config, defaults_map):
    """Applies defaults to the config based on the defaults_map."""
    if 'defaults' in config:
        defaults_names = config['defaults']
        if isinstance(defaults_names, list):
            for defaults_name in defaults_names:
                if defaults_name in defaults_map:
                    defaults = defaults_map[defaults_name]
                    # Apply each default value if the config doesn't already define it
                    for key, value in defaults.items():
                        if key not in config:
                            config[key] = value
                        elif isinstance(config[key], list) and isinstance(value, list):
                            config[key] = value + config[key]
        elif isinstance(defaults_names, str) and defaults_names in defaults_map:
            defaults = defaults_map[defaults_names]
            # Apply each default value if the config doesn't already define it
            for key, value in defaults.items():
                if key not in config:
                    config[key] = value
                elif isinstance(config[key], list) and isinstance(value, list):
                    config[key] = value + config[key]
        else:
            print(f"Warning: 'defaults' is neither a list nor a string in config: {config}")
    return config
