from Analyst import *
from optparse import OptionParser
        
usage = "python field_search.py <keyword> <file_path_prefix> [-q] [-s]"
parser = OptionParser(usage=usage)
parser.set_defaults(print_out=True)
parser.set_defaults(for_session=False)
#parser.add_option("--key", metavar='KEY', dest="key", help="keyword")
#parser.add_option("--s", metavar='SESSION_PATHS', dest="session_paths", help="logs of this session")
parser.add_option("-q", action="store_false", dest="print_out", help="don't print out result")
parser.add_option("-s", action="store_true", dest="for_session", help="get all logs of this session")
(options, args) = parser.parse_args()

#print('options: ' + repr(options))
#print('args: ' + repr(args))

if len(args) != 2:
    parser.error("invalid argument count, expect {0}, actual {1}".format(2, len(args)))

key = args[0]
path = args[1]


SAME_SESSION_MAP = {
                    'UpopBiz.log': ['UpopBiz.log', 'UpopWeb.log'],
                    'upop-web.log': ['upop-web.log']
                    }

if (options.for_session):
    meta_for_key = LogSetMeta.create_from_path_prefix(path)
    metas_for_session = [LogSetMeta(meta_for_key.dir_path, s_path, meta_for_key.date) for s_path in SAME_SESSION_MAP[meta_for_key.file_base_name]]
        
    analyst = OrderSessionAnalyst(meta_for_key, metas_for_session, options.print_out)
    analyst.execute(key)
else:
    key_meta = LogSetMeta.create_from_path_prefix(path)
    upop_web_meta = LogSetMeta.create_from_path_prefix(path)
    analyst = KeySearchAnalyst(key_meta, options.print_out)
    analyst.execute(key)