"""
<Program Name>
  views.py

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  Provides Django views to serve requests related to the interactive frontend
  of the Custom Installer Builder. Most are intended to be called by an
  AJAX request.
"""

import os
import sys
import tempfile

# The reasons for wanting simplejson as json seem lost in time.
# Let's try our best to have some JSON support!
try:
  import simplejson as json
except ImportError:
  import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect, \
    FileResponse
from django.shortcuts import render

import custominstallerbuilder.common.constants as constants
import custominstallerbuilder.common.packager as packager
import custominstallerbuilder.common.validations as validations
from custominstallerbuilder.common.build_manager import BuildManager
from custominstallerbuilder.common.logging import log_exception





###############
## Constants ##
###############

DEFAULT_BUILD_STRING = json.dumps({
  'vessels': [{'percentage': 80, 'owner': None, 'users': []}],
  'users': [],
});





################
## Decorators ##
################

def require_post(function):
  """
  <Purpose>
    A decorator that forces requests handled by the given function to have POST
    data. Otherwise, redirects the user back to the main builder page.
  <Arguments>
    The function to be wrapped by the decorator.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    The wrapped function.
  """
  def wrapper(request, *args, **kwargs):
    if request.method == 'POST':
      return function(request, *args, **kwargs)
    else:
      return HttpResponseRedirect(reverse('builder'))
    
  return wrapper






######################
## Helper functions ##
######################

def TextResponse(message=''):
  return HttpResponse(message, content_type='text/plain')

def ErrorResponse(message=''):
  return HttpResponse(message, status=500, content_type='text/plain')





################
## AJAX views ##
################

def build_installers(request):
  """
  <Purpose>
    Uses the build data from the user's session to build the installers and
    cryptogrpahic key packages. Designed for AJAX use.

  <Arguments>
    request:
      A Django request.

  <Exceptions>
    None.

  <Side Effects>
    The created packages will be written to the appropriate location on disk.

  <Returns>
    A Django response with text indicating success or error.
  """
  
  if 'build_string' not in request.session:
    return ErrorReponse('No build data provided.')
    
  build_data = json.loads(request.session['build_string'])

  user_data = {}
    
  for user in build_data['users']:
    user_data[user['name']] = {'public_key': user['public_key']}
    
  try:
    manager = BuildManager(vessel_list=build_data['vessels'], user_data=user_data)
    build_results = manager.prepare()
  except validations.ValidationError as e:
    return ErrorResponse(e)
  except:
    log_exception(request)
    return ErrorResponse('Unknown error occured while trying to build the installers.')
  else:
    # Save the build results so that the download pages can access the information.
    build_id = build_results['build_id']
    
    if 'build_results' in request.session:
      request.session['build_results'][build_id] = build_results
      request.session.save()
    else:
      request.session['build_results'] = {build_id: build_results}
    
    return TextResponse(reverse('download-keys-page', kwargs={'build_id': manager.build_id}))




    
@require_post
def save_state(request):
  """
  <Purpose>
    Saves the current build state to the user's session. Designed for AJAX use.
  <Arguments>
    request:
      A Django request with build information in the POST data.
  <Exceptions>
    None.
  <Side Effects>
    User's session data is manipulated.
  <Returns>
    A Django response without any content.
  <Note>
    Uses the require_post decorator to enforce the presence of POST data.
  """
  if 'build_string' not in request.POST:
    return ErrorResponse('Unable to save configuration.')

  request.session['build_string'] = request.POST['build_string']

  return TextResponse()





def restore_state(request):
  """
  <Purpose>
    Retrieves the archives build state from the user's session. Designed for
    AJAX use.
  <Arguments>
    request:
      A Django request.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A Django response containing a JSON representation of the archived build.
    state.
  """
  if 'build_string' not in request.session:
    request.session['build_string'] = DEFAULT_BUILD_STRING
        
  return TextResponse(request.session['build_string'])





def reset_state(request):
  """
  <Purpose>
    Resets the build state in the user's session back to default. Designed for
    AJAX use.
  <Arguments>
    request:
      A Django request.
  <Exceptions>
    None.
  <Side Effects>
    User's session data is reset.
  <Returns>
    A Django response containing a JSON representation of the default state.
  """
  request.session['build_string'] = DEFAULT_BUILD_STRING
    
  return TextResponse(request.session['build_string'])





