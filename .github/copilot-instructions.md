# smartmirrord Copilot Instructions

## Environment and agent scope

- This daemon targets Raspberry Pi OS and requires the controller's GPIO, camera, and UART hardware. Picamera2 is provided by the target system and is not installed from pip.
- The AI agent's role is limited to development in the repository. It has no access to the remote Raspberry Pi and must not run the daemon, access hardware, install or deploy the application, or invoke deployment scripts. Do not provide local run instructions as a validation step.
- Deployment and runtime verification are performed by the user on the target Pi. `deploy.sh` can overwrite the deployed checkout; never invoke it.
- Do not write or add tests for this project currently. There is no maintained automated test suite or lint runner. Do not claim hardware/runtime validation; that can only be done by the user on the target Pi after deployment.

## Architecture

- `smartmirrord/__main__.py` is the composition root. It constructs every service, starts them in the returned dictionary order, injects `IR_SERVICE` into the Flask app, runs Flask on a daemon thread, and stops all services on `SIGTERM`/`SIGINT`.
- `hardware/` owns device access: `PowerStatus` watches GPIO power-LED edges, `IREmulator` bit-bangs Samsung NEC codes through GPIO, `Camera` wraps Picamera2, and `UartTransport` owns the serial reader thread and serialized writes.
- `services/` converts device events into policy. `PowerService` debounces `PowerStatus` changes and emits stable power callbacks. `MotionService` emits cooldown-limited motion callbacks. `DisplayAvailabilityService` retries the IR `power` command when power is off. `DisplayPolicyService` uses motion, quiet hours, and power events to request video mute changes.
- Video mute state is acknowledgement-driven: `VideoMuteService` sends UART commands but only updates its observed panel/backlight state from UART lines routed by `UartDispatcher`. The desired state, transition timer, and power state must remain distinct from observed state.
- `web/routes.py` exposes the UI and `POST /send_command`; both use the same injected `IRService`. The available commands come from `hardware/ir_codes.py`, so adding a code automatically affects the UI and API validation.

## Repository conventions

- Keep hardware access inside `hardware/`; services should consume those wrappers rather than call GPIO, serial, camera, or IR APIs directly.
- Services use idempotent `start()`/`stop()` methods and register callbacks during `start()`. New long-lived work must stop threads/timers and release hardware resources in `stop()`.
- Callback fan-out and UART dispatch isolate individual handler failures with logging. Preserve that isolation when adding handlers.
- Power is active-low: `PowerStatus` reports `Value.INACTIVE` as display power on. Keep the debounce in `PowerService` rather than reacting directly to GPIO edges.
- UART handlers implement `can_handle(line)` and `handle(line)` and are registered with `UartDispatcher`; `UartTransport` dispatches complete, stripped newline-delimited lines.
- Runtime configuration is imported as module-level values from `config.py`. Add new environment settings there and document them in `.env.example`; quiet hours currently come from `SCHEDULE_JSON` in `config.py`, not `.env`.
- `smartmirrord.service` runs with restricted filesystem access. If runtime code needs persistent paths, ensure they are allowed by `ReadWritePaths`.
