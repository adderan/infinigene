# Copyright (c) 2019-2021 Roger L. Deran
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject
# to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in  all copies or substantial portions
# of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
# THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Other parts of the InfinityDB software are not free and/or not open-source.

"""InfinityDB database access utilities

Allow access to an InfinityDB database server via http(s) 
REST requests and JSON encoded data or blobs. See boilerbay.com. 
The rest of the InfinityDB software is not free or open source.

Requires Python v3. 
"""
import base64
import datetime
import dateutil.parser
import json
import re
import urllib.request
from requests import Request, Session

__author__ = 'Roger L Deran'
__version__ = '1.1'
__all__ = ['InfinityDBAccessor',
           'escape_uri_components',
           'underscore_quote',
           'underscore_quote_key',
           'underscore_unquote',
           'parse_primitive',
           'to_json_extended',
           'Attribute',
           'EntityClass',
           'Index',
           'flatten_to_tuples',
           'unflatten_from_tuples',
           'flatten_lists_to_indexes',
           'unflatten_lists_from_indexes',
           'compact_tree_tips',
           'uncompact_tree_tips',
           'is_legal_entity_class_name',
           'is_legal_attribute_name',
           'parse_token_string_into_components',
           'item_to_tuples',
           'json_quote_primitives',
           'json_quote_primitive'
           ]

"""
'first_item',
'first_component',
'first_tuple',
'next_item',
'next_component',
'next_tuple',
'last_item',
'last_component',
'last_tuple',
'previous_item',
'previous_component',
'previous_tuple',
'get_items'
'get_items_batch'
'execute_query'
"""


def is_legal_entity_class_name(s):
    return (_entity_class_attribute_regex.match(s)
            and s[0] >= 'A' and s[0] <= 'Z')


def is_legal_attribute_name(s):
    return (_entity_class_attribute_regex.match(s)
             and s[0] >= 'a' and s[0] <= 'z')

""" The special InfinityDB components that can appear in an Item.

Their names match [a-zA-Z][a-zA-Z0-9_.-]* or are numeric ids.
An EntityClass component is normally first and can be thought of as
a 'table name'.  It can occur later frequently.
An Attribute component is like a 'column name'.  For an 
EntityClass 'E' and a primitive or composite called 'entity', 
and an Attribute 'a', and a primitive  or composite 'v', 
one often sees: [E, e, a, v] as a 'quad', sometimes with 
an 'inversion' [EInverse, v, aInverse, e]. EntityClasses 
start with an uppercase letter, Attributes with lowercase.
"""


# TODO it would be good to be able to compare magnitudes of different
# component types, including EntityClass, Attribute, and Index,
# as well as the primitive component types since that is possible
# in InfinityDB as components of Items. In fact all component types
# can be compared, and there is a fixed order of the types,
# with Index last.
#
# Also, EC and Att identified using ids should sort differently
# from the named ones, but we just use the string in any case,
# and that comparison will be slower, but the
# id-based ones are rare now.
class EntityClass:
    """ EntityClass corresponds to the InfinityDB EntityClass 
    component type.
    
    When a JSON-encoded access to the InfinityDB server occurs, 
    any EntityClass components in the Items transferred use 
    EntityClass instances as the keys in corresponding dict. 
    
    An EntityClass is identified solely by its string 
    value, or if that is not given, then it is 
    identified by its integer id.
    """

    def __init__(self, value):
        if isinstance(value, str):
            self.s = value
            self.id = -1
            if not is_legal_entity_class_name(value):
                raise ValueError(
                    "InfinityDB EntityClass name "
                    "must match [A-Z][A-Za-z0-9._-]*: " + value
                    )
        elif isinstance(value, int):
            self.s = 'EntityClass(' + str(value) + ')'
            self.id = int(value)
        else:
            raise ValueError("An EntityClass "
                             "requires a string or int")

    def __str__(self):
        return self.s

    def __repr__(self):
        return self.s

    def __hash__(self):
        return hash(self.id) if self.id != -1 else hash(self.s)

    def __eq__(self, other):
        return isinstance(other, EntityClass) and self.s == other.s

    def __ne__(self, other):
        return not isinstance(other, EntityClass) or self.s != other.s

    def __lt__(self, other):
        if not isinstance(other, EntityClass):
            raise TypeError("Unorderable types:"
                            "not both InfinityDB EntityClasses")
        return self.s < other.s

    def __gt__(self, other):
        if not isinstance(other, EntityClass):
            raise TypeError("Unorderable types: "
                            "not both InfinityDB EntityClasses")
        return self.s > other.s

    def __le__(self, other):
        if not isinstance(other, EntityClass):
            raise TypeError("Unorderable types: "
                            "not both InfinityDB EntityClasses")
        return self.s <= other.s

    def __ge__(self, other):
        if not isinstance(other, EntityClass):
            raise TypeError("Unorderable types: "
                            "not both InfinityDB EntityClasses")
        return self.s >= other.s


class Attribute:
    """ Attribute corresponds to the InfinityDB 
    Attribute component type.
    
    When a JSON-encoded access to the InfinityDB 
    server occurs, any Attribute components in the Items 
    transferred use Attribute instances as the keys
    in corresponding dict.
    
    An Attribute is identified solely by its string 
    value, or if that is not given, then it is 
    identified by its integer id.
    """

    def __init__(self, value):
        if isinstance(value, str):
            self.s = value
            self.id = -1
            if not is_legal_attribute_name(value):
                raise ValueError(
                    "InfinityDB Attribute name must "
                    "match [a-z][A-Za-z0-9._-]*: " + value)
        elif isinstance(value, int):
            self.s = 'Attribute(' + str(value) + ')'
            self.id = int(value)
        else:
            raise ValueError(
                    "An InfinityDB Attribute requires "
                    "a string or int id")

    def __str__(self):
        return self.s

    def __repr__(self):
        return self.s

    def __hash__(self):
        return hash(self.id) if self.id != -1 else hash(self.s)

    def __eq__(self, other):
        return isinstance(other, Attribute) and self.s == other.s

    def __ne__(self, other):
        return not isinstance(other, Attribute) or self.s != other.s

    def __lt__(self, other):
        if not isinstance(other, Attribute):
            raise TypeError("Unorderable types: not "
            "both InfinityDB Attributes")
        return self.s < other.s

    def __gt__(self, other):
        if not isinstance(other, Attribute):
            raise TypeError("Unorderable types: "
            "not both InfinityDB Attributes")
        return self.s > other.s

    def __le__(self, other):
        if not isinstance(other, Attribute):
            raise TypeError("Unorderable types: "
            "not both InfinityDB Attributes")
        return self.s <= other.s

    def __ge__(self, other):
        if not isinstance(other, Attribute):
            raise TypeError(
                "Unorderable types: not "
                "both InfinityDB Attributes")
        return self.s >= other.s


