// for an explanation why this file is needed, see: https://stackoverflow.com/questions/52556223/typescript-use-types-for-explicit-import
declare module "webextension-polyfill" {
    // Refers to the global `browser` and exports it as the default of `webextension-polyfill`.
    export default browser;
}