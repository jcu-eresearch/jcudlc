// JCUDLC - JCU Digital Library Catalogue - v0.5.0
// copyright (c) James Cook University
// globals ============================================== 
const jcudlcVersion = '0.5.0'
console.log(`JCUDLC version ${jcudlcVersion}`)
// ------------------------------------------------------ 
const defaultHeaderFields = ['header', 'title', 'name']
const defaultMaxResultCount = 100
let config = {}
let allFields = []
let allItems = []
let activeFilters = {field: [], string: []}
let filteredItems = []
// init process ========================================= 
// find an element to put our catalog into
preparePage()

reportProgress('loading configuration...')
let configLoader = fetch('./jcudlc-config.json')
configLoader.then( (cfgResponse) => {
    reportProgress('parsing configuration...')
    let cfgParser = cfgResponse.json()
    cfgParser.then( (cfg) => {
        // here we have the config loaded from the JSON file
        config = cfg

        // now we have config, we can load the items
        let itemLoader = fetch(config?.dataUrl || './jcudlc-data.json')
        itemLoader.then( (itemResponse) => {
            reportProgress('parsing data...')
            let itemParser = itemResponse.json()
            itemParser.then( (items) => {
                reportProgress('preparing page...')
                // here we have the items loaded from the JSON file
                allItems = items
                applyConfig()
                buildFilters()
                applyFilters()
                buildResultList()
            }).catch( err => {
                reportError('Catalog could not parse the item list.')
            })
        }).catch( err => {
            reportError('Catalog could not load the item list.')
        })
        // done loading items

    }).catch( err => {
        reportError('Catalog could not parse configuration file.')
    })
}).catch( err => {
    reportError('Catalog could not load configuration file.')
})
// Utility functions ==================================== 
// compact function for making a DOM element
function makeNode(tag, className, ...content) {
    let node = document.createElement(tag)
    if (className) {
        node.className = className
    }
    node.append(...content)
    return node
}
// ------------------------------------------------------ 
function getFieldLabel(fieldId) {
    return config.fields[fieldId]?.label || fieldId.replaceAll('_', ' ')
}
// ------------------------------------------------------ 
function findUsefulField(item, fieldId) {
    const itemKeys = Object.keys(item)
    downcaseItemKeys = itemKeys.map( k => k.toLowerCase() )
    fieldIndex = downcaseItemKeys.indexOf(fieldId.toLowerCase())
    if (fieldIndex > -1) {
        if (item[itemKeys[fieldIndex]].toString().length > 0) {
            return itemKeys[fieldIndex]
        }
    }
    return false
}
// ------------------------------------------------------ 
// make a display field with a label and value 
// (unless it should not show the label, or 
// should be hidden entirely)
function makeField(fieldId, fieldValue, labelled, format) {

    fieldInfo = config.fields[fieldId]

    // if the display format says not to show it, return nothing
    if (fieldInfo?.display === 'hide') return ''

    // if the value is a hideValue, then return nothing
    if (config.hideValues.includes(fieldValue)) return ''

    let field
    let className = ['field', format].join(' ')
    if (labelled) {
        // label is the override from the config, or the fieldId with underscores replaced by spaces
        label = getFieldLabel(fieldId)
        let fieldLabel = makeNode('dt', 'fieldLabel', label)
        let fieldContent = makeNode('dd', 'fieldValue', fieldValue)
        field = makeNode('dl', className, fieldLabel, fieldContent)
    } else {
        field = makeNode('p', className, fieldValue)
    }
    return field
}
// ------------------------------------------------------ 
function reportStatus(msg) {
    reportMessage(msg)
}
// ------------------------------------------------------ 
function reportProgress(msg) {
    reportMessage(msg, 'status progress')
}
// ------------------------------------------------------ 
function reportError(err) {
    reportMessage(err, 'error', config.supportText ?? undefined)
}
// ------------------------------------------------------ 
function reportMessage(msg, style='status', additionalContent) {
    let res = document.querySelector('section.results')
    res.innerHTML = ''
    res.appendChild( prepMessage(msg, style, additionalContent) )
}
// ------------------------------------------------------ 
function prepMessage(msg, style='status', additionalContent) {
    const mainMsg = makeNode('div', 'msg', msg)
    const msgContainer = makeNode('div', 'message ' + style, mainMsg)
    if (additionalContent) {
        msgContainer.append(makeNode('div', 'msg smaller', additionalContent))
    }
    return msgContainer
}
// ------------------------------------------------------ 
// convenience function to add a filter to the 
// active filters list. If there's no field given,
// assume it's a string search filter
function addFilter(value, field) {
    if (field) {
        activeFilters.field.push({fieldName: field, value: value})
    } else {
        console.log('string search filter: ', value)
        activeFilters.string.push(value)
    }
}
// ------------------------------------------------------ 
// convenience function to remove a filter from
// the active filters list. If there's no field 
// given, assume it's a string search filter
function removeFilter(value, field) {
    if (field) {
        // take the filter out of the list
        activeFilters.field = activeFilters.field.filter(f => !(f.fieldName === field && f.value === value))
        // un-check the filter in the filter sidebar
        const filterCheckbox = document.querySelector(`section.filters input[data-field="${field}"][data-value="${value}"]`)
        if (filterCheckbox) {
            filterCheckbox.checked = false
        }
    } else {
        activeFilters.string = activeFilters.string.filter(f => f !== value)
    }
}
// apply config / defaults ============================== 
// 
function applyConfig() {
    const styles = new CSSStyleSheet()
    // if there are colours speficied in the config, write them into the page
    ;[
        ['filterText', '--jcudlc-filter-text'],
        ['filterColumnBackground', '--jcudlc-filter-bg'],
        ['filterItemBackground', '--jcudlc-filter-item'],
        ['filterActiveBackground', '--jcudlc-filter-active'],
        ['filterHighlightBackground', '--jcudlc-filter-highlight'],
    
        ['dataText', '--jcudlc-data-text'],
        ['dataColumnBackground', '--jcudlc-data-bg'],
        ['dataItemBackground', '--jcudlc-data-item'],
        ['dataActiveBackground', '--jcudlc-data-active'],
        ['dataHighlightBackground', '--jcudlc-data-highlight'],

        ['interfaceText', '--jcudlc-interface-text'],
        ['interfaceBackground', '--jcudlc-interface-bg'],

        ['alertInfoText', '--jcudlc-message-good-text'],
        ['alertInfoBackground', '--jcudlc-message-good-bg'],
        ['alertErrorText', '--jcudlc-message-bad-text'],
        ['alertErrorBackground', '--jcudlc-message-bad-bg'],
    ].forEach( ([configKey, cssVarName]) => {
        if (config[configKey]) {
            applyCssVar(styles, cssVarName, config[configKey])
        }
    })
    console.log('applying styles: ', styles.cssRules)
    document.adoptedStyleSheets.push(styles)
}
// ------------------------------------------------------ 
function applyCssVar(styleSheet, varName, varValue) {
    styleSheet.insertRule(`:root { ${varName}: ${varValue}; }`)
}
// construction of page elements ======================== 
// go through the fields we want to filter
// by, and make page elememnts for them
function preparePage() {
    // find the element to put our catalog into
    const wrapperElement = document.querySelector('#jcudlc')

    // if we have a catalog element, move our filters and results sections into it
    if (wrapperElement) {
        const filtersElement = makeNode('section', 'filters')
        const birthStatusElement = makeNode('div', 'message status', 'Initialising...')
        const resultsElement = makeNode('section', 'results', birthStatusElement)
        const catalogElement = makeNode('div', 'catalog', filtersElement, resultsElement)
        wrapperElement.append(catalogElement)
    } else {
        console.error('jcudl: JCU Digital Catalog could not find a #jcudlc element.')
    }
}
// ------------------------------------------------------ 
function buildFilters() {

    // get every field in any item
    allFields = []
    allItems.forEach( item => {
        for (var field in item) {
            if (!allFields.includes(field)) {
                allFields.push(field)
            }
        }
    })

    const filtersElement = document.querySelector('section.filters')
    filtersElement.innerHTML = ''

    const currentFilters = makeNode('div', 'currentFilters')
    filtersElement.append( currentFilters )

    filtersElement.append( makeNode('div', 'filtersHeader', 'Filter by') )

    filtersElement.append( buildTextFilter() )

    allFields.forEach( fieldId => {
        let filter = buildFilter(fieldId)
        if (filter) {
            filtersElement.append(filter)
        }
    })

    // dev mode: add links to our files, to make refreshes easier

    let configLink = makeNode('a', 'faded smaller', 'config')
    configLink.setAttribute('href', './jcudlc-config.json')
    configLink.setAttribute('target', '_blank')

    let jsLink = makeNode('a', 'faded smaller', 'script')
    jsLink.setAttribute('href', './jcudlc.js')
    jsLink.setAttribute('target', '_blank')

    let cssLink = makeNode('a', 'faded smaller', 'style')
    cssLink.setAttribute('href', './jcudlc-style.css')
    cssLink.setAttribute('target', '_blank')

    let devModeLinks = makeNode('div', 'devlinks center faded smaller', jsLink, " ", configLink, " ", cssLink)
    filtersElement.append(devModeLinks)
}


