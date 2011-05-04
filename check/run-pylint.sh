#!/bin/bash
#
# Run pylint on all .py files in the current directory.
#   Output to doc/pylint/filename.html
# Don't bother if the source file hasn't been updated since last run.


for x in *.py; do
    if [[ $x -nt doc/pylint/$x.html ]]; then
        echo "Running pylint on $x ..."
        pylint --html=y $x > doc/pylint/$x.html
    else
        echo "Don't need to run pylint on $x."
    fi
 done
echo "Done."

# Source: http://www.google.com/codesearch?hl=en&q=+package:twowayweb.googlecode.com+pylint+show:wmGH8qWqhfs:mz7H8MB4VRg:orSxj4nAvy4&sa=N&cd=1&ct=rc&cs_p=http://twowayweb.googlecode.com/svn&cs_f=branches/20060627-templates/run-pylint.sh#a0
