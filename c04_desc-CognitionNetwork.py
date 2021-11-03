'''
Author: Feng Sang (sangfeng@mail.bnu.edu.cn)
Date: 2021-10-08 16:56:25
LastEditTime: 2021-10-10 11:05:16
FilePath: /S_task-StrucCovNet/Analysis/a08_desc-dk40/c04_desc-CognitionNetwork.py
'''
import os
import re
import random
import argparse
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV, ShuffleSplit
from sklearn.metrics import mean_absolute_error
# parallel
from concurrent.futures import ProcessPoolExecutor
import warnings
import logging
logging.basicConfig(level=logging.DEBUG)
warnings.filterwarnings('ignore')

# a random model
def func_random_model(i, t_index, v_index, feature, label, cv, paras, n_jobs):
    logging.info(f'permutation {i}')
    shuffle_index = np.copy(t_index)
    random.shuffle(shuffle_index)
    perm_t_X = feature[t_index, :]
    perm_t_y = label[shuffle_index]
    val_t_X = feature[v_index, :]
    val_t_y = label[v_index]
    perm_model = GridSearchCV(
        ElasticNet(), 
        param_grid=paras,
        cv = cv, 
        scoring='neg_mean_absolute_error', 
        refit=True,
        n_jobs=n_jobs
    )
    perm_model.fit(perm_t_X, perm_t_y)
    perm_score = mean_absolute_error(val_t_y, perm_model.best_estimator_.predict(val_t_X))
    return perm_score

def func_get_data(path, cognition='Global', prefix='hub_n'):
    df = pd.read_csv(path, header=0, index_col=0)
    cols = list(filter(lambda x: re.match(f'^{prefix}', x) != None, df.columns))
    mcols = cols
    mcols.append(cognition)
    sub_df = df.loc[:, mcols]
    sub_df = sub_df.dropna(axis=0)
    X = sub_df.loc[:, cols].values
    y = sub_df.loc[:, cognition].values
    return X, y

def func_parse():
    parser = argparse.ArgumentParser(description='submit mission to psb.')
    parser.add_argument('--n-cores', action='store', type=int, default=12)
    parser.add_argument('--cognition', action='store', type=str, default='Memory')
    parser.add_argument('--prefix', action='store', type=str, default='hub_n')
    parser.add_argument('--root', action='store', type=str, default='/Users/fengsang/OneDrive - mail.bnu.edu.cn/Projects/S_task-StrucCovNet')
    parser.add_argument('--data-path', action='store', type=str, default='/Users/fengsang/OneDrive - mail.bnu.edu.cn/Projects/S_task-StrucCovNet/Derivation/ana-net/atl-dk40_node-68/subs_meas-elasticnet_net-js_thrd-bootstrap.csv')
    return parser.parse_args()


if __name__ == '__main__':
    # input data
    parser = func_parse()

    root = parser.root
    cognition = parser.cognition
    prefix = parser.prefix
    path = parser.data_path
    n_cores = parser.n_cores

    res_path = os.path.join(root, f'{cognition}_mes-{prefix}.csv')
    n_splits = 500
    n_cvs = 5
    n_jobs = n_cores
    n_perms = 2000

    # parameter of model
    paras = {
        'alpha': np.linspace(0, 10, num=21),
        'l1_ratio': np.linspace(0, 1, num=11)
    }

    res_df = pd.DataFrame({'Validate':[], 'Random': []})
    
    X, y = func_get_data(path, cognition, prefix)
    X = np.array(X, dtype=np.float64)
    y = np.array(y, dtype=np.float64)

    scaler = StandardScaler()
    scaler.fit(X)
    X = scaler.transform(X)
    shuffle_split = ShuffleSplit(n_splits=n_splits)
    for t_index, v_index in shuffle_split.split(X, y):
        # t_index, train and test dataset index
        # v_index, validate dataset index
        t_X = X[t_index, :]
        t_y = y[t_index]
        v_X = X[v_index, :]
        v_y = y[v_index]

        # grid search and train
        logging.debug('real model')
        model = GridSearchCV(
            ElasticNet(), 
            param_grid=paras,
            cv = n_cvs, 
            scoring='neg_mean_absolute_error', 
            refit=True,
            n_jobs=n_jobs
            )
        model.fit(t_X, t_y)
        # validation
        pre_y = model.best_estimator_.predict(v_X)
        val_score = mean_absolute_error(v_y, pre_y)
        logging.debug(f'cv score = {model.best_score_}, validation score = {val_score}')

        # random model
        logging.debug('random model')
        perm_scores = np.zeros(shape=[n_perms,])
        # with ProcessPoolExecutor(n_cores) as pool:
        #     futures = {pool.submit(func_random_model, i, t_index, v_index, X, y, n_cvs, paras, 0): i for i in range(n_perms)}
        #     for f in futures:
        #         perm_scores[futures[f]] = f.result()
        for i_perm in range(n_perms):
            logging.debug(f'permutation {i_perm}')
            shuffle_index = np.copy(t_index)
            random.shuffle(shuffle_index)
            perm_t_X = t_X
            perm_t_y = y[shuffle_index]
            perm_model = GridSearchCV(
                ElasticNet(), 
                param_grid=paras,
                cv = n_cvs, 
                scoring='neg_mean_absolute_error', 
                refit=True,
                n_jobs=n_jobs
            )
            perm_model.fit(perm_t_X, perm_t_y)
            perm_score = mean_absolute_error(v_y, perm_model.best_estimator_.predict(v_X))
            perm_scores[i_perm] = perm_score

        perm_score = np.mean(perm_scores)
        logging.debug(f'random score = {perm_score}')
        # append the result
        res_df = res_df.append({'Validate': val_score, 'Random': perm_score}, ignore_index=True)

    logging.debug('save result')
    res_df.to_csv(res_path, index=False)
