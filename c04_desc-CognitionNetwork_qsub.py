'''
Author: Feng Sang (sangfeng@mail.bnu.edu.cn)
Date: 2021-10-08 18:56:00
LastEditTime: 2021-10-10 10:40:57
FilePath: /S_task-StrucCovNet/Analysis/a08_desc-dk40/c04_desc-CognitionNetwork_qsub.py
'''
import os
import re
import time
import logging
logging.basicConfig(level=logging.INFO)

def func_submit(mission_name, shell_path, error_path, log_path, num_nodes=1, ppn=2, servername='zhang'):
    n_core = f'nodes={num_nodes}:ppn={ppn}'
    cmd = f'qsub -N {mission_name} -l {n_core} -q {servername} -e {error_path} -o {log_path} {shell_path}'
    logging.info(cmd)
    os.system(cmd)

def func_generate_script(template_path, root, cog, pre, n_cores, data_path, output):
    with open(template_path, 'r') as f:
        lines = f.readlines()
    # replace variable
    lines = [re.sub('{@root&}', root, i) for i in lines]
    lines = [re.sub('{@cog&}', cog, i) for i in lines]
    lines = [re.sub('{@ncores&}', str(n_cores), i) for i in lines]
    lines = [re.sub('{@datapath&}', data_path, i) for i in lines]
    new_lines = [re.sub('{@pre&}', pre, i) for i in lines]
    
    with open(output, 'w') as f:
        f.writelines(new_lines)
    return output

if __name__ == '__main__':
    root = '/brain/babri_in/sangf/Projects/S_task-StrucCovNet'
    template_path = 'c04_desc-CognitionNetwork.sh'
    n_cores = 12
    servername = 'zhang'

    cogs = ['Global', 'Memory', 'Attention', 'Execution', 'Language', 'Visualspatial']
    pres = ['deg', 'hub_n', 'nonhub_n', 'feedn_n', 'feedh_n']
    for cog in cogs:
        for pre in pres:
            logging.info(f"{cog}: {pre}")
            log_path = os.path.join(root, 'Derivation', 'Tmp', 'atl-dk40')
            if not os.path.exists(log_path):
                os.makedirs(log_path)
            shell_path = func_generate_script(
                template_path=os.path.abspath(template_path),
                root=root,
                cog=cog,
                pre=pre,
                n_cores=n_cores,
                data_path=os.path.join(root, 'Derivation', 'ana-net', 'atl-dk40_node-68', 'subs_meas-elasticnet_net-js_thrd-bootstrap.csv'),
                output=os.path.join(log_path, f'{cog}_{pre}.sh'))
            error_path = os.path.join(log_path, f'{cog}_{pre}_error.log')
            func_submit(f'{cog}-{pre}', shell_path, error_path, log_path, ppn=n_cores, servername=servername)
            time.sleep(1)    