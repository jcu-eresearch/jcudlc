#!/bin/bash
#
# all this script does is look in the docs-src directory for markdown 
# files, compiles them to HTML, and then sandwiches that HTML between 
# htmlstart.html and htmlend.html to create a final file in the docs 
# directory.
#
# Any other file found in docs-src is just plain copied into docs.
#
# This is using Marked to do the markdown, but if you really wanted
# you could use an online editor to do it manually.
#

# assume this script is in the repo at jcudlc/scripts

MARKDOWN_COMPILER="marked"
HTML_PREFIX_FILE="htmlstart.html"
HTML_SUFFIX_FILE="htmlend.html"

# sort out some paths

SCRIPT_PATH="$(dirname -- "$(readlink -f -- "$0")")"
echo doc script path:"  $SCRIPT_PATH"

DOCIN_PATH="$SCRIPT_PATH/../docs-src"
echo doc sources:"      $DOCIN_PATH"

DOCOUT_PATH="$SCRIPT_PATH/../docs"
echo doc destination:"  $DOCOUT_PATH"

# find all the markdown files
MARKDOWN_FILES=$(find "$DOCIN_PATH" -name "*.md")

# compile each markdown file to HTML and sandwich it between the prefix and suffix HTML files
for FILE in $MARKDOWN_FILES; do
    BASENAME=$(basename "$FILE" .md)
    echo -n " > processing $FILE..."
    cat "$DOCIN_PATH/$HTML_PREFIX_FILE" > "$DOCOUT_PATH/$BASENAME.html"
    "$MARKDOWN_COMPILER" "$FILE" >> "$DOCOUT_PATH/$BASENAME.html"
    cat "$DOCIN_PATH/$HTML_SUFFIX_FILE" >> "$DOCOUT_PATH/$BASENAME.html"
    echo " done ✅"
done

# find all the non-markdown files (excluding the HTML prefix and suffix files)
NON_MARKDOWN_FILES=$(find "$DOCIN_PATH" -type f ! -name "*.md" ! -name "$HTML_PREFIX_FILE" ! -name "$HTML_SUFFIX_FILE")

# copy each non-markdown file to the destination directory
for FILE in $NON_MARKDOWN_FILES; do
    BASENAME=$(basename "$FILE")
    echo -n " > copying $FILE..."
    cp "$FILE" "$DOCOUT_PATH/$BASENAME"
    echo " done ✅"
done