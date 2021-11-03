import os
import re
import shutil
import glob
import time
import logging
logging.basicConfig(level=logging.INFO)

def qsub_mission(mission_name, shell_path, error_path, log_path, num_nodes=1, ppn=4, servername="zhang"):
    n_core = f'nodes={num_nodes}:ppn={ppn}'
    cmd = f'qsub -N {mission_name} -l {n_core} -q {servername} -e {error_path} -o {log_path} {shell_path}'
    logging.info(cmd)
    os.system(cmd)
    
def get_mission_number(servername="zhang"):
    cmd = f'qstat | grep {servername}'
    return_cmd = os.popen(cmd).readlines()
    return len(return_cmd)

def jobs_exists(job_name):
    cmd = f'qstat | grep {job_name}'
    return_cmd = os.popen(cmd).readlines()
    if len(return_cmd) == 0:
        return False
    else:
        return True

def new_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def gen_script(tem_bash_path, 
               tem_m_path,
               sub_path,
               cat_path,
               surf_file,
               atlas_path,
               atlas_key,
               gifti_path,
               simg_path,
               n_core):
    
    ## some variables
    out_path = new_folder(os.path.join(sub_path, "net"))
    # atlas_key = (os.path.split(atlas_path)[-1]).split(".")[1]
    
    surf_key = surf_file.split(".")[2]
    out_prefix = (surf_file.replace(".gii", "")).replace(".", "_")
    
    ## matlab
    with open(tem_m_path, "r") as f:
        m_lines = f.readlines()
    # replace variable
    m_lines = [re.sub("#{CATROOT}#", cat_path, i) for i in m_lines]
    m_lines = [re.sub("#{NCORE}#", str(n_core), i) for i in m_lines]
    m_lines = [re.sub("#{GIFTIROOT}#", gifti_path, i) for i in m_lines]
    m_lines = [re.sub("#{ATLASNAME}#", atlas_path, i) for i in m_lines]
    m_lines = [re.sub("#{FILENAME}#", os.path.join(sub_path, "anat", "surf", surf_file), i) for i in m_lines]
    new_m_lines = [re.sub("#{OUTPREFIX}#", os.path.join(out_path, f'{out_prefix}_{atlas_key}'), i) for i in m_lines]
    
    ## bash
    with open(tem_bash_path, "r") as f:
        bash_lines = f.readlines()
    # replace variable
    bash_lines = [re.sub("#{SUBPATH}#", sub_path, i) for i in bash_lines]
    bash_lines = [re.sub("#{CODEPATH}#", f"BuildStrucNet{surf_key}{atlas_key}", i) for i in bash_lines]
    bash_lines = [re.sub("#{OUTPREFIX}#", f'{out_prefix}_{atlas_key}', i) for i in bash_lines]
    new_bash_lines = [re.sub("#{SIMGPATH}#", simg_path, i) for i in bash_lines]
    
    
    # subject bash path
    code_root = os.path.abspath(os.path.join(sub_path, "code"))
    code_root = new_folder(code_root)
    
    m_path = os.path.join(code_root, f"BuildStrucNet{surf_key}{atlas_key}.m")
    with open(m_path, "w") as f:
        f.writelines(new_m_lines)
        
    bash_path = os.path.join(code_root, f"BuildStrucNet{surf_key}{atlas_key}.sh")
    with open(bash_path, "w") as f:
        f.writelines(new_bash_lines)
        
    return bash_path

if __name__ == "__main__":
    tem_bash_path = "c01_desc-BuildStrucNet.sh"
    tem_m_path = "c01_BuildStrucNet_surf.m"
    spm_path = "/usr/local/matlab/toolbox/spm12"
    cat_path = os.path.join(spm_path, "toolbox", "cat12")
    gifti_path = os.path.abspath("Resource/toolbox/gifti-master")
    
    root = "/brain/babri_in/sangf/Projects/S_task-StrucCovNet"
    der_root = os.path.abspath("Derivation/pipeline-cat")
    simg_path = os.path.abspath("Resource/envs/senv_matlab_r2020a.simg")
    atlas_path = os.path.abspath("Resource/atlas_surf/lh.BN_Atlas.annot")
    
    # atlas_key = (os.path.split(atlas_path)[-1]).split(".")[1]
    atlas_key = "bna"

    ## for all subjects
    mission_number_limit = 50
    q_name = "zhang"
    n_core = 4
    
    for i in glob.glob(os.path.join(der_root, 'sub-*')):
            
        sub_id = os.path.split(i)[-1]
        
        sub_path = new_folder(os.path.join(der_root, sub_id))
        code_path = new_folder(os.path.join(der_root, sub_id, "code"))
        net_path = new_folder(os.path.join(der_root, sub_id, "net"))
        log_path = new_folder(os.path.join(der_root, sub_id, "log"))
        
        # jsd and kld function
        # if not os.path.exists(os.path.join(sub_path, "KLD.m")):
        #     shutil.copy(os.path.join(root, "KLD.m"), os.path.join(sub_path, "KLD.m"))
        # if not os.path.exists(os.path.join(sub_path, "JSD.m")):
        #     shutil.copy(os.path.join(root, "JSD.m"), os.path.join(sub_path, "JSD.m"))
            
        ## in subject
        for s in glob.glob(os.path.join(i, "anat", "surf", "s15.mesh.thickness.resampled.sub-*.gii")):
            if re.search(f'\.[rl]h\.', s):
                continue
            surf_file = os.path.split(s)[-1]
            surf_key = surf_file.split(".")[2]
                                    
            logging.info(f"{sub_id}: {surf_key}, {atlas_key}")

            # limit the job number in query
            mission_count = get_mission_number(servername=q_name)
            while mission_count >= mission_number_limit:
                # sleep
                time.sleep(2)
                mission_count = get_mission_number(servername=q_name)
            
            if jobs_exists(f"{atlas_key}{surf_key[0:3]}{sub_id.replace('sub-', '')}") | \
                os.path.exists(os.path.join(sub_path, "log", f"BuildStrucNet{surf_key}{atlas_key}.finished")) | \
                os.path.exists(os.path.join(sub_path, "log", f"BuildStrucNet{surf_key}{atlas_key}.lock")):
                continue
                        
            shell_path = gen_script(
                tem_bash_path=tem_bash_path, 
                tem_m_path=tem_m_path,
                sub_path=sub_path,
                cat_path=cat_path,
                surf_file=surf_file,
                atlas_path=atlas_path,
                atlas_key=atlas_key,
                gifti_path=gifti_path,
                simg_path=simg_path,
                n_core=n_core)
            
            error_path = os.path.join(log_path, "error.log")
            with open(os.path.join(sub_path, "log", f"BuildStrucNet{surf_key}{atlas_key}.lock"), "w"):
                pass
            qsub_mission(f"{atlas_key}{surf_key[0:3]}{sub_id.replace('sub-', '')}", shell_path, error_path, log_path, ppn=n_core, servername=q_name)
            time.sleep(1)        
    