all:
	echo '#!'`which python` > parser
	cat main.py >> parser
	chmod +x parser
	echo '#!'`which python` > printer 
	cat main.py >> printer 
	chmod +x printer 
clean:
	rm -f parser printer parsetab.* parser.out parselog.txt *.pyc
.PHONY: test
test: 
	ruby ./test/test.rb

.PHONY: test1
test1:
	cd cs352-test && python main.py ../parser
