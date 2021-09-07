import numpy as np
import pandas as pd
from mbi import Domain, Dataset
import itertools

def powerset(iterable):
    s = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(1,len(s)+1))

def downward_closure(cliques):
    ans = set()
    for proj in cliques:
        ans.update(powerset(proj))
    return list(sorted(ans, key=len))

def discretize(df, schema):

    new = df.copy()
    domain = { }
    for col in schema:
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
    return Dataset(new, domain, None)

def undo_discretize(dataset, schema):
    df = dataset.df
    new = df.copy()

    for col in dataset.domain:
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

        #if 'max' in info:
        #    new[col] = np.minimum(new[col], info['max'])
        #if 'min' in info: 
        #    new[col] = np.maximum(new[col], info['min'])

    dtypes = { col : schema[col]['dtype'] for col in schema }

    return new.astype(dtypes)
