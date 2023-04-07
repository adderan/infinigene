import argparse
import os
import sys

from gtfparse import read_gtf

import intelliwaterai.infinitydb.access as idb

from queries import make_parser, INTERFACE


if __name__ == "__main__":
    parser = make_parser()
    parser.add_argument("--gtf")
    parser.add_argument("--repeat_masker_output")
    parser.add_argument("--genome")
    parser.add_argument("--gene_set")

    args = parser.parse_args()

    server = idb.InfinityDBAccessor(
        server_url = args.server,
        db = args.database,
        user = args.user,
        password = args.password
    )
    server.is_verification_enabled = False

    if args.gtf:

        gtf = read_gtf(args.gtf)

        num_genes = len(gtf)

        for i in range(len(gtf)):
            gene_name = gtf[i,"gene_name"]
            chromosome = gtf[i, "seqname"]
            gene_set = gtf[i, "source"]
            feature = gtf[i, "feature"]
            start = gtf[i, "start"]
            end = gtf[i, "end"]
            strand = gtf[i, "strand"]
            gene_id = gtf[i, "gene_id"]
            exon_number = gtf[i, "exon_number"]
            exon_id = gtf[i, "exon_id"]
            transcript_id = gtf[i, "transcript_id"]

            if i % 1000 == 0:
                print(chromosome)
                print("Uploading gene", i, "of", num_genes)

            if feature == "transcript":
                success, response, response_content_type = server.execute_query(
                    prefix=[INTERFACE, "set_transcript"],
                    data = {
                        idb.Attribute("genome"): args.genome,
                        idb.Attribute("chromosome"): chromosome,
                        idb.Attribute("gene_set"): args.gene_set,
                        idb.Attribute("gene_id"): gene_id,
                        idb.Attribute("transcript_id"): transcript_id,
                        idb.Attribute("start"): int(start),
                        idb.Attribute("end"): int(end),
                        idb.Attribute("strand"): strand
                    },
                    verbose=False
                )
            else: 
                success, response, response_content_type = server.execute_query(
                    prefix=[INTERFACE, "set_exon"],
                    data = {
                        idb.Attribute("genome"): args.genome,
                        idb.Attribute("chromosome"): chromosome,
                        idb.Attribute("transcript_id"): transcript_id,
                        idb.Attribute("exon_id"): exon_id,
                        idb.Attribute("feature"): feature,
                        idb.Attribute("start"): int(start),
                        idb.Attribute("end"): int(end),
                        idb.Attribute("strand"): strand
                    },
                    verbose = False
                )

    elif args.repeat_masker_output:
        seen_repeat_ids = {}
        with open(args.repeat_masker_output, "r") as file:
            next(file) #throw away header lines
            next(file)
            next(file)
            for line in file:
                score, div, deletion, insertion, chromosome, start, end, left, strand, repeat_family, repeat_class, sub_start, sub_end, left2, repeat_num  = line.split()

                unique_repeat_id = "RepeatMasker" + args.gene_set + args.genome + repeat_num

                if unique_repeat_id not in seen_repeat_ids:
                    seen_repeat_ids[unique_repeat_id] = 1
                    success, response, response_content_type = server.execute_query(
                        prefix=[INTERFACE, "set_transcript"],
                        data = {
                            idb.Attribute("genome"): args.genome,
                            idb.Attribute("chromosome"): chromosome,
                            idb.Attribute("gene_set"): args.gene_set,
                            idb.Attribute("gene_id"): repeat_class,
                            idb.Attribute("transcript_id"): unique_repeat_id,
                            idb.Attribute("start"): int(start),
                            idb.Attribute("end"): int(end),
                            idb.Attribute("strand"): strand
                        },
                        verbose=False
                    )
                sub_repeat_id = seen_repeat_ids[unique_repeat_id]
                success, response, response_content_type = server.execute_query(
                    prefix=[INTERFACE, "set_exon"],
                    data = {
                        idb.Attribute("genome"): args.genome,
                        idb.Attribute("chromosome"): chromosome,
                        idb.Attribute("transcript_id"): unique_repeat_id,
                        idb.Attribute("exon_id"): sub_repeat_id,
                        idb.Attribute("feature"): repeat_family,
                        idb.Attribute("start"): int(sub_start),
                        idb.Attribute("end"): int(sub_end),
                        idb.Attribute("strand"): strand
                    },
                    verbose = False
                )   
                seen_repeat_ids[unique_repeat_id] += 1








