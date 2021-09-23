import pandas as pd
import argparse

def default_params():
    """
    Return default parameters to run this program

    :returns: a dictionary of default parameter settings for each command line argument
    """
    params = {}
    params['dataset'] = 'datasets/adult.zip'
    params['save'] = 'resample.csv'

    return params

if __name__ == "__main__":

    description = 'A non-private baseline synthetic data generator, that resamples records with replacement'
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=description, formatter_class=formatter)
    parser.add_argument('--dataset', help='dataset to use')
    parser.add_argument('--save', type=str, help='path to save error report')

    parser.set_defaults(**default_params())
    args = parser.parse_args()

    df = pd.read_csv(args.dataset)
    sy = df.sample(df.shape[0], replace=True)
    sy.to_csv(args.save, index=False)
