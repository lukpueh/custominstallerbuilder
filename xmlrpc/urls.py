"""
<Program Name>
  urls.py

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  A standard Django URL configuration for the XML-RPC functionality of the
  Custom Installer Builder.
"""

from django.conf.urls import url
import custominstallerbuilder.xmlrpc.views as views



# Note: All URLs that have been delegated to these patterns have already
# matched the '^xmlrpc/' prefix. These patterns test against the rest of the
# URL string.

urlpatterns = [
  # Matches the empty string.
  #   Example: http://example.com/custominstallerbuilder/xmlrpc/
  url(r'^$', views.xmlrpc_handler, name='xmlrpc-handler'),
]
