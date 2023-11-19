#!/bin/bash

ot=1.0.1
configid=abc

inner=$(jq -n --arg name oer \
              --arg version "$ot" \
              '$ARGS.named'
)
inner2=$(jq -n --arg name ore \
              --arg version "$ot" \
              '$ARGS.named'
)
final=$(jq -n --arg configId "$configid" \
              --arg objectname "tempfile" \
              --arg test "2021" \
              --argjson artifacts "[$inner,$inner2]" \
              '$ARGS.named'
)
echo "$final"