# Teploty.info Home Assistant integration

This repository contains the custom Home Assistant integration in
`custom_components/teploty_info`. It polls the `ha_rest.php` read endpoint
provided by the Teploty.info web service.

The integration polls Teploty.info once per minute, creates a device for each
probe, and creates entities for its visible sensors. Sensors without a recent
reading remain registered but are marked unavailable. Newly added sensors are
discovered automatically.

## Install with HACS

After this repository is published at
`https://github.com/joysfera/homeassistant-teploty.info`:

1. In HACS, add `joysfera/homeassistant-teploty.info` as a custom **Integration** repository.
2. Download **Teploty.info** and restart Home Assistant.
3. Add **Teploty.info** from **Settings → Devices & services → Add integration**.
4. Enter the Teploty.info login and API key shown under **Hesla a email**.

For a manual test install, copy `custom_components/teploty_info` into the
`custom_components` directory in your Home Assistant configuration, restart,
and add the integration from the UI.

The API key is sent over HTTPS in `X-Teploty-Login` and `X-Teploty-Key` headers,
not in the URL. The key also authorizes commands through Teploty.info's
existing API; this integration currently uses it only to read sensors.

The `ha_rest.php` endpoint must be deployed on the Teploty.info web server for
the integration to connect.
