# McM Scripts
Repository for using McM scripts and example scripts

### How to run this

#### Prerequisite

Create an isolated virtual environment using a Python version >= 3.9 via:

`python3.9 -m venv venv && source ./venv/bin/activate`

#### Development version

If you want to set up a development environment to contribute to this project:

Install `poetry` and the required dependencies.

`pip install poetry && poetry install`

Run the test suite via:
`poetry run pytest -s -vv`

> [!IMPORTANT]
> Make sure your execution environment has a valid Kerberos ticket to consume CERN services!

#### Build package

If you just want to use this package in your own project, install it via:

`pip install git+https://github.com/cms-PdmV/mcm_scripts.git`

Make sure to remove the `sys.path.append(...)` statements to avoid overloading old versions from AFS.

### Basic info
* Link to McM: https://cms-pdmv-prod.web.cern.ch/mcm/
* McM Rest API: https://cms-pdmv-prod.web.cern.ch/mcm/restapi
* Public APIs do not require SSO credentials. Index of public API: https://cms-pdmv-prod.web.cern.ch/mcm/public/restapi/

### SSO credentials
McM supports two authentication mechanisms: Session cookies and ID tokens

#### Session cookies
* Use [`auth-get-sso-cookie`](https://auth.docs.cern.ch/applications/command-line-tools/) command line tool to generate it:
    * `auth-get-sso-cookie --url https://cms-pdmv-dev.web.cern.ch/mcm/ -o dev-cookie.txt`
    * `auth-get-sso-cookie --url https://cms-pdmv-prod.web.cern.ch/mcm/ -o prod-cookie.txt`
* `auth-get-sso-cookie` is already available in lxplus nodes
* It expires after ~10 hours, so be sure to regenerate it
* Dev cookie is valid only for the development environment and the production cookie is valid only for the production environment
* This method doesn't work if 2FA is enabled. If you are using it, please use the following alternative instead of this package.

#### ID tokens
* Configure the McM SDK to request and send ID tokens to authenticate your actions. To achieve this, instantiate it like the following: `McM(id='oidc')`
* Instead of requesting a session cookie, this configuration will start an authentication flow using [Device Authorization Grant](https://auth0.com/docs/get-started/authentication-and-authorization-flow/device-authorization-flow) to request an ID token. Therefore, it requires
human intervention to complete the authentication flow using a browser.

If you want to know more details about how it works, check the code available in `rest.py` module and its unit tests `rest_test.py`

### Priority change
* If you want to use priority-changing scripts or do anything else related to cmsweb, you'll have to use voms-proxy:
    * `voms-proxy-init -voms cms`
    * `export X509_USER_PROXY=$(voms-proxy-info --path)`
