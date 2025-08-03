#!/bin/bash

# Create a simple 32x32 PNG favicon with a white background and black K
# Using imagemagick (if available) or creating a simple icon

# Check if imagemagick is available
if command -v convert &> /dev/null; then
    echo "Creating favicon with ImageMagick..."
    convert -size 32x32 xc:white \
        -fill black \
        -pointsize 20 \
        -gravity center \
        -annotate +0+0 "K" \
        -bordercolor "#e5e7eb" \
        -border 1 \
        /Users/gyeomkim/development/blog/kigo/assets/images/favicon.png
    echo "Favicon created successfully!"
else
    echo "ImageMagick not found. Creating basic favicon..."
    # Copy the SVG as backup and note that manual conversion might be needed
    cp /Users/gyeomkim/development/blog/kigo/static/images/favicon.svg /Users/gyeomkim/development/blog/kigo/assets/images/favicon-backup.svg
    echo "SVG favicon created as backup. You may need to manually convert to PNG."
fi
