# SparqlView - Code Review & Fixes

Forked from [dvcama/LodLive](https://github.com/dvcama/LodLive), currently unchanged from upstream apart from the fixes below.

Live demo: http://en.lodlive.it/
Example: http://en.lodlive.it/?http://fr.dbpedia.org/resource/France

## Completed Fixes

### Critical Security: Removed all eval() calls (lodlive.core.js)
30 instances of `eval()` were used to construct JavaScript objects from SPARQL response data. Any malicious data in a SPARQL response could execute arbitrary JavaScript in the user's browser (XSS/code injection). All replaced with safe direct object construction:
```js
// Before (vulnerable):
eval('uris.push({\'' + value['property']['value'] + '\':\'' + escape(value.object.value) + '\'})');

// After (safe):
var _o = {};
_o[value['property']['value']] = encodeURIComponent(value.object.value);
uris.push(_o);
```

### Bug Fix: Array comparison always false (lodlive.core.js:~2543)
`returnVal == []` always evaluates to `false` in JavaScript since arrays are compared by reference. This meant the `defaultValue` fallback in `getJsonValue()` never triggered. Fixed to `returnVal.length === 0`.

### Bug Fix: Undeclared `start` variable (lodlive.core.js)
The `start` variable used in ~22 debug timing blocks was never declared with `var`, creating an implicit global. Added `var start;` at closure scope.

### Bug Fix: doInverse initialized from wrong key (lodlive.profile-localhost-example.js)
Copy-paste bug: `$.jStorage.set('doInverse', $.jStorage.get('doAutoExpand', true))` was reading `doAutoExpand` instead of `doInverse`. Fixed.

### Bug Fix: Duplicate xmlns attribute (all 4 HTML files)
`xmlns="http://www.w3.org/1999/xhtml"` appeared twice in the `<html>` tag. Removed the duplicate.

### Bug Fix: Wrong lang attributes (app_en.html, app_fr.html)
The English page had `lang="it"` (fixed to `lang="en"`), the French page had `lang="it"` (fixed to `lang="fr"`).

### Removed: Google Analytics (all HTML files, stats.html, lodlive.core.js, profile files)
- Removed the legacy `ga.js` analytics script block from all 4 app HTML files
- Deleted `stats.html` (existed solely as a GA tracking iframe target)
- Removed the `doStats()` method and its call in `openDoc()`
- Removed `doStats` jStorage setting from both profile files

### Removed: Freebase API and exposed Google API key (lodlive.app.js)
Freebase was shut down by Google in 2015. Removed:
- The Freebase option from the simple search dropdown
- The entire Freebase branch from `findConcept()`, including the hardcoded Google API key
- DBpedia search remains as the only keyword search option

### Replaced: Google Maps with OpenStreetMap/Leaflet (all HTML files, lodlive.core.js)
Google Maps required an API key and the `sensor` parameter was deprecated. Replaced with Leaflet.js + OpenStreetMap tiles (no API key needed):
- Replaced `<script src="maps.google.com/...">` and `jquery.gmap3.js` with Leaflet 1.9.4 CDN in all 4 HTML files
- Deleted `js/jquery.gmap3.js`
- Rewrote map functionality:
  - `gmap3({action:'init'})` -> `L.map()` + OSM tile layer
  - `gmap3({action:'clear'})` -> iterate markers array + `removeLayer()`
  - `gmap3({action:'addMarker'})` -> `L.marker().addTo()` with popup
  - `gmap3({action:'autofit'})` -> `leafletMap.fitBounds()`

### jQuery 2.0.3 → 4.0.0 Migration (all HTML files, lodlive.app.js, lodlive.core.js, lodlive.utils.js, lodlive.custom-lines.js)
Updated jQuery from 2.0.3 to 4.0.0. Added jQuery Migrate 3.5.2 plugin as a compatibility bridge for third-party jQuery plugins that still use deprecated APIs internally (fancybox, slimScroll, jCanvas, doTimeout, ThreeDots, jsonp, jStorage). Changes in our own code:
- **`$.trim()` → native `.trim()`**: Replaced all 13 instances across 4 JS files
- **`.bind()`/`.unbind()` → `.on()`/`.off()`**: Replaced 4 instances in lodlive.app.js, 2 in lodlive.core.js
- **`.load()`/`.error()` event aliases → `.on('load', ...)`/`.on('error', ...)`**: Replaced 4 instances in lodlive.core.js
- **`.focus()` event alias → `.on('focus', ...)`**: Replaced 1 instance in lodlive.app.js
- **`$.support.canvas` → native `document.createElement('canvas').getContext`**: Feature detection in lodlive.app.js
- **HTTPS**: jQuery CDN URL updated from `http://` to `https://`
- **Local fallback**: Updated from `jquery-2.0.3.min.js` to `jquery-4.0.0.min.js`

### jQuery UI 1.9.2 → 1.14.1 (all HTML files, lodlive.core.js)
Only `.draggable()` is used from jQuery UI. Updated reference in all 4 HTML files. The `ui-draggable` class check in core.js was modernized from `attr("class").indexOf(...)` to `hasClass()`.

### Files Deleted
- `stats.html` - GA tracking only
- `js/jquery.gmap3.js` - Google Maps plugin, replaced by Leaflet

### Replaced escape()/unescape() with encodeURIComponent()/decodeURIComponent() (lodlive.core.js)
All ~50 instances of `escape()` and `unescape()` replaced atomically. These were used as an internal encode/decode layer for SPARQL result values. The 4 instances used for URL query parameter encoding (`findInverseSameAs`, `findSubject`) are now also correctly encoded with `encodeURIComponent()`.

### Moved debugOn inside closure (lodlive.core.js)
The `var debugOn = false;` declaration was in the global scope above the IIFE. Moved inside the closure to avoid polluting the global namespace.

### Fixed mixed HTTP/HTTPS (all HTML files, lodlive.app.js)
Upgraded all navigable `http://` URLs to `https://` across all 4 HTML files: lodlive.it site links, language switcher, social sharing (Twitter, Facebook), external links (W3C, YouTube, Cambridge Semantics, Creative Commons, opensource.org), and the blog link. Also fixed the DBpedia lookup URL in lodlive.app.js. RDF namespace URIs and SPARQL endpoint URLs in `<link property=...>` tags and profile.js were intentionally left as `http://` since they are semantic identifiers that must match what the endpoints serve.

### Modernized WebFont loader (all HTML files)
Replaced the protocol-sniffing pattern `('https:' == document.location.protocol ? 'https' : 'http') + '://...'` with a direct `'https://...'` URL. Also fixed `wf.async = 'true'` (string) to `wf.async = true` (boolean).

### Replaced `<link rel="image_src">` with `og:image` (all HTML files)
Removed the non-standard `<link rel="image_src">` tag from all 4 HTML files. The `<meta property="og:image">` tag (already present) was kept and updated to use `https://`. The Galician page's relative `./img/` path was replaced with the absolute `https://lodlive.it/img/` URL.

### Added ARIA attributes and keyboard navigation (all HTML files, lodlive.core.js, lodlive.app.js, profile files)
- Added `role="button"`, `tabindex="0"`, and `aria-label` to all interactive `<div>` elements that act as buttons: control panel (options, legend, help, maps, images, close), tool box actions (infoQ, center, newpage, expand, remove), paginators (#nextPage, #prevPage, pagePrev, pageNext), action boxes (contents, tools), submit buttons (inviaForm), and dropdown selects
- Added `role="checkbox"` and `aria-checked` to option list items, with state updates on toggle
- Added `role="toolbar"` to the tool box container
- Added `role="navigation" aria-label="Language selection"` to the language switcher
- Added `role="application" aria-label="SPARQL graph visualization"` to the `#aSpace` container
- Added `tabindex="0"` to the boxTemplate in both profile files, making graph nodes tabbable
- Added `role="button"` and `tabindex="0"` to dynamically created relatedBox and groupedRelatedBox elements
- Added a `makeKeyboardAccessible()` helper function that attaches Enter/Space keydown handlers to trigger click, applied to all the above elements
- Added keyboard Enter/Space handlers to the home page paginators in lodlive.app.js

### Replaced jStorage with native localStorage (all JS files, all HTML files)
Created `js/lodlive.store.js` — a thin wrapper around `localStorage` providing the same `get(key, default)`, `set(key, value)`, `deleteKey(key)`, and `index()` API as jStorage, with automatic JSON serialization. Replaced all `$.jStorage` calls with `lodliveStore` across 8 JS files (profile.js, core.js, app.js, utils.js, lang.js, profile-localhost-example.js) and inline scripts in all 4 HTML files. Replaced `jquery.jstorage.js` script tag with `lodlive.store.js`. User preferences (doInverse, doAutoExpand, etc.) persist across page loads via localStorage.

### Replaced slimScroll with CSS overflow (lodlive.core.js, lodlive.app.js, CSS files, all HTML files)
Removed the slimScroll jQuery plugin. In `lodlive.core.js`, replaced `.slimScroll({height})` with `.css({maxHeight, overflowY: 'auto'})` for the document info panel. In `lodlive.app.js`, replaced `.slimScroll()` + `.slimScrollDiv` wrapper manipulation with direct CSS styling on the selection list elements. Updated all `.slimScrollDiv` CSS selectors in `lodlive.app.css` to target `.selectionList` directly, and `#docInfo .slimScrollDiv` in `lodlive.core.css` to `#docInfo .docContents`. Changed `overflow: hidden` to `overflow-y: auto`. Added `class="docContents"` to the jContents element in core.js. Also fixes the `Unable to preventDefault inside passive event listener` console warning.

### Replaced doTimeout with native setTimeout (lodlive.core.js, lodlive.app.js, all HTML files)
Removed the doTimeout jQuery plugin. Three usage patterns replaced:
- `highlight()`: `object.doTimeout(speed, fn)` → `setTimeout(fn, speed)`
- Auto-expand (repeating pattern where `return true` re-triggers): replaced with recursive `setTimeout` via an `expandNext()` IIFE
- Staggered page navigation: `$.doTimeout(205 * a, fn)` → `setTimeout(fn, 205 * a)`

### Replaced ThreeDots with CSS line-clamp (lodlive.core.js, lodlive.core.css, all HTML files)
Removed the ThreeDots jQuery plugin. Replaced `.ThreeDots({max_rows: 3})` + `.threedots_ellipsis` DOM manipulation with adding an `ellipsis_clamp` CSS class. Added `.ellipsis_clamp` rule in `lodlive.core.css` using `-webkit-line-clamp: 3` (supported in all modern browsers). Replaced the previously commented-out `.ellipsis_text` CSS block.

### Added error logging to empty catch blocks (lodlive.core.js, lodlive.app.js)
Added `console.error(...)` with descriptive prefixes to all empty `catch` blocks: `processDraw` error handler, two `format` error handlers, and six `fromInverse.click()` error handlers in core.js. In app.js, replaced the `try { connection.abort(); } catch (e) {}` pattern with a cleaner `if (connection) { connection.abort(); }` null check.

### Removed commented-out code (lodlive.core.js, lodlive.app.js)
Removed ~40 fragments of commented-out code: old `circleChords` calls, `containerBox.append` alternatives, `alredyInserted` limit checks, unused `context.height/width` calls, `panel.show()`, `handle:'.boxTitle'` draggable option, `$(".tipsy").remove()` calls (5 instances), dead `try/catch` block with commented body, unreachable `console.debug` after `return`, old msgPanel positioning, `destBox` operations, `setBackgroundPosition` block, and scattered `console.debug` debug lines. Left descriptive Italian comments and section markers intact.

### Files Deleted
- `stats.html` - GA tracking only
- `js/jquery.gmap3.js` - Google Maps plugin, replaced by Leaflet
- `js/jquery.jstorage.js` - replaced by `lodlive.store.js`
- `js/jquery.slimScroll.min.js` - replaced by CSS overflow
- `js/jquery.doTimeout.js` - replaced by native `setTimeout`
- `js/jquery.ThreeDots.min.js` - replaced by CSS line-clamp

### Files Added
- `js/lodlive.store.js` - localStorage wrapper replacing jStorage

## Current Status

**jQuery 4.0.0 migration and plugin cleanup are complete.** Four unmaintained jQuery plugins (jStorage, slimScroll, doTimeout, ThreeDots) have been replaced with native alternatives. The app loads and functions correctly. jQuery Migrate 3.5.2 is still required for the remaining third-party plugins (Fancybox, jCanvas, JSONP).

Known cosmetic warnings in console:
- `JQMIGRATE: Migrate is installed` — expected, informational only
- `ERR_NAME_NOT_RESOLVED` / `ERR_CONNECTION_TIMED_OUT` for some SPARQL endpoints — pre-existing, external endpoints being unavailable

## Remaining Issues (Not Yet Fixed)

### Third-Party Plugin Replacements
These plugins still depend on the jQuery Migrate bridge. Replacing them would allow removing the migrate plugin:
- **jquery.jsonp** — replace with CORS + `fetch()` (largest change; the entire SPARQL communication layer uses JSONP via 11 `$.jsonp()` calls in core.js). Only worth doing if target SPARQL endpoints support CORS; otherwise a proxy server would be needed, changing the deployment model.
- **jQuery Fancybox** — old packed version; could replace with a modern lightbox. Low priority — it works, only matters for bundle size or mobile UX.
- **jQuery UI 1.14.1** — only `.draggable()` is used; a custom build would reduce file size. Marginal benefit.

### Code Quality (low priority)
These are real but not worth fixing unless actively developing features in the affected areas:
- **Custom MD5 implementation** in `lodlive.utils.js` (~230 lines) — works correctly; replacing with a library would be pure churn.
- **Inline styles everywhere** — massive refactor for cosmetic DX improvement; not worth it unless actively iterating on styling.
- **Deeply nested callbacks** — rewriting the async flow is high risk for zero user benefit; only makes sense if also rewriting the JSONP layer.
- **Italian comments** throughout core.js — the original developers were Italian; translating adds no value; delete or leave.

### Architecture (not recommended)
These would require rewriting the entire application for architectural purity with no user-visible benefit:
- **No build system** — no minification, bundling, or transpilation. Only worth adding if actively developing features.
- **No module system** — everything communicates via jQuery plugins, global functions, and localStorage. Only matters if multiple developers work on this concurrently.
- **Large monolithic file** — `lodlive.core.js` is ~3000 lines in a single jQuery plugin. Functional as-is.

