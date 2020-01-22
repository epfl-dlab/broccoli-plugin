// importing jQuery and bootstrap
// if JQuery is used with this module syntax, it doesn't add itself to window
import $ from "jquery";
(<any>window).jQuery = $;

// in Firefox the Webextension functionality is offered by "browser"
// in Chrome it's called "chrome"
// we use browser and add a polyfill to be cross-platform compatible
import browser from "webextension-polyfill"

// communication with the python backend
import * as external_api from "./background/external_api"

import {config} from './config'

import firebase from "firebase"
import { networkInterfaces } from "os";

// params for the settings
import { default_settings } from "./defaults/settings"
var settings = default_settings

var firebase_connected = false;
var api_connected = false;

// currently the background page only acts as a hub for communication
// it relays messages from the contentscript to firebase and events from firebase to the python backend
// this is set up here
var user: firebase.User;
var database: firebase.database.Database;
function setupFirebase() {

    console.log('connecting to Firebase')

    
    firebase.initializeApp(config);

    database = firebase.database()

    // Listen for auth state changes.
    firebase.auth().onAuthStateChanged(function (newUser) {
        console.log('User state change detected from the Background script of the Chrome Extension:', newUser);

        // logged in, process all existing data and set up callbacks for new items
        if (newUser != null) {

            console.log('logged in to Firebase')
            user = newUser;

            // store user agent in database
            database.ref("users/" + user.uid + "/user_agents").push(window.navigator)

            firebase_connected = true
            browser.storage.local.set({
                firebase_connected: firebase_connected
            })

        }

        // logged out, remove callbacks
        else if (user != undefined) {
            firebase_connected = false
            api_connected = false
            browser.storage.local.set({
                firebase_connected: firebase_connected,
                api_connected: api_connected
            })
            database.ref("users/" + user.uid + "/exposures").off()
            database.ref("users/" + user.uid + "/feedbacks").off()
            user = undefined;
        }
    });
}

function setupAPIConnection() {


    console.log('trying to connect to API')
    // try to access the python backend
    let resetPromise = external_api.reset()
    resetPromise.then(() => {

        console.log('connected to API')
        api_connected = true
        browser.storage.local.set({
            api_connected: api_connected
        })
        // connect to a database reference and route all items (new and existing) to our api
        function register(reference) {
            // get all existing data once
            database.ref(reference).once("value", function (snapshot) {

                let snapshotData = snapshot.val()

                // we will listen to new data at this reference
                let databaseRef = database.ref(reference).orderByKey();

                // if data exists at this reference already, process it
                // then change the reference to listen only to new data
                if (snapshotData) {
                    var keys = Object.keys(snapshot.val() || {});
                    var lastIdInSnapshot = keys[keys.length - 1]

                    var values = Object.values(snapshot.val() || {});
                    external_api.register(values)

                    // listen for all new elements at this reference
                    // also triggers for the lastIdInSnapshot
                    databaseRef = databaseRef.startAt(lastIdInSnapshot)
                }

                // process new data
                databaseRef.on("child_added", function (new_item) {
                    if (new_item.key === lastIdInSnapshot) { return; }
                    external_api.register([new_item.val()])
                })
            })
        }

        // for the exposures and feedbacks we use the register function,
        // this plays back all the existing data to our python server
        database.ref("users/" + user.uid + "/exposures").off()
        database.ref("users/" + user.uid + "/feedbacks").off()
        register("users/" + user.uid + "/exposures")
        register("users/" + user.uid + "/feedbacks")
        browser.storage.local.set({
            api_connection_pending: false
        })
    }).catch((error) => {
        browser.storage.local.set({
            api_connection_pending: false
        })
    })

}

function setupMessageRouting() {
    console.log('setting up message routing')

    // relay messages from the contentscript
    browser.runtime.onMessage.addListener(function (message, sender, sendResponse) {

        // the message will be forwarded to be stored in firebase,
        // in the database it is timestamped
        // all time values in our application come from this
        message.time = firebase.database.ServerValue.TIMESTAMP

        if ("exposure" in message) {
            if (user) {
                database.ref("users/" + user.uid + "/exposures").push(message);
            }
        }
        else if ("feedback" in message) {
            if (user) {
                database.ref("users/" + user.uid + "/feedbacks").push(message);
            }
        }
        else if ("paragraph" in message) {
            if (user && api_connected) {
                // add settings for processing to the message
                message.settings = settings
                let newRef = database.ref("users/" + user.uid + "/paragraphs").push();
                newRef.set(message)

                // once it is stored in the database, route it to python
                return newRef.once("value").then(snapshot => {

                    // we use the firebase key to uniquely identify this paragraph
                    // before sending it to the python API, we add this key to the message
                    let message = snapshot.val()
                    message.paragraph_key = snapshot.key

                    // the paragraph has been stored successfully in firebase,
                    // now we route it to the python server
                    return external_api.getTargetTokens(message).then(apiResponse => {
                        for (let targetToken of apiResponse.target_token_infos) {

                            // add the time and add to the database
                            // we don't wait for the acknowledgement here
                            targetToken.time = firebase.database.ServerValue.TIMESTAMP
                            targetToken.paragraph_key = snapshot.key
                            database.ref("users/" + user.uid + "/targetTokens").push(targetToken)
                        }
                        return apiResponse
                    })
                });
            }
        }

        return new Promise(function (resolve, reject) {
            resolve(null)
        })
    })
}

$(() => {
    console.log("background script running");

    // initialization: we are not connected to firebase and the python API
    browser.storage.local.set({
        firebase_connected: firebase_connected,
        api_connected: api_connected
    })

    // once we are connected to Firebase, we try to connect to the python backend
    // once we are connected to Python, we set up the message routing
    browser.storage.onChanged.addListener(function (changes, areaName) {
        if ('settings' in changes) {
            settings = changes['settings'].newValue
        }
        if ('firebase_connected' in changes) {
            firebase_connected = changes['firebase_connected'].newValue
            if (changes['firebase_connected'].newValue) {
                setupAPIConnection()
            }
        }
    })
    // this adds listeners to firebase login events
    // as soon as you are authenticated with firebase, we try to connect to python
    // if that fails, you have to connect via the popup
    setupFirebase()

    // the message routing relays runtime messages from the contentscripts to the python API
    // messages are only processed if you are logged into firebase (for feedbacks and exposures)
    // and if you are also logged into python (for target token calculation)
    setupMessageRouting()

    // uses the storage API to communicate with the popup and react if the user wants to reconnect to python backend
    browser.storage.onChanged.addListener((changes)=>{
        if('api_connection_pending' in changes){
            if(changes['api_connection_pending'].newValue){
                setupAPIConnection()
            }
        }
    })
})