from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
#res=tavily_search("Python programming language")
#print(res)
res=search_flights("plane a 7 day trip to Japan from India")
print(res)