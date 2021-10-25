import pandas as pd
import json
import argparse
import sys

def default_params():
    """
    Return default parameters to run this program

    :returns: a dictionary of default parameter settings for each command line argument
    """
    params = {}
    params['dataset'] = 'datasets/adult.zip'
    params['domain'] = 'datasets/adult-domain.json'
    return params

if __name__ == "__main__":

    description = ''
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=description, formatter_class=formatter)
    parser.add_argument('--dataset', help='dataset to use')
    parser.add_argument('--domain', help='domain to use')

    parser.set_defaults(**default_params())
    args = parser.parse_args()

    df = pd.read_csv(args.dataset)
    domain = json.load(open(args.domain, "r"))

    for col in domain:
        if not col in df.columns:
            print('Error: Column %s in domain but not in data' % col)
            sys.exit()

    for col in domain:
        n = domain[col]
        if not df[col].between(0, n, inclusive='left').all():
            print('Error: Values for column %s are not in range [0, %s)' % (col, n))
            sys.exit()

    print('Dataset and domain file look good!')
