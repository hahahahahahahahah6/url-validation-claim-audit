import argparse
import json
import sys
from . import __version__
from .audit import audit

class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(1, f'{self.prog}: error: {message}\n')

def main(argv=None):
    parser = Parser(prog='url-validation-claim-audit')
    parser.add_argument('--version', action='version', version=__version__)
    sub = parser.add_subparsers(dest='command', required=True, parser_class=Parser)
    cmd = sub.add_parser('audit')
    cmd.add_argument('repo', nargs='?', default='.')
    cmd.add_argument('--json', action='store_true')
    cmd.add_argument('--verbose', action='store_true')
    cmd.add_argument('--ignore', action='append', default=[])
    cmd.add_argument('--fail-on', choices=('high', 'medium'), default='high')
    args = parser.parse_args(argv)
    try:
        result = audit(args.repo, args.ignore)
    except (OSError, UnicodeError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2))
    elif result['findings']:
        for finding in result['findings']:
            print(f"{finding['severity']} {finding['id']}")
            if args.verbose:
                for claim in finding['claims']: print(f"  {claim['path']}: {claim['phrase']}")
                for path in finding['evidence']: print(f'  evidence: {path}')
    else:
        print('PASS')
    return 2 if any(f['severity'] == 'HIGH' or args.fail_on == 'medium' for f in result['findings']) else 0

if __name__ == '__main__':
    sys.exit(main())
