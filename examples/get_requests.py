from json import dumps

from rest import McM

mcm = McM(id=McM.OIDC, dev=True, debug=True)

# Example to get ALL requests which are members of a given campaign and are submitted
# It uses a generic search for specified columns: query='status=submitted'
# Queries can be combined: query='status=submitted&member_of_campaign=Summer12'
campaign_requests = mcm.get(
    "requests", query="member_of_campaign=Summer12&status=submitted"
)
assert isinstance(campaign_requests, list)
assert all([isinstance(el, dict)] for el in campaign_requests)

for request in campaign_requests:
    print(request["prepid"])

# Example to retrieve single request dictionary
# More methods are here:
# https://cms-pdmv-dev.web.cern.ch/mcm/restapi/requests/
single_request_prepid = "TOP-Summer12-00368"
single_request = mcm.get("requests", single_request_prepid, method="get")
print(
    'Single request "%s":\n%s'
    % (single_request_prepid, dumps(single_request, indent=4))
)

# Example of how to get multiple requests using a range
requests_query = """
    B2G-Fall13-00001
    B2G-Fall13-00005 -> B2G-Fall13-00015
"""
range_of_requests = mcm.get_range_of_requests(requests_query)
print("Found %s requests" % (len(range_of_requests)))
for request in range_of_requests:
    print(request["prepid"])
