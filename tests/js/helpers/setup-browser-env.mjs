import {JSDOM} from 'jsdom';

const {window} = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = window;
globalThis.document = window.document;
