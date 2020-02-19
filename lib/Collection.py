# Collection.py ---
#
# Filename: Collection.py
# Description:
# Author: Joerg Fallmann
# Maintainer:
# Created: Tue Sep 18 15:39:06 2018 (+0200)
# Version:
# Package-Requires: ()
# Last-Updated: Wed Feb 19 13:40:01 2020 (+0100)
#           By: Joerg Fallmann
#     Update #: 1019
# URL:
# Doc URL:
# Keywords:
# Compatibility:
#
#

# Commentary:
#
#
#
#

# Change Log:
#
#
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Emacs.  If not, see <http://www.gnu.org/licenses/>.
#
#

# Code:
#import os, sys, inspect
# # realpath() will make your script run, even if you symlink it :)
# cmd_folder = os.path.dirname(os.path.realpath(os.path.abspath( inspect.getfile( inspect.currentframe() )) ))
# if cmd_folder not in sys.path:
#     sys.path.insert(0, cmd_folder)

#
# # Use this if you want to include modules from a subfolder
# cmd_subfolder = os.path.join(os.path.dirname(os.path.realpath(os.path.abspath( inspect.getfile( inspect.currentframe() )) )),"lib")
# if cmd_subfolder not in sys.path:
#     sys.path.insert(0, cmd_subfolder)
#
# # Info:
# # cmd_folder = os.path.dirname(os.path.abspath(__file__)) # DO NOT USE __file__ !!!
# # __file__ fails if the script is called in different ways on Windows.
# # __file__ fails if someone does os.chdir() before.
# # sys.argv[0] also fails, because it doesn't not always contains the path.

import glob, os, snakemake
import numpy as np
import heapq
from operator import itemgetter
from natsort import natsorted, ns
import traceback as tb
import sys
import re
import pprint
from io import StringIO
from Bio import SeqIO
import gzip
import math
import inspect
import subprocess
import collections
from collections import defaultdict, OrderedDict
import six
import logging

cmd_subfolder = os.path.join(os.path.dirname(os.path.realpath(os.path.abspath(inspect.getfile( inspect.currentframe() )) )),"../lib")
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

try:
    scriptname = os.path.basename(inspect.stack()[-1].filename)
    log=logging.getLogger(scriptname)
except Exception as err:
    exc_type, exc_value, exc_tb = sys.exc_info()
    tbe = tb.TracebackException(
        exc_type, exc_value, exc_tb,
    )
    log.error(''.join(tbe.format()))

#Class
class NestedDefaultDict(defaultdict):
    def __init__(self, *args, **kwargs):
        super(NestedDefaultDict, self).__init__(NestedDefaultDict, *args, **kwargs)

    def __repr__(self):
        return repr(dict(self))

    def merge(self, *args):
        self = merge_dicts(self,*args)

# Code:All subs from here on
##############################
########Snakemake Subs########
##############################
def check_run(func):
    def func_wrapper(*args, **kwargs):
        logid=scriptname+'.Collection_func_wrapper: '
        try:
            return func(*args, **kwargs)

        except Exception as err:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tbe = tb.TracebackException(
                exc_type, exc_value, exc_tb,
            )
            log.error(logid+''.join(tbe.format()))
    return func_wrapper

@check_run
def sources(config):
    logid=scriptname+'.Collection_sources: '
    ret = list()
    for key in config["SOURCE"] and config["SAMPLES"]:
        ret.append(str(key))
    log.debug(logid+str(ret))
    return ret

@check_run
def samples(config):
    logid=scriptname+'.Collection_samples: '
    ret = list()
    for x,y in config["SOURCE"].items():
        k = find_innermost_value_from_dict(config["SAMPLES"][x])
        for l in k:
            ret.append(os.path.join(str(x),str(l)))
    log.debug(logid+str(ret))
    return ret

@check_run
def get_samples_from_dir(id, condition, setting, config):
    logid = scriptname+'.Collection_get_samples_from_dir: '
    pat = os.path.abspath(os.path.join('FASTQ',id, condition, '*.fastq.gz'))
    log.info(logid+str(pat))
    ret = natsorted(glob.glob(pat), key=lambda y: y.lower())
    if len(ret) >0:
        seqtype = getFromDict(config, ['SEQUENCING', id, condition, setting])
        for x in seqtype:
            if 'unpaired' not in x:
                ret = list(set([re.sub('_r1|_r2|.fastq.gz','',os.path.basename(s)) for s in ret]))
                renamelist = [re.sub('_R\d', lambda pat: pat.group(1).lower(), s) for s in ret]
                for i in range(len(renamelist)):
                    if renamelist[i] != ret[i]:
                        os.rename(ret[i],renamelist[i])
            else:
                ret = list(set([re.sub('.fastq.gz','',os.path.basename(s)) for s in ret]))
    else:
        ret = None
    log.debug(logid+str(ret))
    return list(set(ret))

