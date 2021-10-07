"""This is a module for the SchemaGenerator class, which is used
to create schema files based on an existing CSV file.

The schema generator takes as input a comma-separated datafile.
The output is two files, a ``parameters.json`` file and a
``column_datatypes.json`` file. These files can be written
out using the output_prarmeters_json and output_column_datatypes_json
methods.

  Typical usage example:

.. code-block:: python

  schema_generator = schemagen.SchemaGenerator()
  input_file = "/path/to/file.csv"
  schema_generator.read_and_parse_csv(input_file)
  parameters_json = schema_generator.get_parameters_json()
"""

import os.path
import json
import math
import logging
import pandas as pd
import numpy as np

# Allow long lines in docs. pylint: disable=line-too-long
DEFAULT_MAX_VALUES_FOR_CATEGORICAL = 40 #: *(default)* columns with fewer than this many values will be considered categorical
DEFAULT_NUM_BINS = 10 #: *(default)* informational "number of bins" into which a consumer of the schema should bucket the values
DEFAULT_INCLUDE_NA = False #: *(default)* whether or not to include NaN as a value for categorical fields
DEFAULT_INCLUDE_TEXT = False #: *(default)* whether or not to include columns of kind "text" (non-categorical string columns)
DEFAULT_PADDING_PERCENTAGE = 0.05
NAME_FOR_PARAMETERS_FILE = "parameters.json"
NAME_FOR_DATATYPES_FILE = "column_datatypes.json"
# pylint: enable=line-too-long

