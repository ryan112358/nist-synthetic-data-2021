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

# Import things from the file to make it easier for importing code to use it

from .schemagen import SchemaGenerator
from .schemagen import DEFAULT_MAX_VALUES_FOR_CATEGORICAL
from .schemagen import DEFAULT_NUM_BINS
from .schemagen import DEFAULT_INCLUDE_NA
from .schemagen import DEFAULT_INCLUDE_TEXT
