#!/bin/bash

source /afs/cern.ch/user/p/pgunnell/public/getCookie.sh
python CrossSectionEvaluation.py $1
source script.sh
