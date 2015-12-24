import subprocess
import glob
import logging
import os

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
#ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

def linux_unzip_file(file_name):
    gunzip_cmd = 'gunzip {filePattern}'.format(filePattern = file_name)
    p = subprocess.Popen(gunzip_cmd, stdout=subprocess.PIPE, shell=True)
    p.wait()

def file_pattern_exist(file_name):
    return len(glob.glob(file_name)) > 0

def file_exist(file_name):
    return os.path.exists(file_name) and os.path.isfile(file_name)

def linux_grep_to_file(key, input_file, output_file):
    #full_output_path = os.path.abspath(output_file)
    remove_file(output_file)
    grep_cmd = 'egrep "{key}" {inputFile} >> "{outputFile}"'.format(key = key, inputFile = input_file, outputFile = output_file)
    p = subprocess.Popen(grep_cmd, stdout=subprocess.PIPE, shell=True)
    p.wait()

'''   
def grep(key, input_file):
    grep_cmd = 'egrep "{key}" {inputFile}'.format(key = key, inputFile = input_file)
    print(grep_cmd)
    p = subprocess.Popen(grep_cmd, stdout=subprocess.PIPE, shell=True)
    text = p.communicate()[0]
    print(text)
'''

def print_file(file_name):
    with open(file_name, 'r') as f:
        for line in f:
            print(line.rstrip())
        
def remove_file(file_name):
    if (os.path.exists(file_name) and os.path.isfile(file_name)):
        os.remove(file_name)
        
def persist(file_name, lines):
    with open(file_name, 'w') as f:
        for line in lines:
            f.write(line + '\n')
            
def truncate(key, max, append_to_end='...'):
    return key if len(key) <= max else key[:max] + append_to_end

def remove_duplicate(list):
    result = []
    for l in list:
        if l not in result:
            result.append(l)
            
    return result

def file_content(file_name):
    content = ''
    with open(file_name, 'r') as f:
        for line in f:
            content += line.strip()
    
    return content