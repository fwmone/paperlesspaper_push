# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.9] - 2026-07-19

## Deprecated

`paperlesspaper_push` is now deprecated.

The manufacturer of the paperlesspaper frame has chosen to support the more comprehensive [`paperlesspaper-ha`](https://github.com/djiwondee/paperlesspaper-ha) integration, which provides UI-based configuration, automatic device discovery, multi-frame support, Media Browser integration, and additional device entities and events.

To avoid maintaining two largely overlapping integrations and to make the choice easier for users, no further feature development is planned for `paperlesspaper_push`.

Existing installations may continue to work for the time being, but compatibility with future Home Assistant releases or paperlesspaper API changes is no longer guaranteed.

Users are encouraged to migrate to `paperlesspaper-ha`.

A detailed migration guide is available in [`MIGRATION.md`](https://github.com/fwmone/paperlesspaper_push/blob/main/MIGRATION.md).

## [0.1.8] - 2026-05-08

### Changed
- No integration update, but updating README file to reflect update of paperlesspaper API service. As of ~20. April 2026, paperlesspaper changed their uploadSingleImage API call so that it includes their new, optimized version of EPDOptimize. Therefore, you do **not need** to pre-dither the images anymore, only resize them and save as PNG. Pre-dithering / pre-optimizing using EPDOptimize leads to wrong colors. In case you use the optimization script (https://github.com/fwmone/eink-optimize) to pre-dither images, please disable EPDOptimize and re-render all your images. I provide further explanation in the optimization script's README.

## [0.1.7] - 2026-04-25

### Changed
- changing max length of file list from 50 to 250 to have better randomization

## [0.1.6] - 2026-03-15

### Changed
- URL of API seems to have changed to api.paperlesspaper.de

## [0.1.5] - 2026-03-01

### Added
- Added long-term statistics support for battery-related sensors.
- Battery voltage and battery percentage sensors are now marked as measurement
  sensors, enabling Home Assistant long-term statistics and historical trends.
- Added `battery_percent_rechargeable` sensor to provide a more realistic battery
  level estimation when using rechargeable batteries (e.g. NiMH).

### Changed
- Improved battery sensor metadata to align with Home Assistant best practices
  for long-term statistics (state class and measurement semantics).
- Clarified separation between vendor-style battery percentage and
  rechargeable battery estimation.

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
