# Web address claim audit

An offline static audit compares documentation about well-formed web addresses with Python source. It reports discrepancies for human review.

## Usage

```sh
url-validation-claim-audit audit .
url-validation-claim-audit audit . --json --verbose --ignore vendor --fail-on medium
url-validation-claim-audit --version
python3 -m url_validation_claim_audit audit .
```

The optional directory defaults to the current directory. Repeat `--ignore` for each relative path prefix. The default threshold is high; medium also fails on test-only evidence. Exit status is 0 for a pass, 2 for findings at the threshold, and 1 for usage or I/O errors.

## Findings

```text
documented-url-validation-claim-false
documented-no-url-validation-claim-false
```

The first finding is high without production evidence, or medium when evidence appears only in tests. The second is high when a denial conflicts with production evidence. A positive claim without Python files is high; a denial without Python files passes.

## Scope

The root README and Markdown files under a docs directory are read as prose; fenced blocks are excluded and inline code counts. Matches ignore case, expand contractions, replace hyphens with spaces, and collapse whitespace within paragraphs. Denials are removed before positive matches. Python files are parsed without execution; symlinks and fixture, docs, and example directories are excluded from evidence. Test files are assessed separately. Syntax errors supply no evidence.

Recognized calls include the following, with aliases resolved from imports. The second route requires both construction and an instance call in one module. Generic named methods and imported functions are also recognized.

```text
validators.url
 django.core.validators.URLValidator
pydantic.AnyUrl / HttpUrl / AnyHttpUrl
rfc3987.parse / match
```

## Differentiation

This audit covers well-formed web addresses. It does not cover generic input checking, ownership confirmation by a one-time code or link, authentication against a stored password hash, password hashing, password generation, PDF encryption, email sending, SMS sending, document extraction, barcode decoding, email address checking, phone number checking, password strength, JSON Schema conformance, JSON decoding, regex matching, address parsing, network fetching, or bare domain checking.

Other families cover spreadsheet reading and generation, word-document reading and generation, presentation reading and generation, PDF extraction, generation, merging, splitting, rotation, form-filling, watermarking, redaction, compression and annotation, table extraction, OCR, e-signature, payment processing, screen recording, video generation, QR and barcode generation, barcode scanning, audio mixing, generation and editing, source separation, speech recognition, text-to-speech, noise suppression, music generation and transcription. Their claims are outside this phrase set.

## Limitations

Static patterns are not semantic judgment. Each case below needs human review.

- This phrase can describe a database or remote policy rather than local code:

  ```text
  validate url
  ```

- This phrase can describe a manual runbook step:

  ```text
  check url
  ```

- This phrase can describe a roadmap item:

  ```text
  url validation
  ```

- This phrase can refer to a hosted page:

  ```text
  url validator
  ```

- This phrase can be advice to a reader:

  ```text
  valid url
  ```

- This phrase can describe a successful fetch:

  ```text
  url is valid
  ```

- This phrase can describe reachability testing:

  ```text
  url check
  ```

- This phrase can describe a service that pings addresses:

  ```text
  url checker
  ```

- This phrase can describe a documented pattern without code:

  ```text
  url format check
  ```

- This phrase can describe ownership confirmation:

  ```text
  verify url
  ```

- This phrase can describe a length rule alone:

  ```text
  detect invalid url
  ```

- This phrase can occur in a theoretical discussion:

  ```text
  url well formed
  ```

- This phrase can describe generated output rather than input checking:

  ```text
  is valid url
  ```

- This phrase can name a specification section without code:

  ```text
  url validity
  ```

- A recognized library call counts even when it never runs.
- A library reference passed through an untracked variable chain is missed.
- A library import alone is not evidence.
- Roadmap, changelog and TODO prose still count as claims when in scope.
- Denials outside the listed phrases are not recognized.
- A top-level changelog outside the documentation directory is invisible.
- Evidence split between modules does not count as a pair.
- Locally defined route names shadow imports, even for wrappers.
- Dead code counts.
- A subprocess invoking an external checker is not evidence.
- A generic input check alone is not evidence.
- An email address check alone is not evidence.
- A phone number check alone is not evidence.
- An extraction call alone is not evidence.
- A locally defined generic name is shadowed, even if it implements the capability.
- Generic aliases passed through untracked chains are missed.
- Exact phrases are matched, not meaning; paraphrases can be missed and unrelated uses can be flagged.
- Source in other languages is invisible.
- Runtime-only imports and plugins are invisible; no code runs and no network is used.
- A checker construction without an instance call is not evidence, including one passed in a list of field validators.
- A field annotation alone is not evidence.
- Parsing or splitting alone is not evidence, even when scheme or host attributes are read.
- Fetching alone is not evidence.
- Encoding or decoding an address alone is not evidence.
- Address transformations alone are not evidence.
- A regular expression match alone is not evidence.
- A domain or IP address check alone is not evidence.