@check_run
def sampleslong(config):
    logid = scriptname+'.Collection_sampleslong: '
    ret = list()
    for x,y in config["SOURCE"].items():
        for s in config["SAMPLES"][x]:
            if s in y:
                log.debug(logid+str([x,y,s]))
                k = list_all_values_of_dict(config["SAMPLES"][x][s])
                for v in k:
                    if isinstance(v, list) or isinstance(v, tuple):
                        for z in v:
                            if isinstance(z, list) or isinstance(z, tuple):
                                for a in z:
                                    ret.append(os.path.join(str(x),str(s),str(a)))
                            else:
                                ret.append(os.path.join(str(x),str(s),str(z)))
                else:
                    ret.append(os.path.join(str(x),str(s),str(v)))
    ret = list(set([x for x in ret if os.path.exists(os.path.join('FASTQ',str(x)+'.fastq.gz'))]))
    log.debug(logid+str(ret))
    return ret

@check_run
def samplesonly(config):        # THIS IS NOT ADVISED, SAMPLES INDEPENDENT OF SOURCE!
    ret = list()
    for x,y in config["SOURCE"].items():
        for s in config["SAMPLES"][x]:
            for n in config["SAMPLES"][x][s]:
                ret.append(str(n))
    return ret

@check_run
def get_placeholder(config):
    ret = list()
    if 'PH' in (config):
        for x in config['PH']:
            ret.append(str(x))
    else:
        ret.append('_')
    return ret

@check_run
def genomepath(s, config):
    logid=scriptname+'.Collection_genomepath: '
    sa = os.path.basename(str(s))
    cond= s.split(os.sep)[-2]
    sk = find_key_for_value(sa, config["SAMPLES"])
    log.debug(logid+'GENOMEPATH: '+str([sa,cond,sk]))
    for skey in sk:
        klist = value_extract(skey, config["SOURCE"])
        for k in klist:
            for x, y in config["GENOME"].items():
                log.debug(logid+'GENOMEPATH: '+str([x,y,k]))
                if str(k) == str(y) or str(k) == str(x):
                    return os.path.join(str(x),str(y))

@check_run
def genome(s, config):
    logid=scriptname+'.Collection_genome: '
    sa = os.path.basename(str(s))
    sp = source_from_sample(str(s)).split(os.sep)[0]
    cond= s.split(os.sep)[-2]
    sk = find_key_for_value(sa, config['SAMPLES'])
    for skey in sk:
        klist = value_extract(skey, config['SOURCE'])
        for k in klist:
            #log.debug(logid+'there: '+str([k,skey,sp,sa,cond]))
            #if str(k) == config['SOURCE'][sp][cond]:
            #log.debug(logid+'k is sp')
            for x, y in config['GENOME'].items():
                log.debug(logid+str([k, x, y]))
                if str(k) == str(x):
                    return str(y)

@check_run
def fullgenomepath(sa, config):
    ret=list()
    for s in sa:
        l = config["GENOME"][s]
        ret.append(os.path.join(str(s),str(l)))
    return ret

@check_run
def genomename(s, config):
    s = os.path.basename(str(s))
    for k,v in config["SAMPLES"].items():
        for g,l in v.items():
            if s in l:
                for x, y in config["GENOME"].items():
                    if g == y:
                        return str(x)

@check_run
def namefromfile(s, config):
    if 'NAME' not in config:
        return ''
    else:
        sa = os.path.basename(str(s))
        cond= s.split(os.sep)[-2]
        sk = find_key_for_value(sa, config["SAMPLES"])
        for skey in sk:
            klist = value_extract(skey, config["NAME"])
            for k in klist:
                if str(skey) == str(cond):
                    return str(k)