@require_post
def add_user(request):
  """
  <Purpose>
    Reponds to an HTML <form> submission to create a new user. Designed for use
    in a hidden <iframe>, due to browser limitations on file uploading.
  <Arguments>
    request:
      A Django request with user info in the POST data.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A Django response containing a JSON representation of the new user, or an
    error.
  """
  
  def ErrorResponse(message=''):
    return TextResponse(json.dumps({'error': message}))
    
  if 'name' not in request.POST:
    return ErrorResponse('User name not specified.')
        
  name = request.POST['name']
  public_key = None

  if 'public_key' in request.FILES:
    public_file = request.FILES['public_key']
    public_key = public_file.read().strip()
        
  try:
    validations.validate_username(name)
        
    if public_key is not None:
      validations.validate_public_key(public_key)
        
  except validations.ValidationError as e:
    return ErrorResponse(e)
  except:
    log_exception(request)
    return ErrorResponse('Unknown error occured while trying to add user.')
  else:
    return TextResponse(json.dumps({'user': {'name': name, 'public_key': public_key}}))





####################
## File downloads ##
####################

def download_installer(request, build_id, platform):
  """
  <Purpose>
    Initiates a download of an installer.
  <Arguments>
    request:
      A Django request.
    build_id:
      The build ID of the file to download.
    platform:
      The platform for which to build the installer.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A Django response which initiates a download through a redirect.
  """
  
  manager = BuildManager(build_id=build_id)

  # Invalid build IDs should results in an error.
  if not os.path.isdir(manager.get_build_directory()):
    raise Http404

  if not manager.installer_exists(platform):
    manager.package(platform)

  installer_url = manager.get_static_urls()[platform]
  return HttpResponseRedirect(installer_url)





def download_keys(request, build_id, key_type):
  """
  <Purpose>
    Initiates a download of a key bundle.
  <Arguments>
    request:
      A Django request.
    build_id:
      The build ID of the file to download.
    key_type:
      The type of key bundle to return ('public' or 'private').
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A Django response which initiates a download through a redirect.
  """
  
  manager = BuildManager(build_id=build_id)

  # Invalid build IDs should results in an error.
  if not os.path.isdir(manager.get_build_directory()):
    raise Http404

  key_filenames = packager.package_keys(request.session['build_results'][build_id]['users'])

  # Generally, it is undesirable to serve files directly through django, but
  # the key bundles should be very small and still download quickly.
  bundle_filename = key_filenames[key_type]
  # FileResponse is a subclass of StreamingHttpResponse optimized
  # for binary files requires  Django >1.8
  response = FileResponse(open(bundle_filename), content_type='application/zip')
  response['Content-Disposition'] = 'attachment; filename=' + os.path.split(bundle_filename)[1]
  response['Content-Length'] = os.path.getsize(bundle_filename)
  
  # The HTML form will not give access to the installers until the user has
  # downloaded the private keys.
  keys_downloaded = request.session['build_results'][build_id].get('keys_downloaded', dict())
  keys_downloaded[key_type] = True
  request.session['build_results'][build_id]['keys_downloaded'] = keys_downloaded
  request.session.save()

  return response





#####################
## Full-page views ##
#####################

def builder_page(request):
  """
  <Purpose>
    Renders the interactive builder page.
  <Arguments>
    request:
      A Django request.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A Django response.
  """
  return render(request, 'builder.html',
      {
        'step': 'build',
      })





def download_keys_page(request, build_id):
  """
  <Purpose>
    Renders the key package download page.
  <Arguments>
    request:
      A Django request.
    build_id:
      The build ID of the results to display.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A Django response.
  """
  
  keys = None
  has_private_keys = False
  keys_downloaded = dict()

  if 'build_results' in request.session:
    if build_id in request.session['build_results']:
      keys = request.session['build_results'][build_id]['users']
      keys_downloaded = request.session['build_results'][build_id].get('keys_downloaded', dict())
  
  if keys is None:
    url = reverse('download-installers-page', kwargs={'build_id': build_id})
    return HttpResponseRedirect(url)
      
  for user in keys:
    if 'private_key' in keys[user]:
      has_private_keys = True
      break

  return render(request, 'download_keys.html',
      {
        'build_id': build_id,
        'has_private_keys': has_private_keys,
        'keys_downloaded': keys_downloaded,
        'step': 'keys',
      })





