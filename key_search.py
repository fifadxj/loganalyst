from Analyst import *
from optparse import OptionParser
        
usage = "python field_search.py <keyword> <file_path_prefix> [-q]"
parser = OptionParser(usage=usage)
parser.set_defaults(print_out=True)
#parser.add_option("--key", metavar='KEY', dest="key", help="keyword")
#parser.add_option("--file", metavar='FILE', dest="file", help="log file name")
parser.add_option("-q", action="store_false", dest="print_out", help="don't print out result")
(options, args) = parser.parse_args()

#print('options: ' + repr(options))
#print('args: ' + repr(args))

if len(args) != 2:
    parser.error("invalid argument count, expect {0}, actual {1}".format(2, len(args)))

key = args[0]
path = args[1]

meta = LogSetMeta.create_from_path_prefix(path)
analyst = KeySearchAnalyst(meta, options.print_out)
analyst.execute(key)