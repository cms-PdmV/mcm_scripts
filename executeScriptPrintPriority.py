strings = ["GS","pLHE","wmLHEGS","DR","iniAOD","anoAOD"]
priority = [63000,70000,80000,85000,90000,91000,92000,93000,94000,95000,96000,97000,98000,99000,100000,105000,110000,111000]

for i in len(strings):

    for j in len(priority):
        python PrintPriority.py -f List -p j -s i

