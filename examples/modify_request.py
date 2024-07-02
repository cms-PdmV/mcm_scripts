from datetime import datetime

from rest import McM

mcm = McM(id=McM.OIDC, dev=True)

# Example to edit a request parameter(-s) and save it back in McM
request_prepid_to_update = "B2G-Fall13-00001"
field_to_update = "notes"

# get a the dictionnary of a request
request = mcm.get("requests", request_prepid_to_update)
assert isinstance(
    request, dict
), f"Request {request_prepid_to_update} does not exist..."

print(
    'Request\'s "%s" field "%s" BEFORE update: %s'
    % (request_prepid_to_update, field_to_update, request[field_to_update])
)

# Modify what we want
request[field_to_update] = f"Hace a nice day! {datetime.now().isoformat()}"

# Push it back to McM
update_response = mcm.update("requests", request)
print("Update response: %s" % (update_response))

# Fetch the request again, after the update, to check whether the value changed
request2 = mcm.get("requests", request_prepid_to_update)
assert isinstance(request2, dict)
print(
    'Request\'s "%s" field "%s" AFTER update: %s'
    % (request_prepid_to_update, field_to_update, request2[field_to_update])
)
