%{
#include "compiler.h"
int yylex();
void yyerror(char*);
#include<stdio.h>

%}

	%token ID VAR BASE_OPERATOR MULT_OPERATOR WRITE
	%token MULTI_LINE_STRING BAD_WRITE
	%token END_STATEMENT START_SCRIPT END_SCRIPT NEWLINE
	%start script 

	
	%token INT
	%token STRING_LITERAL

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
			 | stmts NEWLINE
			 ;

	meta_stmt: stmt
					 | meta_stmt END_STATEMENT stmt
					 ;

	stmt: VAR ID
			| VAR ID '=' expr
			| ID '=' expr
			| WRITE '(' args ')'
			;

	args: /*empty*/
			| args ',' expr {
						if($3.which_val == INT){
							printf("%d",$3.num);
						}else{
							if(strncmp("<br />", $3.ptr, strlen($3.ptr))==0){
								printf("\n");	
							}else{
								printf("%s",$3.ptr);
							}
						}
				}
			| expr	{
						if($1.which_val == INT){
							printf("%d",$1.num);
						}else{
							if(strncmp("<br />", $1.ptr, strlen($1.ptr))==0){
								printf("\n");	
							}else{
								printf("%s",$1.ptr);
							}
						}
				}
			;

	mult_expr: operand
					 | mult_expr '*' operand { 
					 					if(yylval.which_val == INT){
											$$.num = $1.num * $3.num; 
										}else{
											printf("Line %d, type violation\n", yylval.lineno);
										}
									}
					 | mult_expr '/' operand { 
					 					if(yylval.which_val == INT){
											$$.num = $1.num / $3.num; 
										}else{
											printf("Line %d, type violation\n", yylval.lineno);
										}
									}
					 ;

	add_expr: mult_expr
					| add_expr '+' mult_expr { 
					 					if(yylval.which_val == INT){
											$$.num = $1.num + $3.num; 
										}else{
											//int len = strlen($1)+strlen($3);
											//TODO CONCAT
										}
									}
					| add_expr '-' mult_expr { 
					 					if(yylval.which_val == INT){
											$$.num = $1.num - $3.num; 
										}else{
											printf("Line %d, type violation\n", yylval.lineno);
										}
									}
					;

	expr: add_expr
			;

	operand: ID /*TODO return val of id*/
				 | INT
				 | STRING_LITERAL
				 | '(' add_expr ')'
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


