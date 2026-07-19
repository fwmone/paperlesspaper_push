# 📖 Table of content

- [📖 Table of content](#-table-of-content)
- [Migration Guide: `paperlesspaper_push` → `paperlesspaper-ha`](#migration-guide-paperlesspaper_push--paperlesspaper-ha)
  - [First of all: A big thank you!](#first-of-all-a-big-thank-you)
  - [Migration overview](#migration-overview)
- [1. Install the new integration](#1-install-the-new-integration)
- [2. Make the image directory available in the Media Browser](#2-make-the-image-directory-available-in-the-media-browser)
- [3. Entity mapping](#3-entity-mapping)
- [4. Replace the upload automation](#4-replace-the-upload-automation)
  - [Previous automation](#previous-automation)
  - [New automation](#new-automation)
    - [Action parameters](#action-parameters)
- [5. Optional template sensor: last uploaded image](#5-optional-template-sensor-last-uploaded-image)
- [6. Optional template sensor: last successful frame sync](#6-optional-template-sensor-last-successful-frame-sync)
- [7. Example dashboard](#7-example-dashboard)
  - [Required custom cards](#required-custom-cards)
  - [Dashboard YAML](#dashboard-yaml)
- [8. Test the migration](#8-test-the-migration)
- [9. Remove `paperlesspaper_push`](#9-remove-paperlesspaper_push)
- [Differences to be aware of](#differences-to-be-aware-of)
- [Support](#support)


# Migration Guide: `paperlesspaper_push` → `paperlesspaper-ha`

## First of all: A big thank you!

First of all, thank you very much to everyone who has used, tested, supported, or contributed feedback to `paperlesspaper_push`.

I originally created this integration for my own paperlesspaper frame and later published it in the hope that it might also be useful to others. I am very pleased that it found users beyond my own Home Assistant installation.

In the meantime, the manufacturer of the paperlesspaper frame has chosen to support a different Home Assistant integration:

**[djiwondee/paperlesspaper-ha](https://github.com/djiwondee/paperlesspaper-ha)**

Thanks @djiwondee for creating this new integration, which provides a more comprehensive feature set, supports configuration through the Home Assistant UI, automatically discovers devices, and supports multiple paperlesspaper frames. It's really a great piece of work!

Rather than asking users to choose between two integrations that provide overlapping functionality, I have decided to deprecate `paperlesspaper_push` and recommend migrating to `paperlesspaper-ha`.

Existing installations of `paperlesspaper_push` may continue to work for the time being. However, no further feature development is planned, and compatibility with future Home Assistant or paperlesspaper API versions cannot be guaranteed.

This guide explains how to migrate an existing setup.

---

## Migration overview

The migration consists of the following steps:

1. Install and configure `paperlesspaper-ha`.
2. Make your image directory available through the Home Assistant Media Browser.
3. Replace entities used in dashboards and automations.
4. Replace calls to `paperlesspaper_push.upload_random`.
5. Optionally create template sensors for information that is not exposed as a native entity.
6. Test the new integration.
7. Remove `paperlesspaper_push`.

It is recommended to keep both integrations installed until the new setup has successfully uploaded and synchronized at least one image.

---

# 1. Install the new integration

Install `paperlesspaper-ha` by following the instructions in its repository:

**https://github.com/djiwondee/paperlesspaper-ha**

The integration can be installed through HACS as a custom repository.

After installation:

1. Restart Home Assistant.
2. Go to **Settings → Devices & services**.
3. Select **Add integration**.
4. Search for **paperlesspaper**.
5. Enter your paperlesspaper API key.
6. Select your organization or group.
7. Confirm the discovered frames.

Unlike `paperlesspaper_push`, the new integration is configured through the Home Assistant UI and supports multiple frames within one installation.

---

# 2. Make the image directory available in the Media Browser

`paperlesspaper-ha` selects images through the Home Assistant Media Browser.

The directory containing your paperlesspaper images must therefore be available under **Media** in the Home Assistant sidebar.

You can check this by opening:

**Home Assistant sidebar → Media**

In my installation, the images are stored below the root directory:

```text
/media
```

I expose this directory to Home Assistant with the following configuration in `configuration.yaml`:

```yaml
homeassistant:
  media_dirs:
    local: /media
```

After changing `configuration.yaml`, restart Home Assistant.

The directory should then be visible in the Media Browser.

For example, an image directory located at:

```text
/media/picture-frames/paperlesspaper
```

is addressed through the Media Source URI:

```text
media-source://media_source/local/picture-frames/paperlesspaper
```

Use the Media Browser to verify that the directory and its images are accessible before configuring the upload automation.

---

# 3. Entity mapping

The entities created by `paperlesspaper_push` do not map one-to-one to entities provided by `paperlesspaper-ha`.

Entity names depend on the name assigned to your frame in Home Assistant. The examples below assume that the frame is called `<YOUR_DEVICE_NAME>`.

| `paperlesspaper_push` entity | Replacement in `paperlesspaper-ha`                                                                                       |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Battery (Rechargeable)       | No separate rechargeable-battery calculation is provided. Use **Battery Level** instead.                                 |
| Battery Voltage              | Use **Battery Voltage**. This diagnostic entity is disabled by default and must first be enabled in the entity settings. |
| Last Reachable               | No direct replacement. An additional helper or template sensor can be created if required (see below).                   |
| Loaded At                    | No direct replacement.                                                                                                   |
| Next Device Sync             | Use **Update Interval**, for example `sensor.<YOUR_DEVICE_NAME>_aktualisierungsintervall`.                                           |
| Paperlesspaper Push Status   | No direct sensor replacement. Use the `paperlesspaper_image_uploaded` event to create an optional template sensor (see below). |
| Updated At                   | No direct replacement. A helper or template sensor can be created if required.                                           |

The new integration additionally provides native entities that were not available in the same form in `paperlesspaper_push`, including:

* picture synchronized
* device reachable
* update pending
* Wi-Fi signal strength
* frame orientation
* sleep interval
* reboot and reset buttons

Check the device page under **Settings → Devices & services → Devices** to see all available entities for your frame.

---

# 4. Replace the upload automation

## Previous automation

A typical `paperlesspaper_push` automation may have looked like this:

```yaml
alias: "paperlesspaper: Upload"
description: ""
triggers:
  - trigger: template
    value_template: >
      {% set next = states('sensor.paperlesspaper_push_next_device_sync') %}
      {% if next not in ['unknown', 'unavailable', 'none', ''] %}
        {{ as_timestamp(next) - 30 * 60 <= now().timestamp() }}
      {% else %}
        false
      {% endif %}

actions:
  - action: paperlesspaper_push.upload_random
    data:
      publish: true
      dry_run: false
```

## New automation

With `paperlesspaper-ha`, the automation can use the frame's native update interval sensor and the `paperlesspaper.upload_random_image` action:

```yaml
alias: "paperlesspaper (YOUR_DEVICE_NAME): Upload"
description: ""

triggers:
  - trigger: template
    value_template: >
      {% set next = states('sensor.YOUR_DEVICE_NAME_aktualisierungsintervall') %}
      {% if next not in ['unknown', 'unavailable', 'none', ''] %}
        {{ as_timestamp(next) - 30 * 60 <= now().timestamp() }}
      {% else %}
        false
      {% endif %}

actions:
  - action: paperlesspaper.upload_random_image
    data:
      device_id: <YOUR_DEVICE_ID>
      media_directory: media-source://media_source/local/picture-frames/paperlesspaper
      max_images: 0
      reuse_existing_paper: true
```

This is the Home Assistant device ID of the target frame. The easiest and safest way to obtain it is to create the action through the Home Assistant automation editor and select the frame from the device selector.

Also replace:

```yaml
media_directory: media-source://media_source/local/picture-frames/paperlesspaper
```

with the Media Source URI of your own image directory.

### Action parameters

The relevant parameters are:

| Parameter              | Meaning                                                                 |
| ---------------------- | ----------------------------------------------------------------------- |
| `device_id`            | Home Assistant device ID of the target frame                            |
| `media_directory`      | Media Source URI of the image directory                                 |
| `max_images`           | Maximum number of images included in the rotation; `0` means all images |
| `reuse_existing_paper` | Reuses the currently assigned paper instead of creating a new one       |

The new integration keeps its own image rotation history and avoids repeating images until the available pool has been exhausted.

---

# 5. Optional template sensor: last uploaded image

The new integration fires the Home Assistant event:

```text
paperlesspaper_image_uploaded
```

after an upload attempt.

The event includes information such as:

* target device
* image URI
* upload status
* paper ID
* similarity percentage
* whether the upload was skipped because the image was too similar

A trigger-based template sensor can store the URI of the last successfully processed image.

Add the following to your `templates.yaml`, or below the `template:` section of your `configuration.yaml`:

```yaml
- triggers:
    - trigger: event
      event_type: paperlesspaper_image_uploaded
      event_data:
        device_id: "<YOUR_DEVICE_ID>"

  conditions:
    - condition: template
      value_template: >
        {{ trigger.event.data.status in ['success', 'skipped']
           and trigger.event.data.image_uri is defined }}

  sensor:
    - name: "Paperlesspaper <YOUR_DEVICE_NAME> Image Uploaded"
      unique_id: "<YOUR_DEVICE_NAME>_image_uri"
      icon: mdi:image-frame
      state: "{{ trigger.event.data.image_uri }}"
      attributes:
        pp_device_id: "{{ trigger.event.data.pp_device_id }}"
        paper_id: "{{ trigger.event.data.paper_id }}"
        upload_status: "{{ trigger.event.data.status }}"
        action: "{{ trigger.event.data.action }}"
        skipped_upload: >
          {{ trigger.event.data.skipped_upload | default(false) }}
        similarity_percentage: >
          {{ trigger.event.data.similarity_percentage | default(none) }}
        last_upload: "{{ trigger.event.time_fired }}"
```

This example creates:

```text
sensor.paperlesspaper_<YOUR_DEVICE_NAME>_image_uploaded
```

Its state contains a Media Source URI such as:

```text
media-source://media_source/local/picture-frames/paperlesspaper/example.jpg
```

The sensor also retains useful upload information as attributes.

Replace the `device_id`, sensor name, and `unique_id` for each frame.

> Home Assistant does not dynamically create one template entity per device. If you use multiple frames, create one template sensor for each frame and filter each sensor by the corresponding `device_id`.

---

# 6. Optional template sensor: last successful frame sync

`paperlesspaper-ha` provides a binary sensor indicating whether the image is synchronized with the frame.

For example:

```text
binary_sensor.<YOUR_DEVICE_NAME>_bild_synchronisiert
```

The following trigger-based template sensor stores the time at which this binary sensor most recently changed to `on`:

```yaml
- triggers:
    - trigger: state
      entity_id: binary_sensor.<YOUR_DEVICE_NAME>_bild_synchronisiert
      to: "on"

  sensor:
    - name: "Paperlesspaper <YOUR_DEVICE_NAME> Letzter Sync"
      unique_id: <YOUR_DEVICE_NAME>_letzter_sync
      device_class: timestamp
      state: "{{ now() }}"
```

This creates a timestamp sensor such as:

```text
sensor.paperlesspaper_<YOUR_DEVICE_NAME>_letzter_sync
```

It can be used in dashboards to display when the frame last confirmed that the current image was synchronized.

---

# 7. Example dashboard

The following dashboard example displays:

* the last uploaded image
* battery level and voltage
* the last successful synchronization
* the next scheduled synchronization

## Required custom cards

This example uses the following custom cards:

* [`media-source-image-card`](https://github.com/luixal/lovelace-media-source-image-card)
* [`button-card`](https://github.com/custom-cards/button-card)
* [`layout-card`](https://github.com/thomasloven/lovelace-layout-card)
* [`card-mod`](https://github.com/thomasloven/lovelace-card-mod)

Install the cards you need through HACS before using the example.

> Verify the current repository and installation instructions for `media-source-image-card` in HACS. The image card must support Home Assistant `media-source://` URIs and JavaScript templates.

## Dashboard YAML

```yaml
type: grid
column_span: 2

cards:
  - type: heading
    icon: mdi:desk
    heading: <YOUR_DEVICE_NAME>
    heading_style: title

  - type: custom:media-source-image-card
    image: |
      [[[
        return hass.states[
          'sensor.paperlesspaper_<YOUR_DEVICE_NAME>_image_uploaded'
        ]?.state;
      ]]]
    object_position: 50% 50%
    card_mod:
      style: |
        ha-card img {
          height: 400px;
          margin-top: 15px;
          margin-bottom: 20px;
        }

  - type: custom:layout-card
    layout_type: grid
    layout:
      grid-template-columns: 1fr 1fr
      grid-gap: 6px
      margin: "-8px 0 0 0"

    cards:
      - type: custom:button-card
        entity: sensor.<YOUR_DEVICE_NAME>_batteriepegel
        name: Batterie
        show_state: true
        show_label: true
        layout: icon_name_state2nd

        icon: |
          [[[
            const level = parseInt(entity.state);

            if (
              ['unavailable', 'unknown'].includes(entity.state) ||
              isNaN(level)
            ) {
              return 'mdi:battery-unknown';
            }

            if (level <= 5) return 'mdi:battery-outline';
            if (level <= 10) return 'mdi:battery-10';
            if (level <= 20) return 'mdi:battery-20';
            if (level <= 30) return 'mdi:battery-30';
            if (level <= 40) return 'mdi:battery-40';
            if (level <= 50) return 'mdi:battery-50';
            if (level <= 60) return 'mdi:battery-60';
            if (level <= 70) return 'mdi:battery-70';
            if (level <= 80) return 'mdi:battery-80';
            if (level <= 90) return 'mdi:battery-90';

            return 'mdi:battery';
          ]]]

        state_display: |
          [[[
            const invalid = [
              'unknown',
              'unavailable',
              'none',
              'null',
              ''
            ];

            const battery =
              states['sensor.<YOUR_DEVICE_NAME>_batteriepegel']?.state;

            const batteryVoltage =
              states['sensor.<YOUR_DEVICE_NAME>_batteriespannung']?.state;

            const batteryText =
              !battery || invalid.includes(battery)
                ? '–'
                : `${battery} %`;

            const voltageText =
              !batteryVoltage || invalid.includes(batteryVoltage)
                ? '–'
                : `${parseFloat(batteryVoltage)
                    .toPrecision(3)
                    .replace(/\./, ',')} V`;

            return `${batteryText} / ${voltageText}`;
          ]]]

        styles:
          icon:
            - height: 32px
            - color: |
                [[[
                  const level = parseInt(entity.state);

                  if (level <= 20) {
                    return 'var(--label-badge-red)';
                  }

                  if (level <= 55) {
                    return 'var(--label-badge-yellow)';
                  }

                  return 'var(--label-badge-green)';
                ]]]

          card:
            - border-radius: 28px
            - padding: 10px
            - height: 110px

          grid:
            - grid-template-areas: '"i" "n" "s"'
            - grid-template-columns: 1fr
            - grid-template-rows: 1fr min-content min-content

          name:
            - justify-self: center
            - font-weight: bold
            - font-size: 0.9em

          state:
            - justify-self: center
            - font-size: 12px
            - padding-top: 1px

        tap_action:
          action: more-info

        hold_action:
          action: more-info
          entity: sensor.<YOUR_DEVICE_NAME>_batteriepegel

      - type: custom:button-card
        entity: sensor.paperlesspaper_<YOUR_DEVICE_NAME>_letzter_sync
        name: Letzter Sync
        show_state: true
        show_label: true
        layout: icon_name_state2nd

        state_display: |
          [[[
            const value =
              states[
                'sensor.paperlesspaper_<YOUR_DEVICE_NAME>_letzter_sync'
              ]?.state;

            const invalid = [
              'unknown',
              'unavailable',
              'none',
              'null',
              ''
            ];

            if (!value || invalid.includes(value)) {
              return '–';
            }

            const date = new Date(value);

            if (isNaN(date)) {
              return '–';
            }

            return date.toLocaleTimeString('de-DE', {
              hour: '2-digit',
              minute: '2-digit'
            });
          ]]]

        styles:
          icon:
            - height: 32px

          card:
            - border-radius: 28px
            - padding: 10px
            - height: 110px

          grid:
            - grid-template-areas: '"i" "n" "s"'
            - grid-template-columns: 1fr
            - grid-template-rows: 1fr min-content min-content

          name:
            - justify-self: center
            - font-weight: bold
            - font-size: 0.9em

          state:
            - justify-self: center
            - font-size: 12px
            - padding-top: 1px

        tap_action:
          action: more-info

      - type: custom:button-card
        entity: sensor.<YOUR_DEVICE_NAME>_aktualisierungsintervall
        name: Nächster Sync
        show_state: true
        show_label: true
        layout: icon_name_state2nd

        state_display: |
          [[[
            const value =
              states[
                'sensor.<YOUR_DEVICE_NAME>_aktualisierungsintervall'
              ]?.state;

            const invalid = [
              'unknown',
              'unavailable',
              'none',
              'null',
              ''
            ];

            if (!value || invalid.includes(value)) {
              return '–';
            }

            const date = new Date(value);

            if (isNaN(date)) {
              return '–';
            }

            return date.toLocaleTimeString('de-DE', {
              hour: '2-digit',
              minute: '2-digit'
            });
          ]]]

        styles:
          icon:
            - height: 32px

          card:
            - border-radius: 28px
            - padding: 10px
            - height: 110px

          grid:
            - grid-template-areas: '"i" "n" "s"'
            - grid-template-columns: 1fr
            - grid-template-rows: 1fr min-content min-content

          name:
            - justify-self: center
            - font-weight: bold
            - font-size: 0.9em

          state:
            - justify-self: center
            - font-size: 12px
            - padding-top: 1px

        tap_action:
          action: more-info
```

Replace all example entity IDs with the entities created for your own frame.

---

# 8. Test the migration

Before removing `paperlesspaper_push`, verify the following:

* The new integration is loaded without errors.
* Your frame appears as a Home Assistant device.
* Battery and synchronization entities receive values.
* Your image directory is visible in the Media Browser.
* `paperlesspaper.upload_random_image` selects and uploads an image.
* The frame retrieves and displays the uploaded image.
* Any migrated dashboard cards show the expected values.
* Any optional template sensors update correctly.

It is advisable to observe at least one complete regular wake-up and synchronization cycle before removing the old integration.

---

# 9. Remove `paperlesspaper_push`

Once the migration has been successfully tested:

1. Disable or remove all automations that call:

   ```text
   paperlesspaper_push.upload_random
   ```

2. Remove old `paperlesspaper_push` entities from dashboards.

3. Remove the `paperlesspaper_push:` section from `configuration.yaml`.

4. Remove the corresponding API key from `secrets.yaml` if it is no longer used elsewhere.

5. Restart Home Assistant.

6. Remove `paperlesspaper Push` through HACS.

7. Restart Home Assistant again.

8. Optionally remove the directory:

   ```text
   /config/custom_components/paperlesspaper_push
   ```

   if it still exists after uninstalling the integration.

9. Remove obsolete entities from the Home Assistant entity registry if they remain visible after the integration has been removed.

Do not remove the image directory under `/media` if it is now used by `paperlesspaper-ha`.

---

# Differences to be aware of

Although both integrations provide random image uploads, their internal image-selection history is not shared.

After migration, the new integration therefore starts with a fresh rotation history. Images recently displayed by `paperlesspaper_push` may initially be selected again.

The old `publish` option is also no longer required for uploading images. The new integration directly exposes the selected Media Browser URI through the `paperlesspaper_image_uploaded` event, which can be stored in a template sensor and displayed with a compatible dashboard card.

The `dry_run` and `force_file` parameters provided by `paperlesspaper_push` do not have direct equivalents in `paperlesspaper.upload_random_image`. To upload a specific image, use the separate:

```text
paperlesspaper.upload_image
```

action.

---

# Support

For questions or problems relating to the new integration, please use the issue tracker of:

**https://github.com/djiwondee/paperlesspaper-ha**

Issues concerning the migration guide or the previous behavior of `paperlesspaper_push` may still be reported in this repository.

Please note that `paperlesspaper_push` itself is deprecated and is no longer planned to receive new features.
