%{
#include "compiler.h"
#include "y.tab.h"
%}


%%
"var"									{return VAR;}
"<script type=\"text/JavaScript\">" {return START_SCRIPT;}
"</script>"							{return END_SCRIPT;}
"document.write"			{return WRITE;}
[a-zA-Z][a-zA-Z0-9_]*	{yylval.ptr = strdup(yytext); yylval.which_val = STRING_LITERAL; yylval.lineno = yylineno; return ID;} 
[0-9]+								{yylval.num = atoi(yytext); yylval.which_val = INT; yylval.lineno = yylineno; return INT;}
"\n"									{yylineno++;return NEWLINE;}
";"										{return END_STATEMENT;}
\"[^\n^\"]*\"						{yylval.ptr = strndup(yytext+1,strlen(yytext)-2); yylval.which_val = STRING_LITERAL; yylval.lineno = yylineno; return STRING_LITERAL;}
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
":"										{return ':';}
"."										{return '.';}
[ \t]									{}						//discard

\"[^\"]*\n[^\"]*\"						{return MULTI_LINE_STRING;}
document[^\n]+write				{return BAD_WRITE;}

%%


