import pandas as pd
import json
import itertools
import argparse
from mbi import Dataset, Domain
import numpy as np

def score(data, synth, targets=[]):
    """ Compute the total variation distance between marginals of data and synth.

    :param data: an mbi.Dataset object
    :param synth: an mbi.Dataset object
    :param targets: A list of columns in the data domain
    """
    workload = list(itertools.combinations(data.domain.invert(targets), 2)) 
    errors = {}
    for a, b in workload:
        key = [a,b] + targets
        xhat = synth.project(key).datavector()
        x = data.project(key).datavector()
        errors[tuple(key)] = 0.5*np.linalg.norm(x - xhat, 1) / data.records
    return pd.Series(errors).sort_values()

   
def default_params():
    """
    Return default parameters to run this program

    :returns: a dictionary of default parameter settings for each command line argument
    """
    params = {}
    params['dataset'] = 'datasets/adult.zip'
    params['domain'] = 'datasets/adult-domain.json'
    params['synthetic'] = 'out.csv'
    params['targets'] = []
    params['save'] = 'error.csv'

    return params

if __name__ == "__main__":

    description = 'A script to score the quality of synthetic data'
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=description, formatter_class=formatter)
    parser.add_argument('--dataset', help='dataset to use')
    parser.add_argument('--domain', help='domain of dataset')
    parser.add_argument('--synthetic', help='synthetic dataset to use')
    parser.add_argument('--targets', type=str, nargs='+', help='target columns to define evaluation criteria')
    parser.add_argument('--save', type=str, help='path to save error report')

    parser.set_defaults(**default_params())
    args = parser.parse_args()

    df = pd.read_csv(args.dataset)
    sy = pd.read_csv(args.synthetic)
    domain = Domain.fromdict(json.load(open(args.domain, "r")))
    data = Dataset(df, domain)
    synth = Dataset(sy, domain)
    
    errors = score(data, synth, args.targets)
    errors.to_csv(args.save)
    
    print(errors)
    
    print('Average Error: ', errors.mean())