class Index:
    """ Index corresponds to the InfinityDB Index component type.
    
    Transferring data as JSON to and from the InfinityDB REST
    access encodes the lists as JSON lists. However, internally
    InfinityDB stores lists as Items having Index components.
    
    It is possible to flatten a list to a pure dict in which the
    keys are Indexes. This allows dicts and lists to be
    flattened to dict trees in which the keys are tuples that
    represent paths, and which can contain Indexes in the tuples.
    Such a representation is more convenient in some situations,
    and it corresponds more directly to the encoding of data
    in InfinityDB as sets of Items.
    
    An Index is identified solely buy its index integer attribute.
    The dicts containing Index component keys will automatically be
    encoded as Python lists, however, transparently.
    """

    def __init__(self, index):
        if isinstance(index, int):
            self.index = index
        else:
            raise ValueError("An InfinityDB Index "
                             "component requires an int")

    def __str__(self):
        return '[' + str(self.index) + ']'

    def __repr__(self):
        return '[' + str(self.index) + ']'

    def __hash__(self):
        return hash(self.index)

    def __eq__(self, other):
        return isinstance(other, Index) and self.index == other.index

    def __ne__(self, other):
        return (not isinstance(other, Index) or
                self.index != other.index)

    def __lt__(self, other):
        if not isinstance(other, Index):
            raise TypeError("Unorderable types: not "
                "both InfinityDB Indexes")
        return self.index < other.index

    def __gt__(self, other):
        if not isinstance(other, Index):
            raise TypeError("Unorderable types: not "
                "both InfinityDB Indexes")
        return self.index > other.index

    def __le__(self, other):
        if not isinstance(other, Index):
            raise TypeError("Unorderable types: not "
            "both InfinityDB Indexes")
        return self.index <= other.index

    def __ge__(self, other):
        if not isinstance(other, Index):
            raise TypeError("Unorderable types: not "
            "both InfinityDB Indexes")
        return self.index > other.index

    def get_index(self):
        return self.index


def escape_uri_components(*k):
    """ This is for accessing the InfinityDB via a URL 
    that ends with a path down into the database, which 
    can be considered to be a key prefix to traverse 
    the logical JSON.
     
    The escaped path has '/' separators but the components 
    do not. For example, to access the 10'th element of the
    outer array, and the "temp" key of the object at that 
    position, do escape_uri_components([10],'temp'). The 
    keys do not have to be strings, because we store 
    logically extended json. Keys can be dates as well.
    """
    p = []
    for s in k:
        if s == None:
            p.append('null')
        elif s is True:
            p.append('true')
        elif s is False:
            p.append('false')
        elif isinstance(s, str):
            p.append('"' + s + '"')
        elif isinstance(s, datetime.datetime):
            p.append(s.isoformat())
        elif isinstance(s, list):
            # A one-element list is just used to represent
            # an index into a JSON array
            if len(s) != 1 or not isinstance(s[0], int):
                raise TypeError(
                    "an array index must be a single int")
            p.append('[' + str(s[0]) + ']')
        elif isinstance(s, float) or isinstance(s, int):
            p.append(str(s))
        elif isinstance(s, EntityClass) or isinstance(s, Attribute):
            p.append(str(s))
        elif isinstance(s, Index):
            p.append('[' + s.get_index() + ']')
        else: raise TypeError("a primitive, index, "
            "or date is expected")
    return ''.join(['/' + urllib.request.quote(s, safe='') for s in p])


def to_json_extended(o, indention=0):
    """ Return a string encoded in the infinitydb 
    extended JSON format for a structure o, including 
    dates and non-string keys. Tuples become arrays.
    """
    is_first = True
    s = ''
    ind = ' ' * indention
    if o == None:
        return 'null'
    elif o is True:
        return 'true'
    elif o is False:
        return 'false'
    elif isinstance(o, dict):
        s = '{'
        for k in o:
            if not is_first: s += ','
            s += '\r\n   ' + ind + to_json_extended(k, indention + 4)
            s += ' : ' + to_json_extended(o[k], indention + 4)
            is_first = False
        if not is_first: s += '\r\n' + ind
        s += '}'
    elif isinstance(o, (list, tuple)):
        s = '['
        for v in o:
            if not is_first: s += ','
            s += '\r\n    ' + ind + to_json_extended(v, indention + 4)
            is_first = False
        if not is_first: s += '\r\n' + ind
        s += ']'
    elif isinstance(o, str): s = json_quote_string(o)
    elif isinstance(o, datetime.datetime): s = o.isoformat()
    else: s = str(o)
    return s


# experimental
def json_quote_string(s):
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    quoted = '"'
    # duplicate any backslashes
    for c in s:
        quoted += c if c != '\\' else '\\\\'
    return quoted + '"'


# start is offset in s. Return parsed_string, True if found, offset after string
# Using json.loads(s) has no start, after_string, or found boolean result.
# experimental
def json_parse_string(s, *, start=0):
    if len(s) <= start or  s[start] != '"':
        return '', False, start
    content = ''
    i = start + 1
    while i < len(s):
        c = s[i]
        if c == '"':
            return content, True, i + 1
        elif c == '\\':
            i += 1
            if i >= len(s):
                raise TypeError("end of string after backslash in: '" + s + "'")
            content += s[i]
        else:
            content += c
        i += 1
    raise TypeError("ending quote not found in: '" + s + "'")


# Only for differentiating ints and floats
# Regexes may have ReDOS characteristics for some input data,
# which cannot easily be proved, so it should be done differently.
_float_regex = re.compile('[+-]?[0-9]+[.]')
# only for differentiating numbers and dates
_date_regex = re.compile('[0-9]+[-]')
_entity_class_attribute_regex = re.compile('[a-zA-Z][a-zA-Z0-9_.-]*')


