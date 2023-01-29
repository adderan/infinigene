import intelliwaterai.infinitydb.access as idb
from build import INTERFACE

server = idb.InfinityDBAccessor(
    server_url = "http://localhost:37411/infinitydb/data",
    db = "boilerbay/genomics",
    user="ai",
    password="ai"
)

success, response, response_content_type = server.execute_query(
    prefix=[INTERFACE, "count_bases"],
    data = {
        idb.Attribute("genome"): "grch38",
        idb.Attribute("chromosome"): "chr1"
    }
)
print("Number of bases:", list(response[idb.Attribute("num_bases")].keys())[0])

success, response, response_content_type = server.execute_query(
    prefix=[INTERFACE, "get_gc_content"],
    data = {
        idb.Attribute("genome"): "grch38",
        idb.Attribute("chromosome"): "chr1"
    }
)

print(response)