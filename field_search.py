from Analyst import *
from optparse import OptionParser
        
usage = "python field_search.py <field,field..> <keyword> <file_path_prefix> [-q]"
parser = OptionParser(usage=usage)
parser.set_defaults(print_out=True)
parser.add_option("-q", action="store_false", dest="print_out", help="don't print out result")
(options, args) = parser.parse_args()

if len(args) != 3:
    parser.error("invalid argument count, expect {0}, actual {1}".format(3, len(args)))

fields = args[0].split(',')
key = args[1]
path = args[2]

meta = LogSetMeta.create_from_path_prefix(path)
analyst = RequestFieldsAnalyst(meta, fields, options.print_out)
analyst.execute(key)