@check_run
def create_subworkflow(config, subwork, conditions, stage=''):
    logid = scriptname+'.Collection_create_subworkflow: '
    log.debug(logid+str([config, subwork, conditions, stage]))
    toollist = list()
    configs = list()
    for condition in conditions:
        try:
            env = str(subDict(config[subwork],condition)[stage+'ENV'])
        except:
            log.warning('Key ENV not found for '+subwork+' this can be intentional')
            env = ''
        try:
            exe = str(subDict(config[subwork],condition)[stage+'BIN'])
        except:
            log.warning('Key BIN not found for '+subwork+' this can be intentional')
            exe = ''
        src, treat, setup = condition
        log.debug(logid+str([env,exe,src,treat,setup]))
        tempconf = NestedDefaultDict()
        try:
            for key in ['REFERENCE', 'BINS','MAXTHREADS']:
                tempconf[key] = config[key]
        except KeyError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tbe = tb.TracebackException(
                exc_type, exc_value, exc_tb,
            )
            log.error(''.join(tbe.format()))
        try:
            matchinggenome=config['SOURCE'][src][treat][setup]
            tempconf['GENOME'][matchinggenome] = config['GENOME'][matchinggenome]
            if 'NAME' in config:
                tempconf['NAME'][src] = config['NAME'][src]
            for key in ['SOURCE', 'SAMPLES', 'SEQUENCING', subwork]:
                tempconf[key][src][treat][setup] = config[key][src][treat][setup]
            if 'COUNTING' in config:
                tempconf['COUNTING']['FEATURES'] = config['COUNTING']['FEATURES']

        except KeyError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tbe = tb.TracebackException(
                exc_type, exc_value, exc_tb,
            )
            log.error(''.join(tbe.format()))

        tempconf[subwork+'ENV'] = env
        tempconf[subwork+'BIN'] = exe
        toollist.append([env,exe])
        configs.append(tempconf)

    log.debug(logid+str([toollist,configs]))

    return toollist, configs

@check_run
def namefrompath(p, config):
    p = os.path.dirname(p).split(os.sep)
    klist = getFromDict(config["NAME"],p) if 'NAME' in config else list('')
    for k in klist:
        return str(k)

@check_run
def pathstogenomes(samples, config):
    ret = list()
    for s in samples:
        s = os.path.basename(s)
        for k,v in config["SAMPLES"].items():
            for g,l in v.items():
                if s in l:
                    for x, y in config["GENOME"].items():
                        if g == y:
                            ret.append(os.path.join(str(x),str(y)))
    return sorted(list(set(ret)))

@check_run
def tool_params(sample, runstate, config, subconf):
    logid=scriptname+'.Collection_tool_params: '
    log.debug(logid+'Samples: '+str(sample))
    t = genome(sample,config)
    mp = OrderedDict()
    if runstate is None:
        runstate = runstate_from_sample([sample], config)[0]
    x = source_from_sample(sample).split(os.sep)
    log.debug(logid+str([sample,runstate,subconf,t,x]))
    if runstate not in x:
        x.append(runstate)
    mp = subDict(config[subconf],x)
    log.debug(logid+'DONE: '+str(mp))
    return mp

@check_run
def env_bin_from_config(samples, config, subconf):
    logid=scriptname+'.Collection_env_bin_from_config: '
    s = samples[0].split(os.sep)[:-1]
    mb,me = [None,None]
    for k in getFromDict(config[subconf],s):
        mb, me = k['BIN'], k['ENV']
    return mb,me

@check_run
def env_bin_from_config2(samples, config, subconf):
    logid=scriptname+'.Collection_env_bin_from_config2: '
    for s in samples:
        log.debug(logid+s)
        log.debug(logid+str(config[subconf]))
        for k in getFromDict(config[subconf],conditiononly(s,config)):
            mb = k['BIN']
            me = k['ENV']
    log.debug(logid+str([str(mb),str(me)]))
    return mb, me

@check_run
def rmempty(check):
    ret = list()
    for f in check:
        if os.path.isfile(f):
            ret.append(f)
    return ret

@check_run
def source_from_sample(sample):
    ret = str(os.path.join(*os.path.split(str(sample))[0:-1]))
    return ret

@check_run
def sample_from_path(path):
    ret = str(os.path.join(os.path.split(str(path))[-1]))
    return ret

@check_run
def anno_from_file(sample, config, step):
    logid = scriptname+'.Collection_anno_from_file: '
    p = os.path.dirname(genomepath(sample, config))
    s = source_from_sample(sample)
    ret = os.path.join(config["REFERENCE"],p,subDict(config["ANNOTATE"],s)[step])
    log.debug(logid+str(ret))
    return ret

