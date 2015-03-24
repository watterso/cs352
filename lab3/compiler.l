%{
#include "compiler.h"
#include "y.tab.h"
%}


%%
"var"									{return VAR;}
"true"								{return B_TRUE;}
"false"								{return B_FALSE;}
"<script type=\"text/JavaScript\">" {return START_SCRIPT;}
"</script>"							{return END_SCRIPT;}
"document.write"			{return WRITE;}
"if"									{return I_COND;}
"else"								{return E_COND;}
"while"								{return WHILE;}
"do"									{return DO;}
[a-zA-Z][a-zA-Z0-9_]*	{yylval.ptr = strdup(yytext); yylval.which_val = STRING_LITERAL; yylval.lineno = yylineno; return ID;} 
[0-9]+								{yylval.num = atoi(yytext); yylval.which_val = INT; yylval.lineno = yylineno; return INT;}
"\n"									{yylineno++;return NEWLINE;}
";"										{return END_STATEMENT;}
\"[^\n^\"]*\"						{yylval.ptr = strndup(yytext+1,strlen(yytext)-2); yylval.which_val = STRING_LITERAL; yylval.lineno = yylineno; return STRING_LITERAL;}
"!="										{return NE;}
"=="										{return EQ;}
">="										{return GTE;}
"<="										{return LTE;}
"<"										{return LT;}
">"										{return GT;}
"&&"										{return AND;}
"||"										{return OR;}
"!"										{return NOT;}
"="										{return '=';}
"("										{return '(';}
")"										{return ')';}
","										{return ',';}
"+"										{return '+';}
"-"										{return '-';}
"*"										{return '*';}
"/"										{return '/';}
"{"										{return '{';}
"}"										{return '}';}
"["										{return '[';}
"]"										{return ']';}
":"										{return ':';}
"."										{return '.';}
[ \t]									{}						//discard

\"[^\"]*\n[^\"]*\"						{return MULTI_LINE_STRING;}
document[^\n]+\.[^\n]+write				{return BAD_WRITE;}

%%


