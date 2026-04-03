"""
FastAPI SPARQL server for SparqlView.

Serves the LodLive frontend and a read-only SPARQL 1.1 endpoint
backed by Turtle files loaded from the data/ folder.
"""

import glob
import io
import csv
import os
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

import rdflib
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"

# --- RDF Graph -----------------------------------------------------------

graph = rdflib.Dataset()


@asynccontextmanager
async def lifespan(app):
    load_data()
    yield

app = FastAPI(title="SparqlView", lifespan=lifespan)


def load_data():
    """Load all .ttl files from the data directory into the graph."""
    ttl_files = list(DATA_DIR.glob("*.ttl"))
    if not ttl_files:
        print("Warning: No .ttl files found in", DATA_DIR)
        return
    for ttl_file in ttl_files:
        print(f"Loading {ttl_file.name} ...")
        graph.parse(str(ttl_file), format="turtle")
    print(f"Loaded {len(graph)} triples from {len(ttl_files)} file(s).")


# --- Format negotiation --------------------------------------------------

# Map various format strings to (rdflib_format, content_type) tuples.
# SELECT/ASK results formats:
SELECT_FORMATS = {
    "application/sparql-results+json": ("json", "application/sparql-results+json"),
    "application/json":                ("json", "application/sparql-results+json"),
    "json":                            ("json", "application/sparql-results+json"),
    "application/sparql-results+xml":  ("xml", "application/sparql-results+xml"),
    "xml":                             ("xml", "application/sparql-results+xml"),
    "text/csv":                        ("csv", "text/csv"),
    "csv":                             ("csv", "text/csv"),
    "text/tab-separated-values":       ("tsv", "text/tab-separated-values"),
    "tsv":                             ("tsv", "text/tab-separated-values"),
}

# CONSTRUCT/DESCRIBE results formats:
GRAPH_FORMATS = {
    "application/rdf+xml":             ("xml", "application/rdf+xml"),
    "rdf/xml":                         ("xml", "application/rdf+xml"),
    "xml":                             ("xml", "application/rdf+xml"),
    "text/turtle":                     ("turtle", "text/turtle"),
    "turtle":                          ("turtle", "text/turtle"),
    "application/sparql-results+json": ("json-ld", "application/ld+json"),
    "application/json":                ("json-ld", "application/ld+json"),
    "json":                            ("json-ld", "application/ld+json"),
    "text/csv":                        ("turtle", "text/turtle"),
    "text/tab-separated-values":       ("turtle", "text/turtle"),
}


def negotiate_format(format_param: str | None, accept_header: str | None, is_graph: bool):
    """Determine output format from explicit parameter or Accept header."""
    lookup = GRAPH_FORMATS if is_graph else SELECT_FORMATS
    default = ("turtle", "text/turtle") if is_graph else ("json", "application/sparql-results+json")

    # Explicit format parameter takes priority
    if format_param:
        key = format_param.strip().lower()
        if key in lookup:
            return lookup[key]

    # Fall back to Accept header
    if accept_header:
        for part in accept_header.split(","):
            mime = part.split(";")[0].strip().lower()
            if mime in lookup:
                return lookup[mime]

    return default


def serialize_select_csv(results) -> str:
    """Serialize SELECT results to CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(results.vars)
    for row in results:
        writer.writerow([str(val) if val is not None else "" for val in row])
    return output.getvalue()


def serialize_select_tsv(results) -> str:
    """Serialize SELECT results to TSV."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t")
    writer.writerow(results.vars)
    for row in results:
        writer.writerow([str(val) if val is not None else "" for val in row])
    return output.getvalue()


def serialize_select_json(results) -> str:
    """Serialize SELECT results to SPARQL Results JSON."""
    import json

    vars_list = [str(v) for v in results.vars]
    bindings = []
    for row in results:
        binding = {}
        for i, var in enumerate(results.vars):
            val = row[i]
            if val is None:
                continue
            entry = {"value": str(val)}
            if isinstance(val, rdflib.URIRef):
                entry["type"] = "uri"
            elif isinstance(val, rdflib.BNode):
                entry["type"] = "bnode"
            elif isinstance(val, rdflib.Literal):
                entry["type"] = "literal"
                if val.language:
                    entry["xml:lang"] = str(val.language)
                if val.datatype:
                    entry["datatype"] = str(val.datatype)
            binding[str(var)] = entry
        bindings.append(binding)

    result = {
        "head": {"vars": vars_list},
        "results": {"bindings": bindings},
    }
    return json.dumps(result)


