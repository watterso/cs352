#include <string.h>
#include <map>
#include "ast.h"
typedef struct {
	int num;
	char* ptr;
	int which_val;
	int lineno;
} YYSTYPE;
#define YYSTYPE_IS_DECLARED
typedef struct {
	int num;
	char* ptr;
	int which_val;
	int defined;
} Variable;
struct cmp_str
{
	bool operator()(const char *a, const char *b) const
	{
		return strcmp(a, b) < 0;
	}
};
typedef std::map<char*,Variable,cmp_str>SymbolTable;
typedef std::map<int,Variable>OmniArray;

int yylex();
void yyerror(char*);
int my_cmp(YYSTYPE left, YYSTYPE right, int cmpr);
int truthy_val(YYSTYPE val);
int same_type(YYSTYPE left, YYSTYPE right);
int is_type(YYSTYPE val, int type);
int defined(YYSTYPE val);
void undeclared(int lineno, char* var_name);
void value_error(int lineno, char* var_name);
void type_violation(int lineno);
void dump_sym();
void dump_var(Variable var);
void dump_obj(char* id, SymbolTable obj_sym, int pad);