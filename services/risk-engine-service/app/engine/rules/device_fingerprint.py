"""Device fingerprint change detection rule."""

from app.engine.rules.base_rule import BaseRule


class DeviceFingerprintRule(BaseRule):
    """Flags transactions from a new or changed device fingerprint.

    Checks if the device fingerprint differs from the sender's known devices.
    In production, this would query a device registry/DB.
    """

    @property
    def name(self) -> str:
        return "DEVICE_CHANGE"

    def evaluate(self, transaction: dict) -> dict:
        device_fingerprint = transaction.get("device_fingerprint", "")
        metadata = transaction.get("metadata") or {}
        known_devices = metadata.get("known_devices", [])
        is_new_device = metadata.get("is_new_device", False)

        if not device_fingerprint:
            return self._result(
                triggered=True,
                score=0.4,
                reason="No device fingerprint provided",
            )

        if is_new_device or (known_devices and device_fingerprint not in known_devices):
            return self._result(
                triggered=True,
                score=0.6,
                reason="Transaction from an unrecognized device",
            )

        return self._result(
            triggered=False,
            score=0.0,
            reason="Device fingerprint matches known device",
        )
