#!/bin/bash
set -eu
d=$1;db=$(mktemp);fs=$(mktemp);trap "rm -f $db $fs" EXIT
jq -r '.[].uri//empty'|sed 's|^file://||;s/#.*//'|sort>$db
find $d -type f -not -path '*/.*'|sort>$fs
(comm -23 $db $fs|sed 's/.*/{"path":"&","status":"missing"}/';comm -13 $db $fs|sed 's/.*/{"path":"&","status":"unspecified"}/')|awk 'BEGIN{print"["}NR>1{print","}{printf"  %s",$0}END{print"\n]"}'