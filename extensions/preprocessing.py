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

VALID_TAXI_DATA_FILE = str(pathlib.Path(__file__).parent.joinpath("files/taxi_data/ground_truth.csv"))

class Discretization(unittest.TestCase):
  """Test class for the discretization methods
  """

  def test_discretize(self):
    dataframe = pd.read_csv(VALID_TAXI_DATA_FILE)
    schema_gen = SchemaGenerator()
    parse_success = schema_gen.parse_dataframe(dataframe, max_values_for_categorical=100,
            num_bins=0)
    self.assertTrue(parse_success)
    schema = schema_gen.get_parameters_json()["schema"]
    schema["taxi_id"]["kind"] = "id"

    schema["fare"]["bins"] = 1000
    schema["trip_total"]["bins"] = 1000
    schema["trip_seconds"]["bins"] = 100

    # Run the discretize function to produce an mbi.dataset
    mbi_dataset = discretize(dataframe, schema)

    # Run the undo_discretize function on the results
    undiscretized_dataset = undo_discretize(mbi_dataset, schema)

    # Visually compare the original with the discretized / undiscretized
    undiscretized_dataset.to_csv("result.csv", index=False)