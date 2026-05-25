# webstore-dl-and-analysis

Chrome extension download and analysis framework developed for the master's thesis **"Investigating the prevalent risks with residual trust within browser extensions"** at **Chalmers University of Technology** (Samuel Bach, Albin Karlsson, 2024).

The project downloads Chrome extensions (`.crx`) and analyzes them for:

- URL extraction from JavaScript, HTML, JSON, and related source files
- Manifest URL and permission analysis
- DNS-based identification of expired or abandoned referenced domains
- RDAP registration data lookups
- Static JavaScript analysis via a Node.js/Esprima service
- Dynamic analysis via Selenium-driven Chrome automation

Results are written to a SQLite database, `thesis.db`.

## Architecture

- `search.py` — main entrypoint; discovers work, manages worker threads, and coordinates runs
- `analyze.py` — per-extension analysis pipeline
- `keywords_search.py` — extracts URLs and action patterns from extension source files
- `manifest.py` — parses `manifest.json` for permissions, host patterns, and URLs
- `domain_analysis.py` — DNS and RDAP analysis
- `static_analysis.py` — static JavaScript AST analysis
- `dynamic.py` — Selenium-based dynamic analysis
- `dynamic_standalone.py` — standalone runner for dynamic analysis
- `db.py` — thread-safe SQLite wrapper and schema management
- `globals.py` — shared configuration and runtime flags
- `helpers.py` — queueing, domain extraction, and persistence helpers
- `esprima.py` — wrapper for the Node.js Esprima service
- `copy-n.py` — utility for creating smaller test sets

## Analysis pipeline

For each extension, the framework performs the following high-level steps:

1. Extract the `.crx` archive
2. Scan source files for URLs and request-like actions
3. Parse the extension manifest
4. Optionally run static JavaScript analysis
5. Optionally run dynamic Selenium analysis
6. Resolve referenced domains with DNS and optionally RDAP
7. Persist results to SQLite

## Requirements

- Python 3.10+
- Node.js (for static analysis)
- Go (to build `zdns`)
- Chrome/Chromium and Xvfb (for dynamic analysis outside Docker)
- Python dependencies from `requirements.txt`
- `zdns` git submodule initialized and built

## Setup

```bash
git submodule update --init --recursive
pip install -r requirements.txt
cd node && npm install
cd ../zdns && go build
cd ..
```

## Usage

Main entrypoint:

```bash
python3 search.py [options] [path_to_extensions ...]
```

Example:

```bash
python3 search.py -t 4 --rdap --static ./extensions
```

### CLI options (`search.py`)

- `-t`, `--threads N` — number of worker threads (default: `1`, env: `NUM_THREADS`)
- `-a`, `--all` — analyze all versions of each extension (env: `RUN_ALL_VERSIONS`)
- `-e`, `--extension PATH` — analyze a single extension file
- `-s`, `--stfu` — disable the progress bar (env: `STFU_MODE`)
- `-R`, `--reset` — drop and recreate runtime tables/files (env: `DROP_TABLES`)
- `-r`, `--random` — randomize extension processing order (env: `RANDOM_EXTENSION_ORDER`)
- `-p`, `--pickle` — resume from the last saved queue state
- `--static` — enable static JavaScript analysis (env: `STATIC_ENABLE`)
- `--dynamic` — enable Selenium-based dynamic analysis (env: `DYNAMIC_ENABLE`)
- `--rdap` — enable RDAP domain registration lookup (env: `RDAP_ENABLE`)
- `--common-urls` — enable common URL frequency counting (env: `COMMON_URLS_ENABLE`)
- `--pretty` — pretty-print JSON output files (env: `PRETTY_OUTPUT`)
- `path_to_extensions` — one or more extension directories (default: `extensions/`)

### Standalone dynamic analysis

To run the dynamic analysis stage separately:

```bash
python3 dynamic_standalone.py -t 1
```

## Docker

A `docker-compose.yml` file is included for containerized execution. The Docker setup sets `IN_DOCKER=true` automatically.

```bash
docker compose up --build
```

The default compose service runs the search pipeline; `docker-entrypoint.sh` also supports the standalone dynamic runner.

## Environment variables

The framework is configured primarily through environment variables, with CLI flags available for the main runtime options.

| Variable | Purpose | Default |
| --- | --- | --- |
| `NUM_THREADS` | Number of worker threads | `1` |
| `RUN_ALL_VERSIONS` | Analyze every version of each extension | `False` |
| `DATE_FORMAT` | Timestamp format for generated files | `%Y-%m-%d_%H:%M:%S` |
| `STFU_MODE` | Disable progress output | `False` |
| `DROP_TABLES` | Reset runtime tables/files before execution | `False` |
| `DEFAULT_EXTENSIONS_PATH` | Default extension directory | `extensions/` |
| `NODE_PATH` | Path to the Node.js executable | `node` |
| `NODE_APP_PATH` | Path to the Esprima Node application | `./node/app.js` |
| `RANDOM_EXTENSION_ORDER` | Randomize processing order | `False` |
| `PICKLE_FILE` | Queue checkpoint file | `search.pkl` |
| `DISPLAY_PORT` | X display used for local dynamic analysis | `99` |
| `DNS_ENABLE` | Enable DNS analysis | `True` |
| `STATIC_ENABLE` | Enable static JavaScript analysis | `False` |
| `RDAP_ENABLE` | Enable RDAP lookup | `False` |
| `DYNAMIC_ENABLE` | Enable Selenium-based dynamic analysis | `False` |
| `COMMON_URLS_ENABLE` | Enable common URL aggregation | implementation-dependent |
| `PRETTY_OUTPUT` | Pretty-print JSON output files | implementation-dependent |
| `DYNAMIC_WAIT_TIME` | Wait time used during dynamic analysis | implementation-dependent |
| `GODADDY_API_KEY` | GoDaddy API key for availability workflows | unset |
| `GODADDY_API_SECRET` | GoDaddy API secret for availability workflows | unset |
| `IN_DOCKER` | Enables Docker-specific runtime behavior | unset / set by Docker |

## Output

### Database

Results are stored in `thesis.db`.

Main tables:

- `domain` — domains referenced by extensions and the source file where they were found
- `domain_meta` — DNS status, timestamps, and RDAP payloads
- `action` — request-like actions such as `fetch`, `get`, `post`, `href`, or `src`
- `common` — aggregated URL frequency counts
- `dynamic` — URLs observed during Selenium-driven execution

### Runtime artifacts

- `time.txt` — per-extension timing breakdown by analysis stage
- `failed.txt` — extensions that failed during processing
- `unknown-ext.txt` — unknown file extensions encountered during extraction/scanning

## Notes

- The database wrapper in `db.py` is designed for multi-threaded SQLite access.
- Static analysis requires the Node.js helper in `node/`.
- Dynamic analysis requires a working Chrome/Chromium + Selenium environment, or Docker/Selenium Grid.
