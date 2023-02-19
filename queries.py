import intelliwaterai.infinitydb.access as idb
import argparse

INTERFACE = "com.boilerbay.genomics"
GENOME = idb.Attribute("genome")
CHROMOSOME = idb.Attribute("chromosome")
POSITION = idb.Attribute("position")
BASE = idb.Attribute("base")

import warnings
import urllib3
warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)


class GenomicsServer(idb.InfinityDBAccessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="https://localhost:37411/infinitydb/data")
    parser.add_argument("--database", type=str, default="boilerbay/genomics")
    parser.add_argument("--user", type=str, default="ai")
    parser.add_argument("--password", type=str, default="ai")
    return parser

def add_gene():
    pass

def get_sequence(server, genome, chromosome, start, end):
    success, response, response_content_type = server.execute_query(
        prefix=[INTERFACE, "get_sequence"],
        data = {
            GENOME: genome,
            CHROMOSOME: chromosome,
            idb.Attribute("start"): int(start),
            idb.Attribute("end"): int(end)
        }
    )
    sequence = [idb.flatten_to_tuple(x)[0] for x in response]
    return "".join(sequence)

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


if __name__ == "__main__":
    parser = make_parser()
    parser.add_argument("query", type=str)
    parser.add_argument("--genome", type=str, default=None)
    parser.add_argument("--chromosome", type=str, default=None)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=0)
    args = parser.parse_args()
    server = idb.InfinityDBAccessor(server_url=args.server, db=args.database, user=args.user, password=args.password)
    server.is_verification_enabled = False


    if args.query == "get_sequence":
        print(get_sequence(
            server=server, 
            genome=args.genome, 
            chromosome=args.chromosome, 
            start=args.start, 
            end=args.end)
        )
    