/*****************************************************************
<File Name>
  download.js

<Started>
  January 2011

<Author>
  Alex Hanson

<Purpose>
  Provides interactivity for the download page of the Custom
  Installer Builder.
*****************************************************************/


$(document).ready(function () {
  $('#download_private_keys').click(function () {
    addCheck(this);
    
    $('#public_keys').fadeIn(function () {
      $('#installers').fadeIn();
    });
  });
  
  $('#download_public_keys').click(function () {
    addCheck(this);
  });
});


function addCheck(button) {
  /*****************************************************************
  <Purpose>
    Adds class "checked" to  button (passed as argument) to display
    a lovely unicode check mark in front of the button text using
    the :before pseudo element
  <Arguments>
    button:
      A button DOM element.
  <Returns>
    None.
  *****************************************************************/
  $(button).addClass('checked');
}