@check_run
def anno_from_source(source, config, step):
    logid = scriptname+'.Collection_anno_from_source: '
    s = source.split(os.sep)[0:-1]
    p = s[0]
    samp = source.split(os.sep)[-1]
    log.debug(logid+str(s))
    runstate = runstate_from_sample([samp], config)[0]
    lst = list()
    lst.extend(s)
    lst.append(runstate)
    log.debug(logid+str(lst))
    ret = os.path.join(config["REFERENCE"],p,subDict(config["ANNOTATE"],lst)[step])
    log.debug(logid+str(ret))
    return ret

@check_run
def runstate_from_sample(sample,config):
    logid = scriptname+'.Collection_runstate_from_sample: '
    ret = list()
    for s in sample:
        s = os.path.basename(s)
        for k,v in config["SAMPLES"].items():
            for f in find_key_for_value(s,v):
                log.debug(logid+f)
                ret.append(f)
    return ret

@check_run
def samplecond(sample,config):
    logid = scriptname+'.Collection_samplecond: '
    ret = list()
    paired = False
    for s in sample:
        check = os.path.dirname(s).split(os.sep)
        log.debug(logid+str(check))
        for r in runstate_from_sample([s],config):
            tmplist = check
            tmplist.append(r)
            log.debug(logid+str(tmplist))
            if getFromDict(config['SEQUENCING'],tmplist) is 'paired':
                paired = True
            if paired:
                s=re.sub(r'_[r|R|\A\Z][1|2]','',s)
            ret.append(os.path.join("{p}".format(p=os.path.dirname(s)),"{c}".format(c=r),os.path.basename(s)))
    log.debug(logid+str(ret))
    return ret

@check_run
def conditiononly(sample,config):
    logid = scriptname+'.Collection_conditiononly: '
    ret = list()
    paired = False
    check = os.path.dirname(sample).split(os.sep)
    log.debug(logid+str(check))
    for r in runstate_from_sample([sample],config):
        log.debug(logid+str(r))
        ret.extend(check)
        if r not in ret:
            ret.append(r)
    log.debug(logid+str(ret))
    return ret

@check_run
def checkpaired(sample,config):
    logid = scriptname+'.Collection_checkpaired: '
    ret = list()
    paired = ''
    for s in sample:
        check = os.path.dirname(s).split(os.sep)
        for r in runstate_from_sample([s],config):
            tmplist = check
            tmplist.append(r)
            if 'paired' in getFromDict(config['SEQUENCING'],tmplist)[0]:
                paired = getFromDict(config['SEQUENCING'],tmplist)[0].split(',')[0]
    log.debug(logid+'PAIRED: '+str(paired))
    return paired

@check_run
def checkstranded(sample,config):
    logid = scriptname+'.Collection_checkstranded: '
    ret = list()
    stranded = ''
    for s in sample:
        check = os.path.dirname(s).split(os.sep)
        for r in runstate_from_sample([s],config):
            tmplist = check
            tmplist.append(r)
            if ',' in getFromDict(config['SEQUENCING'],tmplist)[0]:
                stranded = getFromDict(config['SEQUENCING'],tmplist)[0].split(',')[1]
    log.debug(logid+'STRANDEDNESS: '+str(stranded))
    return stranded

@check_run
def checkclip(sample,config):
    logid = scriptname+'.Collection_checkclip: '
    ret = list()
    clip = ''
    for s in sample:
        check = os.path.dirname(s).split(os.sep)
        log.debug(logid+str(check))
        r = runstate_from_sample([s],config)
        tmplist = check
        tmplist.extend(r)
        log.debug(logid+str(tmplist))
        if 'CLIP' in subDict(config['PEAKS'],tmplist):
            clip = subDict(config['PEAKS'],tmplist)['CLIP']
        else:
            log.debug(logid+'Key CLIP not found in config')
    log.debug(logid+str(clip))
    return str(clip)

@check_run
def check_tool_params(sample, runstate, config, subconf, idx):
    try:
        par = tool_params(sample, runstate ,config, subconf)['OPTIONS'][idx]
        if par is not '':
            return par
        elif subconf == 'MAPPING':
            return 'std'
        else:
            return ''
    except:
        if subconf == 'MAPPING':
            return 'std'
        else:
            return ''

@check_run
def aggregate_input(wildcards):
    return expand("post/{sample}/{i}.txt",
           sample=wildcards.sample,
           i=glob_wildcards(os.path.join(checkpoint_output, "{i}.txt")).i)

