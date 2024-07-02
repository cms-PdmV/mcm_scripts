from json import dumps

from rest import McM

mcm = McM(id=McM.OIDC, dev=True)

# Script clones a request to another campaign.
# Define a list of modifications
# If member_of_campaign is different, it will clone to another campaign
modifications = {"extension": 1, "total_events": 101, "member_of_campaign": "Summer12"}

request_prepid_to_clone = "SUS-RunIIWinter15wmLHE-00040"

# Get a request object that we want to clone
request = mcm.get("requests", request_prepid_to_clone)
assert isinstance(request, dict)

# Make predefined modifications
for key in modifications:
    request[key] = modifications[key]

clone_answer = mcm.clone_request(request)
if clone_answer.get("results"):
    print("Clone PrepID: %s" % (clone_answer["prepid"]))
else:
    print("Something went wrong while cloning a request. %s" % (dumps(clone_answer)))
