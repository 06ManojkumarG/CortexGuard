
from __future__ import annotations

import csv
import html
import math
import sys
import webbrowser
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

        self.record_button = QPushButton("Generate Report")
        self.record_button.clicked.connect(self.generate_report)
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
        """Clear dashboard data without deleting previously saved reports."""
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

        self.future_risk.setText("FUTURE RISK: WAITING FOR TELEMETRY")
        self.risk_confidence.setText("RISK CONFIDENCE: NOT AVAILABLE")
        self.last_update.setText("Last telemetry: waiting for first packet")

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

        bg, fg = colours.get(level.upper(), ("#333333", "#f3f3f3"))

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
            self.system_label.setText("SYSTEM STATUS: FAULT DETECTED")
        elif sev in ("MEDIUM", "MODERATE", "WARNING"):
            self.set_status_colour("MODERATE")
            self.system_label.setText("SYSTEM STATUS: WARNING")

    def _update_fault_summary(self) -> None:
        counts = {"MEMORY": 0, "CPU": 0, "STACK": 0, "TIMING": 0}

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

        # STM32F446 uses 32-bit StackType_t units.
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

        values = [name, str(words), str(words * 4), status]

        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setBackground(QColor(colour))
            self.task_table.setItem(row, col, item)

        if name.lower() == "diagnosticstask":
            self.stack_value.setText(f"{words} words")

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
            self._set_task_row(str(name), int(words), simulated=False)
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
                f"{port.device} — {port.description}", port.device
            )

        if not ports:
            self.port_combo.addItem("No serial ports found", "")
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
                str(port), int(self.baud_combo.currentText())
            )
            receiver.connect()
            self.receiver = receiver
        except Exception as exc:
            self.receiver = None
            QMessageBox.critical(self, "Connection failed", str(exc))
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
        self.system_label.setText("SYSTEM STATUS: SIMULATION MODE")
        self.detail_label.setText(
            "STM32 disconnected. Generated demo telemetry is active."
        )
        self.set_status_colour("LOW")

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.pause_button.setText(
            "Resume monitoring" if self.paused else "Pause monitoring"
        )

    def reset_graph(self) -> None:
        self.cpu_history.clear()
        self.heap_history.clear()
        self.cpu_curve.setData([], [])
        self.heap_curve.setData([], [])

    # ---------------------------------------------------------
    # HTML REPORT GENERATION
    # ---------------------------------------------------------
    @staticmethod
    def _html_escape(value) -> str:
        return html.escape(str(value if value is not None else ""))

    def _table_html(self, table: QTableWidget) -> str:
        """Convert the current contents of a dashboard table to HTML."""
        headers = []

        for col in range(table.columnCount()):
            header = table.horizontalHeaderItem(col)
            headers.append(header.text() if header else f"Column {col + 1}")

        parts = ["<table><thead><tr>"]

        for header in headers:
            parts.append(f"<th>{self._html_escape(header)}</th>")

        parts.append("</tr></thead><tbody>")

        if table.rowCount() == 0:
            parts.append(
                f'<tr><td colspan="{max(1, len(headers))}">'
                "No records available in this session."
                "</td></tr>"
            )
        else:
            for row in range(table.rowCount()):
                parts.append("<tr>")
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    value = item.text() if item else ""
                    parts.append(f"<td>{self._html_escape(value)}</td>")
                parts.append("</tr>")

        parts.append("</tbody></table>")
        return "".join(parts)

    @staticmethod
    def _history_summary(values, unit: str) -> str:
        if not values:
            return "No retained samples"

        minimum = min(values)
        maximum = max(values)
        average = sum(values) / len(values)

        return (
            f"Min: {minimum:.2f} {unit} | "
            f"Max: {maximum:.2f} {unit} | "
            f"Average: {average:.2f} {unit} | "
            f"Samples: {len(values)}"
        )

    def generate_report(self) -> None:
        """Generate and open an HTML snapshot of the dashboard."""
        try:
            # main_window.py is in dashboard/app/dashboard/.
            project_root = Path(__file__).resolve().parents[3]
            report_dir = project_root / "reports" / "generated"
            report_dir.mkdir(parents=True, exist_ok=True)

            created_at = datetime.now()
            report_path = report_dir / (
                f"CortexGuard_Report_{created_at:%Y%m%d_%H%M%S}.html"
            )

            cpu_samples = list(self.cpu_history)
            heap_samples = list(self.heap_history)

            # Keep the two history series aligned for the sample table.
            sample_count = min(len(cpu_samples), len(heap_samples))
            sample_rows = []

            for index in range(sample_count):
                sample_rows.append(
                    "<tr>"
                    f"<td>{index + 1}</td>"
                    f"<td>{cpu_samples[index]:.2f}%</td>"
                    f"<td>{heap_samples[index]:.2f} KB</td>"
                    "</tr>"
                )

            if not sample_rows:
                sample_rows.append(
                    '<tr><td colspan="3">No retained graph samples.</td></tr>'
                )

            metric_rows = [
                ("Session", self.session_name),
                ("Connection", self.connection_label.text()),
                ("System status", self.system_label.text()),
                ("CPU usage", self.cpu_value.text()),
                ("RAM / heap usage", self.ram_value.text()),
                ("Free heap", self.heap_value.text()),
                ("Minimum free heap", self.min_heap_value.text()),
                ("Diagnostics task stack", self.stack_value.text()),
                ("FreeRTOS task count", self.task_count_value.text()),
                ("Rule-based risk", self.future_risk.text()),
                ("Risk confidence", self.risk_confidence.text()),
                ("AI state", self.ai_label.text()),
                ("Last update", self.last_update.text()),
                ("Fault event count", self.fault_count),
            ]

            metric_html = "".join(
                "<tr>"
                f"<th>{self._html_escape(name)}</th>"
                f"<td>{self._html_escape(value)}</td>"
                "</tr>"
                for name, value in metric_rows
            )

            cpu_summary = self._history_summary(cpu_samples, "%")
            heap_summary = self._history_summary(heap_samples, "KB")

            task_table_html = self._table_html(self.task_table)
            fault_table_html = self._table_html(self.fault_table)

            status_text = self._html_escape(self.system_label.text())
            session_text = self._html_escape(self.session_name)
            created_text = created_at.strftime("%d %B %Y, %H:%M:%S")

            report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CortexGuard Diagnostics Report</title>
