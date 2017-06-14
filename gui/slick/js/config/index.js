import getMeta from '../utils/get-meta';

const config = {};

config.srRoot = getMeta('srRoot');
config.srDefaultPage = getMeta('srDefaultPage');
config.themeSpinner = getMeta('themeSpinner');
config.anonURL = getMeta('anonURL');
config.srPID = getMeta('srPID');

export default config;
