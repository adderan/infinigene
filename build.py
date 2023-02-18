import argparse
import os
import sys

from Bio import SeqIO
import intelliwaterai.infinitydb.access as idb

from queries import INTERFACE, get_last_position, make_parser


if __name__ == "__main__":
    parser = make_parser()
    parser.add_argument("--fasta")
    parser.add_argument("--genome")
    parser.add_argument("--batch_size", type=int, default=1000000)
    parser.add_argument("--start_position", type=int, default=0)

    args = parser.parse_args()

    server = idb.InfinityDBAccessor(
        server_url = args.server,
        db = args.database,
        user = args.user,
        password = args.password
    )
    server.is_verification_enabled = False


    
    with open(args.fasta) as fh:
        for chromosome in SeqIO.parse(fh, "fasta"):
            print("Starting on chromosome", chromosome.id, "at position", args.start_position)
            query_data = {}
            for pos in range(args.start_position, len(chromosome.seq)):
                base = chromosome.seq[pos]
                query_data[(
                    idb.Attribute("genome"), args.genome,
                    idb.Attribute("chromosome"), str(chromosome.id),
                    idb.Attribute("position"), int(pos),
                    idb.Attribute("base"), base
                )] = None
            
                if pos%args.batch_size == 0:
                    print("Uploading up to position", pos)
                    server.execute_query(
                        prefix = [INTERFACE, "set_base"],
                        data = query_data,
                        verbose = False
                    )
                    query_data = {}
                    print("Genome length is now", get_last_position(server, args.genome, chromosome.id))
            #upload rest of last batch
            server.execute_query(
                prefix = [INTERFACE, "set_base"],
                data = query_data,
                verbose = False
            )
            