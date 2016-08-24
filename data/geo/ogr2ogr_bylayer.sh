#!/bin/bash

#layers=$(ogrinfo -ro -so doc.kml | tail -n+3 | awk -F': ' '{print $2"\n"}')
#for layer in $(ogrinfo -ro -so doc.kml | tail -n+3 | awk -F ': ' '{print $2}' | sed 's/ /_/g')
for layer in $(ogrinfo -ro -so j.kml | tail -n+3 | sed -r 's/[0-9]+: (.*) \(.*/\1/' | sed 's/ /_/g')
do
    layerFixed=$(echo $layer | sed 's/_/ /g')
    echo $layer
    echo $layerFixed
    ogr2ogr -f "GeoJSON" "${layer}.json" j.kml "${layerFixed}"
done
