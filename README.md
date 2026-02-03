# 📖 Table of content

- [📖 Table of content](#-table-of-content)
- [Features](#features)
- [📦 Installation](#-installation)
  - [Option A: Installation via HACS (recommended)](#option-a-installation-via-hacs-recommended)
  - [Option B: Manual installation](#option-b-manual-installation)
- [Configuration](#configuration)
  - [Folder Setup](#folder-setup)
    - [Input directory](#input-directory)
    - [Publish directory (optional)](#publish-directory-optional)
- [Entities](#entities)
  - [Sensor](#sensor)
    - [State:](#state)
    - [Attributes:](#attributes)
  - [Services](#services)
  - [Automation Examples](#automation-examples)
- [API / Upload Method](#api--upload-method)
- [Troubleshooting](#troubleshooting)
  - [Upload succeeds but frame shows old image](#upload-succeeds-but-frame-shows-old-image)
  - [Blocking calls in logs](#blocking-calls-in-logs)
- [Roadmap / Ideas](#roadmap--ideas)
- [Support / Issues](#support--issues)
- [License](#license)
- [🙏 Note](#-note)

# Features

A small Home Assistant custom integration to **upload images from the Home Assistant server to a Paperlesspaper e-paper frame** using the WireWire API. The integration is designed to work well with Home Assistant automations (e.g. upload a new image twice a day), and provides a *“varied random”* image selection that avoids repeating the same images too often.

- Upload a random image from an input folder to a Paperlesspaper frame via API
- "Varied random" selection:
  - remembers recently used images
  - recent-window size = **50% of available images** (min 5, max 50)
  - avoids repetition until the pool is exhausted
- Optional publish/copy of the selected image into `/config/www/...` for preview/debugging
- Optional cleanup of the publish directory before publishing
- Robust upload retries with exponential backoff
- Home Assistant sensor showing:
  - last upload timestamp
  - current file name
  - last result (success/failed/dry_run)
  - last HTTP status / error

# 📦 Installation

## Option A: Installation via HACS (recommended)

1. Open **HACS → Integrations**
2. Click on **“Custom Repositories”**
3. Add this repository: https://github.com/fwmone/paperlesspaper_push, Category: **Integration**
4. Install **paperlesspaper Push**
5. Restart Home Assistant

## Option B: Manual installation

1. Download this repository
2. Copy the custom_components/paperlesspaper_push folder to: <config>/custom_components/paperlesspaper_push (this is usually /config)
3. Restart Home Assistant

# Configuration

This integration currently uses YAML configuration.

Add this to your `configuration.yaml`:

```yaml
paperlesspaper_push:
  api_key: !secret paperlesspaper_api_key
  paper_id: !secret paperlesspaper_paper_id

  # optional:
  base_url: https://api.memo.wirewire.de/v1
  input_dir: /media/picture-frames/paperlesspaper
  publish_dir: /config/www/picture-frames/paperlesspaper
  timeout: 30
  max_attempts: 4
  publish: true
```

Add the secrets to secrets.yaml:

```yaml
paperlesspaper_api_key: "YOUR_API_KEY"
paperlesspaper_paper_id: "YOUR_PAPER_ID"
```

Restart Home Assistant after changing YAML.

## Folder Setup
### Input directory

Place images in ```/media/picture-frames/paperlesspaper```. 

Supported formats:
- .png
- .jpg / .jpeg

### Publish directory (optional)

If enabled, the integration copies the chosen image to: ```/config/www/picture-frames/paperlesspaper```.

This is useful for debugging or previewing the selected image from Home Assistant (served under /local/...).

# Entities
## Sensor

```sensor.paperlesspaper_push_status```

### State:

- never or last upload timestamp (UTC ISO format)

### Attributes:

- current_filename
- last_result
- last_http_status
- last_error
- published_name

## Services
```paperlesspaper_push.upload_random```

Uploads a (varied) random image.

Example:

```yaml
service: paperlesspaper_push.upload_random
data:
  dry_run: false
  publish: true
```

Fields:
- dry_run (bool, optional): select/publish only, do not upload
- publish (bool, optional): publish/copy the chosen file to publish_dir
- force_file (string, optional): force a specific file name from the input folder

```paperlesspaper_push.reset_recent```

Clears the internal "recent images" history list.

Example:

```yaml
service: paperlesspaper_push.reset_recent
```

## Automation Examples

Upload twice per day:

```yaml
alias: Paperlesspaper Upload Morning
trigger:
  - platform: time
    at: "05:45:00"
action:
  - service: paperlesspaper_push.upload_random

---

alias: Paperlesspaper Upload Afternoon
trigger:
  - platform: time
    at: "16:45:00"
action:
  - service: paperlesspaper_push.upload_random
```

# API / Upload Method

The upload is performed using a multipart form-data request similar to:

```bash
curl -X POST "https://api.memo.wirewire.de/v1/papers/uploadSingleImage/<PAPER_ID>" \
  -H "x-api-key: <API_KEY>" \
  -F "picture=@/path/to/image.png;type=image/png"
```

# Troubleshooting
## Upload succeeds but frame shows old image

The Paperlesspaper frame pulls images from the cloud in configurable intervals.
Make sure the device is configured to wake up and fetch images.

## Blocking calls in logs

This integration avoids blocking filesystem operations inside the event loop by using Home Assistant's executor helpers.

If you still see blocking call warnings, please open an issue with logs.

# Roadmap / Ideas
- Config Flow (UI-based configuration)
- Additional sensors (e.g. success/failure binary sensor)
- Optional "keep last N published images" instead of cleaning publish_dir fully
- Support multiple Paper IDs

# Support / Issues

Please open issues on GitHub if you encounter bugs or have feature requests.

# License

This project is licensed under the terms of the MIT License.

# 🙏 Note

This integration has no official connection to the manufacturer of paperlesspaper frames.