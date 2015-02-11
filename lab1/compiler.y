%{
#include<stdio.h>
%}

	%token ID INT EOS VAR STRING_LITERAL BASE_OPERATOR MULT_OPERATOR START_SCRIPT END_SCRIPT WRITE
	%start prog 

%%
	prog: errors script errors
	
	errors: /*empty*/
				|	errors error
				;

	script: START_SCRIPT EOS stmts END_SCRIPT 
				;

	stmts: /*empty*/
			 | stmts stmt EOS
			 ;

	stmt: /*empty*/
			| VAR ID
			| VAR ID '=' expr
			| ID '=' expr
			| WRITE '(' args ')'
			;

	args: /*empty*/
			| args ',' expr
			| expr
			;

	mult_expr: operand
					 | mult_expr MULT_OPERATOR operand
					 ;

	add_expr: mult_expr
					| add_expr BASE_OPERATOR mult_expr
					;

	expr: add_expr;

	operand: ID
				 | INT
				 | STRING_LITERAL
				 | '(' expr ')'
				 ;
		
%%

#ifdef DEBUG
#   define YY_DEBUG 1
#else
#   define YY_DEBUG 0 
#endif

FILE *yyin;
int yylineno;
yyerror(char *s)
{
	fprintf(stderr, "error: %s, line: %d\n", s, yylineno);
}

main(int argc, char *argv[])
{
	yydebug = YY_DEBUG;
	if (argc == 2) {
		FILE *file;

		file = fopen(argv[1], "r");
		if (!file) {
			fprintf(stderr, "could not open %s\n", argv[1]);
		} else{
			yyin = file;
			//yyparse() will call yylex()
			yyparse();
		}
	} else{
		fprintf(stderr, "format: ./parser [filename]\n");
	}
}


