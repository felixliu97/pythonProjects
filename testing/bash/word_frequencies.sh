#!/bin/bash

cat input/words.txt | tr ' ' '\n' | grep -v '^$'| sort | uniq -c | sort -rn | awk '{print $2" "$1}'