##############################
#########Python Subs##########
##############################
@check_run
def dict_inst(d):
    logid=scriptname+'.Collection_dict_inst: '
    if isinstance(d,dict) or isinstance(d,OrderedDict) or isinstance(d,defaultdict) or isinstance(d,NestedDefaultDict):
        return True

@check_run
def getFromDict(dataDict, mapList):
    logid = scriptname+'.Collection_getFromDict: '
    log.debug(logid+str(mapList))
    ret=list()
    for k in mapList:
        dataDict = dataDict[k]
    ret.append(dataDict)
    log.debug(logid+str(ret))
    return ret

@check_run
def subDict(dataDict, mapList):
    ret=dict()
    for k in mapList:
        if k in dataDict:
            ret = dataDict[k]
    return ret

@check_run
def nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value

@check_run
def merge_dicts(d,u):
    # https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    # python 3.8+ compatibility
    try:
        collectionsAbc = collections.abc
    except:
        collectionsAbc = collections

    for k, v in six.iteritems(u):
        dv = d.get(k, {})
        if not isinstance(dv, collectionsAbc.Mapping):
            d[k] = v
        elif isinstance(v, collectionsAbc.Mapping):
            d[k] = merge_dicts(dv, v)
        else:
            d[k] = v
    return d

@check_run
def list_all_keys_of_dict(dictionary):
    logid = scriptname+'.Collection_list_all_keys_of_dict: '
    if dict_inst(dictionary):
        for key, value in dictionary.items():
            if dict_inst(value):
                yield (key, value)
                yield from list_all_keys_of_dict(value)
            else:
                yield (key, value)
                yield ('last','key')
    else:
        yield dictionary

@check_run
def list_all_values_of_dict(dictionary):
    if dict_inst(dictionary):
        for key, value in dictionary.items():
            if dict_inst(value):
                #yield (key, value)
                yield from list_all_values_of_dict(value)
            else:
                yield (key, value)
                #yield ('last','value')
    else:
        yield dictionary

@check_run
def find_all_values_on_key(key, dictionary):
    if dict_inst(dictionary):
        for k, v in dictionary.items():
            if dict_inst(v):
                yield from find_all_values_on_key(key, v)
            elif k == key:
                yield v

    else:
        return dictionary

@check_run
def find_key_for_value(val, dictionary):
    logid=scriptname+'.Collection_find_key_for_value: '
    log.debug(logid+str(val))
    if dict_inst(dictionary):
        for k, v in dictionary.items():
            if dict_inst(v):
                log.debug(logid+'item'+str(v))
                yield from find_key_for_value(val, v)
            elif v == val or val in v:
                yield k
    else:
        return dictionary

@check_run
def value_extract(key, var):
    logid=scriptname+'.Collection_value_extract: '
    log.debug(logid+str(var))
    if hasattr(var,'items'):
        for k, v in var.items():
            if k == key:
                yield v
            if dict_inst(v):
                for result in value_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in value_extract(key, d):
                        yield result

@check_run
def find_innermost_value_from_dict(dictionary):
    logid=scriptname+'.Collection_find_innermost_value_from_dict: '
    if dict_inst(dictionary):
        for k, v in dictionary.items():
            if dict_inst(v):
                 return(find_innermost_value_from_dict(v))
            else:
                return v
    else:
        return dictionary
    return ret

@check_run
def removekey(d, key):
    logid=scriptname+'.Collection_removekey: '
    r = dict(d)
    del r[key]
    return r

@check_run
def getlowest_list(a, n):
    if n > len(a) - 1:
        b = len(a) - 1
    else:
        b = n
    if len(a) > 0 and n > 0:
        return list(np.partition(a, b)[:n])
    else:
        return list(None for i in range(n))

@check_run
def gethighest_list(a, n):
    if len(a)-n < 0:
        b = len(a)-1
    else:
        b = len(a)-n
    if len(a) > 0 and n > 0:
        return list(np.partition(a, b)[-n:])
    else:
        return list(None for i in range(n))

@check_run
def getlowest_dict(a, n):
    if n > len(a):
        b = len(a)
    else:
        b = n
    if len(a) > 0:
        return dict(heapq.nsmallest(b,a.items(), key=itemgetter(1)))
    else:
        return dict({i:None for i in range(n)})

@check_run
def gethighest_dict(a, n):
    if n > len(a):
        b = len(a)
    else:
        b = n
    if len(a) > 0:
        return dict(heapq.nlargest(b,a.items(), key=itemgetter(1)))
    else:
        return dict({i:None for i in range(n)})

