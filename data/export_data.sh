#!/bin/bash
aws dynamodb scan --endpoint-url http://localhost:8042 --profile local --table-name art | jq '{"art": [.Items[] | {PutRequest: {Item: .}}]}' > ./items.json