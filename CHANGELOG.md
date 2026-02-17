# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.4] - 2026-02-17

### Added
- Added `battery_percent_rechargeable` sensor to provide a more realistic
  battery level estimation for rechargeable batteries (e.g. NiMH).
- The new sensor derives remaining charge from pack voltage and is intended
  for monitoring and automations when using rechargeable cells.
- Existing `battery_percent` sensor continues to reflect the vendor/device
  battery percentage logic.

### Changed
- Clarified separation between vendor-reported battery percentage and
  voltage-based rechargeable battery estimation.

## [0.1.3] - 2026-02-15

### Changed

- Battery voltage min to 4.0V and max to 6.2V

## [0.1.2] - 2026-02-08

### Changed

- Timestamp of paperlesspaper_push_state is now regular UTC timestamp

## [0.1.1] - 2026-02-07

### Added

- Added battery level and last updated sensors

## [0.1.0] - 2026-02-03

### Added

- Initial release of the paperlesspaper Push custom integration.