def underscore_quote(o):
    """ Pre-process a general structure o by changing its 
    keys and dates to strings using prefixed underscores 
    as a quote.
    
    The result is suitable for JSON encoding.
    TODO: byte[], char[], ByteString
    """
    if isinstance(o, dict):
        return {underscore_quote_key(k) : underscore_quote(v)
                for k, v in o.items()}
    elif isinstance(o, list):
        return [underscore_quote(v) for v in o]
    elif isinstance(o, tuple):
        return tuple(underscore_quote(v) for v in o)
    elif isinstance(o, bytes):
        o = o.decode('utf-8')
        return o if o[0] != '_' else '_' + o
    elif isinstance(o, str):
            # stuff an extra underscore
            return o if o == '' or o[0] != '_' else '_' + o
    elif isinstance(o, datetime.datetime):
        return '_' + o.isoformat()
    elif isinstance(o, EntityClass) or isinstance(o, Attribute):
        return '_' + str(o)
    else: return o


def underscore_quote_key(k):
    """ Make any primitive or date into an 'underscore-quoted' 
     string for use as a JSON key when serializing into JSON"""
    if k == None:
        return '_null'
    elif isinstance(k, bool):
        return '_true' if k else '_false'
    elif isinstance(k, int) or isinstance(k, float):
        return '_' + str(k)
    elif isinstance(k, bytes):
        k = k.decode('utf-8')
        # stuff an extra underscore if necessary
        return k if k[:1] != '_' else '_' + k
    elif isinstance(k, str):
        # stuff an extra underscore if necessary
        return k if k[:1] != '_' else '_' + k
    elif isinstance(k, datetime.datetime):
        return '_' + k.isoformat()
    elif isinstance(k, EntityClass) or isinstance(k, Attribute):
        return '_' + str(k)
    else:
        raise TypeError('keys must be primitive or date')


def underscore_unquote(o):
    """ Take a limited structure that was read in as
    JSON and convert to a more general Python structure 
    having non-string keys as well as key or value dates.
    
    The non-string keys and dates are encoded as strings 
    with an initial '_', while strings originally starting 
    with '_' have another '_' stuffed at the front. Keys 
    must be primitives, however. e.g.: 
    o = underscore_unquote(json.loads(s))
    """
    # TODO bug: index primitives break in parse_primitive(),
    # but should turn into lists.
    if isinstance(o, dict):
        return {underscore_unquote(k) :
                 underscore_unquote(v) for k, v in o.items()}
    elif isinstance(o, list):
        return [underscore_unquote(v) for v in o]
    elif isinstance(o, tuple):
        return tuple(underscore_unquote(v) for v in o)
    elif isinstance(o, str):
        if len(o) == 0:
            return o
        elif o[0:2] == '__':
            # Undo the 'underscore stuffing' for
            # strings containing an initial '_'
            return o[1:]
        elif o[0] == '_':
            # an underscore-quoted primitive
            return parse_primitive(o[1:])
        else: return o
    else: return o


# TODO: byte string, byte array, char array
def parse_primitive(s):
    if len(s) == 0:
        raise TypeError("InfinityDB primitive "
                        "value expected, but is empty")
    elif s == 'true':
        return True
    elif s == 'false':
        return False
    elif s == 'null':
        return None
    elif s[0].isdigit() or s[0] == '+' or s[0] == '-':
        if _date_regex.match(s):
            return dateutil.parser.parse(s)
#        elif match(_float_regex, s):
        elif '.' in s:
            # BUG
            # we lose the distinction between float and double
            # provided by InfinityDB
            return float(s if s[-1:] != 'f' else s[:-1])
        else: return int(s)
    elif s[0] == '[':
        if s.find(']') != len(s) - 1:
            raise TypeError(
                "InfinityDB primitive index component "
                "does not end with ']': " + s)
        try:
            index = int(s[1:-1])
        except TypeError:
            raise TypeError("InfinityDB primitive index "
                "component must contain an int: '" + s + "'")
        return Index(index)
    elif _entity_class_attribute_regex.match(s):
        c = s[0]
        if 'A' <= c <= 'Z':
            return EntityClass(s)
        elif 'a' <= c <= 'z':
            return Attribute(s)
    elif s[0] == '"':
        parsed_string, found, offset_after_string = json_parse_string(s);
        if found:
            if offset_after_string != len(s):
                raise TypeError("InfinityDB string "
                                "does not end at component end: '" + s + "'")
            return parsed_string
    raise TypeError('InfinityDB primitive value expected: ' + s)


# Note \r and \n are considered white space between tokens
def parse_token_string_into_components(s):
    """ Convert a string into a list of components as tokens """
    components = []
    component = ''
    i = 0;
#    while i < len(s) and s[i] not in '\r\n\t\v\f':
    while True:
        # handle embedded white
        parsed_string, found, offset_after_string = json_parse_string(s, start=i)
        if  found:
            i = offset_after_string
            component = parsed_string
        else:
            # Skip non-white. Only strings contain white.
            j = i
            while j < len(s) and s[j] not in ' \r\n\t\v\f':
                j += 1
            component = parse_primitive(s[i:j])
            i = j
        components.append(component)
        # skip white between components
        while i < len(s) and s[i] in ' \r\n\t\v\f':
            i += 1
        if i == len(s):
            break
    return components


def json_quote_primitives(o):
    """ Pre-process recursively a structure of dicts, lists and tuples 
    by changing dates to quoted ISO strings, strings to JSON quoted 
    strings, everything else to a quoted string. However None, 
    numbers and booleans are left alone except as keys as they 
    are left alone by json.dumps().
    
    The result is suitable for JSON encoding by json.dumps().
    """
    if o == None or isinstance(o, float) or isinstance(o, int) or isinstance(o, bool):
        return o
    elif isinstance(o, dict):
        return {json_quote_primitive(k) : json_quote_primitives(v)
                for k, v in o.items()}
    elif isinstance(o, list):
        return [json_quote_primitives(v) for v in o]
    elif isinstance(o, tuple):
        return tuple(json_quote_primitives(v) for v in o)
    else:
        return json_quote_primitive(o)


def json_quote_primitive(o):
    """ TODO InfinityDB CharArray, ByteArray, and ByteString 
    component types, which need
    their own classes like EntityClass and Attribute.
    However, we use those only in the db itself, because
    we access them as blobs except ByteString, which is not 
    used much.
    """
    if isinstance(o, bytes):
        o = o.decode('utf-8')
    if isinstance(o, str):
        # doubly-quoted
        return '"' + json_quote_string(o) + '"'
    elif isinstance(o, datetime.datetime):
        return '"' + o.isoformat() + '"'
    return '"' + str(o) + '"'


