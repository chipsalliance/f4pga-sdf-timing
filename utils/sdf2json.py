# Copyright 2022 Tomas Brabec
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
import os.path
import argparse
import json
from sdf_timing import sdfparse

def get_path_sufixes(path):
    sufixes = []
    [path,sufix] = os.path.splitext(path)
    while sufix:
        sufixes.insert(0,sufix[1:])
        [path,sufix] = os.path.splitext(path)
    return sufixes

def get_path_noextname(path):
    sufixes = []
    [path,sufix] = os.path.splitext(path)
    while sufix:
        sufixes.insert(0,sufix[1:])
        [path,sufix] = os.path.splitext(path)
    return path

# Define command-line API
opt_parser = argparse.ArgumentParser(description='Converts SDFs into JSON data format.')
opt_parser.add_argument('--dir', type=str, default=None,
        help='Path to a directory where to write out converted JSON file (unless --stdout).' + \
                ' Defaults to the same folder as the input file so that JSON file lies next to the input SDF file.', metavar='<path>'
        );
opt_parser.add_argument('--stdout', default=False, action='store_true',
        help='Print to standard output instead to a file.'
        );
opt_parser.add_argument('--force', default=False, action='store_true',
        help='Overwrites the output file if already exists.'
        );
opt_parser.add_argument('--gzip', default=False, action='store_true',
        help='Compresses the output file with gzip. Ignored when using --stdout.'
        );
opt_parser.add_argument('--indent', type=int, default=2, metavar='N',
        help='Number of spaces for indentation.'
        );
opt_parser.add_argument('files', nargs='+', metavar='file',
        help='List of SDF files to parse.'
        );

# parse command line arguments
args = opt_parser.parse_args();


if args.dir is not None and not os.path.isdir(args.dir):
    print("Not a directory: " + str(args.dir), file=sys.stderr);
else:
    for f in args.files:
        if not os.path.exists(f):
            print("Does not exists: '%s'" % f, file=sys.stderr);
        else:
            sdf = None;
            print("Reading %s ..." % f, file=sys.stderr);
            if f.endswith('gz'):
                import gzip;
                with gzip.open(f,'rt') as sdffile:
                    sdf = sdfparse.parse(sdffile.read())
            else:
                with open(f) as sdffile:
                    sdf = sdfparse.parse(sdffile.read())

            if sdf is not None:
                if not args.stdout:
                    exts = get_path_sufixes(f);
                    of = get_path_noextname(f);

                    if exts[-1] == 'gz': del exts[-1];
                    if exts[-1] == 'sdf': del exts[-1];

                    while len(exts) > 0:
                        of += '.' + exts.pop(0);

                    of += '.json';

                    if args.dir is not None:
                        of = os.path.join(args.dir, os.path.basename(of));

                    if args.gzip: of += '.gz';

                    if os.path.exists(of) and not args.force:
                        print("File already exists, not writing: %s" % of, file=sys.stderr);
                        continue;

                    print("Writing %s ..." % of, file=sys.stderr);
                    if args.gzip:
                        import gzip;
                        with gzip.open(of,'wt') as outfile:
                            json.dump(sdf, outfile, indent=args.indent)
                    else:
                        with open(of,'w') as outfile:
                            json.dump(sdf, outfile, indent=args.indent)
                else:
                    json.dump(sdf, sys.stdout, indent=args.indent)

