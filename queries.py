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

def get_gene_sequence(server, gene_id):
    success, response, response_content_type = server.execute_query(
        prefix=[INTERFACE, "get_gene_sequence"],
        data = {
            idb.Attribute("gene_id"): gene_id
        }
    )
    response = response[idb.Attribute('transcript')]
    sequences = {transcript:"".join([idb.flatten_to_tuple(x)[0] for x in response[transcript]]) for transcript in response}

    return sequences

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

def get_gene(server, gene_id):
    success, response, response_content_type = server.execute_query(
        prefix=[INTERFACE, "get_gene"],
        data = {
            idb.Attribute("gene_id"): gene_id
        }
    )
    if not success:
        return None
    return response

def get_transcript(server, transcript_id):
    success, response, response_content_type = server.execute_query(
        prefix=[INTERFACE, "get_transcript"],
        data = {
            idb.Attribute("transcript_id"): transcript_id
        }
    )
    if not success:
        return None
    return response

def get_transcripts_in_range(server, genome, chromosome, start, end):
    success, response, response_content_type = server.execute_query(
        prefix=[INTERFACE, "get_transcripts_in_range"],
        data = {
            idb.Attribute("genome"): genome,
            idb.Attribute("chromosome"): chromosome,
            idb.Attribute("start"): start,
            idb.Attribute("end"): end
        }
    )
    if not success:
        return None
    return response


if __name__ == "__main__":
    parser = make_parser()
    parser.add_argument("query", type=str)
    parser.add_argument("--genome", type=str, default=None)
    parser.add_argument("--chromosome", type=str, default=None)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=0)
    parser.add_argument("--gene_id", type=str, default=None)
    parser.add_argument("--transcript_id", type=str, default=None)
    args = parser.parse_args()
    server = idb.InfinityDBAccessor(server_url=args.server, db=args.database, user=args.user, password=args.password)
    server.is_verification_enabled = False


    if args.query == "get_sequence":
        print(get_sequence(
            server=server, 
            genome=args.genome, 
            chromosome=args.chromosome, 
            start=args.start, 
            end=args.end
        ))

    elif args.query == "get_gene_sequence":
        print(get_gene_sequence(server, args.gene_id))

    elif args.query == "get_gene":
        print(get_gene(server, args.gene_id))

    elif args.query == "get_transcript":
        print(get_transcript(server, args.transcript_id))

    elif args.query == "get_transcripts_in_range":
        print(get_transcripts_in_range(server, args.genome, args.chromosome, args.start, args.end))
    