def flatten_to_tuples(o, *, flattened_lists, compact_tips):
    """Convert a nested dict tree into one with tuple keys 
    that represent paths within the original tree. 
     
    This is very  convenient for working with trees that 
    represent sets of Items to  be logically interchanged with 
    InfinityDB, as the models are similar. The tuple keys may 
    have zero or more elements, with mixed lengths. A tuple that
    is a prefix of another cannot, however, be represented
    in the normal non-tuple tree form of nested dicts and will 
    disappear after converted back.
    
    Any EntityClass or Attribute keys found delimit the tuples, 
    so they never occur within the tuple elements. The resulting 
    tree is then an alternation depth-wise between keys that are 
    simple EntityClass and Attribute instances, and tuple keys 
    between them. This allows a high degree of forwards and 
    backwards compatibility, as the tuples can be various 
    lengths and can be extended in future databases without 
    causing incompatibilities with old code. InfinityDB can deal 
    with its Items in the same way.
    
    The InfinityDB accessor does no conversion, and the client code
    must do it, so that there are no tuple keys given to or 
    returned by the accessor. The accessor works logically 
    on JSON, i.e. nested Python lists and dicts with non-tuple
    keys. Also, the accessor assumes the terminals have been 
    compacted with compact_tree_tips(), because a terminal {} 
    will cause the Item to disappear.
    
    Note that the flattening functions sometimes try to share
    references to components and subtrees rather than 
    copying them.
    
    Args:
    flattened_lists: if not, make the resulting tree have lists, or else
        put Indexes in the tuples to represent them. The Index class
        is a simple integer key that represents the position of 
        the child tree within the list. So, for flattened_lists true,
        {x,[{y:0}]} becomes {(x,Index(0),y,0):None}
    compact_tips: if a tip can be represented without 
        nesting, do so. So {k:{}} becomes k, and {(k):None} becomes
        k. The result is some compact {k:v} terminals where k is 
        a non-tuple and v is not a dict or list. For multi-key dicts, 
        {k1:{},k2:{}} becomes {k1:None,k2:None}
        If None, do nothing to the tips.
        
    Returns:
        flattened  tree
    """
    if flattened_lists:
        # lists become dicts with keys that are
        # Indexes having increasing ids
        rslt = flatten_lists_to_indexes(o)
    else:
        rslt = unflatten_lists_from_indexes(o, strict=False)
    rslt = flatten_to_tuples_preserving_lists(rslt)
    if compact_tips == None:
        return rslt
    elif compact_tips:
        return compact_tree_tips(rslt)
    else:
        return uncompact_tree_tips(rslt)

""" Flatten, preserving lists.

Any Index keys i.e. components already there 
become part of the tuples.
"""


def flatten_to_tuples_preserving_lists(o):
    if not o:
        return o
    if isinstance(o, dict):
        rslt = {}
        for k, v in o.items():
            nested = flatten_to_tuples_preserving_lists(v)
            if nested == {}:
                return {(k,):None}
            elif isinstance(nested, dict):
                for k2, v2 in nested.items():
                    if isinstance(k, (EntityClass, Attribute)):
                        if isinstance(k2, (EntityClass, Attribute)):
                            rslt[k] = {():{k2:v2}}
                        else:
                            if not k in rslt:
                                rslt[k] = {}
                            rslt[k][k2] = v2
                    else:
                        if isinstance(k2, (EntityClass, Attribute)):
                            rslt[(k,)] = {k2:v2}
                        else:
                            rslt[(k, *k2)] = v2
            elif isinstance(nested, (EntityClass, Attribute, list)):
                if isinstance(k, (EntityClass, Attribute)):
                    rslt[k] = nested
                else:
                    rslt[(k,)] = nested
            elif v == None:
                rslt[(k)] = None
            else:
                rslt[(k, v)] = None
        return rslt
    elif isinstance(o, list):
        return [flatten_to_tuples_preserving_lists(e) for e in o]
    return {(o,):None}

""" Convert lists in the dict tree to lists.

This prepares for flattening_to_tuples().
"""


def flatten_lists_to_indexes(o):
    if isinstance(o, dict):
        return {k:flatten_lists_to_indexes(v) for k, v in o.items()}
    elif isinstance(o, list):
        return {Index(i):flatten_lists_to_indexes(e)
                for i, e in enumerate(o)}
    else:
        return o

""" 
Undo the effects of flatten_to_tuples() except for 
the conversion of Index components back into lists.
Also see unflatten_lists_from_indexes().So for {(x,y):z}
you get {x :{y: {z: None}}}. Use compact_tree_tips() if
you want, so that {..{x: {y: None}}} becomes {..{x:y}}.
A simple {x:y} is unchanged.
The form {x : {y : {}}} is not used, because it 
can be interpreted as non-existent even though it
is more appealing and might sometimes be easier to work with.
Also, x or [y,z] is unchanged but [(x,y),(z)] becomes
[{x: {y: None}},{z: None}]. A bare (x,y) becomes {x: {y: Nnne}}
Generally, the server regards x and {x : None} as the same, 
both representing a singleton x.

This makes everything convertible into JSON and from JSON
into Items, for the REST interface to InfinityDB v6 server.
However, the reverse conversion does not produce the same
tuple keys, and tuple keys are only created when nested
inside or outside of metas. The reverse conversion also
normalizes by combining immediately nested tuple keys 
into a single tuple key. 
"""


def make_tuples_into_nested_objects(o):
    if not o:
        return None
    if isinstance(o, tuple):
            return {o[0] : make_tuples_into_nested_objects(o[1:])}
    elif isinstance(o, dict):
        o2 = {}
        for k in o:
            if k == ():
                if isinstance(o[k], dict):
                    for k2 in o[k]:
                        o2[k2] = make_tuples_into_nested_objects(o[k])
                else:
                    o2[k] = ()
            elif isinstance(k, tuple):
                if len(k) == 1:
                    o2[k[0]] = make_tuples_into_nested_objects(o[k])
                else:
                    o2[k[0]] = make_tuples_into_nested_objects({k[1:] : o[k]})
            elif isinstance(k, (list, dict)):
                raise TypeError
            else:
                o2[k] = make_tuples_into_nested_objects(o[k])
        return o2
    elif isinstance(o, list):
        return [make_tuples_into_nested_objects(o[i]) for i, _ in enumerate(o)]
    else:
        return o


