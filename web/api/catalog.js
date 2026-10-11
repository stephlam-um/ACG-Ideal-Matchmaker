import {catalog} from '../lib/catalog.mjs';
export default {fetch(){return Response.json({count:catalog.characters.length,configured:Boolean(process.env.OPENAI_API_KEY),embeddingModel:catalog.model,characters:catalog.characters.slice(0,6)},{headers:{'Cache-Control':'no-store'}});}};
