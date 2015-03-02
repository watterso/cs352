%{
int yylex();
void yyerror(char*);
#include<stdio.h>
%}

	%token ID INT VAR STRING_LITERAL BASE_OPERATOR MULT_OPERATOR WRITE
	%token END_STATEMENT START_SCRIPT END_SCRIPT NEWLINE
	%start script 

%%
	script: errors START_SCRIPT NEWLINE stmts END_SCRIPT errors
				;

	errors: /*empty*/
				|	errors error
				|	errors NEWLINE 
				;

	stmts: /*empty*/
			 | stmts meta_stmt NEWLINE
			 | stmts meta_stmt END_STATEMENT NEWLINE
			 ;

	meta_stmt: /*empty*/
					 | stmt
					 | meta_stmt END_STATEMENT stmt
					 ;

	stmt: VAR ID
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

extern FILE *yyin;
extern int yylineno;
extern char* yytext;
void yyerror(char *s)
{
	fprintf(stderr, "syntax error\n");
}

int main(int argc, char *argv[])
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


