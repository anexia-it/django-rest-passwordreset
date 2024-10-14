# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

PyPi: [https://pypi.org/project/django-rest-passwordreset/](https://pypi.org/project/django-rest-passwordreset/).

## [Unreleased]

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

[Unreleased]: https://github.com/anexia-it/django-rest-passwordreset/compare/1.4.2...HEAD
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
