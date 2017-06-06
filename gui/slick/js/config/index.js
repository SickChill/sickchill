import {getMeta} from '../utils';

const defaults = {
    srRoot: getMeta('srRoot'),
    srDefaultPage: getMeta('srDefaultPage'),
    themeSpinner: getMeta('themeSpinner'),
    anonURL: getMeta('anonURL'),
    srPID: getMeta('srPID')
};

const config = {...defaults};

export default config;
