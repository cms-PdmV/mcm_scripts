# NEEDS wmcontrol path to be added. run this before the script
# export PATH=/afs/cern.ch/cms/PPD/PdmV/tools/wmcontrol:${PATH}
# voms-proxy-init also has to be set

import subprocess

from rest import McM

mcm = McM(id=McM.OIDC, dev=True)


def run_wmpriority(workflow, priority):
    print("Changing priority of %s to %s" % (workflow, priority))
    p = subprocess.Popen(["wmpriority.py", workflow, priority], stdout=subprocess.PIPE)
    output = p.communicate()[0]
    print(output)


if __name__ == "__main__":
    list_of_requests = ["B2G-PhaseIISpr18AODMiniAOD-00054"]
    for prepid in list_of_requests:
        # Get request we want to change:
        request = mcm.get("requests", prepid, method="get")
        assert isinstance(request, dict)
        workflow: str = request["reqmgr_name"][-1]["name"]

        # Run actual priority change
        run_wmpriority(workflow, "85001")
