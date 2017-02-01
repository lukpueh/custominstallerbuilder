"""
<Program Name>
  views.py

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  Provides an XML-RPC handler as a Django view.
  
  Note: The actual XML-RPC functions are stored elsewhere, in functions.py.

  This code was inspired by dispatcher.py in the earlier
  custom_installer_website, written by Justin Samuel. He, in turn, based his
  code off the example here: http://code.djangoproject.com/wiki/XML-RPC
"""

from SimpleXMLRPCServer import CGIXMLRPCRequestHandler

from django.http import HttpResponse
from django.shortcuts import render

from custominstallerbuilder.xmlrpc.functions import PublicFunctions


def xmlrpc_handler(request):
  """
  <Purpose>
    Sends XML-RPC requests to the PublicFunctions dispatcher. Displays a
    helpful page if viewed in a web browser.

  <Arguments>
    request:
      A Django HTTP request.

  <Exceptions>
    None.

  <Side Effects>
    The called XML-RPC functions may have side effects.

  <Returns>
    A Django HTTP response.
  """

  if request.method == 'GET':
    response = render(request, 'xmlrpc-info.html')

  elif request.method == 'POST':
    # Not all languages have the notion of "None".
    xmlrpc_handler = CGIXMLRPCRequestHandler(allow_none=False, encoding=None)
    xmlrpc_handler.register_instance(PublicFunctions())

    response = HttpResponse(content_type='application/xml')
    response.write(xmlrpc_handler._marshaled_dispatch(request.body))

  return response
