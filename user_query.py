import intelliwaterai.infinitydb.access as idb

from queries import make_parser, INTERFACE

parser = make_parser()

parser.add_argument("query")
parser.add_argument("data")
args = parser.parse_args()

server = idb.InfinityDBAccessor(
    server_url = args.server,
    db = args.database,
    user = args.user,
    password = args.password
)
server.is_verification_enabled = False

query_data = {}
params = args.data.split()
if not len(params) % 2 == 0:
    raise RuntimeError("Each parameter must have an attribute")

for i in range(0, len(params), 2):
    attrib = idb.Attribute(params[i])
    val = params[i+1]
    query_data[attrib] = val

success, result, response_content_type = server.execute_query(
    prefix = [INTERFACE, args.query],
    data = query_data
)
if success:
    print("Query was successful.")
    for attrib in result:
        print(str(attrib) + ":", *list(result[attrib].keys()))
        print(result)
else:
    print("Query failed.")