#! /bin/sh
find . -name "*.py"  | xargs pylint > pylint.log
