#!/usr/bin/env python
"""Utilities for working with Revit shared parameter files

Usage:
    rsparam.py (-h | --help)
    rsparam.py (-V | --version)
    rsparam.py [-q -e <encod>] list [-a -s <sort_by> -c <columns>] <src_file>
    rsparam.py [-q -e <encod>] list [-p -g -s <sort_by> -c <columns>] <src_file>
    rsparam.py [-q -e <encod>] list -p [-f <groupid>] <src_file>
    rsparam.py [-q -e <encod>] find dupl [-n -a -p -g -s <sort_by> -c <columns>] <src_file>
    rsparam.py [-q -e <encod>] find <regex_pattern> [-p -g -s <sort_by> -c <columns>] <src_file>
    rsparam.py [-q -e <encod>] comp [-p -g -1 -2 -s <sort_by> -c <columns>] <first_file> <second_file>
    rsparam.py [-q -e <encod>] merge <dest_file> <src_files>...
    rsparam.py [-q -e <encod>] sort [-n] <src_file>

Options:
    -h, --help                          Show this help
    -V, --version                       Show version
    -q, --quiet                         Quiet mode [default: False]
    -e <encod>, --encode <encod>        File encoding [default: utf-8]
    -a, --all                           All items
    -p, --params                        Parameters only
    -g, --groups                        Parameter groups only
    -s <sort_by>, --sortby <sort_by>    Sort by "name", "group" [default: name]
    -c <columns>, --columns <columns>    List of data columns separated by :
    -f <groupid>, --filter <groupid>    Filter by group id
    -n, --byname                        Compare by name
    -1, --first                         First file only
    -2, --second                        Second file only
"""


from docopt import docopt
import colorful
from tabulate import tabulate

import rsparam


# process command line args
args = docopt(__doc__, version='rsparam {}'.format(rsparam.__version__))


def report(message):
    if not args['--quiet']:
        print(message)


def report_globals():
    enc_report = 'encoding={}'.format(args['--encode']) if args['--encode'] \
        else 'encoding not set'
    report(colorful.yellow(enc_report))


def report_filenames(sparam_files,
                     title='shared parameter file: ',
                     colorfunc=colorful.blue):
    if not isinstance(sparam_files, list):
        sparam_files = [sparam_files]
    for sparam_file in sparam_files:
        report(colorfunc(f'{title}{sparam_file}'))


def list_params(src_file, sparams=None):
    if not sparams:
        sparams = rsparam.get_params(src_file, groupid=args['--filter'])

    sparamdata = []
    if args['--columns']:
        sparamattrs = args['--columns'].split(':')
    else:
        sparamattrs = ['guid', 'name', 'datatype', 'group', 'lineno']
    for sp in sparams:
        spcolumns = []
        for spattr in sparamattrs:
            spcolumns.append(getattr(sp, spattr, None))
        sparamdata.append(tuple(spcolumns))

    if args['--sortby'] == 'group':
        sparamdata = sorted(sparamdata, key=lambda x: getattr(x, 'name', 0))

    print(tabulate(sparamdata,
                   headers=('Guid', 'Name', 'Datatype', 'Group', 'Line #')))
    report("Total of {} items.".format(len(sparamdata)))


def list_groups(src_file, spgroups=None):
    if not spgroups:
        spgroups = rsparam.get_paramgroups(src_file, encoding=args['--encode'])

    spgroupdata = []
    if args['--columns']:
        sgroupattrs = args['--columns'].split(':')
    else:
        sgroupattrs = ['guid', 'name', 'lineno']
    for spg in spgroups:
        spgcolumns = []
        for spgattr in sgroupattrs:
            spgcolumns.append(getattr(spg, spgattr, None))
        spgroupdata.append(tuple(spgcolumns))

    print(tabulate(spgroupdata, headers=('Id', 'Description', 'Line #')))
    report("Total of {} items.".format(len(spgroupdata)))


def list_all(src_file):
    list_groups(src_file)
    list_params(src_file)


