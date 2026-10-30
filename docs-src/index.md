
# JCU Digital Library Catalogue

The JCU Digital Library Catalogue is a nice way to let people look through your collection of items searchable, filterable list.

The Catalogue interface offers a sidebar of filterable dimensions, and a item list displaying the items that match your currently selected filters and searches.

The JCUDLC comes in two parts with separate documentation:

<center>

**[back end data preparation](./backend.html)**

**[front end](./frontend.html)**

</center>

----

# Tasks

> TODO remove this whole section

- [ ] for each filter item, show result count for that additional filter
- [ ] mobile layout
- [ ] fonts
    - [x] inherit from page
    - [ ] support font specification in config
- [ ] version numbering
    - [x] write to console
    - [ ] check against config version, etc
- [ ] thorough documentation
- [ ] divider string (and format?) for displaying multi-value lists
- [ ] config: support aliases `aliases: { "field_A": "Human Name A", ... }`

#### Lower Priority

- [ ] support no-config-just-defaults
- [ ] look up licencing for local hosting of the Material Symbols font
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

