import {readFileSync} from 'node:fs';
import {prepareIndex} from './matching.mjs';
export const catalog=JSON.parse(readFileSync(new URL('../data/index.json',import.meta.url),'utf8'));
export const index=prepareIndex(catalog.vectors);
