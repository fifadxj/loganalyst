import datetime
import glob
import re
import sys
import Utils
from Utils import logger


KEYWORD_MAP = {
               'UpopBiz.log': [('<POST:', 'form'), ('send to acp', 'json')], 
               'upop-web.log': [('Browers agent=', 'json_array'), ('send to acp', 'json')]
               }

'''
example (logs/upop.log.20141111*):

dir_path = "logs/"
file_base_name = "upop.log"
date = "20141111"
file_name_prefix = "upop.log.20141111"
file_path_prefix = "logs/upop.log.20141111"
file_path_pattern = "logs/upop.log.20141111*"
'''
class LogSetMeta:
    @staticmethod
    def create_from_path_prefix(path):
        if path.find('.log') == -1:
            raise Exception("'log file name prefix invalid: must contains '.log'")
        
        dir_end_index = path.rfind('/')

        if path.endswith('.log'):
            file_name_prefix_end_index = len(path) - 1
        else:
            file_name_prefix_end_index = path.rfind('.log') + 3

        dir_path = path[0 : (dir_end_index + 1)]
        file_base_name = path[(dir_end_index + 1) : file_name_prefix_end_index + 1]
        date = path[(file_name_prefix_end_index + 2) :]
        
        return LogSetMeta(dir_path, file_base_name, date)
        
    def __init__(self, dir_path, file_base_name, date):
        self.dir_path = dir_path
        self.file_base_name = file_base_name
        self.date = date
        
        self.file_name_prefix = self.__build_file_name_prefix()
        self.file_path_prefix = self.__build_file_path_prefix()
        self.file_path_pattern = self.__build_file_path_pattern()
        self.file_path_list = glob.glob(self.__build_file_path_pattern())
        
        #print('dir_path: ' + self.dir_path)
        #print('file_base_name: ' + self.file_base_name)
        #print('date: ' + self.date)
        #print("file_name_prefix: " + self.file_name_prefix)
        #print("file_path_prefix: " + self.file_path_prefix)
        #print("file_path_pattern: " + self.file_path_pattern)
    
    def __build_file_name_prefix(self):
        if len(self.date) > 0:
            return self.file_base_name + '.' + self.date
        else:
            return self.file_base_name

    def __build_file_path_prefix(self):
        return self.dir_path + self.__build_file_name_prefix()

    def __build_file_path_pattern(self):
        return self.__build_file_path_prefix() + '*'

class LogSet:
    def __init__(self, meta):
        self.meta = meta
    
    def __build_grep_result_file_name(self, key, file_name_prefix):
        Utils.truncate(key, 30)
        return 'results/grep__{file_name_prefix}__{key}'.format(key=key, file_name_prefix=file_name_prefix)
    
    def grep_by_key(self, key, result_key = None):
        self.__unzip_if_need()
        logger.debug('grep start: ' + self.meta.file_name_prefix)
        
        if not result_key:
            result_key = key
            
        grep_result_file_path = self.__build_grep_result_file_name(result_key, self.meta.file_name_prefix)
        Utils.linux_grep_to_file(key, self.meta.file_path_pattern, grep_result_file_path)
                
        logger.debug('grep done: ' + self.meta.file_name_prefix)
        
        return grep_result_file_path

    def __unzip_if_need(self):
        if (self.__is_unzipped()):
            logger.debug("unzip start: " + self.meta.file_name_prefix)
            Utils.linux_unzip_file(self.meta.file_path_pattern)
            logger.debug('unzip done: ' + self.meta.file_name_prefix)
        elif (self.__is_exist()):
            logger.debug("log files are already unzipped: " + self.meta.file_name_prefix)
        else:
            logger.error('no log files: ' + self.meta.file_name_prefix)
            sys.exit(1)
    
    def __is_unzipped(self):
        return Utils.file_pattern_exist(self.meta.file_path_pattern + '.gz')
    
    def __is_exist(self):
        return Utils.file_pattern_exist(self.meta.file_path_pattern)
    
    def is_request_log(self, line):
        keywords = KEYWORD_MAP[self.meta.file_base_name]
        if keywords is not None:
            for (key, fmt) in keywords:
                if line.find(key) != -1:
                    return True

        return False
    
    def build_field_matcher(self, field, line):
        keywords = KEYWORD_MAP[self.meta.file_base_name]
        if keywords is not None:
            for (key, fmt) in keywords:
                if line.find(key) != -1:
                    return Matcher.create_field_matcher(fmt, field)

        return None

class Matcher:
    def __init__(self, expr):
        self.expr = expr
        
    @staticmethod
    def create_field_matcher(log_format, field):
        if log_format == 'form':
            return FormFieldMatcher(field)
        elif log_format == 'json_array':
            return JsonArrayFieldMatcher(field)
        elif log_format == 'json':
            return JsonFieldMatcher(field)
        else:
            raise Exception('invalid type')
        
    def match(self, text, group=0):
        m = re.search(self.expr, text)
        if (m is None):
            return None
        else:
            return m.group(group)


class FormFieldMatcher(Matcher):
    def __init__(self, field):
        self.field = field
        #  merId=.*?(?=&)|merId=.*
        #  {field}=.*?(?=&)|{field}=.*
        expr = field + '=[^}&]*'
        Matcher.__init__(self, expr)

