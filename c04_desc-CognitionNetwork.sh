###
 # @Author: Feng Sang (sangfeng@mail.bnu.edu.cn)
 # @Date: 2021-10-08 17:23:36
 # @LastEditTime: 2021-10-10 10:53:00
 # @FilePath: /S_task-StrucCovNet/Analysis/a08_desc-dk40/c04_desc-CognitionNetwork.sh
### 
#!/bin/bash
export root={@root&}
export cog={@cog&}
export pre={@pre&}
export ncores={@ncores&}
export datapath={@datapath&}

source /opt/software/anaconda3/etc/profile.d/conda.sh
conda activate ~/env_py3
cd $root
python c04_desc-CognitionNetwork.py \
    --n-cores $ncores \
    --root $root \
    --cognition $cog \
    --prefix $pre \
    --data-path $datapath
echo 'done'