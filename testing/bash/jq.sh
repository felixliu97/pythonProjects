#!/bin/bash

# cat students.json | jq -r '.'
cat students.json | jq -r '.[] | .name'