def remove_empty_tuples(o):
    if isinstance(o, dict):
        if () in o:
            return remove_empty_tuples(o[()])
    return remove_empty_tuples(o)


def compact_tree_tips(o):
    """ Translate from terminals like {k:{}} to k and from {(k):None} 
    to k, possibly at the ends of the branches of a tree. This means
    that {k1:{k2:{}} becomes {k1:k2}.
    
    But note that, {(k):{}} becomes (k).
    We do not combine {(k):{(k2):{}}} to become {(k,k2):None} though.
    To do that, convert and re-establish the tuples with 
    make_tuples_into_nested_objects() and then flatten_to_tuples().
    Also, multi-key dicts like {k:{},k2:{}} are left intact, 
    but those with tuples like {(k1):None,k2:{}} become {k1:{},k2:{}}
    """
    if isinstance(o, dict):
        if len(o) == 1:
            for k, v in o.items():
                if v == {}:
                    return k
                elif isinstance(k, tuple) and len(k) == 1:
                    if v == None:
                        return k[0]
                    else:
                        return {k:compact_tree_tips(v)}
                elif isinstance(k, (dict, list)):
                    raise TypeError("impossible dict: "
                                    "keys are dicts or lists")
                break
        return {k:compact_tree_tips(v) for k, v in o.items()}
    elif isinstance(o, list):
        return [compact_tree_tips(e) for e in o]
    else:
        return o


def uncompact_tree_tips(o):
    """ Normalize the tree so {k,v} becomes {k:{v: None}}.
    
    This undoes compact_tree_tips(). Note {(k1,k2):None} is 
    not affected. For that, use make_tuples_into_nested_objects()
    """
    if isinstance(o, dict):
        rslt = {}
        for k, v in o.items():
            if isinstance(k, tuple) and v == None:
                if len(k) == 1:
                    rslt[k[0]] = None
                else:
                    # Can't get rid of a long tuple here.
                    # Use unflatten().
                    rslt[k] = None
            elif (not isinstance(k, (tuple, dict, list))
                  and not isinstance(v, (tuple, dict, list))):
                rslt[k] = {v: None}
            else:
                rslt[k] = uncompact_tree_tips(v)
        return rslt
    elif isinstance(o, list):
        return [uncompact_tree_tips(e) for e in o]
    else:
        return {o: None}


def unflatten_lists_from_indexes(o, *, strict=True,
                             collapse_sparseness=False):
    """ Change a dict that has Index keys into an actual 
    list recursively.
    
    Keys must not be tuples, so first use an 
    unflatten_from_tuples() if necessary. A dict that is to be 
    converted to a list must have only Index keys.
    
    An Index component is an instance of the Index class, and 
    it contains an int that represents the position in a list 
    when it is a dict key. So, dicts may be used in place of 
    lists, by using Index keys. InfinityDB has a corresponding 
    Index component type that can be mixed with any other component 
    type, such as primitive components, in any Item at any position.
    
    InfinityDB can compare components of any of its 12 
    component types according to a strict inter-type ordering 
    that puts Index components last. So, InfinityDB never 
    causes errors in constructing Items or comparing Items, 
    while Python cannot compare, say strings and numbers.
    
    strict: 
        the conversion raises ValueError if a mixture of Index and 
        others are present as keys in a given dict. No mixtures will be 
        present if the tuple keys were created using 
        flatten_to_tuples() when
        it works on actual lists, but if there are Index components 
        already there as as bare keys in a dict, they can end up 
        mixed with non-Index components. InfinityDB can represent 
        any mixture.
    collapse_sparseness: 
        if a dict contains Index component keys alone, it can 
        be converted to  a list, but the Index components do 
        not necessarily ascend monotonically, and if not, we can 
        remove the logical None's between them. 
        flatten_to_tuples() always creates monotonic Indexes,
        but InfinityDB can represent sparse arrays without Nones.
    """
    if isinstance(o, list):
        return [
            unflatten_lists_from_indexes(e,
                strict=strict,
                collapse_sparseness=collapse_sparseness) for e in o]
    if not isinstance(o, dict) or len(o) == 0:
        return o
    # Tf any element is not an index, we can't convert to a
    # real list, so we have to leave the Index components in there.
    # InfinityDB can mix Index components with others.
    contains_index = False
    contains_non_index = False
    for k in o:
        if isinstance(k, Index):
            contains_index = True
        else:
            contains_non_index = True
        if contains_index and contains_non_index and strict:
            raise ValueError
        if contains_non_index:
            break
    if contains_index and contains_non_index and strict:
        raise ValueError
    if contains_index and not contains_non_index:
        # all keys are Index components, so we can convert it to a list
        rslt = []
        i = 0
        # The sort never raises a TypeError because there
        # are no non-Index keys
        for index in sorted(o):
            # handle sparseness if present
            if not collapse_sparseness:
                while i < index.get_index():
                    rslt.append(None)
                    i += 1
            rslt.append(unflatten_lists_from_indexes(
                o[index], strict=strict,
                collapse_sparseness=collapse_sparseness
                ))
            i += 1
        return rslt
    else:
        # Actually InfinityDB can represent mixtures of
        # any type, under any given prefix, so after this,
        # there may still be some Indexes there as keys.
        return {
            k: unflatten_lists_from_indexes(
                v,
                strict=strict,
                collapse_sparseness=collapse_sparseness
                )
             for k, v in o.items()
             }


def item_to_tuples(item):
    """ Change an Item, which is a list of components, into a list
    of tuples, EnitityClasses, and Attributes, 
    like [[],MyEC,['some entity',9],my_att,['some value',42]]. 
    There is always at least one tuple, but it may be empty. Tuples are
    delimited by the start and end, and by any intervening
    EntityClasses and Attribute components. Each EntityClass or
    Attribute comes between tuples, so there are n + 1 tuples,
    where n is the number of EntityClasses plus Attributes.
    Because there is almost always an initial EntityCLass,
    the first tuple will almost always be empty.
    """
    tuple = []
    tuples = []
    for i in range(len(item)):
        if isinstance(item[i], (EntityClass, Attribute)):
            tuples.append(tuple)
            tuple = []
            tuples.append(item[i])
        else:
            tuple.append(item[i])
    tuples.append(tuple)
    return tuples


class InfinityDBError(IOError):

    def __init__(self, *, code, reason=None):
        super().__init__(code, reason)


