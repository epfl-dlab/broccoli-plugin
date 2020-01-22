import $ from "jquery";
(<any>window).jQuery = $;

import "popper.js"
import "bootstrap";
import Mustache from 'mustache';

import * as assets from "./assets"
import * as colors from "./colors"
import * as api from "./internal_api"
import {Popover} from "./popover"

import {settingsInterface} from '../defaults/settings'


export class PopupManager {
    popovers: Popover[];

    constructor(target_token_infos: api.ITargetTokenInfo[], settings:settingsInterface) {
        //let popovers = $('[data-toggle="popover"]').not(".processed")
        
        for(let i=0; i<target_token_infos.length; i++){
            let target_token_info = target_token_infos[i]
            let mark_id = target_token_info["mark_id"]
            let mark_html = $("#"+mark_id).not(".processed")
            let popover = new Popover(target_token_infos[i], mark_html[0], settings);
        }
    }
}