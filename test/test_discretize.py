"""Test methods for the discretize and undiscretize methods
from util.py.

  Typical usage example:

  python -m unittest

  or

  python -m unittest -k test_discretize
"""
import unittest
import pathlib
import numpy as np
import pandas as pd
import json

from util import discretize, undo_discretize, score
from mbi import Domain, Dataset
from schemagen import SchemaGenerator

# Assumes that a subdirectory called files/taxi_data exists and that the
# taxi data file is in that subdirectory called "ground_truth.csv"
VALID_TAXI_DATA_FILE = str(pathlib.Path(__file__).parent.joinpath("files/taxi_data/ground_truth.csv"))

class TestDiscretization(unittest.TestCase):
  """Test class for the discretization methods
  """

  def test_discretize(self):
    """
    Test discretize function
    """
    # Get the test taxi file as a dataframe
    dataframe = pd.read_csv(VALID_TAXI_DATA_FILE)
    # Create a schema, with custom values for
    # max categorical and number of bins
    schema_gen = SchemaGenerator()
    parse_success = schema_gen.parse_dataframe(dataframe, max_values_for_categorical=100,
            num_bins=100)
    self.assertTrue(parse_success)
    schema = schema_gen.get_parameters_json()["schema"]

    # Set the appropriate ID column and adjust some of the bins.
    # Normally, this would be done manually in the
    # parameters.json file by the researcher, after creating
    # the schema with the schema generator but before creating the
    # synthetic data. For this test file, we'll just hard-code it.
    schema["taxi_id"]["kind"] = "id"
    schema["taxi_id"].pop("bins") # Don't bin taxi ID even though the schema generator thought it was a numeric column

    schema["fare"]["bins"] = 1000
    schema["trip_total"]["bins"] = 1000
    schema["trip_seconds"]["bins"] = 10000

    # Run the discretize function to produce an mbi.dataset
    mbi_dataset = discretize(dataframe, schema, 200)

    # Run the undo_discretize function on the results
    undiscretized_dataset = undo_discretize(mbi_dataset, schema)

    # Visually compare the original with the discretized / undiscretized
    undiscretized_dataset.to_csv("result.csv", index=False)
