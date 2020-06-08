#!/usr/bin/env python3
import argparse
import subprocess
import logging
from pprint import pprint
from collections import defaultdict
import re
import os

RED = ("\033[1;31m", "\033[1;0m")
BLUE = ("\033[1;34m", "\033[1;0m")
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('NM_TOOL', help='nm binary')
    parser.add_argument('NAME ELF', help='tuples to analyze, '
                        'e.g. special: special_version.elf',
                        nargs='+')
    parser.add_argument('-C', '--force-color', action='store_true',
                        help='force colorized changes')
    parser.add_argument('--change', help='limit output to certain class of changes',
                        choices=['segment', 'size', 'all'],
                        default=os.environ.get('CHANGE', 'all'))
    parser.add_argument('--symbols', help='limit output to certain class of symbols',
                        choices=['common', 'unique', 'all', 'merged'],
                        default=os.environ.get('KEYSET', 'all'))
    parser.add_argument('--sort', help='define sort criterium',
                        choices=['name', 'size'],
                        default=os.environ.get('SORT', 'name'))
    parser.add_argument('--segment', help='limit output to symbols appearing in listed segments',
                        default=os.environ.get('SEGMENT', None))

    args = parser.parse_args()

    if not (args.force_color or os.isatty(1)):
        global RED, BLUE
        RED = ("","")
        BLUE = RED

    inp = getattr(args, 'NAME ELF', [])
    if len(inp) % 2:
        parser.print_help()
    pairs = [(inp[i], inp[i+1]) for i in range(0,len(inp), 2)]

    data = defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:' ')))
    keys = defaultdict(lambda:set())
    for pair in pairs:
        name, filename = pair
        parse_elf(args.NM_TOOL, name, filename, data, keys)


    all_keys = keys[name].union(*keys.values())
    common_keys = keys[name].intersection(*keys.values())
    unique_keys = keys[name].union(*keys.values()) - common_keys

    lens = {name: len(name) for name in keys.keys()}

    fields = [f'{n:^{lens[n]+2}}' for n in keys.keys()]
    fields += ['name']
    print(" | ".join(fields))


    keysets = []
    if args.symbols in ['unique', 'all']:
        keysets.append(unique_keys)
    if args.symbols in ['common', 'all']:
        keysets.append(common_keys)
    if args.symbols in ['merged']:
        keysets = [list(unique_keys) + list(common_keys)]

    for keyset in keysets:
        sorted_keyset = None
        if args.sort == 'name':
            sorted_keyset = sorted(keyset)
        elif args.sort == 'size':
            sorted_keyset = sorted(keyset,
                                   key=lambda idx:
                                   int(list(data[idx].values())[0]['size'])
            )
        for key in sorted_keyset:
            d = data[key]
            sizes = [d[k]['size'] for k in keys.keys()]
            segments = set([i['segment'] for i in d.values()])
            if len(set(sizes)) == 1 and len(segments) == 1:
                continue
            elif args.change == 'segment' and len(segments) == 1:
                continue
            elif args.change == 'size' and len(set(sizes)) == 1:
                continue
            if args.segment is not None:
                if not any([seg in args.segment for seg in segments]):
                    continue
            segments -= set(" ")
            size_color = ("","") if len(set(sizes)-set(" ")) == 1 else BLUE
            seg_color = ("","") if len(segments) == 1 else RED
            fields = [f"{size_color[0]}{d[n]['size']:{lens[n]}}{size_color[1]} "
                      f"{seg_color[0]}{d[n]['segment']}{seg_color[1]}"
                      for n in keys.keys()]
            fields += [f"{key}"]
            print(" | ".join(fields))
        print('\n')


def parse_elf(nm, elf_name, elf, data, keys):
    result = subprocess.run([nm, '-SP', elf],
                            check=True,
                            stdout=subprocess.PIPE)
    for line in result.stdout.decode().strip().split('\n'):
        match = re.match("(?P<name>\S+) (?P<seg>\S) (?P<addr>\S+) (?P<size>\S*)",
                         line)
        if not match:
            logging.debug("failed line: %s", line)
            if ' N ' in line or line.startswith('N '):
                continue
            return
        name = match.group('name')
        data[name][elf_name] = {
            'segment': match.group('seg'),
            'size': int(match.group('size') or '0', 16),
            'addr': match.group('addr'),
            'name': name,
        }
        keys[elf_name].add(name)


if __name__ == '__main__':
    import sys
    main()
