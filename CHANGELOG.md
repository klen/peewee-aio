# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.15.0] - 2022-12-21

- Support union

## [0.14.7] - 2022-11-14

- Fix `prefetch`, support peewee `3.15.4`

## [0.14.3] - 2022-11-07

### Fixed

- Fix `DeferredKey` support

## [0.13.1] - 2021-12-01

### Fixed

- Fix `delete_instance` to follow peewee defaults

## [0.13.0] - 2021-11-29

### Added

- AIOModel.save now supports `on_select_ignore` keyword argument

## [0.12.4] - 2021-11-01

### Fixed

- Fixed `returning` clause

## [0.12.3] - 2021-10-29

### Fixed

- `Model.insert_many` now supports `on_conflict`

## [0.12.1] - 2021-10-27

### Added

### Changed

### Removed

[unreleased]: https://github.com/klen/peewee-aio/compare/0.14.7...HEAD
[0.14.7]: https://github.com/klen/peewee-aio/compare/0.14.3...0.14.7
[0.14.3]: https://github.com/klen/peewee-aio/compare/0.13.1...0.14.3
[0.13.1]: https://github.com/klen/peewee-aio/compare/0.13.0...0.13.1
[0.13.0]: https://github.com/klen/peewee-aio/compare/0.12.4...0.13.0
[0.12.4]: https://github.com/klen/peewee-aio/compare/0.12.3...0.12.4
[0.12.3]: https://github.com/klen/peewee-aio/compare/0.12.1...0.12.3
[0.12.1]: https://github.com/klen/peewee-aio/compare/0.1.0...0.12.1
[0.1.0]: https://github.com/klen/peewee-aio/releases/tag/0.1.0