// ------------------------------------------------------ 
// add a string filter, then do the filtering, then display the results
function addTextFilter(text) {
    text = text.trim()

    // don't add blank strings
    if (text === '') return

    // don't add duplicates
    let dupe = activeFilters.string.some(s => s.toLowerCase() === text.toLowerCase())
    if (!dupe) {
        addFilter(text)
        applyFilters()
        buildResultList()
    }
}
// ------------------------------------------------------ 
// make page elements for the string matching filter
function buildTextFilter() {
    let textInput = makeNode('input', 'searchFilterText')
    textInput.setAttribute('type', 'text')
    textInput.setAttribute('placeholder', 'search...')
    let textButton = makeNode('button', 'searchNow clickable', '\u{1F50E}\uFE0E')

    // clicking the button will add the string to the filters
    textButton.addEventListener('click', (event) => { 
        addTextFilter(textInput.value)
        textInput.value = ''
    })
    // hitting enter will also add the string to the filters
    textInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            addTextFilter(textInput.value)
            textInput.value = ''
        }
    })

    return makeNode('div', 'filter text', textInput, textButton)
}
// ------------------------------------------------------ 
// make page elements for a single filter
function buildFilter(fieldId) {

    // if the config says not to filter by this, skip it
    if (config.noFilter.includes(fieldId)) return

    // if the config says not to filter on this field, skip it
    if (config.fields[fieldId]?.filter === 'none') return

    // get field's domain from all items list
    let domain = []

    allItems.forEach( item => {
        let fieldValue = item[fieldId]
        // sometimes fields are arrays of values, make anything
        // that's NOT an array into one
        if (!(fieldValue instanceof Array)) {
            fieldValue = [fieldValue]
        }
        fieldValue.forEach( val => {
            if (!domain.includes(val)) {
                domain.push(val)
            }
        })
    })
    // sorrt alphabetically but put "empty" values at the start of the list
    domain.sort( (a, b) => {
        // TODO: does this need to handle "both empty"?
        if (config.hideValues.includes(a)) return -1
        if (config.hideValues.includes(b)) return 1
        // otherwise sort alphabetically
        return a.localeCompare(b)
    })

    let filterLabel = makeNode('b', 'filterLabel', getFieldLabel(fieldId))
    let filterToggle = makeNode('button', 'filterToggle clickable')
    filterToggle.addEventListener('click', (event) => {
        // when the toggle is clicked, add or remove 
        // the "closed" class on the parent filter
        event.target.closest('.filter').classList.toggle('closed')

    }) 
    let filterHead = makeNode('div', 'filterHead', filterLabel, filterToggle)

    let checkboxList = domain.map( domItem => buildCheckboxItem(domItem, fieldId))
    let filterList = makeNode('div', 'filterList', ...checkboxList)

    let filterElement = makeNode('div', 'filter closed', filterHead, filterList)

    return filterElement
}
// ------------------------------------------------------ 
// make a checkbox item for one possible
// value for a given field's filter
function buildCheckboxItem(value, field) {
    let cb = makeNode('input')
    cb.setAttribute('type', 'checkbox')
    cb.setAttribute('data-field', field)
    cb.setAttribute('data-value', value)

    cb.addEventListener('change', (event) => {
        if (event.target.checked) {
            addFilter(value, field)
        } else {
            removeFilter(value, field)
        }
        applyFilters()
        buildResultList()
    })

    let label = makeNode('label', '', cb, value)
    let item = makeNode('div', 'filterItem', label)
    return item
}
// ------------------------------------------------------ 
// make page elements for the active filters
function buildCurrentFiltersDisplay() {

    let currentFiltersElement = makeNode('div', 'currentFilters')

    let hasFilters = activeFilters.field.length > 0 || activeFilters.string.length > 0
    if (hasFilters) {
        currentFiltersElement.append( makeNode('span', 'filtersLabel', 'Current filters:') )
    }

    activeFilters.string.forEach( filterString => {
        let filterLabel = 'text'
        let filterPill = makeNode('span', 'filterPill', `\u275d\u2009${filterString}\u2009\u275e`)
        let removeButton = makeNode('button', 'removeFilter clickable', '\u00d7') // \u00d7 is a multiplication sign
        removeButton.addEventListener('click', (event) => {
            removeFilter(filterString)
            applyFilters()
            buildResultList()
        })
        filterPill.append(removeButton)
        currentFiltersElement.append(filterPill)
    })

    activeFilters.field.forEach( f => {
        let filterLabel = getFieldLabel(f.fieldName)
        let filterValue = f.value
        let filterPill = makeNode('span', 'filterPill', `${filterLabel}: ${filterValue}`)
        let removeButton = makeNode('button', 'removeFilter clickable', '\u00d7') // \u00d7 is a multiplication sign
        removeButton.addEventListener('click', (event) => {
            removeFilter(filterValue, f.fieldName)
            applyFilters()
            buildResultList()
        })
        filterPill.append(removeButton)
        currentFiltersElement.append(filterPill)
    })
    return currentFiltersElement

}
// ------------------------------------------------------ 
// filter the list of all items by whatever is
// selected in the filter list
function applyFilters() {

    filteredItems = allItems

    console.log(activeFilters)
    const hideFromSearch = config?.hideFromSearch ?? []

    if (activeFilters.field.length < 1 && activeFilters.string.length < 1) {
        filteredItems = allItems
    } else {
        // if we have any active filters, we need to apply them
        filteredItems = allItems.filter( item => {

            let filterResult = activeFilters.field.every( f => {
                // if the item doesn't have the field, it CAN'T match, so we're out
                if (!item[f.fieldName]) return false

                // if the item has the field, but it's not an array, make it an array
                let itemValues = item[f.fieldName]
                if (!(itemValues instanceof Array)) {
                    itemValues = [itemValues]
                }

                // if an item's field value is in the list of filter values, keep it
                if (itemValues.some( val => val === f.value )) {
                    return true
                }
                return false
            })

            let stringResult = activeFilters.string.every( s => {
                s = s.toLowerCase()
                for (field in item) {
                    // if the field isn't searchable, it's fine
                    // TODO this config option for no-string-search fields
                    if (hideFromSearch.includes(field)) continue

                    // if the item has the field, but it's not an array, make it an array
                    let itemValues = item[field]
                    if (!(itemValues instanceof Array)) {
                        itemValues = [itemValues]
                    }

                    // if the string search is in an item's field value, keep it
                    if (itemValues.some( val => val.toLowerCase().includes(s) )) {
                        return true
                    }
                }
                return false
            })

            return filterResult && stringResult
        })
    }
}
// ------------------------------------------------------ 
// go through the filtered list of results and
// make page elements for them all
function buildResultList() {

    let resultElement = document.querySelector('section.results')
    resultElement.innerHTML = ""

    // show the active filters at the top of the results
    resultElement.append(buildCurrentFiltersDisplay())

    // do we have more results than our display cap?
    const displayCap = config.maxResultCount || defaultMaxResultCount
    let capInfo = `showing all ${filteredItems.length} results`
    if (filteredItems.length === 1) {
        capInfo = `showing the only result`
    }
    if (filteredItems.length > displayCap) {
        capInfo = `showing first ${displayCap} results`
        filteredItems = filteredItems.slice(0, displayCap)
    }

    // do we have no results?
    if (filteredItems.length < 1) {
        // if no results, just show filters and this message
        resultElement.append( prepMessage('no items to display') )
    } else {
        // if there are any results, show them
        resultElement.append( makeNode('div', 'interface', capInfo) )
        filteredItems.forEach( item => {
            resultElement.append(buildResult(item))
        })
        resultElement.append( makeNode('div', 'interface', capInfo) )
    }

}
// ------------------------------------------------------ 
// make page elements for a single result item 
function buildResult(item) {

    // header
    let header = makeNode('div', 'header clickable')

    // if we can do an icon, that's the first thing into the header
    let iconFieldName = config.iconField || findUsefulField(item, 'icon')
    let iconClickUrl = config.iconUrl || findUsefulField(item, 'url')
    let iconTooltip = config.iconTooltip || findUsefulField(item, 'iconDescription')
    if (iconFieldName) {
        let icon = makeNode('div', 'icon', item[iconFieldName])
        if (iconTooltip) {
            icon.setAttribute('title', item[iconTooltip])
        }
        if (iconClickUrl 
                && iconClickUrl.toString().length > 0 
                && item[iconClickUrl] 
                && item[iconClickUrl].toString().length > 0
            ) {
            icon.classList.add('clickable')
            icon.addEventListener('click', (event) => {
                window.open(item[iconClickUrl], '_blank')
            })
        }
        header.append(icon)
    }

    let fieldIdList = Object.keys(config.fields)

    // are there any fields nominated for the header?
    let headerFields = fieldIdList.filter( fieldId => config.fields[fieldId].display?.includes('header') )

    if (headerFields.length === 0) {
        // if the config doesn't help find header fields, look at
        // each of our default header field names in turn
        defaultHeaderFields.forEach( fieldId => {
             let headerField = findUsefulField(item, fieldId)
             if (headerField) { 
                headerFields.push(headerField)
            }
        })
        // if we didn't have config'd headers and also didn't find
        // any default header fieldnames, use the item's first field
        if (headerFields.length === 0) {
            headerFields.push(Object.keys(item)[0])
        }
    }

    headerFields.forEach( fieldId => {
        cfg = config.fields[fieldId] || { display: '', format: '' }
        let field = makeField(fieldId, item[fieldId], !cfg.display.includes('unlabel'), cfg.format)
        header.append( makeNode('p', '', field) )
    })



    header.addEventListener('click', (event) => {
        // when the title is clicked, add or remove 
        // the "closed" class on the parent result
        event.target.closest('.result').classList.toggle('closed')
    })

    // "normal" details
    const quietFields = config?.quietFields || []

    let details = makeNode('div', 'details')
    for (var fieldKey in item) {
        if (!quietFields.includes(fieldKey) && !headerFields.includes(fieldKey)) {
            let fieldValue = item[fieldKey]
            let field = makeField(fieldKey, item[fieldKey], true)
            details.append(field)
        }
    }

    // "quiet" details
    let hasQuiet = true
    let quietDetails = makeNode('div', 'quiet')
    for (var fieldKey in item) {
        if (quietFields.includes(fieldKey)) {
            let fieldValue = item[fieldKey]
            let field = makeField(fieldKey, item[fieldKey], true)
            quietDetails.append(field)
        }
    }

    let showQuiet = ''
    if (hasQuiet) {
        const quietLabel = config?.quietLabel || 'more >'
        const quietLabelFormat = config?.quietLabelFormat || 'faded italic center'
        showQuiet = makeNode('p', 'quietLabel clickable ' + quietLabelFormat, quietLabel)
        showQuiet.addEventListener('click', (event) => {
            // when the showQuiet is clicked, add or remove 
            // the "terse" class on the parent result
            event.target.closest('.result').classList.toggle('terse')
        })
        details.append(showQuiet)
    }

    result = makeNode('div', 'result closed terse', header, details, quietDetails)

    return result
}
