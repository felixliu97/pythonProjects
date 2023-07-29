#!/bin/bash

# cat students.json | jq -r '.'
cat students.json | jq -r '.[] | .name'
cat students.json | jq -r '.[].list[0].a'