class InfinityDBAccessor:
    """ The essential accessor class.
    
    infdb=InfinityDBAccessor('https://infinitydb.com:37411',
    user='testUser', password='db')
    
    In order to read the the documentation out of the 
    read-only demo database go to: https://infinitydb.com:37411/
    infinitydb/data/demo/readonly/Documentation?action=edit
    success, content = db.get_json('demo/readonly','Documentation')
    """

    # cafile, cacerts, cadata are for an explicit truststore
    # with the old v2 mode before Requests.

    # The old v2 mode with urllib2 cannot keep-alive, but
    # the new mode with Requests does. That eliminates
    # the problem with running out of ephemeral ports. You
    # get 60K ports that each go into TIME_WAIT mode for
    # 4 minutes.
    def __init__(self, server_url, *, db=None, user=None, password=None,
                 cafile=None, cacerts=None, cadata=None, v2=False,
                 default_parameters={}):
        self.server_url = server_url
        # default if not provided in client call
        self.db = db
        self.user = user
        self.password = password
        self.context = None
        self.next_buf = None
        self.default_parameters = default_parameters.copy()
        # Version 2 of urllib2, otherwise version 3, with Requests, for
        # keep-alive, and more speed, especially with SSL/TLS.
        self.v2 = v2
        if v2:
            if server_url[0:5].lower() is 'https':
                import ssl
                self.context = ssl.create_default_context(cafile=cafile,
                                                        cacerts=cacerts,
                                                        cadata=cadata)
        else:
            import ssl
            print(ssl.get_default_verify_paths())
            self.session = Session()

    def _make_headers(self, content_type=None):
        headers = {}
        if self.user is not None:
            b = '%s:%s' % (self.user, self.password)
            b = b.encode()
            b = base64.encodebytes(b)[:-1]
            b = b.decode()
            headers['Authorization'] = 'Basic %s' % b
        if content_type is not None:
            headers['Content-Type'] = content_type
        return headers

    def head(self):
        # TODO only for v3
        if self.v2:
            raise ValueError
        full_url = self.server_url + '/' + self.db
        headers = self._make_headers()
        """ To be used to verify connectivity."""
#         request = Request('HEAD', self.server_url, headers=headers)
#         prepped_request = self.session.prepare_request(request)
#        response = self.session.send(prepped_request)
# TODO XXX remove verify=False
        response = self.session.request('HEAD', full_url,
                                        headers=headers, verify=False)
        if (response.status_code == 204):
            response.status_code = 200
        return response.status_code, response.reason

    def create_params(self, **kwargs):
        params = ''
        kwargs_copied = self.default_parameters.copy()
        kwargs_copied.update(kwargs)
        for kw, value in kwargs_copied.items():
            params += '&' if params else '?'
            if value is None:
                # this leaves an extra '&'
                pass
            elif value is True:
                params += kw + '=true'
            elif value is False:
                params += kw + '=false'
            elif isinstance(value, str):
                params += kw + '=' + value
            elif isinstance(value, int):
                params += kw + '=' + str(value)
            else:
                raise ValueError
        return params

    QUERY_REQUEST_PARAMETER = "query-parameter"
    
    def _do_command(self, prefix, *, db, action=None,
                   content_type=None, method='GET',
                   data=None, no_content=False, always_return_none=False,
                   query_request_parameter=None, 
                   **kwargs):
        prefix = underscore_unquote(prefix)
        if action:
            kwargs['action'] = action
        if query_request_parameter:
            kwargs[self.QUERY_REQUEST_PARAMETER] = query_request_parameter
        if self.db is None and db is None:
            raise ValueError('Missing self.db or db')
        full_url = (self.server_url + '/' + (db if db else self.db)
                    +escape_uri_components(*prefix)
                    +self.create_params(**kwargs))
        headers = self._make_headers(content_type=content_type)
        if self.v2:
            # OBSOLETE
            request = urllib.request.Request(full_url, method=method,
                                     headers=headers)
            response = urllib.request.urlopen(request, data=data,
                                              context=self.context)
            content = response.read()
            if not response.code in (200, 204):
                raise InfinityDBError(code=response.code, reason=response.reason)
            if always_return_none:
                return None
            if no_content:
                return response.code == 200
            return response.code == 200, content
        else:
# TODO XXX remove verify=False
            response = self.session.request(method, full_url,
                                            headers=headers,
                                            data=data, verify=False)
            # touching this finishes the operation
            content = response.content
            if content == None:
                raise InfinityDBError(code=400, reason="Null content")
            if not response.status_code in (200, 204):
                raise InfinityDBError(code=response.status_code, reason=response.reason)
            if always_return_none:
                return None
            if no_content:
                return response.status_code == 200
            return response.status_code == 200, content

    def get_blob(self, prefix, *, db=None, **kwargs):
        return self._do_command(prefix, db=db,
                                action='get-blob', **kwargs)

    def get_json(self, prefix, *, db=None, **kwargs):
        """ get Items from an infinitydb db as a
        dict decoded from the json.
        """
        success, content = self._do_command(prefix, db=db,
                                         action='as-json', **kwargs)
        if not success:
            return False, None
        data_quoted = json.loads(content)
        content = underscore_unquote(data_quoted)
        return True, content

    def get_items(self, prefix, db=None, **kwargs):
        """ get Items from an infinitydb db encoded as components
        under a given key prefix, up to a limit.
        Param limit is the max item count.
        """
        return self._do_command(prefix, action='as-items', db=db, **kwargs)

    def get_items_batch(self, prefix, db=None, **kwargs):
        """ get Items from an infinitydb db encoded as components
        starting at the key prefix, up to a limit.
        Param limit is the max item count
        """
        return self._do_command(prefix, action='as-items-batch', db=db, **kwargs)

    def put_blob(self, prefix, data, content_type, db=None, **kwargs):
        return self._do_command(prefix,
                                db=db,
                                content_type=content_type,
                                action='put',
                                method='put',
                                data=data, always_return_none=True, **kwargs)

    def put_json(self, prefix, data, *, db=None, **kwargs):
        # Convert non-string keys and dates to
        # 'underscored quoted' string form
        data_quoted = underscore_quote(data)
        # convert the structure to a byte array
        json_data = json.dumps(data_quoted).encode()
        return self._do_command(prefix,
                                db=db,
                                content_type='application/json',
                                method='put',
                                data=json_data, always_return_none=True, **kwargs)

    def post_json(self, prefix, data, *, db=None, **kwargs):
        # Convert non-string keys and dates to
        # 'underscored quoted' string form
        data_quoted = underscore_quote(data)
        # convert the structure to a byte array
        json_data = json.dumps(data_quoted).encode()
        success, content = self._do_command(prefix,
                                db=db,
                                content_type='application/json',
                                method='post',
                                data=json_data,
                                **kwargs)
        if not success:
            return False, None
        components = parse_token_string_into_components(content.decode())
        return True, components

    def delete(self, prefix, *, db=None, **kwargs):
        return self._do_command(prefix,
                                db=db,
                                content_type='application/json',
                                method='delete',
                                always_return_none=True,
                                **kwargs)

    def execute_query(self, prefix, data, *, db=None,
                      unflatten=True, flatten=True, is_blob_expected=False, 
                      query_request_parameter=None, **kwargs):
        # Must compact the tips, or it is interpreted as empty
        if unflatten:
            data = make_tuples_into_nested_objects(data)
        print('unflattened input data to execute_query():', data)
        data_quoted = underscore_quote(data)