class JsonFieldMatcher(Matcher):
    def __init__(self, field):
        self.field = field
        expr = '"{field}":"(.*?)"'.format(field=field)
        Matcher.__init__(self, expr)

class JsonArrayFieldMatcher(Matcher):
    def __init__(self, field):
        self.field = field
        expr = '"{field}":\["(.*?)"\]'.format(field=field)
        Matcher.__init__(self, expr)

class LogSessionIdentifierMatcher(Matcher):
    def __init__(self):
        expr = '(?<=\[).*?(?=\])'
        #expr = '\[([^\]]*)'
        Matcher.__init__(self, expr)
        
class Analyst:
    def __init__(self):
        pass
    
    def execute(self, key):
        pass
    
class KeySearchAnalyst(Analyst):
    def __init__(self, meta, print_out=True):
        self.log_set = LogSet(meta)
        self.print_out = print_out
        
    def execute(self, key):
        result_file_name = self.log_set.grep_by_key(key)
        
        if self.print_out:
            #Utils.print_file(grep_result_file_path)
            with open(result_file_name, mode='r') as f:
                for line in f:
                    line = line.rstrip("\r\n")
                    print line

class OrderSessionAnalyst(Analyst):
    def __init__(self, meta_for_key, metas_for_session, print_out=True):
        self.log_set_for_key = LogSet(meta_for_key)
        self.log_sets_for_session = []
        for meta_for_session in metas_for_session:
            log_set_for_session = LogSet(meta_for_session)
            self.log_sets_for_session.append(log_set_for_session)
        self.print_out = print_out
        
    def execute(self, key):
        result_file_name = self.log_set_for_key.grep_by_key(key)
        
        session_matcher = LogSessionIdentifierMatcher()
        session_ids = []
        with open(result_file_name, mode='r') as f:
            query_request_catched = False
            for line in f:
                line = line.rstrip("\r\n")
                if (self.log_set_for_key.is_request_log(line)):
                    if (line.find('<POST:/api/Query.action') != -1):
                        if query_request_catched:
                            continue
                        else:
                            query_request_catched = True
    
                    session_id = session_matcher.match(line)
                    if session_id:
                        session_ids.append(session_id)
            
            session_ids = Utils.remove_duplicate(session_ids)
        
        print('found sessions: ' + repr(session_ids))
        session_search_key = '|'.join(session_ids)
        session_map = dict()
        for s_id in session_ids:
            session_map[s_id] = []
        for log_set_for_session in self.log_sets_for_session:
            result_file_name = log_set_for_session.grep_by_key(session_search_key, key + '-' + session_search_key)
            with open(result_file_name, mode='r') as f:
                lines = f.readlines()
            for s_id in session_ids:
                session_map[s_id] += filter(lambda line: line.find(s_id) != -1, lines)
        
        outputs = []
        for s_id in session_ids:
            outputs.append('================[{s_id}]==============='.format(s_id=s_id))
            outputs += session_map.get(s_id)
            outputs.append('\r\n')

        file_name = self.__build_analyst_result_file_name(key, self.log_set_for_key.meta.file_name_prefix)
        Utils.persist(file_name, outputs)
        if self.print_out:
            Utils.print_file(file_name)
        
    def __build_analyst_result_file_name(self, key, file_name_prefix):
        Utils.truncate(key, 30)
        return 'results/analyst_session__{file_name_prefix}__{key}'.format(key=key, file_name_prefix=file_name_prefix) 

            
class RequestFieldsAnalyst(Analyst):
    def __init__(self, meta, fields, print_out=True):
        self.log_set = LogSet(meta)
        self.fields = fields
        self.print_out = print_out
        
    def __analyst(self, results):
        filtered = set()
        for result in results:
            def format_field(field):
                field = '[' + field + ']' if field else "[]"
                return field.ljust(30)
                
            fields = map(format_field, result['fields'])
            text = ' '.join(fields)
            filtered.add(text)
         
        return filtered 
     
    def __collect(self, key):
        result_file_name = self.log_set.grep_by_key(key)
        results = []
        
        with open(result_file_name, mode='r') as f:
            for line in f:
                line = line.rstrip("\r\n")
                if (self.log_set.is_request_log(line)):
                    line_result = []
                    for field in self.fields:
                        matcher = self.log_set.build_field_matcher(field, line)
                        result = matcher.match(line)
                        line_result.append(result)

                    s = '<POST:([^\|]*)'
                    s = '(?<=<POST:).*?(?=\|)'
                    results.append({'fields': line_result, 'action': Matcher(s).match(line)})
               
        return results
    
    def output(self, file_name, lines):
        Utils.persist(file_name, lines)
        if self.print_out:
            Utils.print_file(file_name)
       
    def __build_analyst_result_file_name(self, key, file_name_prefix):
        Utils.truncate(key, 30)
        return 'results/analyst__{file_name_prefix}__{key}'.format(key=key, file_name_prefix=file_name_prefix)   

    def execute(self, key): 
        results = self.__collect(key)
        lines = self.__analyst(results)
        file_name = self.__build_analyst_result_file_name(key, self.log_set.meta.file_name_prefix)
        self.output(file_name, lines)









