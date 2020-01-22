// importing jQuery and bootstrap
// if JQuery is used with this module syntax, it doesn't add itself to window
// but bootstrap expects window.jQuery, so we add it manually
import $ from "jquery";
(<any>window).jQuery = $;
import Popper from 'popper.js';
import "bootstrap";

// in Firefox the Webextension functionality is offered by "browser"
// in Chrome it's called "chrome"
// we use browser and add a polyfill to be cross-platform compatible
import browser from "webextension-polyfill";

import {default_settings} from "./../defaults/settings"

var active = true
var settings = default_settings

$(() => {

    $('[data-toggle="tooltip"]').tooltip()

    // code from https://stackoverflow.com/questions/45007712/bootstrap-4-dropdown-with-search
    //Initialize with the list of symbols
    let tuples = [["Afrikaans", "af"],
    ["Arabic", "ar"],
    ["Bulgarian", "bg"],
    ["Bangla", "bn"],
    ["Bosnian (Latin)", "bs"],
    ["Catalan", "ca"],
    ["Chinese Simplified", "zh-Hans"],
    ["Czech", "cs"],
    ["Welsh", "cy"],
    ["Danish", "da"],
    ["German", "de"],
    ["Greek", "el"],
    ["Spanish", "es"],
    ["Estonian", "et"],
    ["Persian", "fa"],
    ["Finnish", "fi"],
    ["Faroese", "ht"],
    ["French", "fr"],
    ["Hebrew", "he"],
    ["Hindi", "hi"],
    ["Croatian", "hr"],
    ["Hungarian", "hu"],
    ["Indonesian", "id"],
    ["Icelandic", "is"],
    ["Italian", "it"],
    ["Japanese", "ja"],
    ["Korean", "ko"],
    ["Lithuanian", "lt"],
    ["Latvian", "lv"],
    ["Maltese", "mt"],
    ["Malay", "ms"],
    ["Hmong Daw", "mww"],
    ["Dutch", "nl"],
    ["Norwegian", "nb"],
    ["Polish", "pl"],
    ["Portuguese", "pt"],
    ["Romanian", "ro"],
    ["Russian", "ru"],
    ["Slovak", "sk"],
    ["Slovenian", "sl"],
    ["Serbian (Latin)", "sr-Latn"],
    ["Swedish", "sv"],
    ["Kiswahili", "sw"],
    ["Tamil", "ta"],
    ["Thai", "th"],
    ["Klingon", "tlh"],
    ["Turkish", "tr"],
    ["Ukrainian", "uk"],
    ["Urdu", "ur"],
    ["Vietnamese", "vi"]]

    let names = tuples.map(x => x[0])
    let lang_codes = tuples.map(x => x[1])

    //Find the input search box
    let search: HTMLInputElement = <HTMLInputElement>document.getElementById("searchLanguages")

    //Find every item inside the dropdown
    let items = document.getElementsByClassName("dropdown-item")
    function buildDropDown(values) {
        let contents = []
        for (let name of values) {
            contents.push('<input type="button" class="dropdown-item" type="button" value="' + name + '"/>')
        }
        $('#menuItems').append(contents.join(""))

        //Hide the row that shows no items were found
        $('#empty').hide()
    }

    //Capture the event when user types into the search box
    window.addEventListener('input', function () {
        filter(search.value.trim().toLowerCase())
    })

    //For every word entered by the user, check if the symbol starts with that word
    //If it does show the symbol, else hide it
    function filter(word) {
        let length = items.length
        let collection = []
        let hidden = 0
        for (let i = 0; i < length; i++) {
            if ((<HTMLButtonElement>items[i]).value.toLowerCase().startsWith(word)) {
                $(items[i]).show()
            }
            else {
                $(items[i]).hide()
                hidden++
            }
        }

        //If all items are hidden, show the empty view
        if (hidden === length) {
            $('#empty').show()
        }
        else {
            $('#empty').hide()
        }
    }


    var minDistSlider: HTMLInputElement = <HTMLInputElement>document.getElementById("minDistSlider");
    var sliderValue = document.getElementById("sliderValue");
    settings.min_dist = parseInt(minDistSlider.value)
    sliderValue.innerHTML = "" + settings.min_dist;

    // Update the current slider value (each time you drag the slider handle)
    minDistSlider.oninput = function () {
        settings.min_dist = parseInt(minDistSlider.value)
        sliderValue.innerHTML = "" + settings.min_dist;
    }

    //If the user clicks on any item, set the title of the button as the text of the item
    $('#menuItems').on('click', '.dropdown-item', function () {
        let language_name = $(this)[0].value
        let language_index = names.indexOf(language_name)
        settings.language_id = lang_codes[language_index]
        $('#dropdown_languages').text(language_name)
        $("#dropdown_languages").dropdown('toggle');
    })

    $('#save-button').click(() => {
        browser.storage.local.set({ settings: settings });
        browser.storage.local.set({ active: active });
    })
    $('#active-checkbox').click(function () {
        active = (<HTMLInputElement>this).checked
    })

    $('#riddle-checkbox').click(function () {
        settings.show_riddle = (<HTMLInputElement>this).checked
    })
    $('#stopwordfilter-checkbox').click(function () {
        settings.filter_stopwords = (<HTMLInputElement>this).checked
    })

    buildDropDown(names)

    browser.storage.local.get("settings")
        .then((result) => {
            console.log('options_ui startup got settings', result)
            if (result.settings) {
                result = result.settings
                if ("language_id" in result) {
                    settings.language_id = result.language_id
                    let language_index = lang_codes.indexOf(settings.language_id)
                    let language_name = names[language_index]
                    $('#dropdown_languages').text(language_name)
                }
                if ("min_dist" in result) {
                    settings.min_dist = result.min_dist
                    sliderValue.innerHTML = "" + settings.min_dist
                    minDistSlider.value = "" + settings.min_dist
                }
                if('show_riddle' in result){
                    settings.show_riddle = result.show_riddle
                    $('#riddle-checkbox').prop('checked', settings.show_riddle)
                }
            }
        }, (error) => { console.log(error) });

    browser.storage.local.get("active")
        .then((result) => {
            if (result) {
                active = result.active
                $("#active-checkbox").prop('checked', active)
            }
        }, (error) => { console.log(error) });

    browser.storage.onChanged.addListener(function (changes, areaName) {
        if ('active' in changes) {
            active = changes['active'].newValue
            $("#active-checkbox").prop('checked', active)
        }
    })
})