#        print('quoted:', data_quoted)
        json_data = json.dumps(data_quoted).encode()
#        print('json_data:', json_data)
        action = 'execute-blob-query' if is_blob_expected else 'execute-query'
        if query_request_parameter != None:
            query_request_parameter = make_tuples_into_nested_objects(query_request_parameter)
            query_request_parameter = underscore_quote(query_request_parameter)
            query_request_parameter = json.dumps(query_request_parameter).encode()
        success, content = self._do_command(prefix,
                            db=db,
                            content_type='application/json',
                            method='post',
                            data=json_data,
                            action=action,
                            query_request_parameter=query_request_parameter,
                             **kwargs)
        if not success:
            return False, None
        if content == None:
            raise InfinityDBError(code=400, reason="Null content")
        if is_blob_expected:
            return True, content
        if content == b'':
            data_quoted = {}
        else:
            data_quoted = json.loads(content)
        content = underscore_unquote(data_quoted)
        if flatten:
            content = flatten_to_tuples(content, flattened_lists=False, compact_tips=True)
#        print('flattened output content from execute_query():', content)
        return True, content

    def move(self, action, prefix, *, db, **kwargs):
        success, content = self._do_command(prefix,
                                db=db,
                                content_type='application/json',
                                action=action,
                                **kwargs)
        if not success:
            return False, None
        data = content.decode()
        components = parse_token_string_into_components(data)
        return True, components

    def first_item(self, prefix, *, db=None, **kwargs):
        """ Move to the nearest greater than or equal Item,
        with the prefix length set to 0. Because the prefix
        length is 0, the entire database can be iterated. """
        return self.move('first-item', prefix, db=db, **kwargs)

    def first_component(self, prefix, *, db=None, **kwargs):
        """ Move to the nearest greater than or equal component, 
        with the prefix length set to the beginning of the 
        last component in the key"""
        return self.move('first-component', prefix, db=db, **kwargs)

    def first_tuple(self, prefix, *, db=None, **kwargs):
        """ Move to the nearest greater than or equal tuple, 
        with the prefix length set to the beginning of the 
        last tuple in the key"""
        return self.move('first-tuple', prefix, db=db, **kwargs)

    """ For next speed, keep a single buffer in memory that is a list
    of Items, each being a list.
    """

    # get more Items into the next_buf starting at prefix
    def _fill_next_buf(self, prefix, bound_type, *, db, **kwargs):
        success, next_item = self.next_bounded(prefix,
                                            bound_type, db=db, **kwargs)
        if not success:
            return False, []
        success, content = self.get_items_batch(
            next_item,
            limit=self.next_buf.size, db=db, **kwargs)
        if not success:
            return False, None
        lines = content.decode().splitlines()
        items = [parse_token_string_into_components(line) for line in lines]
        return True, items

    def _buffered_next(self, prefix, bound, *, db, **kwargs):
        # lazy construction
        if not self.next_buf:
            self.next_buf = NextBuf(self._fill_next_buf)
        return self.next_buf.next(prefix, bound, db=db, **kwargs)

    def set_next_buffer(self, *, flush=True, size=None):
        if not self.next_buf:
            self.next_buf = NextBuf(self._fill_next_buf)
        if  flush:
            self.next_buf.flush()
        if size:
            self.next_buf.set_size(size)

    def next_bounded(self, prefix, bound_type, *, db=None, **kwargs):
        if bound_type == Bound.ITEM:
            return self.move('next-item', prefix, db=db, **kwargs)
        elif bound_type == Bound.TUPLE:
            return self.move('next-tuple', prefix, db=db, **kwargs)
        elif bound_type == Bound.COMPONENT:
            return self.move('next-component', prefix, db=db, **kwargs)
        else:
            raise ValueError

    def next_item(self, prefix, *, db=None, buffered=False, flush=False, **kwargs):
        if flush:
            self.next_buf.flush()
        if buffered:
            return self._buffered_next(prefix, Bound.ITEM, db=db if db else self.db, **kwargs)
        else:
            return self.move('next-item', prefix, db=db, **kwargs)

    def next_component(self, prefix, *, db=None, buffered=False, flush=False, **kwargs):
        if flush:
            self.next_buf.flush()
        if buffered:
            return self._buffered_next(prefix, Bound.COMPONENT, db=db if db else self.db, **kwargs)
        else:
            return self.move('next-component', prefix, db=db, **kwargs)

    def next_tuple(self, prefix, *, db=None, buffered=False, flush=False, **kwargs):
        if flush:
            self.next_buf.flush()
        if buffered:
            return self._buffered_next(prefix, Bound.TUPLE, db=db if db else self.db, **kwargs)
        else:
            return self.move('next-tuple', prefix, db=db, **kwargs)

    def last_item(self, prefix, *, db=None, **kwargs):
        return self.move('last-item', prefix, db=db, **kwargs)

    def last_component(self, prefix, *, db=None, **kwargs):
        return self.move('last-component', prefix, db=db, **kwargs)

    def last_tuple(self, prefix, *, db=None, **kwargs):
        return self.move('last-tuple', prefix, db=db, **kwargs)

    def previous_item(self, prefix, *, db=None, **kwargs):
        return self.move('previous-item', prefix, db=db, **kwargs)

    def previous_component(self, prefix, *, db=None, **kwargs):
        return self.move('previous-component', prefix, db=db, **kwargs)

    def previous_tuple(self, prefix, *, db=None, **kwargs):
        return self.move('previous-tuple', prefix, db=db, **kwargs)

    def exists(self, item, *, db=None, **kwargs):
        return self._do_command(item,
                                db=db,
                                content_type='application/json',
                                no_content=True,
                                action='exists', **kwargs)

    def _simple_item_output_command(self, item, action, *, db, **kwargs):
        return self._do_command(item,
                                db=db,
                                content_type='application/json',
                                always_return_none=True,
                                action=action, **kwargs)

    def insert_item(self, item, *, db=None, **kwargs):
        self._simple_item_output_command(item, 'insert-item', db=db, **kwargs)

    def delete_item(self, item, *, db=None, **kwargs):
        self._simple_item_output_command(item, 'delete-item', db=db, **kwargs)

    def delete_subspace(self, item, *, db=None, **kwargs):
        self._simple_item_output_command(item, 'delete-subspace', db=db, **kwargs)

    def commit(self, *, db=None, **kwargs):
        """ The global commit, not the optimistic commit 
            You can use wait_for_durable and retry_time_out, in
            milliseconds.
            
            Uses not application/json, but application/infinitydb
        """
        # TODO untested
        self._do_command(None,
                        db=db,
                        content_type='application/infinitydb',
                        action='commit',
                        always_return_none=True,
                        wait_for_durable=True, **kwargs)

    def roll_back(self, *, db=None, **kwargs):
        """ The global rollback, not the optimistic rollback 
            Uses not application/json, but application/infinitydb
        """
        # TODO untested
        self._do_command(None, db=db,
                        content_type='application/infinitydb',
                        always_return_none=True,
                        action='commit', **kwargs)

    # TODO incomplete
    # data is the dict for the query definition and source/dest prefixes,
    # plus operation type: clear_results, merge_with_results, subtract_from_results.
    # Also, a prefix referring to a stored query can be handled,
    # but then we need to be able to override parts of it, especially
    # the constants in the Where.
