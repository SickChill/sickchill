#! /bin/sh

PYTHON="$1"
tag="$2"

test -n "$tag" || { echo "usage: $0 PY TAG"; exit 1; }

mkdir -p tmp
diffs="tmp/output.$tag.diffs"
rm -f "$diffs"

quiet=""
quiet="1"

vprintf=printf
vecho=echo

if test -n "$quiet"; then
  echo "[$tag] testing structure dump"
  vprintf=true
  vecho=true
fi

result=0
for f in test/files/*.rar; do
  $vprintf "%s -> %-30s .. " "$tag" "$f"
  "$PYTHON" dumprar.py -v -ppassword "$f" > "$f.$tag"
  if diff -uw "$f.exp" "$f.$tag" > /dev/null; then
    $vecho "ok"
    rm -f "$f.$tag"
  else
    $vecho "FAIL"
    if test -n "$quiet"; then
      printf "[%s] %-30s .. FAILED\n" "$tag" "$f"
    fi
    echo "#### $py ####" >> "$diffs"
    diff -uw "$f.exp" "$f.$tag" >> "$diffs"
    result=1
  fi
done

exit $result

