UNAME := $(shell uname)
DEBUG := 0

detectOS:
	make $(UNAME)

Linux: y.tab.c lex.yy.c
	g++ -DDEBUG=$(DEBUG) y.tab.c lex.yy.c -o parser -lfl
Darwin: y.tab.c lex.yy.c
	g++ -DDEBUG=$(DEBUG) y.tab.c lex.yy.c -o parser -ll -Wno-write-strings 

y.tab.c: compiler.y
	yacc --yacc -dv -g -t compiler.y
lex.yy.c: compiler.l
	lex compiler.l
clean:
	rm -f lex.yy.c y.tab.c y.tab.h y.dot y.output y.vcg

.PHONY: test
test: 
	ruby ./test/test.rb
