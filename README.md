# SparqlView

A self-contained RDF data explorer: load Turtle files, query them via a built-in SPARQL endpoint, and visually navigate the graph using LodLive.

## Overview

SparqlView bundles a Python FastAPI server with a modernised fork of [LodLive](https://github.com/dvcama/LodLive) to provide:

1. **SPARQL Endpoint** (`/sparql`) -- a read-only SPARQL 1.1 query service backed by `.ttl` (Turtle) files loaded from the `data/` folder at startup. Includes a browser-based query editor.
2. **Visual Graph Browser** (`/`) -- the LodLive interface, pre-configured to connect to the local SPARQL endpoint. Point-and-click navigation across subjects, predicates, and objects.

All data stays local. No external services are required to explore your own RDF datasets.

## Quick Start

```bash
pip install -r requirements.txt
python server.py
```

Open `http://localhost:8000` to browse the graph visually, or `http://localhost:8000/sparql` to write SPARQL queries directly.

## Adding Your Own Data

Place any number of `.ttl` files in the `data/` folder. All files are loaded into a single in-memory graph on startup. URIs in the sample data use the `http://localdata/` namespace, but any URIs will work.

The LodLive profile (`js/lodlive.profile.js`) is pre-configured to match `http://localdata/` URIs to the local endpoint. To browse resources with a different URI base, add a corresponding connection entry in the profile file.

## Project Structure

```
server.py                  Python FastAPI/uvicorn server (port 8000)
requirements.txt           Python dependencies (fastapi, uvicorn, rdflib)
data/
  sample.ttl               Sample RDF data (countries, cities, people, projects)
templates/
  sparql_editor.html       Browser-based SPARQL query editor
js/
  lodlive.profile.js       LodLive endpoint configuration (includes local SPARQL)
  lodlive.core.js          LodLive graph navigation engine
  lodlive.app.js           LodLive application bootstrap
  lodlive.store.js         localStorage wrapper (replaces jStorage)
  lodlive.lang.js          UI string translations
  lodlive.utils.js         Utility functions
  lodlive.custom-lines.js  Custom graph edge rendering
  ...                      jQuery, jQuery UI, Fancybox, jCanvas, JSONP plugin
css/                       LodLive stylesheets
img/                       LodLive sprites and icons
```

## SPARQL Endpoint

The `/sparql` endpoint supports SPARQL 1.1 queries via HTTP GET:

```
/sparql?query=SELECT+*+WHERE+{?s+?p+?o}+LIMIT+10
```

**Query types:** SELECT, ASK, CONSTRUCT, DESCRIBE

**Result formats** (via `format` query parameter or `Accept` header):

| Format | Content Type |
|--------|-------------|
| JSON (default) | `application/sparql-results+json` |
| XML | `application/sparql-results+xml` |
| CSV | `text/csv` |
| TSV | `text/tab-separated-values` |
| RDF/XML | `application/rdf+xml` (CONSTRUCT/DESCRIBE) |
| Turtle | `text/turtle` (CONSTRUCT/DESCRIBE) |

JSONP is supported via the `callback` query parameter, which is how LodLive communicates with the endpoint.

## Sample Data

The included `data/sample.ttl` contains interconnected resources for testing:

- **5 countries** (Ireland, France, Germany, Spain, Italy) with populations and `owl:sameAs` links to DBpedia
- **7 cities** (Dublin, Paris, Berlin, Cork, Galway, Madrid, Rome) with geo-coordinates, capital/located-in relations
- **3 organisations** headquartered in different cities
- **4 people** with employment and project involvement relations
- **3 projects** linking people, cities, and countries
- **Ontology classes and properties** under `http://localdata/ontology/`

## LodLive Fork

The LodLive frontend is forked from [dvcama/LodLive](https://github.com/dvcama/LodLive) with the following changes:

- **Security:** Removed all `eval()` calls (30 instances of XSS-vulnerable SPARQL response processing)
- **jQuery 2.0.3 to 4.0.0** with jQuery Migrate 3.5.2 as a compatibility bridge
- **jQuery UI 1.9.2 to 1.14.1**
- **Replaced Google Maps** with OpenStreetMap/Leaflet (no API key needed)
- **Replaced 4 unmaintained jQuery plugins** with native alternatives (jStorage, slimScroll, doTimeout, ThreeDots)
- **Removed** Google Analytics, Freebase API, and an exposed Google API key
- **Added** ARIA attributes and keyboard navigation for accessibility
- **Fixed** multiple bugs (array comparison, undeclared variables, wrong config keys, duplicate attributes, incorrect lang tags)
- **Replaced** deprecated `escape()`/`unescape()` with `encodeURIComponent()`/`decodeURIComponent()`

See [PROJECT.md](PROJECT.md) for detailed change notes.

## Credits

LodLive was created by Diego Valerio Camarda, Silvia Mazzini, and Alessandro Antonuccio.
Licensed under the [MIT License](https://www.opensource.org/licenses/mit-license.php).
