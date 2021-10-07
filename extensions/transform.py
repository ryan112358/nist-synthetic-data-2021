import numpy as np
import pandas as pd
import argparse
from mbi import Domain, Dataset
import json

def discretize(df, schema):
    new = df.copy()
    domain = { }
    for col in new.columns:
        if col not in schema:
            continue
        info = schema[col]
        if 'bins' in info:
            # Things that should be binned are marked in the schema with
            # the number of bins into which to bin them; they will also
            # have min and max values.
            bin_info = np.r_[np.linspace(info['min'], info['max'], num=info['bins'],
                    endpoint=False).astype(info['dtype']), info['max']]

            new[col] = pd.cut(df[col], bin_info, right=False).cat.codes
            domain[col] = len(bin_info) - 1
        elif 'values' in info:
            new[col] = df[col].astype(pd.CategoricalDtype(info['values'])).cat.codes
            domain[col] = len(info['values'])
        else:
            new[col] = df[col] - info['min']
            domain[col] = info['max'] - info['min'] + 1

    domain = Domain.fromdict(domain)
    return Dataset(new, domain, None).df, domain

def undo_discretize(df, schema):
    new = df.copy()

    for col in schema.keys():
        info = schema[col]
        if 'bins' in info:
            # Things that should be binned are marked in the schema with
            # the number of bins into which to bin them; they will also
            # have min and max values.
            bin_info = np.r_[np.linspace(info['min'], info['max'], num=info['bins'],
                    endpoint=False).astype(info['dtype']), info['max']]
            low = bin_info[:-1];
            high = bin_info[1:]
            low[0] = low[1]-2
            high[-1] = high[-2]+2
            mid = (low + high) / 2
            new[col] = mid[df[col].values]
        elif 'values' in info:
            mapping = np.array(info['values'])
            new[col] = mapping[df[col].values]
        else:
            new[col] = df[col] + info['min']

    dtypes = { col : schema[col]['dtype'] for col in schema }

    return new.astype(dtypes)

if __name__ == "__main__":
    description = "Pre and post processing functions for the Adagrid mechanism"
    formatter = argparse.ArgumentDefaultsHelpFormatter

    parser = argparse.ArgumentParser(description=description, formatter_class=formatter)
    required = parser.add_argument_group('required arguments')


    required.add_argument('--transform', help='either discretize or \
        undo_discretize', required=True)
    required.add_argument('--df', help='path to dataset', required=True)
    required.add_argument('--schema', help='path to schema file from schemagen',
                            required=True)
    required.add_argument('--output', help='output path for transformed data',
                            required=True)

    #parser.set_defaults(**default_params)
    args = parser.parse_args()

    transform = args.transform
    output_path = args.output
    df = pd.read_csv(args.df)
    with open(args.schema) as f:
        schemagen = json.load(f)
        schema = schemagen["schema"]

    assert transform in ['discretize', 'undo_discretize'], "transform name not \
                                                                valid"
    if transform == 'discretize':
        transformed_df, _ = discretize(df=df, schema=schema)

    if transform == 'undo_discretize':
        transformed_df = undo_discretize(df=df, schema=schema)

    transformed_df.to_csv(output_path, index=False)

