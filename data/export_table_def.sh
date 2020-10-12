#!/bin/bash
aws dynamodb describe-table --table-name art --endpoint-url http://localhost:8042 --profile local | jq ".Table" > ./table.json