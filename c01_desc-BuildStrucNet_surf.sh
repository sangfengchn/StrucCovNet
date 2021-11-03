#! /bin/bash

echo 'Build Structural Covariance Network.'

SUBPATH='#{SUBPATH}#'
SIMGPATH='#{SIMGPATH}#'
CODEPATH='#{CODEPATH}#'
OUTPREFIX='#{OUTPREFIX}#'

cd ${SUBPATH}

if [ -f ${SUBPATH}/log/${CODEPATH}.lock ]
then
    cp ${SUBPATH}/code/${CODEPATH}.m ${SUBPATH}/${CODEPATH}.m
    singularity exec ${SIMGPATH} matlab -nosplash -nodesktop -nojvm -r ${CODEPATH}

    if [ -f ${SUBPATH}/net/${OUTPREFIX}.csv ]
    then
        mv ${SUBPATH}/log/${CODEPATH}.lock ${SUBPATH}/log/${CODEPATH}.finished
    else
        rm ${SUBPATH}/log/${CODEPATH}.lock
    fi
fi

echo 'Done.'