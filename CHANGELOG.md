# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

PyPi: [https://pypi.org/project/django-rest-passwordreset/](https://pypi.org/project/django-rest-passwordreset/).

## [Unreleased]

### Added
- Added Python 3.14 support
- Added Django 5.2 LTS support
- Added Django 6.0 support
- Added Django Rest Framework 3.16 support
- Added Django Rest Framework 3.17 support
- Added `DJANGO_REST_PASSWORDRESET_THROTTLE_CLASSES` to replace the request-token endpoint throttle
  classes. The default remains `ResetPasswordRequestTokenThrottle`; setting it to an empty list
  delegates the request-token endpoint to DRF's global `DEFAULT_THROTTLE_CLASSES`.
- Added a database index on `ResetPasswordToken.created_at` so expired-token cleanup
  (`clearresetpasswodtokens` and the request-token endpoint's `clear_expired_tokens`) can use an
  indexed range filter before deleting matching rows. Documented scheduling the
  `clearresetpasswodtokens` management command (cron, Celery beat, or django-future-tasks) as the
  recommended way to keep the token table small; the validate/confirm endpoints intentionally do not
  run bulk cleanup.

### Security

- Documented a security warning for `RandomNumberTokenGenerator`: the default 5-digit numeric range
  has only about 90,000 possible values and can be brute-forced in roughly a day at one guess per
  second against the validate/confirm endpoints. The README example now uses a much larger numeric
  range, and a warning was added to the class docstring. `RandomStringTokenGenerator` remains the
  safer default.
- The token-validation and password-confirm endpoints no longer declare `throttle_classes = ()`, so
  an operator's global `REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"]` is now respected on those flows.
  Previously, the empty-tuple declaration silently overrode global throttle configuration on these
  security-critical endpoints (CWE-307 / CWE-799). The request-token endpoint retains the library's
  `ResetPasswordRequestTokenThrottle` and built-in `3/day` fallback. This enables configured global
  throttles for token validation and password confirmation; it does not add a new built-in throttle
  to those endpoints.
- The reset-token request endpoint (`POST .../reset_password/`) no longer exposes whether an
  account exists via HTTP status or response body. Previously, by default, a request for a
  non-existent (or inactive / no-usable-password) account returned HTTP 400 with an `email` error,
  while an existing account returned HTTP 200 — a user-enumeration oracle (CWE-204). The default is
  now to always return HTTP 200 with a generic body, matching the behavior of Django's built-in
  password reset and common industry practice.
  - The `DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE` setting now defaults to `True`.
  - Explicitly setting it to `False` re-enables the legacy 400-based oracle; this opt-in is
    deprecated and will be removed in a future major release.
  - Note: a residual timing side channel remains (the existing-account path performs a DB write and
    fires `reset_password_token_created`, which often triggers an SMTP send). The response-status
    oracle is closed; the timing channel is not. A future hardening pass may equalize the two paths.
- The token-validation and password-confirm endpoints now use the same generic HTTP 404 response for
  missing, malformed, expired, and ineligible-user tokens. Expired tokens are still deleted when
  presented, but the response no longer reveals whether the token existed or why it failed.

### Changed

- **Breaking:** `DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE` default changed from `False` to `True`.
  Clients that rendered UI based on the previous 400 response for unknown emails will now always receive 200.
  Set `DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE = False` to temporarily restore the legacy behavior
  (deprecated).
- **Breaking:** Global DRF throttles now apply to the token-validation and password-confirm endpoints.
  Deployments that configure `REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"]` may now receive HTTP 429 from
  those endpoints where earlier versions bypassed the global throttles. For `ScopedRateThrottle`, the
  endpoint scopes are `django-rest-passwordreset-validate-token` and
  `django-rest-passwordreset-confirm`. If the request-token endpoint is delegated to global throttles
  with `DJANGO_REST_PASSWORDRESET_THROTTLE_CLASSES = []`, its scope is
  `django-rest-passwordreset-request-token`. Any active `ScopedRateThrottle` scope must have a matching
  `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` entry; otherwise the affected endpoint raises
  `ImproperlyConfigured` (HTTP 500).
- **Breaking:** Token failure responses on validate/confirm are less specific. Expired tokens now
  return the generic invalid-token 404 response instead of `"The token has expired"`. Confirming a
  valid token whose user is inactive or otherwise ineligible now returns HTTP 404 instead of HTTP 200
  and does not consume the token.
- Removed Django 4.2 and 5.1 from the supported/tested matrix
- Updated CI/CD pipelines to test currently supported Django/Python combinations
- Updated PostgreSQL test service to version 14 (required by Django 5.2)

### Fixed
- Excluded the library's `tests` package from installation to prevent import shadowing (for example `ModuleNotFoundError: No module named 'tests.plugins'` in consumer projects using pytest).

## [1.5.0]

- Added Python 3.13 support
- Added Django 5.1 support
- Added Django Rest Framework 3.15 support
- Removed Python 3.8 support
- Removed Django 3.2 support
- Removed Django Rest Framework 3.14 support

## [1.4.2]

### Fixed

- X-Forwarded-For containing multiple IPs does not respect inet data type (#191)

## [1.4.1]

### Fixed
- Fix the reset_password_token_created signal to be fired even when no token have been created. (#188)

## [1.4.0]

### Added
- `pre_password_reset` and `post_password_reset` signals now provide `reset_password_token
- Add translations to Brazilian Portuguese
- Possibility to return the username and email address when validating a token
- Generating and clearing tokens programmatically 
- Support for Python 3.11, 3.12
- Support for Django 4.2, 5.0
- Support for DRF 3.14

### Changed
- Increase max_length of user_agent to 512
- Dropped support for Django 4.0, 4.1
- Dropped support for DRF 3.12, 3.13
- Dropped support for Python 3.7

## [1.3.0]

### Added
- Support for Python 3.10
- Support for Django 3.2, 4.0, 4.1
- Support for DRF 3.12, 3.13 
### Changed
- Dropped support for Python 3.5, 3.6
- Dropped support Django 2.2, 3.0, 3.1
- Dropped support form DRF 3.11, 3.12

## [1.2.1]
### Fixed
- CVE-2019-19844 potentials

## [1.2.0]
### Added
- Support for Django 3.x, DRF 3.1x 
### Changed
- Dropped support for Python 2.7 and 3.4, Django 1.11, 2.0 and 2.1, DRF < 3.10

## [1.1.0]
### Added
- Token validation endpoint (#45, #59, #60)
- Dynamic lookup field for email (#31)
### Changed
- Fixes #34
- PRs #40, #51, #54, #55

## [1.0.0]
### Added
- Browseable API support, validations (#24)
- Customized token generation (#20)
- Clear expired tokens (#18)

## [0.9.7]
- Fixes #8 (again), #11
## [0.9.6]
- Fixes #8
## [0.9.5]
- Fixes #4
## [0.9.4]
- PR #1
## [0.9.3]
- Maintenance Release
## [0.9.1]
- Maintenance Release
## [0.9.0]
- Initial Release

[Unreleased]: https://github.com/anexia-it/django-rest-passwordreset/compare/1.5.0...HEAD
[1.5.0]: https://github.com/anexia-it/django-rest-passwordreset/compare/1.4.2...1.5.0
[1.4.2]: https://github.com/anexia-it/django-rest-passwordreset/compare/1.4.1...1.4.2
[1.4.1]: https://github.com/anexia-it/django-rest-passwordreset/compare/1.4.0...1.4.1
[1.4.0]: https://github.com/anexia-it/django-rest-passwordreset/compare/1.3.0...1.4.0
[1.3.0]: https://github.com/anexia-it/django-rest-passwordreset/compare/1.2.1...1.3.0
[1.2.1]: https://github.com/anexia-it/django-rest-passwordreset/compare/1.2.0...1.2.1
[1.2.0]: https://github.com/anexia-it/django-rest-passwordreset/compare/1.1.0...1.2.0
[1.1.0]: https://github.com/anexia-it/django-rest-passwordreset/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/anexia-it/django-rest-passwordreset/compare/0.9.7...1.0.0
[0.9.7]: https://github.com/anexia-it/django-rest-passwordreset/compare/0.9.6...0.9.7
[0.9.6]: https://github.com/anexia-it/django-rest-passwordreset/compare/0.9.5...0.9.6
[0.9.5]: https://github.com/anexia-it/django-rest-passwordreset/compare/0.9.4...0.9.5
[0.9.4]: https://github.com/anexia-it/django-rest-passwordreset/compare/0.9.3...0.9.4
[0.9.3]: https://github.com/anexia-it/django-rest-passwordreset/compare/0.9.1...0.9.3
[0.9.1]: https://github.com/anexia-it/django-rest-passwordreset/compare/0.9.0...0.9.1
[0.9.0]: https://github.com/anexia-it/django-rest-passwordreset/0.9.0/