class SchemaGenerator:
  # Allow long lines in docs, because URLs. pylint: disable=line-too-long
  """This is a schema generating class. It can be used to read an input
  comma-separated values file and infer a schema (including datatypes,
  categorical values, and ranges).

  The schema generator takes as input a comma-separated datafile.
  The output is two files, a ``parameters.json`` file and a
  ``column_datatypes.json`` file. These files can be written
  out using the output_prarmeters_json and output_column_datatypes_json
  methods.

  The ``parameters.json`` file contains detailed information about each
  column, and will conform to the
  :download:`parameters.json.schema <../../json_schemae/parameters.json.schema>`.
  The ``column_datatypes.json`` file just contains the datatype information
  for each column in order to make processing easier, and will conform to the
  :download:`column_datatypes.json.schema <../../json_schemae/column_datatypes.json.schema>`.

  """
  # pylint: enable=line-too-long

  def __init__(self):
    """This method creates a new SchemaGenerator.
    The SchemaGenerator can then be used by calling
    the load_csv method to read in a CSV file, and
    the output methods to output the generated schema.
    """
    # Initialize class variables
    self._clear_class_variables()

    # Set up a logger for this module
    self.log = logging.getLogger(__name__)

  def read_and_parse_csv(self, input_csv_file,
            include_text_columns = DEFAULT_INCLUDE_TEXT, skip_columns = None,
            max_values_for_categorical = DEFAULT_MAX_VALUES_FOR_CATEGORICAL,
            num_bins = DEFAULT_NUM_BINS,
            include_na = DEFAULT_INCLUDE_NA,
            categorical_columns = None,
            geographical_columns = None):
    # Allow long lines in docs, because params. pylint: disable=line-too-long
    """This method loads in a new input CSV file and attempts to infer
    a schema from it. If the SchemaGenerator has already been used to
    generate a schema from a different input file, this method will clear
    out the previous schema (even if it encounters an error when
    reading in a new file). (If it is desirable to keep multiple schemae,
    a different SchemaGenerator should be used for each input file.)

    Error-handling: This method will trap and log exceptions directly,
    and return a simple bool indicating success or failure.

    :param input_csv_file: the CSV file that should be examined to determine the schema
    :type input_csv_file: str
    :param include_text_columns: whether or not to include columns that have a kind of "text" (non-categorical string fields)
    :type include_text_columns: bool
    :param skip_columns: a list of names of columns to skip completely
    :type skip_columns: list
    :param max_values_for_categorical: columns with fewer than this many values will be considered categorical
    :type max_values_for_categorical: number
    :param num_bins: informational value to include in the output schema to indicate how many 'bins' should be used for numeric values
    :type num_bins: number
    :param include_na: whether or not to include ``NaN`` as a value for categorical fields
    :type include_na: bool
    :param categorical_columns: a list of names of columns to always treat as categorical, regardless of number of values
    :type categorical_columns: list
    :param geographical_columns: a list of names of columns to always treat as geographical (and therefore categorical), regardless of number of values
    :type geographical_columns: list

    :return: whether or not the loading was successful
    :rtype: bool

    """
    # pylint: enable=line-too-long

    # Since we're reading in a new input file, first we should
    # re-initialize the output schema that we'll be generating
    # from it. Additionally, clear out the dataframe that
    # is being used to generate the schema, and the local
    # tracking variable for the name of the CSV file.
    self._clear_class_variables()

    # Set the local input_csv_file variable, just to track
    # the file that we're reading in.
    self.input_csv_file = input_csv_file

    # Read the file into the local dataframe
    try:
      self.input_data_as_dataframe = self._load_csv(self.input_csv_file)
    except: # Logging the full exception... pylint: disable=bare-except
      # Re-clear these variables to make sure nothing is in a half-loaded state
      self._clear_class_variables()

      self.log.exception("Caught an error when trying to load input file:" )
      return False

    try:
      # Do the processing needed to generate the schema
      (self.output_schema, self.output_datatypes) = \
            self._build_schema(
                self.input_data_as_dataframe,
                include_text_columns=include_text_columns,
                skip_columns=skip_columns,
                max_values_for_categorical=max_values_for_categorical,
                num_bins=num_bins,
                include_na=include_na,
                categorical_columns=categorical_columns,
                geographical_columns=geographical_columns
            )
    except: # Logging the full exception... pylint: disable=bare-except
      # Re-clear these variables to make sure nothing is in a half-loaded state
      self._clear_class_variables()

      self.log.exception("Caught an error when trying to parse schema:" )
      return False

    return True

  def parse_dataframe(self, input_dataframe,
            include_text_columns = DEFAULT_INCLUDE_TEXT, skip_columns = None,
            max_values_for_categorical = DEFAULT_MAX_VALUES_FOR_CATEGORICAL,
            num_bins = DEFAULT_NUM_BINS,
            include_na = DEFAULT_INCLUDE_NA,
            categorical_columns = None,
            geographical_columns = None):
    # Allow long lines in docs, because params. pylint: disable=line-too-long
    """This method will attempt to infer a schema from an already-loaded
    dataframe. If the SchemaGenerator has already been used to
    generate a schema from a different input file, this method will clear
    out the previous schema (even if it encounters an error when
    reading in a new file). (If it is desirable to keep multiple schemae,
    a different SchemaGenerator should be used for each input file.)

    Error-handling: This method will trap and log exceptions directly,
    and return a simple bool indicating success or failure.

    :param input_dataframe: the dataframe that has already been loaded in
    :type input_dataframe: pandas.DataFrame
    :param include_text_columns: whether or not to include columns that have a kind of "text" (non-categorical string fields)
    :type include_text_columns: bool
    :param skip_columns: a list of names of columns to skip completely
    :type skip_columns: list
    :param max_values_for_categorical: columns with fewer than this many values will be considered categorical
    :type max_values_for_categorical: number
    :param num_bins: informational value to include in the output schema to indicate how many 'bins' should be used for numeric values
    :type num_bins: number
    :param include_na: whether or not to include ``NaN`` as a value for categorical fields
    :type include_na: bool
    :param categorical_columns: a list of names of columns to always treat as categorical, regardless of number of values
    :type categorical_columns: list
    :param geographical_columns: a list of names of columns to always treat as geographical (and therefore categorical), regardless of number of values
    :type geographical_columns: list

    :return: whether or not the parsing was successful
    :rtype: bool

    """
    self._clear_class_variables()
    self.input_data_as_dataframe = input_dataframe

    try:
      # Do the processing needed to generate the schema
      (self.output_schema, self.output_datatypes) = \
            self._build_schema(
                self.input_data_as_dataframe,
                include_text_columns=include_text_columns,
                skip_columns=skip_columns,
                max_values_for_categorical=max_values_for_categorical,
                num_bins=num_bins,
                include_na=include_na,
                categorical_columns=categorical_columns,
                geographical_columns=geographical_columns
            )
    except: # Logging the full exception... pylint: disable=bare-except
      # Re-clear these variables to make sure nothing is in a half-loaded state
      self._clear_class_variables()

      self.log.exception("Caught an error when trying to parse schema:" )
      return False

    return True

  def get_parameters_json(self):
    # Allow long lines in docs, because URLs. pylint: disable=line-too-long
    """Returns the content that would be written to the ``parameters.json`` file
    as a Python dict. This contains full information about the different
    properties in the input CSV file that was parsed by the SchemaGenerator.
    It will conform to the
    :download:`parameters.json.schema <../../json_schemae/parameters.json.schema>`
    JSON schema. Returns ``None`` if no file has been parsed, or if the most recent
    file was unable to be parsed.

    :return: a Python dict that contains the ``parameters.json`` content.
    :rtype: dict
    """
    # pylint: enable=line-too-long
    return self.output_schema

  def get_column_datatypes_json(self):
    # Allow long lines in docs, because URLs. pylint: disable=line-too-long
    """Returns the content that would be written to the ``column_datatypes.json``
    file, as a Python dict. This contains information about the column names
    and datatypes that were in the input CSV file that was parsed by the
    SchemaGenerator. It will conform to the
    :download:`column_datatypes.json.schema <../../json_schemae/column_datatypes.json.schema>`
    JSON schema. Returns ``None`` if no file has been parsed, or if the most recent
    file was unable to be parsed.

    :return: a Python dict that contains the ``column_datatypes.json`` content.
    :rtype: dict
    """
    # pylint: enable=line-too-long
    return self.output_datatypes

  def output_parameters_json(self, output_directory = "."):
    # Allow long lines in docs, because URLs. pylint: disable=line-too-long
    """This method outputs the ``parameters.json`` file into
    the specified directory. The ``parameters.json`` file
    contains information about each column in the file, including
    min/max, values, and/or datatype. This file is expected to conform to the
    :download:`parameters.json.schema <../../json_schemae/parameters.json.schema>`
    JSON schema.

    :param output_directory: (optional) the directory into which to output the file. If not specified, will write out to the current working directory.
    :type output_directory: str

    :return: full filepath to the output file, or None if the output was unsuccessful.
    :rtype: str
    """
    # pylint: enable=line-too-long

    output_file = os.path.join(output_directory, NAME_FOR_PARAMETERS_FILE)

    self.log.info("Writing output parameters file %s...", output_file)

    try:
      with open(output_file, "w", encoding="utf-8") as write_file:
        json.dump(self.output_schema, write_file, indent=2)
        write_file.write("\n") # Include a newline at the end because POSIX.
    except FileNotFoundError:
      self.log.error("Can't write to '%s'. Does the parent directory exist?",
                output_file)
      output_file = None
    except: # Logging the full exception... pylint: disable=bare-except
      self.log.exception("Caught error when trying to write parameters file:" )
      output_file = None
    else:
      self.log.info("Done writing output parameters file.")
    return output_file

  def output_column_datatypes_json(self, output_directory = "."):
    # Allow long lines in docs, because params. pylint: disable=line-too-long
    """This method outputs the ``column_datatypes.json`` file into
    the specified directory. The ``column_datatypes.json`` file
    contains a JSON object that identifies just the datatype
    of each column. It also includes a ``skipinitialspace`` property
    that can be set to true or false.

    :param output_directory: (optional) the directory into which to output the file. If not specified, will write out to the current working directory.
    :type output_directory: str

    :return: full filepath to the output file, or None if the output was unsuccessful.
    :rtype: str
    """
    # pylint: enable=line-too-long

    #TODO:
    # - what is the skipinitialspace property?

    output_file = os.path.join(output_directory, NAME_FOR_DATATYPES_FILE)
    self.log.info("Writing output column datatypes file %s...", output_file)

    try:
      with open(output_file, "w", encoding="utf-8") as write_file:
        json.dump(self.output_datatypes, write_file, indent=2)
        write_file.write("\n") # Include a newline at the end because POSIX.
    except FileNotFoundError:
      self.log.error("Can't write to '%s'. Does the parent directory exist?",
                output_file)
      output_file = None
    except: # Logging the full exception... pylint: disable=bare-except
      self.log.exception("Caught error when trying to write column_datatypes:")
      output_file = None
    else:
      self.log.info("Done writing output column datatypes file.")

    return output_file

  # PRIVATE METHODS BELOW HERE
  def _clear_class_variables(self):
    """This method just clears out the class
    variables, and resets the SchemaGenerator to
    its pristine state.
    """
    self.output_schema = None
    self.output_datatypes = None
    self.input_data_as_dataframe = None
    self.input_csv_file = None

  def _load_csv(self, input_csv_file):
    # Allow long lines in docs, because params. pylint: disable=line-too-long
    """
    Loads in the CSV file as a pandas DataFrame.

    :param input_csv_file: the CSV file that should be examined to determine the schema
    :type input_csv_file: str

    :return: The input CSV file as a dataframe (will raise exceptions if it encounters them)
    :rtype: pandas.DataFrame
    """
    # pylint: enable=line-too-long

    self.log.info("Reading CSV file...")

    # Set a default return value
    input_data_as_dataframe = None

    # Read in the input file with pandas. If this fails,
    # throw an error and get out.
    try:
      input_data_as_dataframe = pd.read_csv(input_csv_file)
    except pd.errors.ParserError as err:
      # This is likely to be a common error, so check for it explicitly
      self.log.error("Using input file: '%s', \
'pandas.read_csv()' was unable to parse the input file \
as a CSV. Please confirm that it contains valid comma-separated \
values.", input_csv_file)
      raise err
    except FileNotFoundError as err:
      # This is likely to be a common error, so check for it explicitly
      self.log.error("Using input file: '%s', \
the file was not found. Please confirm the specified \
path, or use a full path instead of a relative path.", input_csv_file)
      raise err
    except pd.errors.EmptyDataError as err:
      # This is likely to be a common error, so check for it explicitly
      self.log.error("\nUsing input file: '%s', \
The file appears to be empty. Please confirm the path.",
          input_csv_file)
      raise err
    except BaseException as err:
      # An error was thrown that we weren't expecting; log and rethrow to caller
      self.log.error("\nUsing input file: '%s', \
The system received an unexpected error when trying to \
parse the input file using 'pandas.read_csv()'.", input_csv_file)
      raise err

    self.log.info("Successfully read CSV file.")

    return input_data_as_dataframe


  def _build_schema(self, input_data_as_dataframe,
            include_text_columns = DEFAULT_INCLUDE_TEXT, skip_columns = None,
            max_values_for_categorical = DEFAULT_MAX_VALUES_FOR_CATEGORICAL,
            num_bins = DEFAULT_NUM_BINS,
            include_na = DEFAULT_INCLUDE_NA,
            categorical_columns = None,
            geographical_columns = None):
    # Allow long lines in docs, because params. pylint: disable=line-too-long
    """This method contains the business logic to build an appropriate
    schema object based on the information from the input dataset. It uses
    numpy helper functions to figure out what the appropriate datatype should
    be, and uses pandas to determine unique values for categorical datatypes.

    This method determines whether a numeric variable is categorical or not by
    comparing the number of values in the file to max_values_for_categorical
    parameter. This parameter defaults to ``DEFAULT_MAX_VALUES_FOR_CATEGORICAL``.

    The method can also optionally include "NaN" as a value for categorical
    variables that contain some rows that do not have values. By default, it
    will not include NaN as a possible value.

    Note that if the input dataset has duplicate column names, they will be
    named as "column", "column.1", "column.2", etc. in the output schema.
    This is how the ``pandas`` package handles duplicate column names, and since
    we expect that most people who are using this module will also be using
    pandas, it seems reasonable to keep this behavior.

    :param input_data_as_dataframe: a pandas DataFrame that should be examined to determine the schema
    :type input_data_as_dataframe: pandas.DataFrame
    :param include_text_columns: whether or not to include columns that have a kind of "text" (non-categorical string fields)
    :type include_text_columns: bool
    :param skip_columns: a list of names of columns to skip completely
    :type include_na: list
    :param max_values_for_categorical: columns with fewer than this many values will be considered categorical
    :type num_bins: number
    :param num_bins: informational value to include in the output schema to indicate how many 'bins' should be used for numeric values
    :type max_values_for_categorical: number
    :param include_na: whether or not to include ``NaN`` as a value for categorical fields
    :type include_na: bool
    :param categorical_columns: a list of names of columns to always treat as categorical, regardless of number of values
    :type include_na: list
    :param geographical_columns: a list of names of columns to always treat as geographical (and therefore categorical)
    :type include_na: list

    :return: tuple of dicts representing the full schema and the column datatypes, respectively
    :rtype: tuple
    """
    # pylint: enable=line-too-long

    if include_na:
      self.log.info("Building schema...")
    else:
      self.log.info("Building schema without using NAs...")

    if not categorical_columns:
      categorical_columns = []
    if not geographical_columns:
      geographical_columns = []
    if not skip_columns:
      skip_columns = []

    # Start the return value off with an empty schema structure
    output_schema = { "schema": {} }
    output_datatypes = { "dtype": {} }

    # loop over each column, and add the values and the datatype to the dict
    for column in input_data_as_dataframe.columns:
      if column.strip(" ") in skip_columns:
        self.log.info("Skipping column %s as requested", column)
        continue

      # The actual values for the column
      series = input_data_as_dataframe[column]
      if not include_na:
        self.log.info("Removing NA values from column %s", column)
        series.dropna(inplace=True)

      # Local variable to store the schema for this particular column
      col_schema = {}

      # Unique values for this column
      values = pd.unique(series)

      (datatype, min_value, max_value) = self._get_series_dtype(series)
      col_schema["dtype"] = datatype

      # Now, decide if this should be treated as a categorical value or
      # something else, by checking to see how many unique values
      # there are.
      if column.strip(" ") in categorical_columns or \
          column.strip(" ") in geographical_columns or \
          len(values) <= max_values_for_categorical:

        # Treat as a categorical value and output a list of unique values
        if column in geographical_columns:
          col_schema["kind"] = "geographical"
        else:
          col_schema["kind"] = "categorical"

        # If we're including NA, it's frequently not going to be sortable,
        # so don't even try
        if not include_na:
          try:
            values.sort()
          except: # Logging the full exception... pylint: disable=bare-except
            self.log.exception("Encountered an error when trying to sort the \
values. Will include them without sorting.")
        col_schema["values"] = values.tolist()
        col_schema["codes"] = list(range(1, len(values)+1))

      else:
        # Not categorical data
        if col_schema["dtype"] == "str":
          if not include_text_columns:
            self.log.warning("Skipping '%s' because it is freetext", column)
            col_schema = None
            continue

          self.log.warning("\nNot using values for column '%s' \
because it is non-numeric and there are more than %s \
unique values for it. This column will be labeled as a \
'text' kind of string, and values will not be included.",
              str(column), str(max_values_for_categorical))
          col_schema["kind"] = "text"
        elif col_schema["dtype"] == "date":
          col_schema["kind"] = "date"
          col_schema["min"] = min_value
          col_schema["max"] = max_value
        else:
          # Treat it as a numeric value.
          col_schema["kind"] = "numeric"
          col_schema["min"] = min_value
          col_schema["max"] = max_value
          if num_bins > 0:
            col_schema["bins"] = num_bins

      output_schema["schema"][column] = col_schema
      # Also add this column and its datatype to the output_datatypes dict
      output_datatypes["dtype"][column] = col_schema["dtype"]

    self.log.info("Schema building successful.")
    return (output_schema, output_datatypes)


  def _get_series_dtype(self, series, fuzz_min_max=False):
    # Allow long lines in docs, because params. pylint: disable=line-too-long
    """
    Determine the datatype that we want to put into our schema files. This isn't
    necessarily the same as what pandas thinks the datatype of the column is.
    Additionally, for numeric or datetime columns, determine the min/max values
    for the column (since we're examining the column anyway).

    :param: series a pandas series to examine
    :type: pandas.series
    :param: fuzz_min_max whether or not to adjust the min/max values for numeric by a percentage; defaults to False
    :type: boolean

    :return: a tuple containing the string version of the datatype to use and, if relevant, min and max values
    :rtype: str
    """
    # pylint: enable=line-too-long

    # default datatype value is "str" when all else fails
    datatype = "str"
    # default min/max are just None
    min_value = None
    max_value = None

    # Ask pandas to figure out the best possible datatype based on the data
    series = series.infer_objects()

    if series.dtype.kind in ['i', 'u']: # pylint: disable=inconsistent-quotes
      # If we believe the datatype is an int, we want to
      # calculate min and max values and then figure out the
      # smallest numpy int datatype that can store it, given the
      # min and max values
      min_value = series.min().item()
      max_value = series.max().item()

      if fuzz_min_max:
        # Given these min and max values, "fuzz" them a little bit
        # by adding / subtracting 5% of the difference between the two
        # (rounded to the nearest int, because this is an int)
        padding_margin = math.ceil((max_value - min_value) *
              DEFAULT_PADDING_PERCENTAGE)
        # Don't fuzz if min_value is equal to zero, because we'd unexpectedly
        # be going negative on it
        if min_value != 0:
          min_value = min_value - padding_margin
        max_value = max_value + padding_margin

      # Now determine the smallest type that will work for both the min
      # and the max value.
      # NOTE (mch): I wasn't able to find a clever way to do this, so since
      # we know it's an int, let's just try them all. (a trick like
      # np.promote_types(np.min_scalar_type(min), np.min_scalar_type(max))
      # won't work because if the min/max are something like -4/4,
      # promote_types will give you an int16 instead of an int8, because
      # you end up with promote_types(int8, uint8) which gives you an int16
      for dtype in [np.uint8, np.int8, np.uint16, np.int16,
              np.uint32, np.int32, np.uint64, np.int64]:
        if np.can_cast(min_value, dtype) and np.can_cast(max_value, dtype):
          smallest_type = dtype(0).dtype.name
          break

      if not smallest_type:
        # Failsafe
        smallest_type = (np.promote_types(np.min_scalar_type(min_value),
            np.min_scalar_type(max_value))).name

      # That's the type we'll put in the schema
      datatype = smallest_type

    elif series.dtype.kind in ['f', 'c']: # pylint: disable=inconsistent-quotes
      # numpy dtypes will be `float32`/`float64`, but we just want `float`.
      datatype = "float"
      min_value = series.min().item()
      max_value = series.max().item()

      if fuzz_min_max:
        # Given these min and max values, "fuzz" them a little bit
        # by adding / subtracting 5% of the difference between the two
        padding_margin = (max_value - min_value) * DEFAULT_PADDING_PERCENTAGE
        min_value = min_value - padding_margin
        max_value = max_value + padding_margin

    else:
      # See if we can parse it as a date
      try:
        dt = pd.to_datetime(series)
        datatype = "date"
      except: # Logging the full exception... pylint: disable=bare-except
        # Default to it just being a string
        datatype = "str"
      else:
        # It's a date; get min/max as dates, rounded to the nearest day
        min_value = str(dt.min().floor("D"))
        max_value = str(dt.max().ceil("D"))

    return (datatype, min_value, max_value)
