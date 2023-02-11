import argparse
import os
import sys

from Bio import SeqIO
import intelliwaterai.infinitydb.access as idb

INTERFACE = "com.boilerbay.genomics"

def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="https://localhost:37411/infinitydb/data")
    parser.add_argument("--database", type=str, default="boilerbay/genomics")
    parser.add_argument("--user", type=str, default="ai")
    parser.add_argument("--password", type=str, default="ai")
    return parser



if __name__ == "__main__":
    parser = make_parser()
    parser.add_argument("--fasta")
    parser.add_argument("--genome_id")
    args = parser.parse_args()

    server = idb.InfinityDBAccessor(
        server_url = args.server,
        db = args.database,
        user = args.user,
        password = args.password
    )

    with open(args.fasta) as fh:
        for chromosome in SeqIO.parse(fh, "fasta"):
            for pos, base in enumerate(chromosome.seq):
                server.execute_query(
                    prefix = [INTERFACE, "set_base"],
                    data = {
                        idb.Attribute("genome_id"): args.genome_id,
                        idb.Attribute("chromosome"): str(chromosome.id),
                        idb.Attribute("position"): int(pos),
                        idb.Attribute("base"): base
                    }

                )