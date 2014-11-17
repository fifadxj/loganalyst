import datetime
import glob
import re
import sys
import Utils
from Utils import logger

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
    def new_upop_web(date, dir_path='web/'):
        return LogSetMeta(dir_path, 'upop-web.log', date)
    @staticmethod
    def old_upop_web(date, dir_path=''):
        return LogSetMeta(dir_path, 'UpopWeb.log', date)
    @staticmethod
    def old_upop_biz(date, dir_path='web/'):
        return LogSetMeta(dir_path, 'UpopBiz.log', date)
    
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
    
    @staticmethod
    def create(file_base_name, date, dir_path):
        return LogSetMeta(dir_path, file_base_name, date)
        
    KEYWORD_MAP = {
                   'UpopBiz.log': [('<POST:', 'form'), ('send to acp', 'json')], 
                   'upop-web.log': [('Browers agent=', 'json_array'), ('send to acp', 'json')]
                   }
    def is_line_need_process(self, line):
        keywords = LogSetMeta.KEYWORD_MAP[self.file_base_name]
        if keywords is not None:
            for (key, fmt) in keywords:
                if line.find(key) != -1:
                    return True

        return False
    
    def build_field_matcher(self, field, line):
        keywords = LogSetMeta.KEYWORD_MAP[self.file_base_name]
        if keywords is not None:
            for (key, fmt) in keywords:
                if line.find(key) != -1:
                    return Matcher.create_field_matcher(fmt, field)

        return None
        
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
        return 'results/grep__[{file_name_prefix}__{key}'.format(key=key, file_name_prefix=file_name_prefix)
    
    def grep_by_key(self, key):
        self.__unzip_if_need()
        logger.debug('grep start: ' + datetime.datetime.now().isoformat())
        
        grep_result_file_path = self.__build_grep_result_file_name(key, self.meta.file_name_prefix)
        Utils.linux_grep_to_file(key, self.meta.file_path_pattern, grep_result_file_path)
                
        logger.debug('grep done: ' + datetime.datetime.now().isoformat())
        
        return grep_result_file_path

    def __unzip_if_need(self):
        if (self.__is_unzipped()):
            logger.debug("unzip start: " + datetime.datetime.now().isoformat())
            Utils.linux_unzip_file(self.meta.file_path_pattern)
            logger.debug('unzip done: ' + datetime.datetime.now().isoformat())
        elif (self.__is_exist()):
            logger.debug("log files are already unzipped")
        else:
            logger.debug('no log files')
            sys.exit(1)
    
    def __is_unzipped(self):
        return Utils.file_pattern_exist(self.meta.file_path_pattern + '.gz')
    
    def __is_exist(self):
        return Utils.file_pattern_exist(self.meta.file_path_pattern)

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
        expr = '{field}=.*?(?=&)|{field}=.*'.format(field=field)
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
        
class LineProcessor:
    def __init__(self):
        pass
        
    def process(self, line, matchers):
        results = []
        for matcher in matchers:
            if matcher:
                result = matcher.match(line)
                results.append(result)

        return results
        
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
        results = []
        
        if self.print_out:
            #Utils.print_file(grep_result_file_path)
            with open(result_file_name, mode='r') as f:
                for line in f:
                    line = line.rstrip("\r\n")
                    print line
               
        return results
            
class RequestFieldsAnalyst(Analyst):
    def __init__(self, meta, fields, print_out=True):
        self.log_set = LogSet(meta)
        self.fields = fields
        self.print_out = print_out
        self.processor = LineProcessor()
        
    def __analyst(self, results):
        filtered = set()
        for result in results:
            fields = ['[' + i + ']' if i else "[]" for i in result['fields']]
            #'[' + result['action'] + '] ' + 
            text = ' '.join(fields)
            filtered.add(text)
         
        return filtered 
     
    def __collect(self, key):
        result_file_name = self.log_set.grep_by_key(key)
        results = []
        
        with open(result_file_name, mode='r') as f:
            for line in f:
                line = line.rstrip("\r\n")
                if (self.log_set.meta.is_line_need_process(line)):
                    matchers = []
                    for field in self.fields:
                        matcher = self.log_set.meta.build_field_matcher(field, line)
                        matchers.append(matcher)

                    line_result = self.processor.process(line, matchers)
                    s = '<POST:([^\|]*)'
                    s = '(?<=<POST:).*?(?=\|)'
                    results.append({'fields': line_result, 'action': Matcher(s).match(line)})
               
        return results
    
    def output(self, file_name, lines):
        Utils.persist(file_name, lines)
        if self.print_out:
            Utils.print_file(file_name)
       
    def __build_analyst_result_file_name(self, key, file_name_prefix):
        return 'results/analyst__{file_name_prefix}__{key}'.format(key=key, file_name_prefix=file_name_prefix)   

    def execute(self, key): 
        results = self.__collect(key)
        lines = self.__analyst(results)
        file_name = self.__build_analyst_result_file_name(key, self.log_set.meta.file_name_prefix)
        self.output(file_name, lines)