<style>
    * {{ box-sizing: border-box; }}
    body {{
        margin: 0;
        padding: 28px;
        background: #f1f5f9;
        color: #1e293b;
        font-family: Arial, Helvetica, sans-serif;
        line-height: 1.5;
    }}
    main {{
        max-width: 1200px;
        margin: auto;
        background: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.08);
    }}
    h1 {{ margin-bottom: 4px; color: #0f172a; }}
    h2 {{
        margin-top: 32px;
        padding-bottom: 8px;
        border-bottom: 2px solid #e2e8f0;
        color: #0f172a;
    }}
    .subtitle {{ color: #64748b; margin-top: 0; }}
    .status {{
        padding: 14px;
        margin: 18px 0;
        background: #e2e8f0;
        border-radius: 7px;
        font-weight: bold;
        overflow-wrap: anywhere;
    }}
    .session {{ color: #475569; overflow-wrap: anywhere; }}
    .summary {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
        gap: 12px;
        margin-top: 16px;
    }}
    .summary-card {{
        padding: 15px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        overflow-wrap: anywhere;
    }}
    .summary-card strong {{ display: block; margin-bottom: 5px; }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 12px;
        font-size: 14px;
    }}
    th, td {{
        border: 1px solid #e2e8f0;
        padding: 9px;
        text-align: left;
        overflow-wrap: anywhere;
    }}
    th {{ background: #eaf0f6; }}
    tbody tr:nth-child(even) {{ background: #f8fafc; }}
    .note {{
        background: #fff7ed;
        border-left: 4px solid #ea580c;
        padding: 14px;
        margin-top: 12px;
    }}
    .footer {{
        margin-top: 35px;
        padding-top: 14px;
        border-top: 1px solid #e2e8f0;
        color: #64748b;
        font-size: 12px;
    }}
    @media print {{
        body {{ padding: 0; background: white; }}
        main {{ box-shadow: none; padding: 0; }}
        h2 {{ break-after: avoid; }}
        table {{ break-inside: auto; }}
        tr {{ break-inside: avoid; }}
    }}
</style>
</head>
<body>
<main>
    <h1>CortexGuard</h1>
    <p class="subtitle">STM32 / FreeRTOS Runtime Diagnostics Report</p>
    <p class="session"><strong>Session:</strong> {session_text}</p>
    <p class="session"><strong>Generated:</strong> {self._html_escape(created_text)}</p>

    <div class="status">{status_text}</div>

    <h2>1. Current System Measurements</h2>
    <table>
        <thead><tr><th>Parameter</th><th>Current value</th></tr></thead>
        <tbody>{metric_html}</tbody>
    </table>

    <h2>2. Retained Telemetry History</h2>
    <div class="summary">
        <div class="summary-card">
            <strong>CPU history</strong>
            {self._html_escape(cpu_summary)}
        </div>
        <div class="summary-card">
            <strong>Free heap history</strong>
            {self._html_escape(heap_summary)}
        </div>
    </div>
    <table>
        <thead>
            <tr><th>Sample</th><th>CPU usage</th><th>Free heap</th></tr>
        </thead>
        <tbody>{''.join(sample_rows)}</tbody>
    </table>

    <h2>3. FreeRTOS Task Stack Monitor</h2>
    <p>
        The high-water mark represents the minimum unused stack observed
        since a task started. A smaller value indicates less stack margin.
    </p>
    {task_table_html}

    <h2>4. Fault Events</h2>
    <p>
        Fault events shown below are those currently retained in the
        dashboard session. A report generated in simulation mode may
        contain simulated events rather than actual hardware faults.
    </p>
    {fault_table_html}

    <h2>5. Diagnostic Interpretation</h2>
    <ul>
        <li>
            <strong>CPU:</strong> High processor usage may indicate
            excessive task execution, busy loops, or scheduling pressure.
        </li>
        <li>
            <strong>Free heap:</strong> Low free heap may indicate
            insufficient heap capacity or excessive dynamic allocation.
            Review allocation and deallocation paths before concluding
            that a memory leak exists.
        </li>
        <li>
            <strong>Task stack:</strong> A low high-water mark indicates
            limited unused stack. Review task stack sizing and investigate
            possible stack overflow.
        </li>
        <li>
            <strong>Timing:</strong> A timing warning should be investigated
            using task periods, execution times, and deadline measurements.
        </li>
    </ul>

    <div class="note">
        <strong>Important limitations</strong>
        <ul>
            <li>
                The graph retains at most 180 samples. This report does
                not represent the complete lifetime history of the device.
            </li>
            <li>
                Resetting the graph clears its retained history. Closing
                the dashboard does not preserve these graph samples in a
                permanent database.
            </li>
            <li>
                CPU history may contain zero for packets where CPU data
                was unavailable. Treat those samples cautiously.
            </li>
            <li>
                RAM/heap values depend on the fields supplied by firmware.
                FreeRTOS heap usage is not a measurement of all physical
                MCU SRAM usage.
            </li>
            <li>
                Risk assessment is rule-based. Unless a trained ML model
                is explicitly connected and used, this report does not
                claim machine-learning predictions or calibrated
                confidence scores.
            </li>
            <li>
                Task stack byte values are approximate and assume a
                4-byte StackType_t on the STM32F446 target.
            </li>
        </ul>
    </div>

    <div class="footer">
        CortexGuard | Generated locally by the desktop dashboard.
        This report records displayed values and is not a substitute
        for validating firmware measurements and fault thresholds.
    </div>
</main>
</body>
</html>
"""

            report_path.write_text(report_html, encoding="utf-8")

            # Open the saved report in the system's default browser.
            webbrowser.open(report_path.resolve().as_uri())

            self.detail_label.setText(
                f"Report generated: {report_path}"
            )

            QMessageBox.information(
                self,
                "Report generated",
                "CortexGuard report saved successfully.\n\n"
                f"{report_path}\n\n"
                "The report has been opened in your default browser.",
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Report generation failed",
                f"Could not generate the report.\n\n{exc}",
            )

    # ---------------------------------------------------------
    # CSV TELEMETRY LOGGING
    # Kept for compatibility with existing logging functionality.
    # The main UI button now generates an HTML snapshot.
    # ---------------------------------------------------------
    def toggle_recording(self) -> None:
        if not self.recording:
            safe_session = self.session_name.lower().replace(" ", "_")

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
                QMessageBox.critical(self, "Report error", str(exc))
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
        self.record_button.setText("Generate Report")

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
            if len(row) == 9:
                row = [row[0], self.session_name, *row[1:]]

            self.csv_writer.writerow(row)
            self.csv_file.flush()

    # ---------------------------------------------------------
    # RULE-BASED RISK
    # ---------------------------------------------------------
    def _risk(self, cpu, heap, min_heap, stack_words=None) -> str:
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
            or (stack_words is not None and stack_words <= 32)
        ):
            level = "HIGH"

        elif (
            cpu >= 75
            or heap < 4096
            or min_heap < 2048
            or (stack_words is not None and stack_words <= 64)
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

        free_heap = max(0, min(total_heap, int(free_heap)))
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
        self.heap_value.setText(f"{free_heap / 1024:.2f} KB")
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

        self._risk(cpu, free_heap, min_free_heap, stack_words)

        # Create one demo event on entry to a fault mode.
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
                    "CPU_FAULT", "MEMORY_FAULT", "STACK_FAULT"
                )
                else "WARNING"
            )

            self.add_fault_event(
                mode.replace("_FAULT", ""),
                severity,
                descriptions.get(mode, "Simulated diagnostic event."),
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

        for packet in packets:
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
                        f"{pct:.1f}% ({ram_used:,}/{ram_total:,} B)"
                    )
                else:
                    self.ram_value.setText("N/A")

            else:
                self.ram_value.setText("N/A — RAM field missing")

            self.heap_value.setText(f"{heap / 1024:.2f} KB")
            self.min_heap_value.setText(f"{min_heap / 1024:.2f} KB")

            if task_count is not None:
                self.task_count_value.setText(str(task_count))

            if stack_words is not None:
                self.stack_value.setText(f"{stack_words} words")

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

            level = self._risk(cpu, heap, min_heap, stack_words)

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
                "Last hardware telemetry: " + now.strftime("%H:%M:%S")
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

        for fault in faults:
            if not self.live_session_started:
                continue

            fault_type = str(fault.get("type", "UNKNOWN"))
            severity = str(fault.get("level", "WARNING"))
            details = str(
                fault.get("detail", "Firmware reported a fault")
            )

            key = (fault_type, severity, details)

            if key in self.seen_live_faults:
                continue

            self.seen_live_faults.add(key)

            self.add_fault_event(
                fault_type, severity, details, source="STM32"
            )

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
