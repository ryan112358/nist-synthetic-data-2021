import numpy as np
import pandas as pd
import json
from mbi import FactoredInference, Factor, Dataset, Domain
from scipy import sparse
from scipy.special import logsumexp
import itertools
import networkx as nx
from disjoint_set import DisjointSet
from cdp2adp import cdp_rho

def powerset(iterable):
    s = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(1,len(s)+1))

def downward_closure(cliques):
    ans = set()
    for proj in cliques:
        ans.update(powerset(proj))
    return list(sorted(ans, key=len))

def get_permutation_matrix(cl1, cl2, domain):
    # permutation matrix that maps datavector of cl1 factor to datavector of cl2 factor
    assert set(cl1) == set(cl2)
    n = domain.size(cl1)
    fac = Factor(domain.project(cl1),np.arange(n))
    new = fac.transpose(cl2)
    data = np.ones(n)
    row_ind = fac.datavector()
    col_ind = new.datavector()
    return sparse.csr_matrix((data, (row_ind, col_ind)), shape=(n,n))

def get_aggregate(cl, matrices, domain):
    children = [r for r in matrices if set(r) < set(cl) and len(r)+1 == len(cl)]
    ans = [sparse.csr_matrix((0,domain.size(cl)))]
    for c in children:
        coef = 1.0 / np.sqrt(len(children))
        a = tuple(set(cl)-set(c))
        cl2 = a + c
        Qc = matrices[c]
        P = get_permutation_matrix(cl, cl2, domain)
        T = np.ones(domain.size(a))
        Q = sparse.kron(T, Qc) @ P
        ans.append(coef*Q)
    return sparse.vstack(ans)
    
def get_identity(cl, post_plausibility, domain):
    # determine which cells in the cl marginal *could* have a count above threshold, 
    # based on previous measurements
    children = [r for r in post_plausibility if set(r) < set(cl) and len(r)+1 == len(cl)]
    plausibility = Factor.ones(domain.project(cl))
    for c in children:
        plausibility *= post_plausibility[c]

    row_ind = col_ind = np.nonzero(plausibility.datavector())[0]
    data = np.ones_like(row_ind)
    n = domain.size(cl)
    Q = sparse.csr_matrix((data, (row_ind, col_ind)), (n,n))
    return Q

def exponential_mechanism(q, eps, sensitivity, prng=np.random, monotonic=False):
    if eps == np.inf:
        eps = np.finfo(np.float64).max
    coef = 1.0 if monotonic else 0.5
    scores = coef*eps/sensitivity*(q-q.max())
    probas = np.exp(scores - logsumexp(scores))
    return prng.choice(q.size, p=probas)

def select(data, model, rho, targets=[]):
    weights = {}
    candidates = list(itertools.combinations(data.domain.invert(targets), 2))
    for a, b in candidates:
        xhat = model.project([a, b] + targets).datavector()
        x = data.project([a, b] + targets).datavector()
        weights[a,b] = np.linalg.norm(x - xhat, 1)

    T = nx.Graph()
    T.add_nodes_from(data.domain.attrs)
    ds = DisjointSet()

    r = len(data.domain) - len(targets)
    epsilon = np.sqrt(8*rho/(r-1))
    for i in range(r-1):
        candidates = [e for e in candidates if not ds.connected(*e)]
        wgts = np.array([weights[e] for e in candidates])
        idx = exponential_mechanism(wgts, epsilon, sensitivity=1.0)
        e = candidates[idx]
        T.add_edge(*e)
        ds.union(*e)

    return [e+tuple(targets) for e in T.edges]


def adagrid(data, epsilon, delta, threshold, targets=[], iters=2500):
    rho = cdp_rho(epsilon, delta)
    rho_per_step = rho/3
    domain = data.domain
    measurements = []
    post_plausibility = {}
    matrices = {}

    step1_outer = [(a,) + tuple(targets) for a in domain if a not in targets]
    step1_all = downward_closure(step1_outer)
    step1_sigma = np.sqrt(0.5/rho_per_step)*np.sqrt(len(step1_all))

    # Step 1: Measure all 1-way marginals involving target(s)
    for k in range(1, len(targets)+2):
        split = [cl for cl in step1_all if len(cl) == k]
        print()
        for cl in split:
            I = sparse.eye(domain.size(cl)) 
            Q1 = get_identity(cl, post_plausibility, domain) # get fine-granularity measurements
            Q2 = get_aggregate(cl, matrices, domain) @ (I - Q1) #get remaining aggregate measurements
            Q1 = Q1[Q1.getnnz(1)>0] # remove all-zero rows
            Q = sparse.vstack([Q1,Q2])
            Q.T = sparse.csr_matrix(Q.T) # a trick to improve efficiency of Private-PGM
            # Q has sensitivity 1 by construction
            print('Measuring %s, L2 sensitivity %.6f' % (cl, np.sqrt(Q.power(2).sum(axis=0).max())))
            #########################################
            ### This code uses the sensitive data ###
            #########################################
            mu = data.project(cl).datavector()
            y = Q @ mu + np.random.normal(loc=0, scale=step1_sigma, size=Q.shape[0])
            #########################################
            est = Q1.T @ y[:Q1.shape[0]]

            post_plausibility[cl] = Factor(domain.project(cl), est >= step1_sigma*threshold)
            matrices[cl] = Q
            measurements.append((Q, y, 1.0, cl))

    engine = FactoredInference(domain,log=True,iters=iters,warm_start=True)
    engine.estimate(measurements)

    # Step 2: select more marginals using an MST-style approach 
    step2_queries = select(data, engine.model, rho_per_step, targets)
   

    # step 3: measure those marginals
    step3_sigma = np.sqrt(len(step2_queries))*np.sqrt(0.5/rho_per_step) 
    for cl in step2_queries:
        I = sparse.eye(domain.size(cl)) 
        Q1 = get_identity(cl, post_plausibility, domain) # get fine-granularity measurements
        Q2 = get_aggregate(cl, matrices, domain) @ (I - Q1) #get remaining aggregate measurements
        Q1 = Q1[Q1.getnnz(1)>0] # remove all-zero rows
        Q = sparse.vstack([Q1,Q2])
        Q.T = sparse.csr_matrix(Q.T) # a trick to improve efficiency of Private-PGM
        # Q has sensitivity 1 by construction
        print('Measuring %s, L2 sensitivity %.6f' % (cl, np.sqrt(Q.power(2).sum(axis=0).max())))
        #########################################
        ### This code uses the sensitive data ###
        #########################################
        mu = data.project(cl).datavector()
        y = Q @ mu + np.random.normal(loc=0, scale=step3_sigma, size=Q.shape[0])
        #########################################

        measurements.append((Q, y, 1.0, cl)) 

    print('Post-processing with Private-PGM, will take some time...')
    model = engine.estimate(measurements)
    return model.synthetic_data()


if __name__ == '__main__':
    

    df = pd.read_csv('datasets/adult.zip')
    domain = Domain.fromdict(json.load(open('datasets/adult-domain.json','r')))
    data = Dataset(df, domain)
   
    synth = adagrid(data, 1.0, 1e-10, 5, targets=['income>50K']) #, iters=250)

#    from IPython import embed; embed()