def serialize_select_xml(results) -> str:
    """Serialize SELECT results to SPARQL Results XML."""
    NS = "http://www.w3.org/2005/sparql-results#"
    sparql = Element("sparql", xmlns=NS)
    head = SubElement(sparql, "head")
    for v in results.vars:
        SubElement(head, "variable", name=str(v))
    results_el = SubElement(sparql, "results")
    for row in results:
        result_el = SubElement(results_el, "result")
        for i, var in enumerate(results.vars):
            val = row[i]
            if val is None:
                continue
            binding = SubElement(result_el, "binding", name=str(var))
            if isinstance(val, rdflib.URIRef):
                uri_el = SubElement(binding, "uri")
                uri_el.text = str(val)
            elif isinstance(val, rdflib.BNode):
                bnode_el = SubElement(binding, "bnode")
                bnode_el.text = str(val)
            elif isinstance(val, rdflib.Literal):
                lit_el = SubElement(binding, "literal")
                lit_el.text = str(val)
                if val.language:
                    lit_el.set("xml:lang", str(val.language))
                if val.datatype:
                    lit_el.set("datatype", str(val.datatype))
    return '<?xml version="1.0"?>\n' + tostring(sparql, encoding="unicode")


def serialize_ask_json(result: bool) -> str:
    """Serialize ASK result to JSON."""
    import json
    return json.dumps({"head": {}, "boolean": result})


def serialize_ask_xml(result: bool) -> str:
    """Serialize ASK result to XML."""
    NS = "http://www.w3.org/2005/sparql-results#"
    sparql = Element("sparql", xmlns=NS)
    SubElement(sparql, "head")
    boolean = SubElement(sparql, "boolean")
    boolean.text = "true" if result else "false"
    return '<?xml version="1.0"?>\n' + tostring(sparql, encoding="unicode")


# --- SPARQL Endpoint ------------------------------------------------------

@app.get("/sparql", response_class=Response)
async def sparql_endpoint(
    request: Request,
    query: str | None = Query(default=None),
    format: str | None = Query(default=None),
    output: str | None = Query(default=None),
    callback: str | None = Query(default=None),
    timeout: str | None = Query(default=None),
):
    """
    SPARQL 1.1 Query endpoint (GET only).
    Without a query parameter, serves the query editor page.
    """
    if not query:
        editor_html = (TEMPLATES_DIR / "sparql_editor.html").read_text(encoding="utf-8")
        return HTMLResponse(content=editor_html)

    # Determine requested format: explicit 'format' param, or 'output' param
    requested_format = format or output

    try:
        results = graph.query(query)
    except Exception as e:
        error_body = f"SPARQL query error: {e}"
        return Response(content=error_body, status_code=400, media_type="text/plain")

    accept_header = request.headers.get("accept")

    if results.type == "SELECT":
        fmt_key, content_type = negotiate_format(requested_format, accept_header, is_graph=False)
        if fmt_key == "json":
            body = serialize_select_json(results)
        elif fmt_key == "xml":
            body = serialize_select_xml(results)
        elif fmt_key == "csv":
            body = serialize_select_csv(results)
        elif fmt_key == "tsv":
            body = serialize_select_tsv(results)
        else:
            body = serialize_select_json(results)
            content_type = "application/sparql-results+json"

    elif results.type == "ASK":
        fmt_key, content_type = negotiate_format(requested_format, accept_header, is_graph=False)
        if fmt_key == "xml":
            body = serialize_ask_xml(results.askAnswer)
        else:
            body = serialize_ask_json(results.askAnswer)
            content_type = "application/sparql-results+json"

    elif results.type == "CONSTRUCT" or results.type == "DESCRIBE":
        fmt_key, content_type = negotiate_format(requested_format, accept_header, is_graph=True)
        result_graph = results.graph
        body = result_graph.serialize(format=fmt_key)

    else:
        return Response(content="Unsupported query type", status_code=400, media_type="text/plain")

    # JSONP support: wrap JSON response in callback if requested
    if callback and content_type in (
        "application/sparql-results+json",
        "application/ld+json",
    ):
        body = f"{callback}({body})"
        content_type = "application/javascript"

    return Response(content=body, media_type=content_type)


# --- Static files & default page ------------------------------------------

# Mount static directories
app.mount("/js", StaticFiles(directory=str(BASE_DIR / "js")), name="js")
app.mount("/css", StaticFiles(directory=str(BASE_DIR / "css")), name="css")
app.mount("/img", StaticFiles(directory=str(BASE_DIR / "img")), name="img")
app.mount("/foafPerson", StaticFiles(directory=str(BASE_DIR / "foafPerson")), name="foafPerson")


@app.get("/favicon.ico")
async def favicon():
    favicon_path = BASE_DIR / "favicon.ico"
    if not favicon_path.exists():
        favicon_path = BASE_DIR / "favicon.png"
    return FileResponse(str(favicon_path))


@app.get("/favicon.png")
async def favicon_png():
    return FileResponse(str(BASE_DIR / "favicon.png"))


@app.get("/{path:path}")
async def serve_root(path: str):
    """Serve app_en.html for the root path, or other root-level files."""
    if not path or path == "/" or path == "index.html":
        return FileResponse(str(BASE_DIR / "app_en.html"), media_type="text/html")

    # Serve other root-level HTML files (app_fr.html, etc.)
    file_path = BASE_DIR / path
    if file_path.exists() and file_path.is_file() and file_path.suffix in (".html", ".txt", ".png", ".ico"):
        return FileResponse(str(file_path))

    return Response(content="Not found", status_code=404, media_type="text/plain")


# --- Startup ---------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
