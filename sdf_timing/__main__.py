import argparse
import json
from .sdfparse import parse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdf', type=str, help='Path to input SDF file')
    parser.add_argument('--json', type=str, help='Path to output JSON')

    args = parser.parse_args()

    with open(args.sdf, 'r') as fp:
        timings = parse(fp.read())

    with open(args.json, 'w') as fp:
        json.dump(timings, fp, indent=4, sort_keys=True)


if __name__ == '__main__':
    main()
