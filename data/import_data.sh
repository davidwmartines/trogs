#!/bin/bash
aws dynamodb batch-write-item --endpoint-url http://localhost:8042 --profile local --request-items file://items.json