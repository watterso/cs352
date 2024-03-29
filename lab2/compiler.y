%{
#include "compiler.h"
int yylex();
void yyerror(char*);
#include<stdio.h>
SymbolTable sym;
const char * MY_UNDEFINED = "undefined";
#define MAX_OBJS 50
SymbolTable objs[MAX_OBJS];
int next_obj = 0;
%}

	%token ID VAR BASE_OPERATOR MULT_OPERATOR WRITE
	%token MULTI_LINE_STRING BAD_WRITE
	%token END_STATEMENT START_SCRIPT END_SCRIPT NEWLINE
	%start script 

	
	%token INT
	%token STRING_LITERAL
	%token OBJ

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

	stmt: VAR ID					{ sym[$2.ptr]; sym[$2.ptr].defined = 0;}
			| VAR ID '=' meta_expr {
							sym[$2.ptr]; 
							sym[$2.ptr].defined = 1;
							sym[$2.ptr].which_val = $4.which_val;
							//Screw conditionals, lets take data we don't even need!
							sym[$2.ptr].num = $4.num;
							sym[$2.ptr].ptr = $4.ptr;

							#if DEBUG == 1
							printf("%d: (%d,%s)\n", $4.which_val, $4.num, $4.ptr);
							#endif

							#if DEBUG == 1
							if(sym[$2.ptr].which_val==INT){
								printf("Declared %s = %d\n",$2.ptr,sym[$2.ptr].num);
							}else{
								printf("Declared %s = %s\n",$2.ptr,sym[$2.ptr].ptr);
							}
							#endif
				}
			| ID '=' expr {
							SymbolTable::iterator it;
							it = sym.find($1.ptr);
							if(it != sym.end()){
								sym[$1.ptr].defined = 1;
								sym[$1.ptr].which_val = $3.which_val;
								//Screw conditionals, lets take data we don't even need!
								sym[$1.ptr].num = $3.num;
								sym[$1.ptr].ptr = $3.ptr;
							}else{
								printf("Line %d, type violation\n", yylval.lineno);
								#if DEBUG == 1
								printf("\tvar not declared\n");
								#endif
							}
				}
			| WRITE '(' args ')'
			| ID '.' ID '=' expr {
							SymbolTable::iterator it;
							it = sym.find($1.ptr);
							if(it != sym.end() && sym[$1.ptr].which_val == OBJ){
								SymbolTable obj_sym = objs[sym[$1.ptr].num];
								obj_sym[$3.ptr].defined = $5.which_val == 0 && $5.num == 0 ? 0 :1;
								obj_sym[$3.ptr].which_val = $5.which_val;
								obj_sym[$3.ptr].num = $5.num;
								obj_sym[$3.ptr].ptr = $5.ptr;
								objs[sym[$1.ptr].num] = obj_sym;
								#if DEBUG == 1
								printf("%d: (%d,%s) ? %d\n", $5.which_val, $5.num, $5.ptr, $5.which_val == 0 && $5.num == 0 ? 0 :1);
								for(SymbolTable::iterator it1 = obj_sym.begin(); it1 != obj_sym.end(); ++it1) {
								                      printf("%s, ",it1->first);
																			                      }
																														printf(" ------END\n");
								#endif
							}else{
								printf("Line %d, type violation\n", yylval.lineno);
								#if DEBUG == 1
								printf("\tobj not declared\n");
								#endif
							}
						}
			;

	args: /*empty*/
			| args ',' expr {
						if($3.which_val == INT){
							printf("%d",$3.num);
						}else if($3.which_val == STRING_LITERAL){
							if(strncmp("<br />", $3.ptr, strlen($3.ptr))==0){
								printf("\n");	
							}else{
								printf("%s",$3.ptr);
							}
						}else if($3.which_val == 0){
							printf("%s", MY_UNDEFINED);
						}else if($3.which_val == OBJ){
							printf("Line %d, type violation\n", yylval.lineno);
							#if DEBUG == 1
							printf("\tcan't print objs\n");
							#endif
							printf("%s", MY_UNDEFINED);
						}
				}
			| expr	{
						if($1.which_val == INT){
							printf("%d",$1.num);
						}else if($1.which_val == STRING_LITERAL){
							if(strncmp("<br />", $1.ptr, strlen($1.ptr))==0){
								printf("\n");	
							}else{
								printf("%s",$1.ptr);
							}
						}else if($1.which_val == 0){
							printf("%s", MY_UNDEFINED);
						}else if($1.which_val == OBJ){
							printf("Line %d, type violation\n", yylval.lineno);
							#if DEBUG == 1
							printf("\tcan't print objs\n");
							#endif
							printf("%s", MY_UNDEFINED);
						}
				}
			;

	maybe_newline: /*empty*/
							 | maybe_newline NEWLINE
							 ;

	meta_expr: expr
					 | obj_expr
					 ;
	
	expr: add_expr
			;

	obj_expr: '{' '}'					{$$.which_val = OBJ; $$.num = next_obj++;}
					| '{' maybe_newline fields '}'	{$$.which_val = OBJ; $$.num = next_obj++;}
					;
	
	fields: field maybe_newline
				| fields ',' maybe_newline field maybe_newline
				;

	field: ID ':' expr {
									SymbolTable obj_sym = objs[next_obj];	
									obj_sym[$1.ptr];
									obj_sym[$1.ptr].defined = 1;
									obj_sym[$1.ptr].which_val = $3.which_val;
									//Screw conditionals, lets take data we don't even need!
									obj_sym[$1.ptr].num = $3.num;
									obj_sym[$1.ptr].ptr = $3.ptr;
									objs[next_obj] = obj_sym;
								}
				;

	add_expr: mult_expr
					| add_expr '+' mult_expr { 
					 					if($1.which_val == INT && $3.which_val == INT){
											#if DEBUG == 1
											printf("add: %d + %d = %d\n", $1.num,$3.num,$1.num+$3.num);
											#endif
											$$.which_val = INT;
											$$.num = $1.num + $3.num; 
										}else if($1.which_val == STRING_LITERAL && $3.which_val == STRING_LITERAL){
											int len1 = strlen($1.ptr);
											int len2 = strlen($3.ptr);
											int len = len1+len2;
											char* catted = (char *)malloc(len+1);
											strncpy(catted, $1.ptr, len1);
											strncpy(catted + len1, $3.ptr, len2);
											catted[len1+len2] = '\0';
											$$.which_val = STRING_LITERAL;
											$$.ptr = catted;
										}else if(($1.which_val == INT && $3.which_val == STRING_LITERAL) || ($1.which_val == STRING_LITERAL && $3.which_val == INT)){
											printf("Line %d, type violation\n", yylval.lineno);
											$$.which_val = 0;
											$$.num = 0;
											#if DEBUG == 1
											printf("\tadd mismatched\n");
											#endif
										}else{
											//undefined
											$$.which_val = 0;
											$$.num = 0;
										}
									}
					| add_expr '-' mult_expr { 
					 					if($1.which_val == INT && $3.which_val == INT){
											#if DEBUG == 1
											printf("subtract: %d - %d = %d\n", $1.num,$3.num,$1.num-$3.num);
											#endif
											$$.num = $1.num - $3.num; 
											$$.which_val = INT;
										}else if(($1.which_val == INT && $3.which_val == STRING_LITERAL) || ($1.which_val == STRING_LITERAL && $3.which_val == INT)){
											printf("Line %d, type violation\n", yylval.lineno);
											#if DEBUG == 1
											printf("\tsubtract mismatched\n");
											#endif
										}else if($1.which_val == $3.which_val && $3.which_val == STRING_LITERAL){
											printf("Line %d, type violation\n", yylval.lineno);
											#if DEBUG == 1
											printf("\tsubtract strings\n");
											#endif
										}else{
											//undefined
											$$.which_val = 0;
											$$.num = 0;
										}
									}
					;

	mult_expr: operand
					 | mult_expr '*' operand { 
					 					if($1.which_val == INT && $3.which_val == INT){
											#if DEBUG == 1
											printf("multiply: %d * %d = %d\n", $1.num,$3.num,$1.num*$3.num);
											#endif
											$$.num = $1.num * $3.num; 
										}else if(($1.which_val == INT && $3.which_val == STRING_LITERAL) || ($1.which_val == STRING_LITERAL && $3.which_val == INT)){
											printf("Line %d, type violation\n", yylval.lineno);
											#if DEBUG == 1
											printf("\tmultiply mismatched\n");
											#endif
										}else if($1.which_val == $3.which_val && $3.which_val == STRING_LITERAL){
											printf("Line %d, type violation\n", yylval.lineno);
											#if DEBUG == 1
											printf("\tmultiply strings\n");
											#endif
										}else{
											//undefined
											$$.which_val = 0;
											$$.num = 0;
										}
									}
					 | mult_expr '/' operand { 
											#if DEBUG == 1
											printf("divide: %d / %d = %d\n", $1.num,$3.num,$1.num/$3.num);
											#endif
					 					if($1.which_val == INT && $3.which_val == INT){
											#if DEBUG == 1
											printf("divide: %d / %d = %d\n", $1.num,$3.num,$1.num/$3.num);
											#endif
											$$.num = $1.num / $3.num; 
										}else if(($1.which_val == INT && $3.which_val == STRING_LITERAL) || ($1.which_val == STRING_LITERAL && $3.which_val == INT)){
											printf("Line %d, type violation\n", yylval.lineno);
											#if DEBUG == 1
											printf("%d: (%d,%s)\n", $1.which_val, $1.num, $1.ptr);
											printf("%d: (%d,%s)\n", $3.which_val, $3.num, $3.ptr);
											printf("\tdivide mismatched\n");
											#endif
										}else if($1.which_val == $3.which_val && $3.which_val == STRING_LITERAL){
											printf("Line %d, type violation\n", yylval.lineno);
											#if DEBUG == 1
											printf("\tdivide strings\n");
											#endif
										}else{
											//undefined
											$$.which_val = 0;
											$$.num = 0;
										}

									}
					 ;


	operand: ID {
							SymbolTable::iterator it;
							it = sym.find($1.ptr);
							if(it != sym.end() && it->second.defined==1){
								$$.which_val = sym[$1.ptr].which_val;
								$$.num = sym[$1.ptr].num;
								$$.ptr = sym[$1.ptr].ptr;
							}else if(it != sym.end()){
								printf("Line %d, %s has no value\n", yylval.lineno, $1.ptr);
								#if DEBUG == 1
								printf("\trender ID\n");
								#endif
								$$.which_val = 0;
								$$.num = 0;
							}else{
								printf("Line %d, type violation\n", yylval.lineno);
								#if DEBUG == 1
								printf("\trender ID\n");
								#endif
								$$.which_val = 0;
								$$.num = 0;
							}
							#if DEBUG == 1
							if(it != sym.end()){
							  printf("%s = [%d](%d,%s)\n",$1.ptr,sym[$1.ptr].defined,sym[$1.ptr].num,sym[$1.ptr].ptr);
							}else{
							  printf("Variable %s is undefined!\n",$1.ptr);
							}
							#endif
						}
				 | INT
				 | STRING_LITERAL
				 | '(' add_expr ')' {$$.which_val = $2.which_val; $$.num = $2.num; $$.ptr = $2.ptr;}
				 | ID '.' ID {
							SymbolTable::iterator it;
							it = sym.find($1.ptr);
							if(it != sym.end() && it->second.defined==1 && it->second.which_val == OBJ){
								SymbolTable obj_sym = objs[sym[$1.ptr].num];
								it = obj_sym.find($3.ptr);
									#if DEBUG == 1
									printf("sub: %d  %s\n",sym[$1.ptr].num,$3.ptr);
									for(SymbolTable::iterator it1 = obj_sym.begin(); it1 != obj_sym.end(); ++it1) {
										  printf("%s, ",it1->first);
											}

									#endif
								if(it != sym.end() && it->second.defined==1){
									$$.which_val = obj_sym[$3.ptr].which_val;
									$$.num = obj_sym[$3.ptr].num;
									$$.ptr = obj_sym[$3.ptr].ptr;
								}else if(it != sym.end()){
									printf("Line %d, type violation\n", yylval.lineno);
									//printf("Line %d, %s has no value\n", yylval.lineno, $1.ptr);
									#if DEBUG == 1
									printf("\trender obj ID\n");
									#endif
									$$.which_val = 0;
									$$.num = 0;
								}else{
									printf("Line %d, %s has no value\n", yylval.lineno, $1.ptr);
									//printf("Line %d, type violation\n", yylval.lineno);
									#if DEBUG == 1
									printf("\trender obj ID\n");
									#endif
									$$.which_val = 0;
									$$.num = 0;
								}
							}else if(it != sym.end() && it->second.which_val == OBJ){
								printf("Line %d, %s has no value\n", yylval.lineno, $1.ptr);
								#if DEBUG == 1
								printf("\trender ID\n");
								#endif
								$$.which_val = 0;
								$$.num = 0;
							}else{
								printf("Line %d, type violation\n", yylval.lineno);
								#if DEBUG == 1
								printf("\trender ID\n");
								#endif
								$$.which_val = 0;
								$$.num = 0;
							}
						}
				 ;
		
%%

#if DEBUG == 1
#   define YY_DEBUG 0
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


