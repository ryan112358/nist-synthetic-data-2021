"""A script to run the schema generator against a CSV file.

  Typical usage example:

  python main.py my_input_file.csv
"""

import argparse
import logging
import os
import sys
import schemagen
import validate

# Configure the logger to output just warnings and above; logs will
# go to stderr by default
logging.basicConfig(level=os.environ.get("LOGLEVEL", "WARNING"))

def generate_schema(input_file, include_text, skip_cols,
        max_categorical, num_bins, include_na,
        categorical_cols, geographical_cols):
  # Create a SchemaGenerator
  local_schema_generator = schemagen.SchemaGenerator()

  # Parse the input file
  loading_result = local_schema_generator.read_and_parse_csv(
      input_file,
      include_text_columns=include_text,
      skip_columns=skip_cols,
      max_values_for_categorical=max_categorical,
      num_bins=num_bins,
      include_na=include_na,
      categorical_columns=categorical_cols,
      geographical_columns=geographical_cols
  )

  # If the loading was unsuccessful, exit
  if not loading_result:
    logging.error("Unable to load the specified CSV file.")
    return None

  return local_schema_generator

def output_schema(param_schema_generator, output_dir):
  # Output the parameters.json file to the output directory (if specified)
  output_parameters_json = param_schema_generator.output_parameters_json(
      output_directory = output_dir
  )
  output_column_datatypes_json = \
      param_schema_generator.output_column_datatypes_json(
          output_directory = output_dir
      )

  # Validate the output schema
  logging.info("Done generating schema. Validating output files...")
  try:
    validate.validate_schema(output_parameters_json, True)
  except: # Logging the full exception... pylint: disable=bare-except
    logging.exception("Caught an error when trying to validate %s",
        output_parameters_json)
    logging.warning("%s file should be reviewed to ensure it is complete.",
        output_parameters_json)

  try:
    validate.validate_schema(output_column_datatypes_json, False)
  except: # Logging the full exception... pylint: disable=bare-except
    logging.exception("Caught an error when trying to validate %s",
        output_column_datatypes_json)
    logging.warning("%s should be reviewed manually to ensure it is complete.",
        output_column_datatypes_json)

  print("\nSchema generator is complete! Schema files are:")
  print(output_parameters_json)
  print(output_column_datatypes_json)

if __name__ == "__main__":
  # main.py executed as script

  # Set up the argument parser for this helper script
  parser = argparse.ArgumentParser(
          description="Create a schema from an input CSV file."
  )
  parser.add_argument("inputfile", help="The input file to process")

  parser.add_argument("-o", "--outputdir", help=
    "The output directory for the generated files. Defaults to the\
    current working directory", default=".")

  parser.add_argument("-m", "--max_categorical", help=
    "The maximum number of unique values allowed to be considered categorical. \
    Must be an integer. Defaults to " +
    str(schemagen.DEFAULT_MAX_VALUES_FOR_CATEGORICAL),
    default=schemagen.DEFAULT_MAX_VALUES_FOR_CATEGORICAL, type=int)

  parser.add_argument("-b", "--num_bins", help=
    "Provide default 'number of bins' information for numeric variables. \
    This number will be included in the output schema for each numeric \
    variable, for informational purposes only. If needed, overrides for \
    individual variables should be adjusted directly in the output file. \
    Set this to 0 to suppress output of bucketing information. Defaults to " +
    str(schemagen.DEFAULT_NUM_BINS),
    default=schemagen.DEFAULT_NUM_BINS, type=int)

  parser.add_argument("-c", "--categorical", help=
    "A list of column names that should always be considered categorical, \
    regardless of the number of values. Specify in quotes, as a comma-separated\
    list (e.g. \"ColA,Column B,C\")", type=str)

  parser.add_argument("-g", "--geographical", help=
    "A list of column names that should be considered geographical, \
    a special kind of categorical. Specify in quotes, as a comma-separated\
    list (e.g. \"ColA,Column B,C\")", type=str)

  parser.add_argument("-s", "--skip_columns", help=
    "A list of column names that should be skipped entirely. \
    Specify in quotes, as a comma-separated\
    list (e.g. \"ColA,Column B,C\")", type=str)

  parser.add_argument("-i", "--include_na", help=
    "Specify this to include NA as part of the categorical values, if some \
    records don't have a value for that column. Defaults to " +
    str(schemagen.DEFAULT_INCLUDE_NA),
    default=schemagen.DEFAULT_INCLUDE_NA, action="store_true")

  parser.add_argument("-t", "--include_text_columns", help=
    "Specify this to include columns that are type 'text' (non-categorical \
    string columns). Defaults to " +
    str(schemagen.DEFAULT_INCLUDE_TEXT),
    default=schemagen.DEFAULT_INCLUDE_TEXT, action="store_true")

  # The argument parser will error out if the input file isn't specified
  args = parser.parse_args()

  # If the user has specified a list of columns to treat as categorical,
  # parse the string argument into a list
  categorical_columns = None
  if args.categorical:
    categorical_columns = [c.strip(" ") for c in args.categorical.split(",")]

  # If the user has specified a list of columns to treat as geographical,
  # parse the string argument into a list
  geographical_columns = None
  if args.geographical:
    geographical_columns = [c.strip(" ") for c in args.geographical.split(",")]

  # If the user has specified a list of columns to skip,
  # parse the string argument into a list
  skip_columns = None
  if args.skip_columns:
    skip_columns = [c.strip(" ") for c in args.skip_columns.split(",")]

  # Generate the schema
  schema_generator = generate_schema(args.inputfile,
          args.include_text_columns, skip_columns,
          args.max_categorical, args.num_bins,  args.include_na,
          categorical_columns, geographical_columns)

  # The schema wasn't able to be generated
  if not schema_generator:
    logging.error("Unable to generate schema. Please review logs for details.")
    sys.exit()

  # Output the schema files
  output_schema(schema_generator, args.outputdir)

