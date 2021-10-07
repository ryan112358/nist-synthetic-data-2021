"""
This script can be used to run a JSON validator on a generated
schema file or column_datatypes file. This can be useful if the
files have been hand-modified after generating, as it will confirm
that the files are in the same format that is expected.

The JSON schemae for these two files are located in the json_schemae directory.
These schemae can also be used by a consumer to validate schemae when they
are read in, if desired.

  Typical usage example:

  python validate.py -p parameters.json
"""

import logging
import os
import argparse
import pathlib
import json
import sys
from jsonschema import validate

# These are the two schema files
PARAMETERS_SCHEMA = pathlib.Path(__file__).parent.joinpath(
    "json_schemae/parameters.json.schema"
)
DATATYPES_SCHEMA = pathlib.Path(__file__).parent.joinpath(
    "json_schemae/column_datatypes.json.schema"
)

def validate_schema(input_file, is_parameters):
  json_schema = None
  schema_file = None
  # Read in the schema for the appropriate filetype
  if is_parameters:
    schema_file = PARAMETERS_SCHEMA
  else:
    # argparse will take care of making sure one and only one
    # of the two options is specified, so we can assume that
    # any "else" is for the datatypes schema
    schema_file = DATATYPES_SCHEMA

  # load in the schema and the file to validate
  with open(schema_file, encoding="utf-8") as f:
    json_schema = json.load(f)

  with open(input_file, encoding="utf-8") as f:
    file_to_validate = json.load(f)

  validate(instance=file_to_validate, schema=json_schema)

if __name__ == "__main__":
  # validate.py executed as script

  # Configure the logger to output everything; logs will
  # go to stderr by default
  logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

  # Whether we're parsing a parameters.json file or a kwargs / datatype file;
  # if this is true, it's parameters; if it's false, it's kwargs

  # Set up the argument parser for this helper script
  parser = argparse.ArgumentParser(
      description="Validate a schema that was created with an input CSV file."
  )
  parser.add_argument("inputfile", help="The schema file to process")
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("-p", "--parameters",
      help="The file to be validated is a parameters.json file",
      action="store_true"
  )
  group.add_argument("-d", "--datatypes",
      help="The file to be validated is a datatype file",
      action="store_true"
  )

  # The argument parser will error out if the input file isn't specified
  args = parser.parse_args()
  try:
    validate_schema(args.inputfile, args.parameters)
  except: # Logging the full exception... pylint: disable=bare-except
    logging.exception("Caught an error when trying to validate file:" )
    sys.exit()

  logging.info("File %s was successfully validated.", args.inputfile)