@check_run
def toarray(file, ulim):
    x = np.loadtxt(str(file), usecols = (ulim), delimiter = '\t', unpack = True, converters = {ulim: lambda s: convertcol(s.decode("utf-8"))})
    return x

@check_run
def convertcol(entry):
    if isinvalid(entry):
        #       if entry is None or entry == 'NA' or entry == 'nan' or entry is np.nan:
        return np.nan
    else:
        return float(entry)

@check_run
def isvalid(x=None):
    if x:
        if x in ('None', 'nan', 'none', 'NA', 'NAN') or x is None or x is np.nan:
            return False
        else:
            return True
    else:
        return False

@check_run
def isinvalid(x=None):

    if x:
        if x in ('None', 'nan', 'none', 'NA', 'NAN') or x is None or x is np.nan:
            return True
        else:
            return False
    else:
        return True

@check_run
def makeoutdir(outdir):

    if not os.path.isabs(outdir):
        outdir =  os.path.abspath(outdir)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    return outdir

@check_run
def parseseq(sequence):
    if (isinstance(sequence, StringIO)):
        seq = sequence

    elif ( isinstance(sequence, str) and sequence == 'random' ):
        rand = "\n".join(createrandseq(length, gc, number, alphabet))
        seq = StringIO(rand)
        o = gzip.open('Random.fa.gz','wb')
        o.write(bytes(rand,encoding='UTF-8'))
        o.close()

    elif (isinstance(sequence, str) and os.path.isfile(sequence)):
        if '.gz' in sequence :
            seq = gzip.open(sequence,'rt')
        else:
            seq = open(sequence,'rt')
    else:
        header = ">Seq1:default:nochrom:(.)"
        s = sequence
        seq = StringIO("{header}\n{s}".format(header=header, s=s))

    return seq

@check_run
def npprint(a, o=None):#, format_string ='{0:.2f}'):
    out = ''
    it = np.nditer(a, flags=['f_index'])
    while not it.finished:
        out += "%d\t%0.7f" % (it.index+1,it[0])+"\n"
        it.iternext()
    if o:
        o.write(bytes(out,encoding='UTF-8'))
    else:
        print(out)
@check_run
def idfromfa(id):
    goi, chrom, strand = [None, None, None]
    try:
        goi, chrom = id.split(':')[::2]
        strand = str(id.split(':')[3].split('(')[1][0])
    except:
        eprint('Fasta header is not in expected format, you will loose information on strand and chromosome')
        goi = id
        chrom, strand = ['na','na']

    if goi and chrom and strand:
        return [str(goi), str(chrom), str(strand)]
    else:
        sys.exit('Could not assign any value from fasta header, please check your fasta files')

@check_run
def cluster2trna(seqs):
    translater = collections.OrderedDict()
    translater['cluster'] = collections.OrderedDict()
    translater['tRNA'] = collections.OrderedDict()

    for fa in SeqIO.parse(seqs,'fasta'):
        head = str(fa.id).upper()           # cluster1:chr19.tRNA5-LysCTT(+) cluster2:NC_007091.3.tRNA25-ArgTCT
        cluster, info = head.split(':')
        chrom, trna = (info.split('.')[0], info.split('.')[-1].split('(')[0])
        strand = 'u'
        if '(+)' in info or '(-)' in info:
            strand = re.sub('[()]', '_', info.split('.')[-1]).split('_')[1]

        if cluster in translater['cluster']:
            translater['cluster'][cluster].append(trna)
        else:
            translater['cluster'][cluster] = list()
            translater['cluster'][cluster].append(trna)
        if chrom in translater['tRNA']:
            if strand in translater['tRNA'][chrom]:
                translater['tRNA'][chrom][strand].append(trna)
            else:
                translater['tRNA'][chrom][strand] = list()
                translater['tRNA'][chrom][strand].append(trna)
        else:
            translater['tRNA'][chrom] = collections.OrderedDict()
            translater['tRNA'][chrom][strand] = list()
            translater['tRNA'][chrom][strand].append(trna)

    return translater

@check_run
def check_ref(reference):
    if os.path.exists(os.path.abspath(reference)):
        return reference
    elif os.path.exists(os.path.abspath(reference+'.gz')):
        return reference+'.gz'

@check_run
def runjob(jobtorun):
    return subprocess.run(jobtorun, shell=True, universal_newlines=True, capture_output=True)  # python >= 3.7

#
# Collection.py ends here
