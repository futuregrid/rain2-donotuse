#
# Gregor von Laszewski, original modified from cogkit.org and cyberaide.org
#

exe:
	# the copy is here to make it uniform to OSX
	# NOT USED cd src; cp fg-shell fg.py
	rm -rf  ./dist
	@echo "---------------------------------------------------------"
	python setup-exe.py py2exe
	@echo "---------------------------------------------------------"
	@echo "I created an executable file and libraries in  ./dist/"
	@echo " To call the program we can do ./dist/fg-shell.exe"
	@echo "---------------------------------------------------------"

test-exe:
	echo "list defaults" | ./dist/fg-shell.exe 

pylint:
	#check/pyl.sh
	mkdir -p doc
	pylint --rcfile=check/standard.rc shell utils image > doc/pylint-all.txt

pep8:
	mkdir -p doc
	check/pep8.sh > doc/pep8-all.txt

pychecker:
	./check/pycheck.sh

doxygen:
	doxygen config.dox
	open doc/html/index.html

apidoc:
	mkdir -p doc/api
#	cd src; epydoc --graph all --html futurgrid -o ../doc/api
#	firefox doc/api/index.html

app:
# without the .py ending it does not work
	cd src; cp fg-shell fg.py
	python setup-app.py py2app

test-app:
	ln ./dist/fg.app/Contents/MacOS/fg ./dist/fg
	./dist/fg.app/Contents/MacOS/fg

#
# THE NEXT COMMANDS ARE FOR DEBUGGING ONLY
#

c:
	open -a Console

t:
	open -a dist/fg.app

egg:
	python setup.py bdist_egg

tar:
	python setup.py sdist

rpm:
	python setup.py bdist_rpm


d:
	make -f Makefile egg
	make -f Makefile tar
#	make -f Makefile rpm