def download_installers_page(request, build_id):
  """
  <Purpose>
    Renders the installer package download page.
    If the custom installer was built on the fastlane page in the same session
    we also display public and private key.

  <Arguments>
    request:
      A Django request.
    build_id:
      The build ID of the results to display.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A Django response.
  """

  manager = BuildManager(build_id=build_id)

  # Invalid build IDs should result in an error.
  if not os.path.isdir(manager.get_build_directory()):
    raise Http404
    
  # Compile the list of links of where to find the installers and cryptographic
  # key archives.
  installer_links = manager.get_urls()
    
  # If there is a query string appended to the current URL, we don't want that
  # in the share-this-URL box.
  share_url = request.build_absolute_uri().split('?')[0]
  
  # Only show the breadcrumbs if the user has built this installer himself.
  # Otherwise, we assume the user has shared this link with a friend.
  step = None
  user_built = False

  fast_lane = False
  keys_downloaded = {}

  if 'build_results' in request.session:
    if build_id in request.session['build_results']:
      step = 'installers'
      user_built = True

      # TODO: For better user feedback it would be nice to know if this is
      # a fast_lane_build even if we don't have the session.
      if 'fast_lane_build' in request.session['build_results'][build_id]:
        fast_lane = True

        # We don't show the breadcrumbs in a fast lane build
        step = False

        # But we show the keys, and whether they have already been downloaded
        # in this session.
        keys_downloaded = request.session['build_results'][build_id].get(
            'keys_downloaded', dict())


  return render(request, 'download_installers.html',
      {
        'build_id': build_id,
        'installers': installer_links,
        'share_url': share_url,
        'step': step,
        'user_built': user_built,
        'fast_lane': fast_lane,
        'keys_downloaded': keys_downloaded  # Use only if fast_lane is true
      })




def fastlane_page(request):
  """
  <Purpose>
    Creates a custom installer for a default user
    (one 80 per-cent vessel, one owner/user) if it does not yet exist in
    this session.  Then redirects to the download installer view, which shows
    the installer link as if were an interactive build and additionally the
    keys (but only if the installer was created in this session).

  <Arguments>
    request:
      A Django request.

  <Exceptions>
    None.

  <Side Effects>
    If new session
    - Creates and stores vesselinfo to appropriate location on disk
    - Stores generated key pair to session (memory)
  <Returns>
    A Django redirect to the download page.
  """

  try:
    existing_build_result = False

    # We have to check if the user already has a build result in his session
    # and make sure it's a fastlane build, i.e.
    # it does not collide with a build from the interactive CIB

    # Iterate over existing build_result dictionaries and pick the first
    # (should at most be one) that has "fast_lane_build" set true
    if 'build_results' in request.session.keys():
      for val in request.session['build_results'].values():
        if isinstance(val, dict) and val.get("fast_lane_build"):
          existing_build_result = val
          break
    else:
      # This dict will only be saved if the build succeeds
      # TODO: I wonder why I put this here and not under the else below, let's
      # revisit this later.
      request.session['build_results'] = {}


    if existing_build_result:
      # If we have an existing build, we just grab the id and forward to
      # the download page below
      build_id = existing_build_result.get('build_id')

    else:
      # If no build exists, we create a basic custom installer
      # i.e.: 1 owner, 1 vessel, no users
      users = {
        settings.FASTLANE_USER_NAME: {u'public_key': None}
        }
      vessels = [
        {
          u'owner': settings.FASTLANE_USER_NAME, 
          u'percentage': 80, 
          u'users': []
        }
      ]
      
      # Use build manager to create and store vesselinfo
      # and create cryptographic key pair (only stored in memory)
      manager = BuildManager(vessel_list=vessels, user_data=users)
      new_fastlane_build_results = manager.prepare()

      # These are needed in the HTML template to render the proper links
      # to the keys and installer
      build_id = manager.build_id

      # This prevents collision when using interactive CIB and fastlane CIB
      # in the same session
      # also hides breadcrumbs when serving shared (w/o key links) fastlane 
      # download page
      new_fastlane_build_results["fast_lane_build"] = True

      # download_installer and download_keys views get the build_results
      # from the session to serve the correct files
      request.session['build_results'][build_id] = new_fastlane_build_results
      request.session.save()

  except:
    log_exception(request)
    return ErrorResponse('Unknown error occured while' + \
                         ' trying to build the installers.')

  # Builds share_url by using view URLreversing and the request object
  return HttpResponseRedirect(reverse('download-installers-page',
      args=[build_id]))




def error_page(request):
  """
  <Purpose>
    Renders a generic error page.
  <Arguments>
    request:
      A Django request.
  <Exceptions>
    None.
  <Side Effects>
    None.
  <Returns>
    A Django response.
  """
  
  # Automatically choose the email address of the first administrator given
  # in the settings file.
  return render(request, 'error.html',
      {
        'email': settings.ADMINS[0][1]
      })
