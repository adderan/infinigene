import intelliwaterai.infinitydb.access as idb
import argparse

INTERFACE = "com.boilerbay.genomics"
GENOME = idb.Attribute("genome")
CHROMOSOME = idb.Attribute("chromosome")
POSITION = idb.Attribute("position")
BASE = idb.Attribute("base")

def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="https://localhost:37411/infinitydb/data")
    parser.add_argument("--database", type=str, default="boilerbay/genomics")
    parser.add_argument("--user", type=str, default="ai")
    parser.add_argument("--password", type=str, default="ai")
    return parser

server = idb.InfinityDBAccessor(
    server_url = "http://localhost:37411/infinitydb/data",
    db = "boilerbay/genomics",
    user="ai",
    password="ai"
)

def count_bases(server, genome, chromosome):

    success, response, response_content_type = server.execute_query(
        prefix=[INTERFACE, "count_bases"],
        data = {
            GENOME: genome,
            CHROMOSOME: chromosome
        }
    )
    return list(response[idb.Attribute("num_bases")].keys())[0]

def get_gc_content(server, genome, chromosome):

    success, response, response_content_type = server.execute_query(
        prefix=[INTERFACE, "get_gc_content"],
        data = {
            GENOME: genome,
            CHROMOSOME: chromosome
        }
    )
    return response

def get_last_position(server, genome, chromosome):
    success, response, response_content_type = server.execute_query(
        prefix=[INTERFACE, "get_last_position"],
        data = {
            GENOME: genome,
            CHROMOSOME: chromosome
        }
    )
    if not success or idb.Attribute("last_position") not in response:
        return None
    return list(response[idb.Attribute("last_position")].keys())[0]