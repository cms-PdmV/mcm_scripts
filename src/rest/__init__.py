"""
Exposes the REST client for the McM application
like the old structure used to do.
Just to keep backward compatibility.
"""

from rest.applications.base import BaseClient
from rest.applications.mcm.core import McM
from rest.applications.stats.core import Stats2
