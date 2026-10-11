# ACG Ideal Matchmaker · 理想型研究室

Describe the personality and interactions you like, then discover matching anime, comic and game characters. Traditional Chinese Streamlit interface, local BGE-M3 embeddings, and OpenAI trait extraction and interpretation.

## Hosted version on Vercel

The `web/` application is the deployment entrypoint: a responsive static frontend plus Node.js Vercel Functions. It uses OpenAI Responses for trait extraction/report generation and **text-embedding-3-small (1024 dimensions)** for matching, with a separately generated 50-character index. No local Ollama is required online. The original Streamlit/BGE-M3 application remains available for local use.

Set the Vercel project Root Directory to `web`, Framework Preset to Other, and leave Build Command and Output Directory unset. Set `OPENAI_API_KEY` as a sensitive server-side environment variable for the required environments; `OPENAI_MODEL` is optional (default `gpt-4.1-mini`). The key is never included in browser assets. Vercel account authentication protection remains enabled; visitors may need to sign in with project access. Each match uses your OpenAI API quota.

The hosted character index declares its model, dimensions and source catalog SHA-256. Regenerate it when changing the catalog or model:

```powershell
python preprocessing/generate_hosted_embeddings.py
node --test web/tests/*.test.mjs
```

Commit the generated `web/data/index.json` together with related catalog changes. Do not compare its vectors with `character_embeddings_ollama.npy`: these are different embedding spaces despite sharing 1024 dimensions. The offline evaluation below measures the local BGE-M3 retrieval implementation, not hosted OpenAI embedding quality.

Hosted API: `GET /api/catalog` returns catalog previews and readiness; `POST /api/match` accepts `{"description":"...","k":5}`. It validates inputs, bounds model output and request duration, computes stable cosine ranking against the cached index, and retains matches if narrative generation fails. Sessions and downloads live in the browser. Raw descriptions are sent to OpenAI with `store=false` for text requests and are not persisted by the application. This project does not implement a distributed rate limiter or per-user usage billing.

Recorded seed-42 random/Recall@5 results and their limitations are in [docs/evaluation/report.md](docs/evaluation/report.md). CI runs both the Python regression suite and the hosted Node.js suite.

## Quick start (local Streamlit)

Python 3.12 is recommended. The repository already contains character metadata and vectors; preprocessing is optional.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:OPENAI_API_KEY = "your-key"
ollama pull bge-m3
python -m streamlit run app.py
```

Ollama must be running locally; use `ollama serve` if its desktop service is not running. On macOS/Linux activate with `source .venv/bin/activate` and set the key with `export OPENAI_API_KEY="your-key"`. Copy `.env.example` to `.env` to configure a project-local key; `.env` is loaded automatically and excluded from Git and download packages. Environment variables take precedence. The default model is `gpt-4.1-mini`; set `OPENAI_MODEL` to change it. Restart the app after changing credentials.

Without a OpenAI key, the interface still opens and shows the character catalog. Matching requires both the key and Ollama. User descriptions and retrieved character traits are sent to OpenAI; embedding runs locally.

## Matching and scores

1. OpenAI extracts preference keywords.
2. Ollama embeds them using `bge-m3`, the same model used for the stored character vectors.
3. Cosine similarity ranks the catalog; scores are min–max scaled across the full catalog.
4. OpenAI interprets the candidates with their actual stored traits.

A score of 100 means the highest relative score in this search, **not a probability or perfect compatibility**. Scores cannot be compared across searches. If all candidates tie they receive 50. Invalid, non-finite and zero vectors are rejected.

Results stay available across interface reruns and can be downloaded as JSON. If report generation fails, the retrieved matches remain available. This is an exploratory recommendation tool; the dataset may contain incomplete or inaccurate character traits.

## Project structure

- `app.py`: page layout, cached catalog, form, session results and export.
- `pipeline.py`: file loading, lazy OpenAI client, retries, extraction, embeddings, validated ranking and report generation. Data paths resolve relative to the module.
- `preprocessing/`: optional data collection and vector generation scripts.
- `tests/`: ranking regressions and Streamlit startup checks, without remote API calls.
- `.github/workflows/checks.yml`: Python 3.12 tests and syntax checks.

## Development

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py pipeline.py preprocessing
```

