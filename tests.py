import unittest
from build import make_parser
import intelliwaterai.infinitydb.access as idb
from build import INTERFACE


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.server = idb.InfinityDBAccessor(
            server_url = "https://localhost:37411/infinitydb/data",
            db = "boilerbay/genomics",
            user = "ai",
            password = "ai"
        )


    def test_set_bases(self):
        self.server.execute_query(
            prefix = [INTERFACE, "set_bases"],
            data = {
                idb.Attribute("genome"): "dinosaur",
                idb.Attribute("chromosome"): "chr1",
                idb.Attribute("start"): 0,
                idb.Attribute("length"): 10,
                idb.Attribute("bases"): "ACTAGGACAGT"
            }
        )