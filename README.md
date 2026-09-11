# JCU Digital Library Catalog

**Version 0.5.0** | copyright &copy; James Cook University

This is a _plain ol' javascript_ tool to filter items in a JSON list. James Cook University uses it to access and search digital collections.

---

## Setup

A minimum setup includes three `jcudlc` files and your JSON library data file.
- `jcudlc.js` is the core Javascript file that does most of the work
- `jcudlc-style.css` is the CSS required by jcudl
- `jcudlc-config.json` is the configuration for jcudl. Soon this will become optional but for now it's required
- `jcudlc-data.json` is the default name for your library data (you can set a different filename in `jcudlc-config.json`). It should contain an array of objects, each object is a catalogued item with whatever metadata your items need

#### Locate files

- put `jcudlc.js` and `jcudlc-style.css` anywhere on your web server. The examples here assume you have stored them right next to your page's html file, but you can adjust the path to suit.
- put `jcudlc-config.json` next to your page's html file. Unlike other files it MUST be stored in the same directory as your html
- put `jcudlc-data.json` alongside your html file, or if you are specifying a path in the config you can put it anywhere you like

#### Setup your web page

- include `jcudlc-style.css` and the icon font stylesheet in your page by adding these lines to your `<head>` tag. If you saved the CSS file alongside your page's html, that will look like this:
```html
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet" />
    <link rel="stylesheet" href="./jcudlc-style.css" />
```
- include `jcudlc.js` in your page by adding this tag at the bottom of your page, right before the closing `</body>` tag. If you saved the JS file alongside your page's html, that will look like this:
```html
    <script src="./jcudlc.js"></script>
```
- include a div (or other block element) in your page with an id of `jcudlc` wherever you want the catalog to show up:
```html
        <div id="jcudlc">
            <!-- jcudlc library catalog interface goes here -->
        </div>        
```

---

## Colours

Here are the CSS variable names for the colours used by JCUDLC, along with the defaults that will be used if you don't specify it yourself.

```
--jcudlc-filter-bg, #111
--jcudlc-filter-item, #222
--jcudlc-filter-active, #333
--jcudlc-filter-highlight, #000
--jcudlc-filter-text, #ddd

--jcudlc-data-bg, #bbb
--jcudlc-data-item, #fff
--jcudlc-data-active, #eee
--jcudlc-data-highlight, #ffffec
--jcudlc-data-text, #111

--jcudlc-message-bg, #ecf6ff
--jcudlc-message-good-text, #037
--jcudlc-message-bg, #fee
--jcudlc-message-bad-text, #700

--jcudlc-interface-bg, var(--filter-item)
--jcudlc-interface-text, var(--filter-text)
--jcudlc-interface-bg, var(--data-active)
--jcudlc-interface-text, var(--data-text)
```

---

## Running locally

You can open your HTML file right in your browser but pages loaded from a `file://` URL will come with browser security restrictions on loading JSON. So I recommend using a file server like `caddy`.

```bash
    brew install caddy
```

...or visit https://caddyserver.com/docs/install to find an installion method for your platform.

Once you have caddy installed, run

```bash
    caddy file-server
```

to run a http server at http://localhost, or run

```bash
    caddy file-server --domain localhost
```

to run a **https** server at https://localhost. The first time you run this you will have to become an admin and enter your password a couple of times so caddy can install certificates etc.

---

## Todo


#### Changes to data file

- [ ] URL to follow when icon clicked: requires a mod of Pauline's python

#### Higher Priority

- [ ] for each filter item, show result count for that additional filter
- [ ] mobile layout
- [ ] config: support font specification (default to inheriting it)
- [ ] version numbering
    - [x] write to console
    - [ ] check against config version, etc
- [ ] thorough documentation
- [ ] divider string (and format?) for displaying multi-value lists

#### Lower Priority

- [ ] _admin or some similar url thing to switch on "dev" mode
- [ ] URL looking fields (URL, Link, website, email) that renders a clicky-link
- [ ] range for numeric field
- [ ] sorting options
- [ ] open all / close all for the result discosure/show details
- [ ] optional icon feature; on hover, or something, offer a button to copy the link
- [ ] "show all" button to see every item instead of the cap
- [ ] make popup-on-icon-hover text a bit larger than browser default 

#### Complete

- [x] defaults for when no fields are nominated as headers
- [x] packaging: JS lib that you point at the div that should become the filterable list of items
    - [x] split into files
    - [x] specify a page element that everything gets built into
    - [x] trim up the CSS to let the page specify the font and maybe colours
        - [x] default to some nice grey and white, support colours in config
            - [x] allow config to specify CSS vars
- message display refactor
    - [x] existing "message" is too big for general display / list header / etc
    - [x] remember to include support info as specified by config
    - [x] background activity indicator
- [x] include support for icons (just get a name from the Material Icon font)
    - [x] if there's a URL, do that when the icon is clicked
    - [x] support icon field specifying the URL field for clicks ("url" or "URL" field is the default)
    - [x] support specifying a field to supply a pop-up tooltip for the icon ("iconTooltip" is the default)
- [x] "about" key in the config that names the tool, with version number
- [x] fix message backgrounds (good and bad messages don't have separately customisable bgs)
- [x] create config file
- [x] config: include json data filename
- [x] config: quiet field show/hide config
- [x] config: include contact info for support
- [x] config: colour config
- [x] filtering
    - [x] AND between all options
    - [x] show active filters
    - [x] active filters have an "x" button to remove that filter
    - [x] cap at 200 items (or config supplied cap)
    - [x] string search
        - [x] support string searches as a filter type
        - [x] allow "hide from search" fields config


