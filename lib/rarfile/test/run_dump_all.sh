#! /bin/sh

JAVA_OPTIONS="-Dpython.path=`pwd`/.."
export JAVA_OPTIONS

plist="python2.7 python3.2 python3.3 python3.4 python3.5 python3.6 pypy jython jython2.7"

result=0
for py in $plist; do
  if which $py > /dev/null; then
    ./test/run_dump.sh "$py" "$py" || result=1
    echo ""
  else
    echo $py not available
    echo ""
  fi
done

