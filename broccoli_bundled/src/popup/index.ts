// importing jQuery and bootstrap
// if JQuery is used with this module syntax, it doesn't add itself to window
// but bootstrap expects window.jQuery, so we add it manually
import $ from "jquery";
(<any>window).jQuery = $;
import Popper from 'popper.js';
import "bootstrap";

import firebase from "firebase"
import firebaseui from "firebaseui"

// in Firefox the Webextension functionality is offered by "browser"
// in Chrome it's called "chrome"
// we use browser and add a polyfill to be cross-platform compatible
import browser from "webextension-polyfill"

// templating
import Mustache from 'mustache';
import * as assets from "./assets"

var active = true
var api_connected = false


// on page load we start the firebase UI flow
var ui: firebaseui.auth.AuthUI;
$(() => {

  // asynchronously load html templates
  assets.loadAssets().then(() => {

    // configure firebase
    var config = {
      apiKey: "AIzaSyAeF7vB6WAfdx7yhFW7uMGr4hconR_CcBI",
      authDomain: "broccoli-1537781957741.firebaseapp.com",
      databaseURL: "https://broccoli-1537781957741.firebaseio.com",
      projectId: "broccoli-1537781957741",
      storageBucket: "broccoli-1537781957741.appspot.com",
      messagingSenderId: "877182796275"
    };
    firebase.initializeApp(config);
    ui = new firebaseui.auth.AuthUI(firebase.auth())

    // sign-in flow
    firebase.auth().onAuthStateChanged(function (authUser) {
      if (authUser) {
        let context = { mail: firebase.auth().currentUser.email }
        let html = Mustache.render(assets.firebase_ui_container_html, context)
        $("#firebaseui-auth-container").html(html)

        // set up UI components
        $("#signout-button").click(() => {
          firebase.auth().signOut()
        })
        $("#options-button").click(() => {
          browser.runtime.openOptionsPage()
        })

        // toggle Broccoli active on and off
        // synchronize with storage state
        $("#toggle-active").click(function () {
          active = !active
          if (active) {
            $(this).removeClass('btn-danger').addClass('btn-success').text('Broccoli ON')
          }
          else {
            $(this).removeClass('btn-success').addClass('btn-danger').text('Broccoli OFF')
          }
          browser.storage.local.set({
            active: active
          })
        })
        browser.storage.onChanged.addListener((changes) => {
          if ('active' in changes) {
            active = changes['active'].newValue
            if (active) {
              $(this).removeClass('btn-danger').addClass('btn-success').text('Broccoli ON')
            }
            else {
              $(this).removeClass('btn-success').addClass('btn-danger').text('Broccoli OFF')
            }
          }
        })
        // initialize with the stored value
        browser.storage.local.get("active")
          .then((result) => {
            if (result) {
              active = result.active
              if (active) {
                $("#toggle-active").removeClass('btn-danger').addClass('btn-success').text('Broccoli ON')
              }
              else {
                $("#toggle-active").removeClass('btn-success').addClass('btn-danger').text('Broccoli OFF')
              }
            }
          }, (error) => { console.log(error) });

        // display user info
        $("#userRef").text(authUser.uid)

        // reconnect with python api
        // communication with background script is done via browser storage events
        $('#connect-to-api').click(() => {
          $('#connect-to-api').attr("disable", "true")
          browser.storage.local.set({
            api_connection_pending: true
          })
        })
        // when the reconnection is no longer pending, re-enable the button
        browser.storage.onChanged.addListener((changes) => {
          if ('api_connection_pending' in changes) {
            if (!changes['api_connection_pending'].newValue) {
              $('#connect-to-api').removeAttr("disable")
            }
          }
        })

        // display current connection state in #api_connected badge
        // initialize with the stored value
        browser.storage.local.get("api_connected")
          .then((result) => {
            if (result) {
              api_connected = result.api_connected
              if (api_connected) {
                $("#api-connected").removeClass('badge-secondary').addClass('badge-primary').text('API Connected')
              }
              else {
                $("#api-connected").removeClass('badge-primary').addClass('badge-secondary').text('Please start python backend')
              }
            }
          }, (error) => { console.log(error) });
        browser.storage.onChanged.addListener(function (changes, areaName) {
          console.log(changes)
          if ('api_connected' in changes) {
            api_connected = changes['api_connected'].newValue
            if (api_connected) {
              $("#api-connected").removeClass('badge-secondary').addClass('badge-primary').text('API Connected')
            }
            else {
              $("#api-connected").removeClass('badge-primary').addClass('badge-secondary').text('Please start python backend')
            }
          }
        })
      }
      else {
        var uiConfig = {
          callbacks: {
            signInSuccessWithAuthResult: function (authResult, redirectUrl) {
              // User successfully signed in.
              // Return type determines whether we continue the redirect automatically
              // or whether we leave that to developer to handle.

              //ui.start('#firebaseui-auth-container', uiConfig);
              return false;
            }
          },
          // Will use popup for IDP Providers sign-in flow instead of the default, redirect.
          signInFlow: 'popup',
          signInOptions: [
            firebase.auth.EmailAuthProvider.PROVIDER_ID
          ]
        };
        // remove other html
        $("#firebaseui-auth-container").empty()
        ui.start('#firebaseui-auth-container', uiConfig);
      }
    })
  })
})