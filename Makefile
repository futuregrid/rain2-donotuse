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