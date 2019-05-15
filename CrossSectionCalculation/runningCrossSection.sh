#!/bin/bash

#Usage runningCrossSection.sh 'Name_of_MiniAOD_sample_one_wants_to_calculate_the_cross_section_for'
source /afs/cern.ch/user/p/pgunnell/public/getCookie.sh
python CrossSectionEvaluation.py $1
source script.sh
