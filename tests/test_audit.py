import tempfile
import unittest
from pathlib import Path
from url_validation_claim_audit.audit import audit, claims, evidence
from url_validation_claim_audit.phrases import URLVALIDATION, NOURLVALIDATION, GENERIC_NAMES

class AuditTests(unittest.TestCase):
    def test_phrases(self):
        self.assertEqual((len(set(URLVALIDATION)), len(set(NOURLVALIDATION)), len(set(GENERIC_NAMES))), (50, 24, 24))
        for phrase in URLVALIDATION:
            with self.subTest(phrase=phrase): self.assertTrue(claims(phrase)[0])
        for phrase in NOURLVALIDATION:
            with self.subTest(phrase=phrase): self.assertEqual(claims(phrase), ([], [phrase]))
        self.assertEqual(claims('```\nvalidate url\n```\n\n`checks-url`'), (['checks url'], []))

    def test_routes(self):
        cases = ['import validators as v\nv.url()', 'from validators import url as u\nu()', 'import django\ndjango.core.validators.URLValidator()()', 'from django.core.validators import URLValidator as U\nv=U()\nv(x)', 'from django.core.validators import URLValidator\nv: object = URLValidator()\nv(x)', 'from django.core.validators import URLValidator\nwith URLValidator() as v:\n v(x)', 'import pydantic as p\np.HttpUrl(x)', 'from pydantic.networks import AnyUrl as U\nU(x)', 'from pydantic import AnyHttpUrl\nAnyHttpUrl(x)', 'import rfc3987 as r\nr.parse()', 'from rfc3987 import match as m\nm()']
        cases += ['obj.' + name + '()' for name in GENERIC_NAMES]
        cases += ['from helpers import ' + name + ' as f\nf()' for name in GENERIC_NAMES]
        for case in cases:
            with self.subTest(case=case): self.assertTrue(evidence(case))

    def test_not_evidence(self):
        cases = ['import validators', 'from django.core.validators import URLValidator\nURLValidator()', 'from django.core.validators import URLValidator\nf(validators=[URLValidator()])', 'v(x)', 'from pydantic import HttpUrl\nclass C:\n url: HttpUrl', 'url()', 'URLValidator()', 'AnyUrl()', 'HttpUrl()', 'parse()', 'match()', 'obj.url()', 'obj.parse()', 'obj.match()', 'obj.HttpUrl()', 'import subprocess\nsubprocess.run(["validator", "url"])', '"validate url"', 'url', 'def bad(:']
        cases += ['import urllib.parse\nurllib.parse.' + name + '(x).scheme' for name in ('urlparse','urlsplit','urlunparse','urljoin','urlencode','quote','unquote')]
        cases += ['import rfc3987\nrfc3987.' + name + '(x)' for name in ('resolve','normalize','compose')]
        cases += ['import validators\nvalidators.' + name + '(x)' for name in ('domain','hostname','ipv4','ipv6')]
        cases += ['import re\nre.' + name + '("https?://", x)' for name in ('match','search','fullmatch')]
        cases += ['requests.get(x)', 'urlopen(x)', 'httpx.get(x)', 'send_sms(x)', 'send_email(x)', 'validate_email(x)', 'validate_phone(x)', 'check_password(x)', 'authenticate(x)', 'extract(x)', 'decode_barcode(x)']
        cases += ['import validators\nvalidators = x\nvalidators.url(x)', 'from validators import url\ndef url(x): pass\nurl(x)', 'def validate_url(x): pass\nobj.validate_url(x)', 'import helpers\nhelpers = x\nhelpers.validate_url(x)']
        for case in cases:
            with self.subTest(case=case): self.assertFalse(evidence(case))
        self.assertTrue(evidence('obj = thing()\nobj.validate_url(x)'))

    def test_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); (p/'README.md').write_text('validate url')
            self.assertEqual(audit(p)['findings'][0]['severity'], 'HIGH')
            (p/'tests').mkdir(); (p/'tests/test_a.py').write_text('import validators\nvalidators.url(x)')
            self.assertEqual(audit(p)['findings'][0]['severity'], 'MEDIUM')
            (p/'a.py').write_text('import validators\nvalidators.url(x)')
            self.assertFalse(audit(p)['findings'])
            (p/'README.md').write_text('does not validate url')
            self.assertEqual(audit(p)['findings'][0]['severity'], 'HIGH')
            self.assertFalse(audit(p, ['a.py'])['findings'])

    def test_split_and_exclusions(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); (p/'README.md').write_text('validate url')
            (p/'a.py').write_text('from django.core.validators import URLValidator\nv = URLValidator()')
            (p/'b.py').write_text('v(x)')
            for name in ('fixtures', 'docs', 'examples'):
                (p/name).mkdir(); (p/name/'a.py').write_text('import validators\nvalidators.url(x)')
            self.assertEqual(audit(p)['findings'][0]['severity'], 'HIGH')

    def test_readme(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(claims((root/'README.md').read_text()), ([], []))

if __name__ == '__main__': unittest.main()
