#!/bin/bash
aws dynamodb create-table --endpoint-url http://localhost:8042 --profile local --cli-input-json file://table.json