Dependencies have compatible major-version bounds. API credentials and virtual environments are ignored by Git. Do not commit real keys.

## Optional preprocessing

The crawler additionally needs `selenium` and `webdriver-manager`, plus Chrome. Review its target pages and pacing before running it.

```powershell
python -m pip install -r requirements-preprocessing.txt
cd preprocessing
python crawl.py
python generate_embeddings.py
```

The generation script reads `character_database.json` from the current directory. Copy its generated `character_data_with_id.json` and `character_embeddings_ollama.npy` to the repository root **together**. Regenerate all vectors if changing the embedding model; dimensions alone do not guarantee compatibility.

## Troubleshooting

- Missing key: set `OPENAI_API_KEY` in the same terminal before launching, then restart the app.
- Ollama failure: verify its service is running and `bge-m3` is installed.
- OpenAI failure: check credentials, network and quota. The application retries transient requests.
- Invalid catalog or dimensions: regenerate metadata and vectors together.

## Attribution and license

Originally developed by LAM IOK HOI, University of Macau, for CISC3014. Code is MIT licensed; see `LICENSE`. Character traits originate from Moegirl Wiki. The code license does not establish rights to the source dataset; review source attribution and licensing before redistributing data.

## Retrieval engineering and evaluation

`retrieval.CosineIndex` validates, copies and normalizes the corpus once. The Streamlit application caches this index across reruns and users; each search normalizes only the query. It retains stable ordering and the existing relative score display. `pipeline.match_user` remains the uncached reference for equivalence checks. With just 50 candidates, a full stable sort is deliberately retained; approximate nearest-neighbor infrastructure would add complexity without a demonstrated need.

Successful trait extraction and report generation no longer sleep for one second each. Failure retries still use backoff. This removes two seconds of explicit waiting on the successful path, but remote model latency has not been benchmarked.

Run the offline evaluation:

```powershell
python evaluation.py --seed 42 --output evaluation-results
```

The evaluator writes `summary.json` and all 200 query cases to `cases.json`. It samples three existing traits per character, four queries for each of 50 characters, with the source character as the single relevant ID. It compares uniform random sampling without replacement against an exact-trait IDF retrieval baseline, then repeats random recommendation 1,000 times. It additionally checks sensitivity to one, two and three query traits.

**This is an optimistic synthetic source-retrieval proxy, not a real relevance benchmark.** Exact catalog tags appear in queries; other characters may also satisfy the preference but are not labelled relevant. A perfect proxy score must not be reported as semantic matching accuracy. Random expected Recall@5 is 5/50 = 10% here. For multiple relevant IDs, Recall@5 is the number of relevant retrieved IDs divided by the total relevant IDs, not just whether any hit exists.

Dense latency uses 2,000 seeded random vectors against the real corpus, 20 warmups and interleaved reference/index calls. It reports median and p95 and verifies top-5 IDs and scores. These queries measure speed and equivalence only. Index construction and all model/API calls are excluded.

To establish real quality improvement, collect independent natural-language queries and human-labelled relevant character IDs, embed those queries with the same BGE-M3 model, then compare dense-only, lexical-only and hybrid ranking on a held-out set. Do not reuse character embeddings as test query vectors: that would measure self-retrieval. Ollama was unavailable during this run, so dense Recall@5 and end-to-end latency remain unmeasured. The lexical baseline is not enabled as a replacement in the application.

OpenAI text calls use the Responses API with `store=False`, a 30-second request timeout and up to two SDK retries for transient errors. Authentication and quota errors are shown without response bodies or credentials. API details: https://developers.openai.com/api/reference/python/resources/responses/methods/create