def find_param_dupls(src_file):
    byname = args['--byname']
    spentries = rsparam.find_duplicates(src_file, byname=byname)
    duplparam = 'name' if byname else 'guid'
    dupldata = []
    report(colorful.yellow('\nduplicate params by {}:'.format(duplparam)))
    for dlist in spentries.params:
        for d in dlist:
            dupldata.append((d.name if byname else d.guid,
                             d.guid if byname else d.name,
                             d.datatype, d.group, d.lineno))
        print(colorful.yellow('\nduplicates by {}: {}'.format(duplparam,
                                                              dupldata[0][0])))

        if args['--sortby'] == 'group':
            dupldata = sorted(dupldata, key=lambda x: str(x[3]))

        print(tabulate(dupldata,
                       headers=('Name' if byname else 'Guid',
                                'Guid' if byname else 'Name',
                                'Datatype', 'Group', 'Line #')))


def find_group_dupls(src_file):
    byname = args['--byname']
    spentries = rsparam.find_duplicates(src_file, byname=byname)
    duplparam = 'name' if byname else 'guid'
    dupldata = []
    report(colorful.yellow('\nduplicate groups by {}:'.format(duplparam)))
    for dlist in spentries.groups:
        for d in dlist:
            dupldata.append((d.name if byname else d.guid,
                             d.guid if byname else d.name,
                             d.lineno))
        print(colorful.yellow('\nduplicates by {}: {}'.format(duplparam,
                                                              dupldata[0][0])))
        print(tabulate(dupldata,
                       headers=('Name' if byname else 'Guid',
                                'Guid' if byname else 'Name',
                                'Line #')))


def find_all_dupls(src_file):
    find_group_dupls(src_file)
    find_param_dupls(src_file)


def find_matching(src_file):
    search_str = args['<regex_pattern>']
    spentries = rsparam.find(src_file, search_str, encoding=args['--encode'])
    if spentries.groups and not args['--params']:
        report(colorful.yellow('\ngroups matching: {}'.format(search_str)))
        list_groups(None, spgroups=spentries.groups)

    if spentries.params and not args['--groups']:
        report(colorful.yellow('\nparams matching: {}'.format(search_str)))
        list_params(None, sparams=spentries.params)


def comp(first_file, second_file):
    uniq1, uniq2 = rsparam.compare(first_file, second_file,
                                   encoding=args['--encode'])
    if uniq1.groups and not args['--params'] and not args['--second']:
        report(colorful.yellow('\nunique groups in first'))
        list_groups(None, spgroups=uniq1.groups)

    if uniq2.groups and not args['--params'] and not args['--first']:
        report(colorful.yellow('\nunique groups in second'))
        list_groups(None, spgroups=uniq2.groups)

    if uniq1.params and not args['--groups'] and not args['--second']:
        report(colorful.yellow('\nunique parameters in first'))
        list_params(None, sparams=uniq1.params)

    if uniq2.params and not args['--groups'] and not args['--first']:
        report(colorful.yellow('\nunique parameters in second'))
        list_params(None, sparams=uniq2.params)


def merge(dest_file, source_files):
    raise NotImplementedError()


def sort(source_file):
    raise NotImplementedError()


def main():
    # report globals
    report_globals()

    if args['list']:
        # reporting
        src_file = args['<src_file>']
        report_filenames(src_file, title='source file: ')

        # list groups only
        if args['--groups'] and not args['--params']:
            list_groups(src_file)
        # list params only
        elif args['--params'] and not args['--groups']:
            list_params(src_file)
        # list everything
        else:
            list_all(src_file)

    elif args['find']:
        # reporting
        src_file = args['<src_file>']
        report_filenames(src_file, title='source file: ')

        # report duplicates
        if args['dupl']:
            if args['--all']:
                find_all_dupls(src_file)
            elif args['--params']:
                find_param_dupls(src_file)
            elif args['--groups']:
                find_group_dupls(src_file)
        else:
            find_matching(src_file)

    elif args['comp']:
        # reporting
        first_file = args['<first_file>']
        report_filenames(first_file, title='first file: ')
        second_file = args['<second_file>']
        report_filenames(second_file, title='second file: ')

        # compare two shared parame files
        comp(first_file, second_file)

    elif args['merge']:
        # reporting
        dest_file = args['<dest_file>']
        report_filenames(dest_file, title='destination file: ')
        src_files = args['<src_files>']
        report_filenames(src_files, title='source file: ')

        # merge two shared param files
        merge(dest_file, src_files)

    elif args['sort']:
        # reporting
        source_file = args['<src_file>']
        report_filenames(source_file, title='source file: ')

        # sort shared param file
        sort(source_file, byname=args['--byname'])

    report('')
