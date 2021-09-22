# nist-synthetic-data-2021
Source code for the second place submission in the third round of the 2021 NIST differential privacy temporal map challenge.

The contest-submission folder contains the code submitted during the contest, and only works on the contest dataset.  The files in this folder are sparsely commented.  The extensions folder contains a new mechanism, inspired by the solution to the competition, that works on arbitrary discrete datasets.  Several benchmark datasets can be found in the extensions/datasets folder.

## Quick start

This code depends on [Private-PGM](https://github.com/ryan112358/private-pgm).  After setting up Private-PGM, we can generate  synthetic data using the following command

```
$ cd extensions/
$ python adaptive_grid.py --dataset datasets/adult.zip --domain datasets/adult-domain.json --save adult-synthetic.csv

Measuring ('native-country',), L2 sensitivity 1.000000
Measuring ('fnlwgt',), L2 sensitivity 1.000000
Measuring ('relationship',), L2 sensitivity 1.000000
Measuring ('capital-gain',), L2 sensitivity 1.000000
Measuring ('hours-per-week',), L2 sensitivity 1.000000
Measuring ('income>50K',), L2 sensitivity 1.000000
Measuring ('workclass',), L2 sensitivity 1.000000
Measuring ('sex',), L2 sensitivity 1.000000
Measuring ('marital-status',), L2 sensitivity 1.000000
Measuring ('capital-loss',), L2 sensitivity 1.000000
Measuring ('occupation',), L2 sensitivity 1.000000
Measuring ('age',), L2 sensitivity 1.000000
Measuring ('race',), L2 sensitivity 1.000000
Measuring ('education-num',), L2 sensitivity 1.000000

Measuring ('age', 'marital-status'), L2 sensitivity 1.000000
Measuring ('age', 'hours-per-week'), L2 sensitivity 1.000000
Measuring ('age', 'fnlwgt'), L2 sensitivity 1.000000
Measuring ('age', 'capital-gain'), L2 sensitivity 1.000000
Measuring ('age', 'capital-loss'), L2 sensitivity 1.000000
Measuring ('workclass', 'occupation'), L2 sensitivity 1.000000
Measuring ('fnlwgt', 'native-country'), L2 sensitivity 1.000000
Measuring ('fnlwgt', 'race'), L2 sensitivity 1.000000
Measuring ('education-num', 'occupation'), L2 sensitivity 1.000000
Measuring ('marital-status', 'relationship'), L2 sensitivity 1.000000
Measuring ('occupation', 'hours-per-week'), L2 sensitivity 1.000000
Measuring ('relationship', 'sex'), L2 sensitivity 1.000000
Measuring ('relationship', 'income>50K'), L2 sensitivity 1.000000

Post-processing with Private-PGM, will take some time...
```

As we can see, the mechanism measured queries about all 1-way marginal, and a subset of 13 2-way marginals.  This produces an output adult-synthetic.csv that we can radily view

```
$ head adult-synthetic.csv
age,workclass,fnlwgt,education-num,marital-status,occupation,relationship,race,sex,capital-gain,capital-loss,hours-per-week,native-country,income>50K
14,0,13,3,3,9,3,0,0,0,0,46,0,0
10,0,11,12,2,4,5,0,0,0,0,39,0,0
15,0,9,9,0,3,2,0,1,0,45,19,0,0
8,1,16,8,2,10,1,0,0,0,0,19,20,0
32,0,4,13,0,8,2,0,1,0,0,59,0,1
4,0,21,9,2,9,1,0,1,0,0,39,0,0
21,0,10,8,1,7,3,0,0,0,0,39,0,0
31,8,12,6,0,14,2,0,1,0,0,34,0,1
21,0,14,13,1,4,3,3,0,0,0,44,0,0
```

## The target option

By default, this mechanism will try to preserve all 2-way marginals.  If one column has increased importance, we can specify that with the **targets** column.  With this option specified, we will instead try to preserve higher order marginals involving the targets.   If we specify ```--targets="income>50K"``` then the mechanism will try to preserve 3-way marginals involving the income column.  We can pass in multiple targets if desired, although scalability will suffer if the list is longer than a few columns. 

```
$ python adaptive_grid.py --dataset datasets/adult.zip --domain datasets/adult-domain.json --targets="income>50K" --save adult-synthetic-target.csv

Measuring ('income>50K',), L2 sensitivity 1.000000
Measuring ('marital-status',), L2 sensitivity 1.000000
Measuring ('age',), L2 sensitivity 1.000000
Measuring ('race',), L2 sensitivity 1.000000
Measuring ('capital-gain',), L2 sensitivity 1.000000
Measuring ('workclass',), L2 sensitivity 1.000000
Measuring ('relationship',), L2 sensitivity 1.000000
Measuring ('education-num',), L2 sensitivity 1.000000
Measuring ('hours-per-week',), L2 sensitivity 1.000000
Measuring ('capital-loss',), L2 sensitivity 1.000000
Measuring ('fnlwgt',), L2 sensitivity 1.000000
Measuring ('occupation',), L2 sensitivity 1.000000
Measuring ('native-country',), L2 sensitivity 1.000000
Measuring ('sex',), L2 sensitivity 1.000000

Measuring ('marital-status', 'income>50K'), L2 sensitivity 1.000000
Measuring ('race', 'income>50K'), L2 sensitivity 1.000000
Measuring ('relationship', 'income>50K'), L2 sensitivity 1.000000
Measuring ('capital-loss', 'income>50K'), L2 sensitivity 1.000000
Measuring ('fnlwgt', 'income>50K'), L2 sensitivity 1.000000
Measuring ('native-country', 'income>50K'), L2 sensitivity 1.000000
Measuring ('workclass', 'income>50K'), L2 sensitivity 1.000000
Measuring ('occupation', 'income>50K'), L2 sensitivity 1.000000
Measuring ('hours-per-week', 'income>50K'), L2 sensitivity 1.000000
Measuring ('age', 'income>50K'), L2 sensitivity 1.000000
Measuring ('education-num', 'income>50K'), L2 sensitivity 1.000000
Measuring ('capital-gain', 'income>50K'), L2 sensitivity 1.000000
Measuring ('sex', 'income>50K'), L2 sensitivity 1.000000

Measuring ('age', 'marital-status', 'income>50K'), L2 sensitivity 1.000000
Measuring ('age', 'hours-per-week', 'income>50K'), L2 sensitivity 1.000000
Measuring ('age', 'fnlwgt', 'income>50K'), L2 sensitivity 1.000000
Measuring ('age', 'native-country', 'income>50K'), L2 sensitivity 1.000000
Measuring ('age', 'capital-gain', 'income>50K'), L2 sensitivity 1.000000
Measuring ('age', 'capital-loss', 'income>50K'), L2 sensitivity 1.000000
Measuring ('age', 'race', 'income>50K'), L2 sensitivity 1.000000
Measuring ('workclass', 'occupation', 'income>50K'), L2 sensitivity 1.000000
Measuring ('education-num', 'occupation', 'income>50K'), L2 sensitivity 1.000000
Measuring ('marital-status', 'relationship', 'income>50K'), L2 sensitivity 1.000000
Measuring ('occupation', 'hours-per-week', 'income>50K'), L2 sensitivity 1.000000
Measuring ('relationship', 'sex', 'income>50K'), L2 sensitivity 1.000000

Post-processing with Private-PGM, will take some time...
```

As we can see, the mechanism now measured a lot more things about marginals involving the target column.  In particular, it measured all 2-way marginals involving income, and 12 3-way marginals involving income.

## Evaluating the synthetic data

We can score our synthetic data using the score.py function, as follows:

```
$ python score.py --synthetic adult-synthetic.csv
relationship    sex               0.003655
                income>50K        0.003675
marital-status  relationship      0.007279
sex             income>50K        0.008364
marital-status  income>50K        0.011373
                                    ...   
age             education-num     0.139112
occupation      relationship      0.151089
age             hours-per-week    0.157170
occupation      sex               0.159074
age             fnlwgt            0.207127
Length: 91, dtype: float64
Average Error:  0.05595402713661589
```

The error is calculated as an total variation distance between true and synthetic marginals, averaged over all 2-way marginals.  We can see both the breakdown (which marginals are estimated well and which are not), and the overall error.  We can also specify a list of targets, which modifies the evaluation criteria to include the target columns in all evalaution marginals.

```
$ python score.py --synthetic adult-synthetic-target.csv --targets "income>50K"
relationship    sex             income>50K    0.005139
marital-status  relationship    income>50K    0.011445
workclass       race            income>50K    0.024426
sex             capital-loss    income>50K    0.027927
marital-status  sex             income>50K    0.028029
                                                ...   
occupation      relationship    income>50K    0.140740
age             education-num   income>50K    0.151325
occupation      sex             income>50K    0.161418
age             hours-per-week  income>50K    0.163691
                fnlwgt          income>50K    0.174420
Length: 78, dtype: float64
Average Error:  0.06613134555274515
```

**NOTE**: By specifying targets in adaptive_grid.py, we can expect the synthetic data to score better when passing --targets to score.py.  If we score adult-synthetic.csv with the target option enabled, the score is 0.1038, almost 2X worse than the 0.0661 we achieved.


## Full configuration options

The default configuration options are shown below.  The defaults should work fine in most cases.  Interested users can try modifying them if desired.

```
$ cd extensions/
$ python adaptive_grid.py --help
usage: adaptive_grid.py [-h] [--dataset DATASET] [--domain DOMAIN] [--epsilon EPSILON]
                        [--delta DELTA] [--targets TARGETS [TARGETS ...]] [--pgm_iters PGM_ITERS]
                        [--warm_start WARM_START] [--metric {L1,L2}] [--threshold THRESHOLD]
                        [--split_strategy SPLIT_STRATEGY [SPLIT_STRATEGY ...]] [--save SAVE]

A generalization of the Adaptive Grid Mechanism that won 2nd place in the 2020 NIST temporal map
challenge

optional arguments:
  -h, --help            show this help message and exit
  --dataset DATASET     dataset to use (default: datasets/adult.zip)
  --domain DOMAIN       dataset to use (default: datasets/adult-domain.json)
  --epsilon EPSILON     privacy parameter (default: 1.0)
  --delta DELTA         privacy parameter (default: 1e-10)
  --targets TARGETS [TARGETS ...]
                        target columns to preserve (default: [])
  --pgm_iters PGM_ITERS
                        number of iterations (default: 2500)
  --warm_start WARM_START
                        warm start PGM (default: True)
  --metric {L1,L2}      loss function metric to use (default: L2)
  --threshold THRESHOLD
                        adagrid treshold parameter (default: 5.0)
  --split_strategy SPLIT_STRATEGY [SPLIT_STRATEGY ...]
                        budget split for 3 steps (default: [0.1, 0.1, 0.8])
  --save SAVE           path to save synthetic data (default: out.csv)

$ python score.py --help
usage: score.py [-h] [--dataset DATASET] [--domain DOMAIN]
                [--synthetic SYNTHETIC] [--targets TARGETS [TARGETS ...]]
                [--save SAVE]

A script to score the quality of synthetic data

optional arguments:
  -h, --help            show this help message and exit
  --dataset DATASET     dataset to use (default: datasets/adult.zip)
  --domain DOMAIN       domain of dataset (default: datasets/adult-
                        domain.json)
  --synthetic SYNTHETIC
                        synthetic dataset to use (default: out.csv)
  --targets TARGETS [TARGETS ...]
                        target columns to define evaluation criteria (default:
                        [])
  --save SAVE           path to save error report (default: error.csv)
```

