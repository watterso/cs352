%{
#include "y.tab.h"
%}


%%
"var"									{return VAR;}
"<script type=\"text/JavaScript\">" {return START_SCRIPT;}
"</script>"							{return END_SCRIPT;}
"document.write"			{return WRITE;}
[a-zA-Z][a-zA-Z0-9_]*	{return ID;} 
[0-9]+								{return INT;}
"\n"									{yylineno++;return NEWLINE;}
";"										{return END_STATEMENT;}
\"[^\n]*\"						{return STRING_LITERAL;}
"="										{return '=';}
"("										{return '(';}
")"										{return ')';}
","										{return ',';}
[\+-]									{return BASE_OPERATOR;}
[\*/]									{return MULT_OPERATOR;}
[ \t]									{}						//discard

\"[^\"]*\n[^\"]*\"						{return MULTI_LINE_STRING;}
document[^\n]+write				{return BAD_WRITE;}

%%


