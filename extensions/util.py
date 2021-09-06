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

def discretize(df, schema, clip=None):

    weights = None
    if clip is not None:
        # If clipping, the schema must contain a column with a 'kind' of 'id'
        id_col = next((k for k in schema if schema[k]['kind'] == 'id'), None)
        if not id_col:
            print("Can't clip; no column in the schema is marked with a kind of 'id'.")
        else:
            # each individual now only contributes "clip" records
            # achieved by reweighting records, rather than resampling them
            weights = df[id_col].value_counts()
            weights = np.minimum(clip/weights, 1.0)
            weights = np.array(df[id_col].map(weights).values)

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
    return Dataset(new, domain, weights)

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


def score(real, synth):
    # Replicate the NIST scoring metric
    # Calculates score for *every* 2-way marginal instead of a sample of them
    # performs scoring using the mbi.Dataset representation, which is different from raw data format
    # scores should match exactly 
    # to score raw dataset, call score(discretize(real, schema), discretize(synth, schema))
    assert real.domain == synth.domain
    dom = real.domain
    proj = ('pickup_community_area','shift')
    newdom = dom.project(dom.invert(proj))
    keys = dom.project(proj)
    pairs = list(itertools.combinations(newdom.attrs, 2))

    idx = np.argsort(real.project('pickup_community_area').datavector())

    overall = 0
    breakdown = {}
    breakdown2 = np.zeros(dom.size('pickup_community_area'))

    for pair in pairs:
        #print(pair)
        proj = ('pickup_community_area','shift') + pair
        X = real.project(proj).datavector(flatten=False)
        Y = synth.project(proj).datavector(flatten=False)
        X /= X.sum(axis=(2,3), keepdims=True)
        Y /= Y.sum(axis=(2,3), keepdims=True)

        err = np.nan_to_num( np.abs(X-Y).sum(axis=(2,3)), nan=2.0)
        breakdown[pair] = err.mean()
        breakdown2 += err.mean(axis=1)
        overall += err.mean()

    score = overall / len(pairs)

    nist_score = ((2.0 - score) / 2.0) * 1_000
    breakdown2 /= len(pairs)

    return nist_score, pd.Series(breakdown), (2.0 - breakdown2[idx]) / 2.0
