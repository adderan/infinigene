import argparse
import os
import sys

from Bio import SeqIO
import intelliwaterai.infinitydb.access as idb

INTERFACE = "com.boilerbay.genomics"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fasta")
    parser.add_argument("--genome_id")
    args = parser.parse_args()

    server = idb.InfinityDBAccessor(
        server_url = "http://localhost:37411/infinitydb/data",
        db = "boilerbay/genomics",
        user="ai",
        password="ai"
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