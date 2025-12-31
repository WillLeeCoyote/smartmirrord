import threading
from datetime import datetime, time
from typing import Optional, List, Dict


class QuietHoursSchedule:
    def __init__(self, quiet_hours: List[Dict]):
        self._windows = []
        for entry in quiet_hours:
            start = self._parse_time(entry["start"])
            end = self._parse_time(entry["end"])
            self._windows.append((start, end))

    def is_motion_allowed(self, now: datetime) -> bool:
        now_t = now.time()
        for start, end in self._windows:
            if start < end:
                if start <= now_t < end:
                    return False
            else:
                if now_t >= start or now_t < end:
                    return False
        return True

    @staticmethod
    def _parse_time(value: str) -> time:
        h, m = value.split(":")
        return time(int(h), int(m))


class DisplayPolicyService:
    def __init__(
        self,
        video_mute_service,
        motion_service,
        power_service,
        remute_delay: float,
        schedule_json: Dict,
    ):
        self._video = video_mute_service
        self._motion = motion_service
        self._power = power_service
        self._remute_delay = remute_delay

        self._schedule = QuietHoursSchedule(
            schedule_json["quiet_hours"]
        )

        self._videoMute_desired = True
        self._remute_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        self._running = False

    def start(self):
        if self._running:
            return

        self._motion.register_on_motion_on(self._on_motion)
        self._power.register_on_power_on(self._on_power_on)
        self._power.register_on_power_off(self._on_power_off)

        self._running = True

    def stop(self):
        with self._lock:
            self._running = False
            self._cancel_remute_timer()

    def _on_motion(self):
        if not self._running:
            return

        with self._lock:
            self._cancel_remute_timer()

            if not self._schedule.is_motion_allowed(datetime.now()):
                return

            if self._videoMute_desired:
                self._videoMute_desired = False
                self._video.unmute()

            self._schedule_remute()

    def _schedule_remute(self):
        if not self._running:
            return

        self._remute_timer = threading.Timer(
            self._remute_delay,
            self._on_remute_timer,
        )
        self._remute_timer.start()

    def _on_remute_timer(self):
        with self._lock:
            if not self._running:
                return

            self._remute_timer = None

            if not self._videoMute_desired:
                self._videoMute_desired = True
                self._video.mute()

    def _on_power_on(self):
        if not self._running:
            return

        with self._lock:
            if self._videoMute_desired:
                self._video.mute()
            else:
                self._video.unmute()

    def _on_power_off(self):
        if not self._running:
            return

        with self._lock:
            self._cancel_remute_timer()

    def _cancel_remute_timer(self):
        if self._remute_timer:
            self._remute_timer.cancel()
            self._remute_timer = None
