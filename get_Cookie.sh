#!/bin/bash

echo "if that fails, it because a release had been setup first ..."
cern-get-sso-cookie -u https://cms-pdmv-dev.cern.ch/mcm/ -o ~/private/cookie.txt --krb
cern-get-sso-cookie -u https://cms-pdmv.cern.ch/mcm/ -o ~/private/prod-cookie.txt --krb
cern-get-sso-cookie -u https://cms-pdmv-int.cern.ch/mcm/ -o ~/private/int-cookie.txt --krb
cern-get-sso-cookie -u https://cms-pdmv-dev.cern.ch/mcm/ -o ~/private/dev-cookie.txt --krb
