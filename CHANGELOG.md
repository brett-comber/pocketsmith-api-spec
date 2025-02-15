# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).


## [Unreleased]


## [0.3.4] — 2022-01-25
### Fixed
 - Resolved various nullable fields not being marked nullable (addressing further validation errors in strict generated API clients)


## [0.3.3] — 2021-11-25
### Fixed
 - Allow Data Feeds Connection/Account/Provider IDs to be strings or integers (addresses validation errors in generated API clients)


## [0.3.2] — 2021-11-22
### Fixed
 - Fix validation errors in `DataFeedsConnection` schemas with generated API clients
 - Remove intra-spec `$ref` directives in endpoint properties, as these cause issues with generated API clients


## [0.3.1] — 2021-11-22
### Fixed
 - Weaken strict enforcement of `DataFeedsConnection` and `DataFeedsAccount` enums


## [0.3.0] — 2021-11-21
### Added
 - Added Data Feeds Accounts
 - Added Data Feeds fields to Transaction Accounts

### Changed
 - Renamed "Data Connections" to "Data Feeds Connections", to more closely match API paths

### Fixed
 - The `/data_feeds_connections/{id}/data_feeds_accounts` endpoint now correctly returns "Data Feeds Accounts" (not top-level "Accounts")


## [0.2.0] — 2021-11-10
### Added
 - Added tentative Data Connections support
