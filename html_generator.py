def generate_html(configs, output_file):
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Module Information</title>
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid black;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <h1>Module Information</h1>
    <table>
        <tr>
            <th>Type</th>
            <th>Module Type</th>
            <th>Properties</th>
        </tr>
"""

    for config in configs:
        for definition in config['defs']:
            module_type = definition['module_type'] if 'module_type' in definition else 'N/A'
            properties = definition['properties'] if 'properties' in definition else []
            properties_str = ', '.join([f"{prop['name']}: {prop['value']}" for prop in properties])
            html_content += f"""
        <tr>
            <td>{definition['type']}</td>
            <td>{module_type}</td>
            <td>{properties_str}</td>
        </tr>
"""

    html_content += """
    </table>
</body>
</html>
"""

    with open(output_file, 'w') as file:
        file.write(html_content)
