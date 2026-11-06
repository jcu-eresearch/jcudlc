
# JCU DLC - Web Interface

## Overview

This document describes the web front end of the JCU Digital Library Catalogue, a zero-dependency tool to display and filter a list of items.

For general info about the tool, visit the [JCU DLC main page](index.html). For information about preparing your data list, refer to the [JCU DLC Data Prep](dataprep.html) docs.


## Files

Displaying a JCUDLC on a web page requires four files on your web server, in addition to the web page itself.

**`jcudlc.js`** is the main JavaScript file that does the job of creating and managing the Catalogue. You never need to edit this file, it just needs to be loaded onto the page.

**`jcudlc-style.css`** is the CSS file that provides format to the elements within the Catalogue. You never need to edit this file, it just needs to be loaded onto the page.

**`jcudlc-data.json`** is your data, the list of all the items that the Catalogue will be searching and displaying. You prepare this file using the data-prep process documented elsewhere. The name of this data file can be anything you like, just set it in your config file.

**`jcudlc-config.json`** is your configuration. JCUDLC uses sensible defaults so that you will get some kind of reasonable result without having to change much in here, but you will probably want to tweak a few things, and how to do that is documented down below.


## Setup

Add a link to the CSS file inside your page's `<head>` tag. If you use icons, also add a link to the icon font.

```html
<head>
    ...
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" />
    <link rel="stylesheet" href="./jcudlc-style.css" />
    ...
</head>
```

Add an empty `div` tag somewhere in body of your page with an id of `jcudlc`, wherever you want your Catalogue to show up. When the javascript runs, it will build the Catalogue inside this div.

```html
<body>
    ...
    <div id="jcudlc"></div>
    ...
```

Add a link to the javascript just before your page's closing `body` tag.

```html
    ...
    <div id="jcudlc"></div>
    <script src="./jcudlc.js"></script>
</body>
```
That's all the page setup. You also need to make sure your files are in place, and then you're all set!


## Configuration

You use the configuration file to set up how you want the Catalogue to behave.

### Summary tables

These tables offer a brief summary of configuration keys. Further discussion of some of these settings is included below the tables.

#### Configuration summary table

