
from __future__ import annotations

from typing import Any
import serial


class STM32SerialReceiver:
    """
    CortexGuard STM32 UART telemetry receiver.

    Supports aggregate packets:
      CG,cpu=2,ram=26,heap=11328,min_heap=11328,
      heap_used=4032,tasks=5,stack_words=276

    CPU may temporarily be unavailable:
      CG,cpu=NA,ram=26,heap=11328,min_heap=11328,
      heap_used=4032,tasks=5,stack_words=276

    Also supports:
      CGTASK,name=DiagnosticsTask,stack_words=276
      CGFAULT,type=STACK,level=HIGH,detail=Stack margin low

    ram = percentage of configured FreeRTOS heap used.
    heap = currently free FreeRTOS heap in bytes.
    heap_used = currently used FreeRTOS heap in bytes.

    ram_used and ram_total are retained for compatibility
    with older firmware that transmits those fields.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.serial_port: serial.Serial | None = None

        self.buffer = b""
        self.task_messages: list[dict[str, Any]] = []
        self.fault_messages: list[dict[str, Any]] = []
        self.debug_lines: list[str] = []

    def connect(self) -> None:
        self.serial_port = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=0,
        )

        self.buffer = b""
        self.task_messages.clear()
        self.fault_messages.clear()
        self.debug_lines.clear()

    def close(self) -> None:
        if self.serial_port is not None:
            try:
                if self.serial_port.is_open:
                    self.serial_port.close()
            finally:
                self.serial_port = None

    @staticmethod
    def _fields(parts: list[str]) -> dict[str, str]:
        result: dict[str, str] = {}

        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                result[key.strip().lower()] = value.strip()

        return result

    def _debug(self, line: str) -> None:
        self.debug_lines.append(line)

        if len(self.debug_lines) > 100:
            del self.debug_lines[:-100]

    def read_messages(self) -> list[dict[str, Any]]:
        if (
            self.serial_port is None
            or not self.serial_port.is_open
        ):
            return []

        incoming = self.serial_port.read(4096)

        if incoming:
            self.buffer += incoming

        messages: list[dict[str, Any]] = []

        while b"\n" in self.buffer:
            raw, self.buffer = self.buffer.split(b"\n", 1)

            line = raw.decode(
                "utf-8",
                errors="replace",
            ).strip()

            if not line:
                continue

            self._debug(line)

            if line.startswith("CGTASK,"):
                self._parse_task(line)
                continue

            if line.startswith("CGFAULT,"):
                self._parse_fault(line)
                continue

            if not line.startswith("CG,"):
                continue

            fields = self._fields(line.split(",")[1:])

            required = ("heap", "min_heap", "tasks")

            if any(key not in fields for key in required):
                self._debug(
                    "PARSE ERROR: missing heap/min_heap/tasks: "
                    + line
                )
                continue

            try:
                packet: dict[str, Any] = {
                    "heap": int(fields["heap"]),
                    "min_heap": int(fields["min_heap"]),
                    "tasks": int(fields["tasks"]),
                }

                # CPU may be NA during the first measurement.
                cpu_text = fields.get("cpu", "").upper()

                if cpu_text not in ("", "NA", "N/A"):
                    packet["cpu"] = float(cpu_text)

                # Current firmware telemetry.
                for key in (
                    "ram",
                    "heap_used",
                    "stack_words",
                ):
                    if key in fields:
                        packet[key] = int(fields[key])

                # Older firmware compatibility.
                for key in ("ram_used", "ram_total"):
                    if key in fields:
                        packet[key] = int(fields[key])

            except ValueError:
                self._debug(
                    "PARSE ERROR: invalid numeric value: "
                    + line
                )
                continue

            # Validate non-negative metrics.
            non_negative_keys = [
                "heap",
                "min_heap",
                "tasks",
                "ram",
                "heap_used",
                "stack_words",
                "ram_used",
                "ram_total",
            ]

            invalid = any(
                packet[key] < 0
                for key in non_negative_keys
                if key in packet
            )

            if invalid:
                self._debug(
                    "PARSE ERROR: negative metric: " + line
                )
                continue

            if "cpu" in packet and not (
                0 <= packet["cpu"] <= 100
            ):
                self._debug(
                    "PARSE ERROR: CPU outside 0-100: "
                    + line
                )
                continue

            if "ram" in packet and not (
                0 <= packet["ram"] <= 100
            ):
                self._debug(
                    "PARSE ERROR: RAM percentage outside 0-100: "
                    + line
                )
                continue

            if (
                "ram_total" in packet
                and packet["ram_total"] <= 0
            ):
                self._debug(
                    "PARSE ERROR: ram_total must be positive: "
                    + line
                )
                continue

            messages.append(packet)

        return messages

    def _parse_task(self, line: str) -> None:
        fields = self._fields(line.split(",")[1:])

        if "name" not in fields or "stack_words" not in fields:
            self._debug("TASK PARSE ERROR: " + line)
            return

        try:
            words = int(fields["stack_words"])
        except ValueError:
            self._debug(
                "TASK PARSE ERROR: invalid stack_words: "
                + line
            )
            return

        if words < 0:
            self._debug(
                "TASK PARSE ERROR: negative stack_words: "
                + line
            )
            return

        self.task_messages.append(
            {
                "name": fields["name"],
                "stack_words": words,
            }
        )

    def _parse_fault(self, line: str) -> None:
        fields = self._fields(line.split(",")[1:])

        kind = fields.get("type", "").upper()
        level = fields.get("level", "INFO").upper()

        if not kind:
            self._debug(
                "FAULT PARSE ERROR: missing type: " + line
            )
            return

        if kind not in {
            "MEMORY",
            "CPU",
            "STACK",
            "TIMING",
            "CAN",
            "UNKNOWN",
        }:
            kind = "UNKNOWN"

        if level not in {
            "INFO",
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }:
            level = "INFO"

        self.fault_messages.append(
            {
                "type": kind,
                "level": level,
                "detail": fields.get(
                    "detail",
                    "Firmware reported a fault",
                ),
            }
        )

    def read_task_messages(self) -> list[dict[str, Any]]:
        result = self.task_messages[:]
        self.task_messages.clear()
        return result

    def read_fault_messages(self) -> list[dict[str, Any]]:
        result = self.fault_messages[:]
        self.fault_messages.clear()
        return result

    def get_debug_lines(self) -> list[str]:
        return self.debug_lines[:]
