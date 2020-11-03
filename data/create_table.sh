#!/bin/bash
aws dynamodb create-table \
 --cli-input-json file://table.json \
 --endpoint-url http://localhost:8042 --profile local ;

aws dynamodb update-table --table-name art2 \
 --global-secondary-index-updates file://indexes/artist_content/create-index.json \
 --attribute-definitions file://indexes/artist_content/attr-defs.json \
 --profile local --endpoint-url http://localhost:8042 ;

aws dynamodb update-table --table-name art2 \
 --global-secondary-index-updates file://indexes/artists_albums/create-index.json \
 --attribute-definitions file://indexes/artists_albums/attr-defs.json \
 --profile local --endpoint-url http://localhost:8042 ;

aws dynamodb update-table --table-name art2 \
 --global-secondary-index-updates file://indexes/artists_by_owner/create-index.json \
 --attribute-definitions file://indexes/artists_by_owner/attr-defs.json \
 --profile local --endpoint-url http://localhost:8042 ;

 aws dynamodb update-table --table-name art2 \
 --global-secondary-index-updates file://indexes/artists_names/create-index.json \
 --attribute-definitions file://indexes/artists_names/attr-defs.json \
 --profile local --endpoint-url http://localhost:8042 ;