| Config Key         | Default Value                       | Description |
| ------------------ | ----------------------------------- | ----------- |
| `project`          | *(no default)*                      | descriptive |
| `version`          | *(no default)*                      | JCU DLC's version |
| `copyright`        | *(no default)*                      | JCU DLC's copyright statement |
| `dataUrl`          | `./jcudlc-data.json`                | Where to find the data file containing Catalogue items |
| `titleFields`      | `['header', 'title', 'name']`, otherwise use the item's first field | Item fields to include as titles in the Header section |         
| `titleFormat`      | `'bold unlabelled'`                 | Format used for the `titleFields` |
| `subtitleFields`   | `['author', 'authors', 'editors']`  | Item fields to include as subtitles in the Header section |
| `subtitleFormat`   | `'italic'`                          | Format used for the `subtitleFields` |
| `quietFields`      | `[]`                                | Fields that should be hidden until revealed |
| `quietLabel`       | `'more >'`                          | The label the user can click to show the `quietFields` |
| `quietLabelFormat` | `'faded italic center'`             | Format used for the `quietLabel` |
| `maxResultCount`   | 100                                 | The maximum number of items to display |
| `noFilter`         | `[]`                                | Fields that should NOT appear in the filter sidebar |
| `hideValues`       | `[]`                                | Don't show item properties with any of these values |
| `separator`        | `'⧸'` (U+29F8, Big Solidus)         | Glyphs used to separate values for multi-valued fields |
| `separatorFormat`  | `'faded'`                           | Format used for the `separator` |
| `iconField`        | `icon`                              | The field to use as the icon "name" (see [Google Icons](https://fonts.google.com/icons)) |
| `iconUrl`          | `'url'`                             | The field containing a URL to load when the icon is clicked |
| `iconTooltip`      | `iconDescription`                   | The name of the field to use as the icon's tooltip |
| `hideFromSearch`   | `[]`                                | Fields to NOT include when the user is searching for text |
| `supportText`      | `''`                                | Text to show the user when there's an error |
| `aliases`          | Field names with spaces replacing underscores  | Field names to use instead of what's in your data file |


#### Styles summary table

Most of JCU DLC's colours and styling can be set in the config file, or in a CSS variable. The default colours set up a dark filter sidebar and a light result column using shades of grey; use these style settings when you want to match your brand colourings.

| Config Key                  <br>CSS Variable                | Default   | Description |
| ----------------------------------------------------------- | --------- | ----------- |
| `font`                      <br>`--jcudlc-font-family`      | `inherit` | Font family specification |
| `filterText`                <br>`--jcudlc-filter-text`      | `#ddd`    | Text colour for filters |
| `filterColumnBackground`    <br>`--jcudlc-filter-bg`        | `#111`    | Background for the filters column |
| `filterItemBackground`      <br>`--jcudlc-filter-item`      | `#222`    | Background for a single filter field |
| `filterActiveBackground`    <br>`--jcudlc-filter-active`    | `#333`    | Background for a hovered-over filter field |
| `filterHighlightBackground` <br>`--jcudlc-filter-highlight` | `#000`    | Background for a selected filter value |    
| `dataText`                  <br>`--jcudlc-data-text`        | `#111`    | Text colour for the results column |
| `dataColumnBackground`      <br>`--jcudlc-data-bg`          | `#bbb`    | Background for the results column |
| `dataItemBackground`        <br>`--jcudlc-data-item`        | `#fff`    | Background for a single result item |
| `dataActiveBackground`      <br>`--jcudlc-data-active`      | `#eee`    | Background for the icon |
| `dataHighlightBackground`   <br>`--jcudlc-data-highlight`   | `#ffffec` | Background for a hovered-over item |
| `interfaceText`             <br>`--jcudlc-interface-text`   | `dataText` | Text colour for general interface messages |
| `interfaceBackground`       <br>`--jcudlc-interface-bg`     | `dataActiveBackground` | Background for general interface messages |
| `alertInfoText`             <br>`--jcudlc-message-good-text`| `#037`    | Text colour for advice text |
| `alertInfoBackground`       <br>`--jcudlc-message-good-bg`  | `#ecf6ff` | Background for advice text |
| `alertErrorText`            <br>`--jcudlc-message-bad-text` | `#700`    | Text colour for alarm/error text |
| `alertErrorBackground`      <br>`--jcudlc-message-bad-bg`   | `#fee`    | Background for alarm/error text |


### Locate the data file

JCUDLC will load the item list from a JSON file you have prepared with JCU DLC's back end tools or in some other way. The config key `dataUrl` specifies that file. Starting with dot-slash `./` will make the path relative to the web page the Catalogue is running in. By default JCUDLC looks for a file called `jcudlc-data.json` at the same path as your HTML file.

### Display item properties

Within a single item result, there are three sections in which item properties can appear: a header, a main body, and a "quiet" section. Initially results are displayed with just the header section showing. Clicking or tapping the header opens or closes the main body. If there are fields allocated to the "quiet" section, then a link at the bottom of the main body will open or close the quiet section when clicked or tapped.

In the image below, you can see three items. These are all closed, so just their header sections are showing.
![three items showing just their headers](st-tng-closed.png)

The item header has two parts that JCUDLC refer to as the ***Title*** and the ***Subtitle***. You can place fields into these sections using configuration lists `titleFields` and `subtitleFields`. For the example shown, this is set to:

```json
"titleFields": ["title"],
"subtitleFields": ["years"],
```
That configuration will put the item's `title` field into the Title part, and the item's `years` field into the Subtitle part. If not specified in config, JCUDLC will default to `header`, `title`, and `name` as the title fields, so technically the example didn't need to specify `titleFields` at all.

Defaults for subtitle are `author`, `authors`, and `editors`.

The formatting of each part is also customisable using JCUDLC's [formatting keywords](#formatting-keywords). In the example here, we're using:
```json
"titleFormat": "bigger bold unlabelled",
"subtitleFormat": "italic",
```
The defaults for these are `bold unlabelled` for `titleFormat` and `italic` for `subtitleFormat`.

Once the user taps on the "The Next Generation" header, that item expands to display its fields. The image below shows The Next Generation item expanded. In this view, the fields in the header appear only in the header, and the item's main body contains all the remaining fields.
![three items, the central item expanded showing more detail](st-tng-open.png)

Sometimes you might have more obscure, less generally useful fields in your items. You can hide these under a link, so that the expanded item doesn't show these extra fields by default, but the user can see them if they need to by clicking a link. JCUDLC calls these ***quiet*** fields. The image below shows our example item after the user taps on "Additional details".
![three items, the central item expanded showing more detail](st-tng-detailed.png)

### Hide blank values

By default it will show all item proerties, but JCUDLC can hide item properties that seem blank. To get this behaviour, supply the `hideValues` config key, and provide a list of blank-ish values. For example, your data might use any of blank strings, `N/A`, and `NONE` for unspecified values, so set `hideValues` to `["", "N/A", "NONE"]` to omit any item proerties set to one of those values.


## Formatting keywords

JCUDLC uses keywords for convenient configuration of formatted text. You will supply a list of keywords as a single space-separated string, so if you want your titles to be bold and italic and be a bit smaller than normal text, you can set `titleFormat` to `"bold italic smaller"`.

Not all keywords are valid in all config keys; if a format doesn't make sense then it won't work &ndash; for example, `unlabelled` only applies to the format of item properties.

| Formatting keyword | Effect   |
| ------------------ | -------- |
| `bold`             | render text in a **bold** font  |
| `italic`           | render text in an *italic* font |
| `faded`            | render text in a greyed-out colour |
| `smaller`          | render text smaller than normal |
| `bigger`           | render text bigger than normal |
| `right`            | right-align text |
| `center`           | center-align text  |
| `unlabelled`       | don't show the property label |


## Limitations

> TODO not sure what to put here?