#    def pattern_query(self, *, db=None, **kwargs):
#        return self._do_command(None,
#                                db=db,
#                                content_type='application/infinitydb',
#                                action='pattern-query',
#                                  data=query_data,
#                                  **kwargs)


class Bound:
    """ For NextBuf. How to find the prefix length. 
    We go backwards from the end of the Item. The result 
    is the start, the last tuple, or the last component.
    Also, for tuples, truncate before the next EC/Att, and
    for components, truncate after the final component.
     """
    ITEM = 0
    TUPLE = 1
    COMPONENT = 2


class NextBuf:
    """ For reading batches of Items, which can be searched 
    """
    DEFAULT_SIZE = 1000

    def __init__(self, buf_filler):
        # a list of items following the last fill
        self.buf = []
        self.db = None
        # This function returns the next buf after a given item
        self.buf_filler = buf_filler
        self.size = NextBuf.DEFAULT_SIZE

    def flush(self):
        self.buf = []
        self.db = None

    def set_size(self, size):
        self.size = size

    def _get_last_tuple_off(self, item):
        off = 0
        for i in range(len(item)):
            if isinstance(item[i], (EntityClass, Attribute)):
                off = i + 1
        return off

    def _skip_tuple(self, item, off):
        for i in range(off, len(item)):
            if isinstance(item[i], (EntityClass, Attribute)):
                return i
        return len(item)

    def _locate_prefix_in_buf(self, prefix):
        for i in range(len(self.buf)):
            if prefix == self.buf[i][:len(prefix)]:
                return i
        return -1

    def _get_off_of_bound(self, item, bound_type):
        if bound_type == Bound.ITEM:
            return 0
        elif bound_type == Bound.COMPONENT:
            return len(item) - 1 if len(item) > 0 else 0
        elif bound_type == Bound.TUPLE:
            return self._get_last_tuple_off(item)
        else:
            raise ValueError

    def _skip_bound(self, item, bound_type, off):
        if bound_type == Bound.ITEM:
            return len(item)
        elif bound_type == Bound.COMPONENT:
            return off + 1 if off < len(item) else len(item)
        elif bound_type == Bound.TUPLE:
            return self._skip_tuple(item, off)
        else:
            raise ValueError

    """ We can't compare Items for magnitude as we can
    in InfinityDB, so everything must use equality,
    possibly over prefixes. This is not as good,
    being linear in the buffer size, instead of log.

     We have to match the previously found Item up
     to after the last bound (such as the last tuple) or 
     else read a buf starting at the next Item.
    """
    ITEM_NOT_IN_BUF = -1
    FINAL_ITEM = -2

    def _get_next_from_buf(self, item, bound_type):
        if not self.buf:
            return NextBuf.ITEM_NOT_IN_BUF
        # The given Item must be already there for quick success
        pos = self._locate_prefix_in_buf(item)
        if pos == -1:
            # Must do it the hard way, by re-reading the buf.
            return NextBuf.ITEM_NOT_IN_BUF
        # item or its extension is found in buf at pos.
        # find the last component or last tuple, or end of item
        # according to the bound type
        prefix_len = self._get_off_of_bound(item, bound_type)
        # prefix_len is 0, or at last tuple or component
        prefix = item[:prefix_len]
        for i in range(pos, len(self.buf)):
            found_item = self.buf[i]
            if found_item[:prefix_len] != prefix:
                # end of Items in this prefix
                return NextBuf.FINAL_ITEM
            after_bound = self._skip_bound(found_item,
                                           bound_type, prefix_len)
            truncated_found_item = found_item[:after_bound]
            if truncated_found_item != item:
                return truncated_found_item
            # loop over extensions of item
        return NextBuf.ITEM_NOT_IN_BUF

    def next(self, item, bound_type, *, db, **kwargs):
        if db != self.db:
            self.db = db
            self.buf = []
        next_item = self._get_next_from_buf(item, bound_type)
        if next_item == NextBuf.FINAL_ITEM:
            # NO_CONTENT
            return False, None
        elif next_item != NextBuf.ITEM_NOT_IN_BUF:
            return True, next_item
        success, self.buf = self.buf_filler(item, bound_type, db=self.db, **kwargs)
        if not success:
            return False, None
        # First Item in buf is nearest >= given item.
        prefix_length = self._get_off_of_bound(item, bound_type)
        next_item = self.buf[0]
        if next_item == item:
            # shouldn't happen
            next_item = self.buf[1]
        if next_item[:prefix_length] == item[:prefix_length]:
            after_bound = self._skip_bound(next_item, bound_type, prefix_length)
            return True, next_item[:after_bound]
        return False, None

