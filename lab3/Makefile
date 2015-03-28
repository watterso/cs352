all:
	rm -f parser
	echo '#!'`which python` > parser
	cat parser.py >> parser
	chmod +x parser
clean:
	rm -f parser parsetab.* parser.out parselog.txt *.pyc
.PHONY: test
test: 
	ruby ./test/test.rb
