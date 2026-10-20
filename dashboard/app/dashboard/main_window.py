
from __future__ import annotations

import csv
import math
import sys
from collections import deque
from datetime import datetime
from pathlib import Path

import pyqtgraph as pg
import serial.tools.list_ports
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QComboBox, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QMessageBox, QPushButton,
    QScrollArea, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from data_processing.stm32_serial import STM32SerialReceiver


class CortexGuardWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("CortexGuard — STM32 / FreeRTOS Diagnostics")
        self.resize(1450, 1000)
        self.setMinimumSize(1050, 720)

        self.receiver: STM32SerialReceiver | None = None

        self.cpu_history: deque[float] = deque(maxlen=180)
        self.heap_history: deque[float] = deque(maxlen=180)
        self.task_rows: dict[str, int] = {}

        self.fault_count = 0
        self.last_packet_time: datetime | None = None
        self.serial_connected_at: datetime | None = None

        # A new hardware session begins only after a valid CG packet.
        self.live_session_started = False
        self.session_number = 0
        self.session_name = "SIMULATION SESSION"

        self.paused = False
        self.recording = False
        self.csv_file = None
        self.csv_writer = None

        self.simulation_tick = 0
        self.simulated_min_heap = 15360
        self.simulation_total_heap = 15360
        self.last_simulated_fault_mode = None

        # Suppress repeated copies of the same continuously reported fault.
        self.seen_live_faults: set[tuple[str, str, str]] = set()

        self._build_ui()

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.poll_serial)
        self.timer.start()

    # ---------------------------------------------------------
    # USER INTERFACE
    # ---------------------------------------------------------
    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        body = QWidget()
        scroll.setWidget(body)
        self.setCentralWidget(scroll)

        root = QVBoxLayout(body)
        root.setContentsMargins(10, 8, 10, 12)
        root.setSpacing(8)

        title = QLabel("CORTEXGUARD")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:30px;font-weight:bold;padding:3px")
        root.addWidget(title)

        self.connection_label = QLabel(
            "● SIMULATION MODE — STM32 DISCONNECTED"
        )
        self.connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.connection_label)

        serial_box = QGroupBox("Hardware connection")
        serial_row = QHBoxLayout(serial_box)
        serial_row.addWidget(QLabel("Serial port:"))

        self.port_combo = QComboBox()
        serial_row.addWidget(self.port_combo, 1)

        refresh = QPushButton("Refresh ports")
        refresh.clicked.connect(self.refresh_ports)
        serial_row.addWidget(refresh)

        serial_row.addWidget(QLabel("Baud:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["115200", "9600", "57600", "230400"])
        serial_row.addWidget(self.baud_combo)

        self.connect_button = QPushButton("Connect STM32")
        self.connect_button.clicked.connect(self.connect_serial)
        serial_row.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_serial)
        self.disconnect_button.setEnabled(False)
        serial_row.addWidget(self.disconnect_button)

        root.addWidget(serial_box)
        self.refresh_ports()

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Simulation test mode:"))

        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "NORMAL",
            "MEMORY_FAULT",
            "CPU_FAULT",
            "STACK_FAULT",
            "TIMING_FAULT",
        ])
        controls.addWidget(self.mode_combo, 1)

        self.pause_button = QPushButton("Pause monitoring")
        self.pause_button.clicked.connect(self.toggle_pause)
        controls.addWidget(self.pause_button)

        reset = QPushButton("Reset graph")
        reset.clicked.connect(self.reset_graph)
        controls.addWidget(reset)

        self.record_button = QPushButton("Start telemetry report")
        self.record_button.clicked.connect(self.toggle_recording)
        controls.addWidget(self.record_button)

        root.addLayout(controls)

        self.system_label = QLabel("SYSTEM STATUS: SIMULATION MODE")
        self.system_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.system_label)

        self.detail_label = QLabel(
            "Generated demo telemetry is active while STM32 is disconnected."
        )
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_label.setWordWrap(True)
        root.addWidget(self.detail_label)

        self.ai_label = QLabel(
            "AI STATE: NO AI MODEL CONNECTED — RULE-BASED DIAGNOSTICS ONLY"
        )
        self.ai_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.ai_label)

        risk_row = QHBoxLayout()

        self.future_risk = QLabel("FUTURE RISK: NOT AVAILABLE")
        self.future_risk.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.risk_confidence = QLabel("RISK CONFIDENCE: NOT AVAILABLE")
        self.risk_confidence.setAlignment(Qt.AlignmentFlag.AlignCenter)

        risk_row.addWidget(self.future_risk)
        risk_row.addWidget(self.risk_confidence)
        root.addLayout(risk_row)

        grid = QGridLayout()

        self.cpu_value = self.add_metric(grid, 0, 0, "CPU USAGE")
        self.ram_value = self.add_metric(grid, 0, 1, "RAM / HEAP USAGE")
        self.stack_value = self.add_metric(
            grid, 0, 2, "DIAGNOSTICS TASK STACK"
        )
        self.heap_value = self.add_metric(grid, 1, 0, "FREE HEAP")
        self.min_heap_value = self.add_metric(
            grid, 1, 1, "MINIMUM FREE HEAP"
        )
        self.task_count_value = self.add_metric(
            grid, 1, 2, "FREERTOS TASK COUNT"
        )

        root.addLayout(grid)

        graph_heading = QLabel("LIVE TELEMETRY — CPU AND FREE HEAP")
        graph_heading.setStyleSheet("font-size:17px;font-weight:bold")
        root.addWidget(graph_heading)

        self.graph = pg.PlotWidget(title="CPU (%) and free heap (KB)")
        self.graph.setMinimumHeight(300)
        self.graph.setMaximumHeight(380)
        self.graph.setBackground("#080808")
        self.graph.setLabel("bottom", "Recent samples")
        self.graph.setLabel("left", "CPU usage", units="%")
        self.graph.showGrid(x=True, y=True, alpha=0.25)

        plot = self.graph.getPlotItem()
        plot.addLegend()
        plot.showAxis("right")
        plot.getAxis("right").setLabel(
            "Free heap", units="KB", color="#00D9FF"
        )

        self.heap_view = pg.ViewBox()
        plot.scene().addItem(self.heap_view)
        plot.getAxis("right").linkToView(self.heap_view)
        self.heap_view.setXLink(plot)

        self.cpu_curve = plot.plot(
            [],
            [],
            name="CPU usage (%)",
            pen=pg.mkPen("#39D353", width=2.5),
        )

        self.heap_curve = pg.PlotCurveItem(
            [],
            [],
            name="Free heap (KB)",
            pen=pg.mkPen("#00D9FF", width=2.5),
        )
        self.heap_view.addItem(self.heap_curve)

        def resize_heap_view():
            self.heap_view.setGeometry(plot.vb.sceneBoundingRect())
            self.heap_view.linkedViewChanged(
                plot.vb, self.heap_view.XAxis
            )

        plot.vb.sigResized.connect(resize_heap_view)
        resize_heap_view()
        root.addWidget(self.graph)

        task_heading = QLabel(
            "FREERTOS TASK STACK HIGH-WATER MARK MONITOR"
        )
        task_heading.setStyleSheet("font-size:17px;font-weight:bold")
        root.addWidget(task_heading)

        self.task_table = QTableWidget(0, 4)
        self.task_table.setHorizontalHeaderLabels([
            "Task name",
            "High-water mark (words)",
            "Unused stack bytes (approx.)",
            "Status",
        ])

        for col in range(3):
            self.task_table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeMode.ResizeToContents
            )

        self.task_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.task_table.setMinimumHeight(170)
        self.task_table.setMaximumHeight(250)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        root.addWidget(self.task_table)

        fault_heading = QLabel(
            "STM32 FAULT EVENTS AND TELEMETRY REPORT"
        )
        fault_heading.setStyleSheet("font-size:17px;font-weight:bold")
        root.addWidget(fault_heading)

        self.fault_summary = QLabel(
            "Session: SIMULATION SESSION | Faults: 0 | "
            "Memory: 0 | CPU: 0 | Stack: 0 | Timing: 0"
        )
        root.addWidget(self.fault_summary)

        self.fault_table = QTableWidget(0, 4)
        self.fault_table.setHorizontalHeaderLabels([
            "Time", "Fault type", "Severity", "Details"
        ])

        for col in range(3):
            self.fault_table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeMode.ResizeToContents
            )

        self.fault_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.fault_table.setMinimumHeight(150)
        self.fault_table.setMaximumHeight(260)
        self.fault_table.setAlternatingRowColors(True)
        self.fault_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        root.addWidget(self.fault_table)

        self.last_update = QLabel("Last telemetry: waiting")
        root.addWidget(self.last_update)

        self.setStyleSheet("""
            QMainWindow,QWidget{background:#1f1f1f;color:#f3f3f3}
            QGroupBox{border:1px solid #777;border-radius:5px;
            margin-top:8px;padding:8px 5px 5px;font-weight:bold}
            QGroupBox::title{subcontrol-origin:margin;left:8px;padding:0 3px}
            QPushButton,QComboBox{min-height:27px;padding:3px 8px;
            background:#2b2b2b;border:1px solid #444;border-radius:4px}
            QPushButton:hover{background:#383838}
            QTableWidget{background:#292929;alternate-background-color:#303030;
            gridline-color:#444;selection-background-color:#3b526b}
            QHeaderView::section{background:#393939;padding:5px;border:1px solid #444}
        """)

        self.set_status_colour("LOW")

    def add_metric(self, grid, row, col, name):
        box = QGroupBox(name)
        layout = QVBoxLayout(box)

        value = QLabel("N/A")
        value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value.setStyleSheet(
            "font-size:25px;font-weight:bold;padding:5px"
        )

        layout.addWidget(value)
        grid.addWidget(box, row, col)
        return value

    # ---------------------------------------------------------
    # SESSION RESET
    # ---------------------------------------------------------
    def _clear_session_data(self, session_name: str) -> None:
        """
        Clear dashboard session data only.
        Previously saved CSV reports are not deleted.
        """
        self.session_name = session_name

        self.cpu_history.clear()
        self.heap_history.clear()
        self.cpu_curve.setData([], [])
        self.heap_curve.setData([], [])

        self.task_table.setRowCount(0)
        self.task_rows.clear()

        self.fault_table.setRowCount(0)
        self.fault_count = 0
        self.seen_live_faults.clear()

        self.cpu_value.setText("N/A")
        self.ram_value.setText("N/A")
        self.stack_value.setText("N/A")
        self.heap_value.setText("N/A")
        self.min_heap_value.setText("N/A")
        self.task_count_value.setText("N/A")

        self.future_risk.setText(
            "FUTURE RISK: WAITING FOR TELEMETRY"
        )
        self.risk_confidence.setText(
            "RISK CONFIDENCE: NOT AVAILABLE"
        )
        self.last_update.setText(
            "Last telemetry: waiting for first packet"
        )

        self._update_fault_summary()

    # ---------------------------------------------------------
    # COLOURS AND FAULT EVENTS
    # ---------------------------------------------------------
    def set_status_colour(self, level: str) -> None:
        colours = {
            "LOW": ("#14532d", "#bbf7d0"),
            "NORMAL": ("#14532d", "#bbf7d0"),
            "MODERATE": ("#78350f", "#fde68a"),
            "WARNING": ("#78350f", "#fde68a"),
            "HIGH": ("#7f1d1d", "#fecaca"),
            "FAULT": ("#7f1d1d", "#fecaca"),
        }

        bg, fg = colours.get(
            level.upper(), ("#333333", "#f3f3f3")
        )

        style = (
            f"background-color:{bg};color:{fg};"
            "font-weight:bold;padding:5px;border-radius:4px"
        )

        self.system_label.setStyleSheet(style)
        self.future_risk.setStyleSheet(style)
        self.risk_confidence.setStyleSheet(style)

    @staticmethod
    def _row_colour(severity: str) -> str:
        sev = str(severity).upper()

        if sev in ("HIGH", "CRITICAL", "FAULT"):
            return "#702020"

        if sev in ("MEDIUM", "MODERATE", "WARNING"):
            return "#70531A"

        return "#28552E"

    def add_fault_event(
        self, fault_type, severity, details, source="LIVE"
    ) -> None:
        now = datetime.now()
        row = self.fault_table.rowCount()
        self.fault_table.insertRow(row)

        values = [
            now.strftime("%H:%M:%S"),
            fault_type,
            severity,
            f"[{source}] {details}",
        ]

        background = self._row_colour(str(severity))

        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setBackground(QColor(background))
            self.fault_table.setItem(row, col, item)

        self.fault_count += 1

        self._log([
            now.isoformat(timespec="milliseconds"),
            "FAULT", "", "", "", "",
            fault_type, severity, f"[{source}] {details}",
        ])

        self._update_fault_summary()

        sev = str(severity).upper()

        if sev in ("HIGH", "CRITICAL", "FAULT"):
            self.set_status_colour("HIGH")
            self.system_label.setText(
                "SYSTEM STATUS: FAULT DETECTED"
            )
        elif sev in ("MEDIUM", "MODERATE", "WARNING"):
            self.set_status_colour("MODERATE")
            self.system_label.setText(
                "SYSTEM STATUS: WARNING"
            )

    def _update_fault_summary(self) -> None:
        counts = {
            "MEMORY": 0,
            "CPU": 0,
            "STACK": 0,
            "TIMING": 0,
        }

        for row in range(self.fault_table.rowCount()):
            item = self.fault_table.item(row, 1)

            if not item:
                continue

            fault_type = item.text().upper()

            for key in counts:
                if key in fault_type:
                    counts[key] += 1
                    break

        self.fault_summary.setText(
            f"Session: {self.session_name} | "
            f"Faults: {self.fault_count} | "
            f"Memory: {counts['MEMORY']} | "
            f"CPU: {counts['CPU']} | "
            f"Stack: {counts['STACK']} | "
            f"Timing: {counts['TIMING']}"
        )

    # ---------------------------------------------------------
    # FREERTOS TASK STACK TABLE
    # ---------------------------------------------------------
    def _set_task_row(
        self, name: str, words: int, simulated: bool = False
    ) -> None:
        if name not in self.task_rows:
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            self.task_rows[name] = row
        else:
            row = self.task_rows[name]

        # uxTaskGetStackHighWaterMark reports the minimum unused
        # stack in StackType_t units. On STM32F446, one word is 4 bytes.
        if words <= 32:
            status = "CRITICAL — VERY LOW UNUSED STACK"
            colour = "#702020"
            level = "HIGH"
        elif words <= 64:
            status = "WARNING — LOW UNUSED STACK"
            colour = "#70531A"
            level = "MODERATE"
        else:
            status = (
                "SIMULATED — DEMO VALUE"
                if simulated
                else "LIVE — REPORTED BY FIRMWARE"
            )
            colour = "#28552E"
            level = "LOW"

        values = [
            name,
            str(words),
            str(words * 4),
            status,
        ]

        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setBackground(QColor(colour))
            self.task_table.setItem(row, col, item)

        if name.lower() == "diagnosticstask":
            self.stack_value.setText(f"{words} words")

        # Only actual firmware task reports affect the global status here.
        if not simulated and words <= 64:
            self.set_status_colour(level)

    def update_simulated_task_table(
        self, diagnostics_stack_words: int
    ) -> None:
        simulated_tasks = [
            ("SensorTask", 128),
            ("ControlTask", 160),
            ("CommunicationTask", 192),
            ("LoggerTask", 128),
            ("DiagnosticsTask", diagnostics_stack_words),
        ]

        for name, words in simulated_tasks:
            self._set_task_row(name, words, simulated=True)

    def update_live_task(self, name, words) -> None:
        try:
            self._set_task_row(
                str(name), int(words), simulated=False
            )
        except (TypeError, ValueError):
            return

    # ---------------------------------------------------------
    # SERIAL CONNECTION
    # ---------------------------------------------------------
    def refresh_ports(self) -> None:
        old = self.port_combo.currentData()
        self.port_combo.clear()

        ports = list(serial.tools.list_ports.comports())

        for port in ports:
            self.port_combo.addItem(
                f"{port.device} — {port.description}",
                port.device,
            )

        if not ports:
            self.port_combo.addItem(
                "No serial ports found", ""
            )
        elif old:
            idx = self.port_combo.findData(old)
            if idx >= 0:
                self.port_combo.setCurrentIndex(idx)

    def connect_serial(self) -> None:
        port = self.port_combo.currentData()

        if not port:
            QMessageBox.warning(
                self, "No port", "Select the STM32 COM port."
            )
            return

        try:
            receiver = STM32SerialReceiver(
                str(port),
                int(self.baud_combo.currentText()),
            )
            receiver.connect()
            self.receiver = receiver
        except Exception as exc:
            self.receiver = None
            QMessageBox.critical(
                self, "Connection failed", str(exc)
            )
            return

        self.serial_connected_at = datetime.now()
        self.last_packet_time = None
        self.live_session_started = False
        self.simulation_tick = 0

        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)
        self.port_combo.setEnabled(False)
        self.baud_combo.setEnabled(False)

        self.connection_label.setText(
            f"● SERIAL OPEN — WAITING FOR STM32 DATA ({port})"
        )
        self.system_label.setText(
            "SYSTEM STATUS: WAITING FOR FIRST VALID STM32 PACKET"
        )
        self.detail_label.setText(
            "Session data will reset when the first valid STM32 "
            "telemetry packet arrives. Opening the COM port alone "
            "does not count as receiving live data."
        )
        self.set_status_colour("MODERATE")

    def disconnect_serial(self) -> None:
        if self.receiver:
            try:
                self.receiver.close()
            except Exception:
                pass

        self.receiver = None
        self.serial_connected_at = None
        self.last_packet_time = None
        self.live_session_started = False

        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.port_combo.setEnabled(True)
        self.baud_combo.setEnabled(True)

        self.connection_label.setText(
            "● SIMULATION MODE — STM32 DISCONNECTED"
        )
        self.system_label.setText(
            "SYSTEM STATUS: SIMULATION MODE"
        )
        self.detail_label.setText(
            "STM32 disconnected. Generated demo telemetry is active."
        )
        self.set_status_colour("LOW")

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.pause_button.setText(
            "Resume monitoring" if self.paused
            else "Pause monitoring"
        )

    def reset_graph(self) -> None:
        self.cpu_history.clear()
        self.heap_history.clear()
        self.cpu_curve.setData([], [])
        self.heap_curve.setData([], [])

    # ---------------------------------------------------------
    # CSV TELEMETRY REPORT
    # ---------------------------------------------------------
    def toggle_recording(self) -> None:
        if not self.recording:
            safe_session = (
                self.session_name.lower().replace(" ", "_")
            )

            path = Path.cwd() / (
                f"cortexguard_{safe_session}_"
                f"{datetime.now():%Y%m%d_%H%M%S}.csv"
            )

            try:
                self.csv_file = path.open(
                    "w", newline="", encoding="utf-8"
                )
                self.csv_writer = csv.writer(self.csv_file)

                self.csv_writer.writerow([
                    "timestamp",
                    "session_name",
                    "record_type",
                    "cpu_percent",
                    "free_heap_bytes",
                    "min_free_heap_bytes",
                    "task_count",
                    "fault_type",
                    "severity",
                    "details",
                ])

            except OSError as exc:
                QMessageBox.critical(
                    self, "Report error", str(exc)
                )
                self.csv_file = None
                self.csv_writer = None
                return

            self.recording = True
            self.record_button.setText("Stop report")
            self.detail_label.setText(
                f"Recording {self.session_name} report to {path}"
            )

        else:
            self._stop_recording()
            self.detail_label.setText(
                "Telemetry report recording stopped."
            )

    def _stop_recording(self) -> None:
        self.recording = False
        self.record_button.setText("Start telemetry report")

        if self.csv_file:
            try:
                self.csv_file.flush()
                self.csv_file.close()
            except Exception:
                pass

        self.csv_file = None
        self.csv_writer = None

    def _log(self, row) -> None:
        if self.recording and self.csv_writer:
            # Existing log calls supply 9 columns. Insert the session name
            # to match the 10-column report header.
            if len(row) == 9:
                row = [row[0], self.session_name, *row[1:]]

            self.csv_writer.writerow(row)
            self.csv_file.flush()

    # ---------------------------------------------------------
    # RULE-BASED RISK
    # ---------------------------------------------------------
    def _risk(
        self, cpu, heap, min_heap, stack_words=None
    ) -> str:
        if cpu is None:
            self.future_risk.setText(
                "FUTURE RISK: WAITING FOR CPU TELEMETRY"
            )
            self.risk_confidence.setText(
                "RISK CONFIDENCE: NOT AVAILABLE"
            )
            self.set_status_colour("MODERATE")
            return "MODERATE"

        if (
            cpu >= 90
            or heap < 1024
            or min_heap < 512
            or (
                stack_words is not None
                and stack_words <= 32
            )
        ):
            level = "HIGH"

        elif (
            cpu >= 75
            or heap < 4096
            or min_heap < 2048
            or (
                stack_words is not None
                and stack_words <= 64
            )
        ):
            level = "MODERATE"

        else:
            level = "LOW"

        self.future_risk.setText(
            f"FUTURE RISK (RULE-BASED): {level}"
        )
        self.risk_confidence.setText(
            "RISK CONFIDENCE: HEURISTIC ONLY — NOT ML"
        )
        self.ai_label.setText(
            "AI STATE: NO AI MODEL CONNECTED — RULE-BASED DIAGNOSTICS"
        )
        self.set_status_colour(level)

        return level

    # ---------------------------------------------------------
    # SIMULATED TELEMETRY
    # ---------------------------------------------------------
    def update_simulated_telemetry(self) -> None:
        self.simulation_tick += 1

        # Timer is 100 ms. Update values every 500 ms.
        if self.simulation_tick % 5 != 0:
            return

        now = datetime.now()
        phase = self.simulation_tick / 5.0
        mode = self.mode_combo.currentText()

        total_heap = self.simulation_total_heap
        task_count = 5

        if mode == "CPU_FAULT":
            cpu = 93 + 5 * abs(math.sin(phase * 0.5))
            free_heap = 10500 + int(300 * math.sin(phase))
            stack_words = 276

        elif mode == "MEMORY_FAULT":
            cpu = 12 + 5 * abs(math.sin(phase))
            free_heap = 800 + int(
                250 * abs(math.sin(phase * 0.5))
            )
            stack_words = 276

        elif mode == "STACK_FAULT":
            cpu = 10 + 5 * abs(math.sin(phase))
            free_heap = 10500 + int(300 * math.sin(phase))
            stack_words = 24

        elif mode == "TIMING_FAULT":
            cpu = 78 + 8 * abs(math.sin(phase * 0.7))
            free_heap = 9500 + int(400 * math.sin(phase))
            stack_words = 276

        else:
            cpu = 5 + 10 * abs(math.sin(phase * 0.5))
            free_heap = 10800 + int(
                700 * math.sin(phase * 0.4)
            )
            stack_words = 276

        free_heap = max(
            0, min(total_heap, int(free_heap))
        )
        used_heap = total_heap - free_heap

        self.simulated_min_heap = min(
            self.simulated_min_heap, free_heap
        )
        min_free_heap = self.simulated_min_heap
        ram_percent = 100.0 * used_heap / total_heap

        self.cpu_value.setText(f"{cpu:.1f} %")
        self.ram_value.setText(
            f"{ram_percent:.1f}% "
            f"({used_heap:,}/{total_heap:,} B)"
        )
        self.heap_value.setText(
            f"{free_heap / 1024:.2f} KB"
        )
        self.min_heap_value.setText(
            f"{min_free_heap / 1024:.2f} KB"
        )
        self.task_count_value.setText(str(task_count))
        self.stack_value.setText(f"{stack_words} words")

        self.update_simulated_task_table(stack_words)

        self.cpu_history.append(float(cpu))
        self.heap_history.append(free_heap / 1024.0)

        self.cpu_curve.setData(
            list(range(len(self.cpu_history))),
            list(self.cpu_history),
        )
        self.heap_curve.setData(
            list(range(len(self.heap_history))),
            list(self.heap_history),
        )

        self.connection_label.setText(
            "● SIMULATION MODE — GENERATED DEMO VALUES"
        )
        self.system_label.setText(
            f"SYSTEM STATUS: SIMULATED — {mode}"
        )
        self.detail_label.setText(
            f"DEMO DATA ONLY | Mode: {mode} | "
            "Not actual STM32 measurements."
        )
        self.last_update.setText(
            "Last simulated update: " + now.strftime("%H:%M:%S")
        )

        self._risk(
            cpu, free_heap, min_free_heap, stack_words
        )

        # Create one demo event on entry to a fault mode, not on every tick.
        if (
            mode != "NORMAL"
            and mode != self.last_simulated_fault_mode
        ):
            descriptions = {
                "CPU_FAULT": (
                    "Simulated high CPU activity. Review task "
                    "execution time and scheduling."
                ),
                "MEMORY_FAULT": (
                    "Simulated critically low free heap. Review "
                    "allocation patterns and possible memory leaks."
                ),
                "STACK_FAULT": (
                    "Simulated low task stack margin. Review stack "
                    "allocation and overflow checks."
                ),
                "TIMING_FAULT": (
                    "Simulated timing risk. Review task periods "
                    "and deadlines."
                ),
            }

            severity = (
                "HIGH"
                if mode in (
                    "CPU_FAULT",
                    "MEMORY_FAULT",
                    "STACK_FAULT",
                )
                else "WARNING"
            )

            self.add_fault_event(
                mode.replace("_FAULT", ""),
                severity,
                descriptions.get(
                    mode, "Simulated diagnostic event."
                ),
                source="SIMULATION",
            )

        self.last_simulated_fault_mode = mode

        self._log([
            now.isoformat(timespec="milliseconds"),
            "SIMULATION",
            round(cpu, 1),
            free_heap,
            min_free_heap,
            task_count,
            "",
            "",
            f"Simulated mode: {mode}",
        ])

    # ---------------------------------------------------------
    # START A FRESH HARDWARE SESSION
    # ---------------------------------------------------------
    def _start_live_session(self) -> None:
        """
        Called exactly once after the first valid aggregate STM32 packet.
        Clears previous dashboard data without deleting saved CSV reports.
        """
        if self.live_session_started:
            return

        self.session_number += 1
        self.session_name = (
            f"STM32 LIVE SESSION {self.session_number:03d}"
        )

        self._clear_session_data(self.session_name)
        self.live_session_started = True
        self.last_simulated_fault_mode = None

        self.connection_label.setText(
            "● STM32 HARDWARE MODE — LIVE DATA"
        )
        self.system_label.setText(
            "SYSTEM STATUS: LIVE TELEMETRY RECEIVED"
        )
        self.detail_label.setText(
            f"{self.session_name}: previous dashboard session "
            "data cleared. Displaying live STM32 UART data."
        )

        self.set_status_colour("LOW")

    # ---------------------------------------------------------
    # LIVE UART
    # ---------------------------------------------------------
    def poll_serial(self) -> None:
        if self.paused:
            return

        # Simulation is used only when no hardware serial connection is open.
        if not self.receiver:
            self.update_simulated_telemetry()
            return

        try:
            packets = self.receiver.read_messages()
            tasks = self.receiver.read_task_messages()
            faults = self.receiver.read_fault_messages()

        except Exception as exc:
            self.disconnect_serial()
            self.detail_label.setText(
                f"Serial connection lost: {exc}. "
                "Simulation is resuming."
            )
            return

        # Aggregate telemetry packet: CG,cpu=...,heap=...,min_heap=...
        for packet in packets:
            # Do not clear old data for incomplete/invalid packets.
            if (
                packet.get("heap") is None
                or packet.get("min_heap") is None
            ):
                self.detail_label.setText(
                    "Ignoring invalid CG packet: heap fields are missing."
                )
                continue

            self._start_live_session()

            now = datetime.now()
            self.last_packet_time = now

            cpu = packet.get("cpu")
            heap = int(packet["heap"])
            min_heap = int(packet["min_heap"])
            task_count = packet.get("tasks")
            stack_words = packet.get("stack_words")

            self.cpu_value.setText(
                f"{float(cpu):.1f} %"
                if cpu is not None else "N/A"
            )

            ram_percent = packet.get("ram")
            used_bytes = packet.get("heap_used")

            if ram_percent is not None:
                if used_bytes is not None:
                    total_bytes = heap + int(used_bytes)
                    self.ram_value.setText(
                        f"{ram_percent}% "
                        f"({int(used_bytes):,}/{total_bytes:,} B)"
                    )
                else:
                    self.ram_value.setText(
                        f"{ram_percent}% heap used"
                    )

            elif (
                packet.get("ram_used") is not None
                and packet.get("ram_total") is not None
            ):
                ram_used = packet["ram_used"]
                ram_total = packet["ram_total"]

                if ram_total > 0:
                    pct = 100.0 * ram_used / ram_total
                    self.ram_value.setText(
                        f"{pct:.1f}% "
                        f"({ram_used:,}/{ram_total:,} B)"
                    )
                else:
                    self.ram_value.setText("N/A")

            else:
                self.ram_value.setText(
                    "N/A — RAM field missing"
                )

            self.heap_value.setText(
                f"{heap / 1024:.2f} KB"
            )
            self.min_heap_value.setText(
                f"{min_heap / 1024:.2f} KB"
            )

            if task_count is not None:
                self.task_count_value.setText(str(task_count))

            if stack_words is not None:
                self.stack_value.setText(
                    f"{stack_words} words"
                )

            self.cpu_history.append(
                float(cpu) if cpu is not None else 0.0
            )
            self.heap_history.append(heap / 1024.0)

            self.cpu_curve.setData(
                list(range(len(self.cpu_history))),
                list(self.cpu_history),
            )
            self.heap_curve.setData(
                list(range(len(self.heap_history))),
                list(self.heap_history),
            )

            level = self._risk(
                cpu, heap, min_heap, stack_words
            )

            self.connection_label.setText(
                "● STM32 HARDWARE MODE — LIVE DATA"
            )
            self.system_label.setText(
                "SYSTEM STATUS: LIVE TELEMETRY — " + level
            )
            self.detail_label.setText(
                f"{self.session_name} | "
                "Real STM32 telemetry received over UART."
            )
            self.last_update.setText(
                "Last hardware telemetry: "
                + now.strftime("%H:%M:%S")
            )

            self._log([
                now.isoformat(timespec="milliseconds"),
                "TELEMETRY",
                cpu if cpu is not None else "",
                heap,
                min_heap,
                task_count if task_count is not None else "",
                "",
                "",
                "",
            ])

        # Firmware-reported task stack high-water marks.
        for task in tasks:
            if not self.live_session_started:
                continue

            if (
                task.get("name") is not None
                and task.get("stack_words") is not None
            ):
                self.update_live_task(
                    task["name"], task["stack_words"]
                )

        # Firmware-reported fault events.
        for fault in faults:
            if not self.live_session_started:
                continue

            fault_type = str(
                fault.get("type", "UNKNOWN")
            )
            severity = str(
                fault.get("level", "WARNING")
            )
            details = str(
                fault.get("detail", "Firmware reported a fault")
            )

            key = (fault_type, severity, details)

            # Prevent a repeated UART line from creating duplicate table rows.
            if key in self.seen_live_faults:
                continue

            self.seen_live_faults.add(key)

            self.add_fault_event(
                fault_type,
                severity,
                details,
                source="STM32",
            )

        # Hardware is connected: do not inject simulation data into its graphs.
        reference_time = (
            self.last_packet_time or self.serial_connected_at
        )

        if reference_time is not None:
            elapsed = (
                datetime.now() - reference_time
            ).total_seconds()

            if elapsed > 3:
                self.connection_label.setText(
                    "● STM32 SERIAL OPEN — NO RECENT TELEMETRY"
                )
                self.system_label.setText(
                    "SYSTEM STATUS: STM32 TELEMETRY TIMEOUT"
                )
                self.detail_label.setText(
                    "No valid STM32 packet received for more than "
                    "3 seconds. Simulation is disabled while the "
                    "hardware serial connection remains open."
                )
                self.set_status_colour("MODERATE")

    # ---------------------------------------------------------
    # CLOSE
    # ---------------------------------------------------------
    def closeEvent(self, event) -> None:
        if self.receiver:
            try:
                self.receiver.close()
            except Exception:
                pass

        self._stop_recording()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    window = CortexGuardWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
