all: y.tab.c lex.yy.c
	gcc y.tab.c lex.yy.c -o parser -lfl
y.tab.c: compiler.y
	yacc -y -d -g -t compiler.y
lex.yy.c: compiler.l
	lex compiler.l
clean:
	rm -f lex.yy.c y.tab.c y.tab.h y.dot y.output

