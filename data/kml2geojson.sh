#!/bin/bash
for layer in "$(ogrinfo -ro -so -q jerusalem.kml | cut -d ' ' -f 2,3 | sed 's/^ //g')"
do
    ogr2ogr -f "GeoJSON" "file_${layer}.json" jerusalem.kml "${layer}"
done
