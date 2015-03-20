%{
#include<stdio.h>
#include "compiler.h"
#define MAX_OBJS 50
#define MAX_ARRS 50

SymbolTable sym;
const char * MY_UNDEFINED = "undefined";
SymbolTable objs[MAX_OBJS];
int next_obj = 0;
OmniArray arrs[MAX_ARRS];
int next_arr = 0;
int last_line_error = 0;
%}

	%token ID VAR BASE_OPERATOR MULT_OPERATOR WRITE
	%token EQ NE GTE LTE GT LT
	%token AND OR NOT
	%token B_TRUE B_FALSE
	%token I_COND
	%token MULTI_LINE_STRING BAD_WRITE
	%token END_STATEMENT START_SCRIPT END_SCRIPT NEWLINE
	%start script 

	
	%token INT
	%token STRING_LITERAL
	%token OBJ
	%token ARR
	%token BOOL

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
							//printf("%d: (%d,%s)\n", $4.which_val, $4.num, $4.ptr);
							#endif

							#if DEBUG == 1
							printf("Declared %s = \n",$2.ptr);
							dump_var(sym[$2.ptr]);
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
								undeclared(yylval.lineno, $1.ptr);
								sym[$1.ptr]; 
								sym[$1.ptr].defined = 1;
								sym[$1.ptr].which_val = $3.which_val;
								//Screw conditionals, lets take data we don't even need!
								sym[$1.ptr].num = $3.num;
								sym[$1.ptr].ptr = $3.ptr;
								#if DEBUG == 1
								printf("\tvar not declared, creating...\n");
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
								//printf("type %d: (%d,%s), defined: %d\n", $5.which_val, $5.num, $5.ptr, $5.which_val == 0 && $5.num == 0 ? 0 :1);
								dump_obj($1.ptr, obj_sym, 0);
								#endif
							}else{
								type_violation(yylval.lineno);
								#if DEBUG == 1
								printf("\tobj not declared\n");
								#endif
							}
						}
			| ID '[' expr ']' '=' expr{
							if($3.which_val == INT){
								SymbolTable::iterator it;
								it = sym.find($1.ptr);
								if(it != sym.end() && sym[$1.ptr].which_val == ARR){
									OmniArray le_array = arrs[sym[$1.ptr].num];
									le_array[$3.num].defined = $5.which_val == 0 && $5.num == 0 ? 0 :1;
									le_array[$3.num].which_val = $5.which_val;
									le_array[$3.num].num = $5.num;
									le_array[$3.num].ptr = $5.ptr;
									arrs[sym[$1.ptr].num] = le_array;
								}else{
									//TODO arr no exist or var not arr
								}
							}else{
								//TODO array access err
							}
						}
			| I_COND '(' bool_expr ')' '{' NEWLINE stmts NEWLINE '}' {
					if($3.which_val == BOOL){
						//TODO AST bsns do something	
					}else{
						//TODO syntax err, that isn't a boolean expression
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
							type_violation(yylval.lineno);
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
							type_violation(yylval.lineno);
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
					 | arr_expr
					 ;
	
	arr_expr: '[' ']' 				{$$.which_val = ARR; $$.num = next_arr++;}
					| '[' maybe_newline arr_vals ']' {$$.which_val = ARR; $$.num = next_arr++;}

	arr_vals: arr_val maybe_newline
					| arr_vals ',' maybe_newline arr_val maybe_newline
					;

	arr_val: expr {
							OmniArray le_array = arrs[next_arr];
							int i = 0;
							if(le_array.rbegin() != le_array.rend()){
								i = le_array.rbegin()->first + 1;
							}
							le_array[i];
							le_array[i].defined = 1;
							le_array[i].which_val = $1.which_val;
							//Screw conditionals, lets take data we don't even need!
							le_array[i].num = $1.num;
							le_array[i].ptr = $1.ptr;
							arrs[next_arr] = le_array;
						}


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

	expr: bool_expr
			;
	
	bool_expr: rel_expr
					 | bool_expr AND rel_expr {
							int l = truthy_val($1);
							int r = truthy_val($3);
							if(l != -1 && r != -1){
								$$.which_val = BOOL;
								$$.num = l && r;
							}else{
								//TODO error one or both invalid truthy types
								//type violation
							}
						}
					 | bool_expr OR rel_expr {
							int l = truthy_val($1);
							int r = truthy_val($3);
							if(l != -1 && r != -1){
								$$.which_val = BOOL;
								$$.num = l || r;
							}else{
								//TODO error one or both invalid truthy types
								//type violation
							}
						}
					 | NOT rel_expr {
							int v = truthy_val($2);
							if(v != -1){
								$$.which_val = BOOL;
								$$.num = !v;
							}else{
								//TODO error invalid truthy type
								//type violation
							}
					  }
					 ;

	rel_expr: add_expr
					| rel_expr EQ add_expr {
							int le_cmp = my_cmp($1,$3, EQ);
							if(le_cmp == -1){
								//TODO invalid comp, error messages
								$$.which_val = 0;
								$$.num = 0;
							}else{
								$$.which_val = BOOL;
								$$.num = le_cmp;
							}
						}
					| rel_expr NE add_expr {
							int le_cmp = my_cmp($1,$3, NE);
							if(le_cmp == -1){
								//TODO invalid comp, error messages
								$$.which_val = 0;
								$$.num = 0;
							}else{
								$$.which_val = BOOL;
								$$.num = le_cmp;
							}
						} 
					| rel_expr GTE add_expr {
							int le_cmp = my_cmp($1,$3, GTE);
							if(le_cmp == -1){
								//TODO invalid comp, error messages
								$$.which_val = 0;
								$$.num = 0;
							}else{
								$$.which_val = BOOL;
								$$.num = le_cmp;
							}
						} 
					| rel_expr LTE add_expr {
							int le_cmp = my_cmp($1,$3, LTE);
							if(le_cmp == -1){
								//TODO invalid comp, error messages
								$$.which_val = 0;
								$$.num = 0;
							}else{
								$$.which_val = BOOL;
								$$.num = le_cmp;
							}
						} 
					| rel_expr GT add_expr {
							int le_cmp = my_cmp($1,$3, GT);
							if(le_cmp == -1){
								//TODO invalid comp, error messages
								$$.which_val = 0;
								$$.num = 0;
							}else{
								$$.which_val = BOOL;
								$$.num = le_cmp;
							}
						} 
					| rel_expr LT add_expr {
							int le_cmp = my_cmp($1,$3, LT);
							if(le_cmp == -1){
								//TODO invalid comp, error messages
								$$.which_val = 0;
								$$.num = 0;
							}else{
								$$.which_val = BOOL;
								$$.num = le_cmp;
							}
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
											type_violation(yylval.lineno);
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
											type_violation(yylval.lineno);
											#if DEBUG == 1
											printf("\tsubtract mismatched\n");
											#endif
										}else if($1.which_val == $3.which_val && $3.which_val == STRING_LITERAL){
											type_violation(yylval.lineno);
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
											type_violation(yylval.lineno);
											#if DEBUG == 1
											printf("\tmultiply mismatched\n");
											#endif
										}else if($1.which_val == $3.which_val && $3.which_val == STRING_LITERAL){
											type_violation(yylval.lineno);
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
											type_violation(yylval.lineno);
											#if DEBUG == 1
											printf("%d: (%d,%s)\n", $1.which_val, $1.num, $1.ptr);
											printf("%d: (%d,%s)\n", $3.which_val, $3.num, $3.ptr);
											printf("\tdivide mismatched\n");
											#endif
										}else if($1.which_val == $3.which_val && $3.which_val == STRING_LITERAL){
											type_violation(yylval.lineno);
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
								value_error(yylval.lineno, $1.ptr);
								#if DEBUG == 1
								printf("\trender ID\n");
								#endif
								$$.which_val = 0;
								$$.num = 0;
							}else{
								type_violation(yylval.lineno);
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
				 | B_TRUE { $$.which_val = BOOL; $$.num = 1;}
				 | B_FALSE { $$.which_val = BOOL; $$.num = 0;}
				 | '(' bool_expr ')' {$$.which_val = $2.which_val; $$.num = $2.num; $$.ptr = $2.ptr;}
				 | ID '.' ID {
							SymbolTable::iterator it;
							it = sym.find($1.ptr);
							if(it != sym.end() && it->second.defined==1 && it->second.which_val == OBJ){
								SymbolTable obj_sym = objs[sym[$1.ptr].num];
								it = obj_sym.find($3.ptr);
									#if DEBUG == 1
									printf("Accessing %s.%s\n", $1.ptr, $3.ptr);
									#endif
								if(it != sym.end() && it->second.defined==1){
									$$.which_val = obj_sym[$3.ptr].which_val;
									$$.num = obj_sym[$3.ptr].num;
									$$.ptr = obj_sym[$3.ptr].ptr;
								}else if(it != sym.end()){
									//in the sym table, but field undefined on object
									int obj_len = strlen($1.ptr);
									int combo_len = obj_len+strlen($3.ptr);
									char combo_name[combo_len+2];
									combo_name[combo_len+1] = '\0';
									combo_name[obj_len] = '.';
									strncpy(combo_name, $1.ptr, obj_len);
									strcpy(combo_name+obj_len+1, $3.ptr);
									value_error(yylval.lineno, combo_name);
									//type_violation(yylval.lineno);
									#if DEBUG == 1
									printf("\trender obj ID\n");
									#endif
									$$.which_val = 0;
									$$.num = 0;
								}else{
									value_error(yylval.lineno, $1.ptr);
									#if DEBUG == 1
									printf("\trender obj ID\n");
									#endif
									$$.which_val = 0;
									$$.num = 0;
								}
							}else if(it != sym.end() && it->second.which_val == OBJ){
								value_error(yylval.lineno, $1.ptr);
								#if DEBUG == 1
								printf("\trender ID\n");
								#endif
								$$.which_val = 0;
								$$.num = 0;
							}else{
								type_violation(yylval.lineno);
								#if DEBUG == 1
								printf("\trender ID\n");
								#endif
								$$.which_val = 0;
								$$.num = 0;
							}
						}
				 | ID '[' expr ']' {
							if($3.which_val == INT){
								SymbolTable::iterator it;
								it = sym.find($1.ptr);
								if(it != sym.end() && sym[$1.ptr].which_val == ARR){
									OmniArray le_array = arrs[sym[$1.ptr].num];
									OmniArray::iterator it = le_array.find($3.num);
								  if(it != le_array.end() && it->second.defined==1){
										$$.which_val = le_array[$3.num].which_val;
										$$.ptr = le_array[$3.num].ptr;
										$$.num = le_array[$3.num].num;
									}else{
										//key did not exist, AKA indexoutofbounds
										int name_len = strlen($1.ptr);
										char digits[5];
										sprintf(digits,"%d",$3.num);
										int index_size = strlen(digits);
										char combo[name_len+index_size+3];
										strncpy(combo, $1.ptr, name_len);
										combo[name_len] = '[';
										sprintf(combo+name_len+1,"%s", digits);
										combo[name_len+index_size+1] = ']';
										combo[name_len+index_size+2] = '\0';
										value_error(yylval.lineno, combo);
										$$.which_val = 0; //set undefined
										$$.num = 0;
									}
								}else{
								 	//TODO arr no exist or var not arr
									$$.which_val = 0; //set undefined
									$$.num = 0;
								}
							}else{
								//TODO array access err
								$$.which_val = 0; //set undefined
								$$.num = 0;
							}
				 	}
				 ;
		
%%
void dump_sym(){
	int pad = 2;
	const char* pad_str = "                                           ";
	printf("variables : {\n");
	for(SymbolTable::iterator it = sym.begin(); it != sym.end(); ++it) {
		if(it->second.which_val != OBJ){
			printf("%*.*s%s: ", pad, pad, pad_str, it->first);
		}
		switch(it->second.which_val){
			case INT: printf("%d\n", it->second.num);
								break;
			case STRING_LITERAL: printf("'%s'\n", it->second.ptr);
													 break;
			case OBJ: dump_obj(it->first, objs[it->second.num], pad); 
								break;
			case ARR: printf("arr[%d]\n", it->second.num);
								break;
			default: printf("undefined\n");
		}
	}
	printf("}");
}
void dump_var(Variable var){
	switch(var.which_val){
		case INT: printf("%d\n", var.num);
			break;
		case STRING_LITERAL: printf("%s\n", var.ptr);
			break;
		case OBJ: dump_obj(var.ptr, objs[var.num], 0);
			break;
		case ARR: printf("arr[%d]\n", var.num);
			break;
		default: printf("undefined\n");
	}
}
void dump_obj(char* id, SymbolTable obj_sym, int pad){
	const char* pad_str = "                                           ";
	printf("%*.*s%s : {\n", pad, pad, pad_str, id);
	for(SymbolTable::iterator it1 = obj_sym.begin(); it1 != obj_sym.end(); ++it1) {
		printf("%*.*s  %s: ", pad, pad, pad_str, it1->first);
		switch(it1->second.which_val){
			case INT: printf("%d\n", it1->second.num);
								break;
			case STRING_LITERAL: printf("'%s'\n", it1->second.ptr);
													 break;
			case OBJ: printf("obj{%d}\n",	it1->second.num);
								break;
			case ARR: printf("arr[%d]\n", it1->second.num);
								break;
			default: printf("undefined\n");
		}
	}
	printf("%*.*s}\n", pad, pad, pad_str);
}
void undeclared(int lineno, char* var_name){
	if(lineno > last_line_error){
		fprintf(stderr, "Line %d, %s undeclared\n", lineno, var_name);
		last_line_error = lineno;
	}
}
void value_error(int lineno, char* var_name){
	if(lineno > last_line_error){
		fprintf(stderr, "Line %d, %s has no value\n", lineno, var_name);
		last_line_error = lineno;
	}
}
void type_violation(int lineno){
	printf("%d ? %d\n", lineno, last_line_error);
	if(lineno > last_line_error){
		fprintf(stderr, "Line %d, type violation\n", lineno);
		last_line_error = lineno;
	}
}
int my_cmp(YYSTYPE left, YYSTYPE right, int cmpr){
	if(same_type(left, right)){
		if(defined(left)){
			switch(left.which_val){
				case BOOL:
					switch(cmpr){
						case EQ: return left.num == right.num; break;
						case NE: return left.num != right.num; break;
						default: return -1;
					}break;
				case INT:
					switch(cmpr){
						case EQ: return left.num == right.num; break;
						case NE: return left.num != right.num; break;
						case GTE: return left.num >= right.num; break;
						case LTE: return left.num <= right.num; break;
						case GT: return left.num > right.num; break;
						case LT: return left.num < right.num; break;
						default: return -1;
					}break;
				case STRING_LITERAL:
					switch(cmpr){
						case EQ: return strcmp(left.ptr,right.ptr) == 0; break;
						case NE: return strcmp(left.ptr,right.ptr) != 0; break;
					}break;
				default: return -1;
			}
		}else{
			return -1;
		}
	}else{
		return -1;
	}
	//crazy case, same defined type but switches don't catch it?
	//impossibru!
	return -1;
}
int truthy_val(YYSTYPE val){
	int ret = 0;
	switch(val.which_val){
		case BOOL: ret = val.num; break;
		case INT: ret = val.num!=0; break;
		case STRING_LITERAL: ret = strlen(val.ptr)!=0; break;
		default: ret = -1; //arr and objs can't be used in bool expressions
	}
	return ret;
}
int same_type(YYSTYPE left, YYSTYPE right){
	return left.which_val == right.which_val;
}
int is_type(YYSTYPE val, int type){
	return val.which_val == type;
}
int defined(YYSTYPE val){
	return val.which_val !=0 && val.num !=0;
}
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
			#if DEBUG ==1
			dump_sym();
			#endif
		}
	} else{
		fprintf(stderr, "format: ./parser [filename]\n");
	}
}


