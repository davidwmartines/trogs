
aws dynamodb update-table --table-name art2 --global-secondary-index-updates file://drop-index.json --profile local --endpoint-url http://localhost:8042

aws dynamodb update-table --table-name art2 --global-secondary-index-updates file://create-index.json --attribute-definitions file://attr-defs.json --profile local --endpoint-url http://localhost:8042
