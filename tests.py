import unittest
from build import make_parser
import intelliwaterai.infinitydb.access as idb
from build import INTERFACE

GENOME = idb.Attribute("genome")
CHROMOSOME = idb.Attribute("chromosome")
POSITION = idb.Attribute("position")
BASE = idb.Attribute("base")

class QueryTests(unittest.TestCase):
    def setUp(self):
        self.server = idb.InfinityDBAccessor(
            server_url = "https://localhost:37411/infinitydb/data",
            db = "boilerbay/genomics",
            user = "ai",
            password = "ai"
        )



    def test_set_bases(self):
        data = {
            (GENOME, "dinosaur", CHROMOSOME, "chr1", POSITION, 0, BASE, "A"): None,
            (GENOME, "dinosaur", CHROMOSOME, "chr1", POSITION, 1, BASE, "C"): None,
            (GENOME, "dinosaur", CHROMOSOME, "chr1", POSITION, 2, BASE, "T"): None
        }

        self.server.execute_query(
            prefix = [INTERFACE, "set_base"],
            data = data,
        )