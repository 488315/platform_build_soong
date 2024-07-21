# file : build/soong/xml/xml_parser.py
# description: Parses XML files and validates them against a schema
# copyright: (c) 2024 by 488315
#!/usr/bin/env python3
import os
import subprocess
import json

def run_command(command):
    """Runs a shell command and returns the output."""
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(f"Command failed: {command}\nError: {result.stderr}")
    return result.stdout.strip()

class PrebuiltEtcXml:
    def __init__(self, source_file, schema=None):
        self.source_file = source_file
        self.schema = schema
        self.timestamp_file = f"{source_file}-timestamp"

    def generate_build_actions(self):
        if self.schema:
            if self.schema.endswith(".dtd"):
                self._validate_dtd()
            elif self.schema.endswith(".xsd"):
                self._validate_xsd()
            else:
                raise Exception(f"Unsupported schema extension: {self.schema}")
        else:
            self._validate_minimal()

    def _validate_dtd(self):
        command = f"xmllint --dtdvalid {self.schema} {self.source_file} > /dev/null && touch {self.timestamp_file}"
        run_command(command)

    def _validate_xsd(self):
        command = f"xmllint --schema {self.schema} {self.source_file} > /dev/null && touch {self.timestamp_file}"
        run_command(command)

    def _validate_minimal(self):
        command = f"xmllint {self.source_file} > /dev/null && touch {self.timestamp_file}"
        run_command(command)

def prebuilt_etc_xml_factory(source_file, schema=None):
    module = PrebuiltEtcXml(source_file, schema)
    module.generate_build_actions()
    return module

# Example usage
if __name__ == "__main__":
    source_file = "example.xml"
    schema = "example.xsd"
    module = prebuilt_etc_xml_factory(source_file, schema)
    print(f"Build actions for {source_file} with schema {schema} generated.")
