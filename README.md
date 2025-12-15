# smartmirrord

`smartmirrord` is a small Raspberry Pi daemon for **state management and hardware control** of a smart mirror conversion built from a **Lululemon workout mirror**. It exposes a minimal **Flask API + simple web UI** for basic remote control and monitoring.

This project is a work in progress. Still to come is video based motion detection as well as debug UART interface for video mute control (quick display on/off).
## What it does

- Hosts a lightweight **remote UI** (for quick manual control from a phone/laptop on your LAN).
- Exposes a **Flask HTTP API** for automations/integrations.
- Monitors **TV power state** via GPIO:
  - **Power status is derived from the power LED signal on the TV controller board** (tapping/reading the LED state to infer ON/OFF).
- Sends **IR commands** direct IR emulation, without LED or receiver, to control the display/controller as needed.

## Running

Start the daemon:
```bash
python -m smartmirrord
```

Configure your GPIO pins in `config.py`.
## Web UI Remote

Open the remote UI in a browser:

- `http://<pi-ip>:5000/`

## API

### `POST /send_command`

Send a named command (typically forwarded to the IR/control layer).

**Request**
- `Content-Type: application/json`
```json 
{ "command": "power" }
```


**Response**
- `200 OK` on success
- `400` for unknown/invalid commands

## Notes

- This project is intended to run on hardware with GPIO access (e.g., a Raspberry Pi).
- Power-state monitoring depends on your specific controller board/LED wiring—ensure the LED signal is safely level-shifted/conditioned for 3.3V GPIO if necessary.