from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import pyqtgraph as pg

from data_processing.telemetry_simulator import TelemetrySimulator
from analytics.health_analyzer import HealthAnalyzer


class CortexGuardWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CortexGuard")
        self.resize(1200, 750)

        # ===== Telemetry Data Storage =====
        self.cpu_data = []
        self.ram_data = []
        self.stack_data = []
        self.heap_data = []
        self.temperature_data = []
        self.current_data = []
        self.speed_data = []

        self.max_points = 60

        # ===== CortexGuard Components =====
        self.telemetry_simulator = TelemetrySimulator()
        self.health_analyzer = HealthAnalyzer()

        self.build_dashboard()
        self.start_simulation()

    def build_dashboard(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # =====================================================
        # Header
        # =====================================================

        title = QLabel("CORTEXGUARD")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 28px; font-weight: bold;"
        )

        self.connection_label = QLabel("● SIMULATION MODE")
        self.connection_label.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(title)
        main_layout.addWidget(self.connection_label)

        # =====================================================
        # Simulation Mode Selector
        # =====================================================

        self.mode_selector = QComboBox()

        self.mode_selector.addItems([
            "NORMAL",
            "CPU_FAULT",
            "MEMORY_FAULT",
            "STACK_FAULT",
        ])

        self.mode_selector.currentTextChanged.connect(
            self.telemetry_simulator.set_mode
        )

        main_layout.addWidget(self.mode_selector)

        # ===== Monitoring Controls =====
        self.pause_button = QPushButton("PAUSE MONITORING")

        self.pause_button.clicked.connect(
            self.toggle_monitoring
        )

        main_layout.addWidget(self.pause_button)

        self.reset_button = QPushButton("RESET GRAPHS")

        self.reset_button.clicked.connect(
            self.reset_graphs
        )

        main_layout.addWidget(self.reset_button)

        # =====================================================
        # System Status
        # =====================================================

        self.status_label = QLabel("SYSTEM STATUS: NORMAL")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; padding: 12px;"
        )

        main_layout.addWidget(self.status_label)

        # =====================================================
        # Monitoring Cards
        # =====================================================

        cards_layout = QGridLayout()

        self.cpu_value = QLabel("0 %")
        self.ram_value = QLabel("0 %")
        self.stack_value = QLabel("0 %")
        self.heap_value = QLabel("0 KB")
        self.temperature_value = QLabel("0 °C")
        self.current_value = QLabel("0.00 A")
        self.speed_value = QLabel("0 RPM")

        cards = [
            ("CPU", self.cpu_value),
            ("RAM", self.ram_value),
            ("STACK", self.stack_value),
            ("HEAP", self.heap_value),
            ("TEMPERATURE", self.temperature_value),
            ("CURRENT", self.current_value),
            ("SPEED", self.speed_value),
        ]

        for index, (name, value_label) in enumerate(cards):
            card = QFrame()
            card.setFrameShape(QFrame.Box)

            card_layout = QVBoxLayout(card)

            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignCenter)

            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet(
                "font-size: 24px; font-weight: bold;"
            )

            card_layout.addWidget(name_label)
            card_layout.addWidget(value_label)

            row = index // 4
            column = index % 4

            cards_layout.addWidget(card, row, column)

        main_layout.addLayout(cards_layout)

        # =====================================================
        # System Performance Graph
        # =====================================================

        self.graph = pg.PlotWidget()

        self.graph.setTitle("REAL-TIME PERFORMANCE")
        self.graph.setLabel("left", "Usage")
        self.graph.setLabel("bottom", "Samples")
        self.graph.setYRange(0, 100)
        self.graph.showGrid(x=True, y=True)

        self.cpu_curve = self.graph.plot(name="CPU")
        self.ram_curve = self.graph.plot(name="RAM")
        self.stack_curve = self.graph.plot(name="STACK")
        self.heap_curve = self.graph.plot(name="HEAP")

        self.graph.addLegend()

        main_layout.addWidget(self.graph)

        # =====================================================
        # Temperature Graph
        # =====================================================

        self.temperature_graph = pg.PlotWidget()

        self.temperature_graph.setTitle("TEMPERATURE")
        self.temperature_graph.setLabel(
            "left",
            "Temperature",
            units="°C",
        )
        self.temperature_graph.setLabel(
            "bottom",
            "Samples",
        )
        self.temperature_graph.showGrid(
            x=True,
            y=True,
        )

        self.temperature_curve = self.temperature_graph.plot(
            name="Temperature"
        )


        # =====================================================
        # Current Graph
        # =====================================================

        self.current_graph = pg.PlotWidget()

        self.current_graph.setTitle("CURRENT")
        self.current_graph.setLabel(
            "left",
            "Current",
            units="A",
        )
        self.current_graph.setLabel(
            "bottom",
            "Samples",
        )
        self.current_graph.showGrid(
            x=True,
            y=True,
        )

        self.current_curve = self.current_graph.plot(
            name="Current"
        )


        # =====================================================
        # Speed Graph
        # =====================================================

        self.speed_graph = pg.PlotWidget()

        self.speed_graph.setTitle("SPEED")
        self.speed_graph.setLabel(
            "left",
            "Speed",
            units="RPM",
        )
        self.speed_graph.setLabel(
            "bottom",
            "Samples",
        )
        self.speed_graph.showGrid(
            x=True,
            y=True,
        )

        self.speed_curve = self.speed_graph.plot(
            name="Speed"
        )

        # =====================================================
        # Application Graph Layout
        # =====================================================

        application_graphs_layout = QGridLayout()

        application_graphs_layout.addWidget(
            self.temperature_graph, 0, 0
        )

        application_graphs_layout.addWidget(
            self.current_graph, 0, 1
        )

        application_graphs_layout.addWidget(
            self.speed_graph, 0, 2
        )

        main_layout.addLayout(application_graphs_layout)

        # =====================================================
        # Alerts
        # =====================================================

        alerts_frame = QFrame()
        alerts_frame.setFrameShape(QFrame.Box)

        alerts_layout = QVBoxLayout(alerts_frame)

        alerts_title = QLabel("ALERTS")
        alerts_title.setStyleSheet(
            "font-weight: bold;"
        )

        self.alerts_message = QLabel("No alerts")

        alerts_layout.addWidget(alerts_title)
        alerts_layout.addWidget(self.alerts_message)

        main_layout.addWidget(alerts_frame)

    # =========================================================
    # Simulation
    # =========================================================

    def toggle_monitoring(self):
        if self.timer.isActive():
            self.timer.stop()
            self.pause_button.setText("RESUME MONITORING")
        else:
            self.timer.start(1000)
            self.pause_button.setText("PAUSE MONITORING")

    def reset_graphs(self):
        self.cpu_data.clear()
        self.ram_data.clear()
        self.stack_data.clear()
        self.heap_data.clear()

        self.temperature_data.clear()
        self.current_data.clear()
        self.speed_data.clear()

        self.cpu_curve.clear()
        self.ram_curve.clear()
        self.stack_curve.clear()
        self.heap_curve.clear()

        self.temperature_curve.clear()
        self.current_curve.clear()
        self.speed_curve.clear()

    def start_simulation(self):
        self.timer = QTimer()
        self.timer.timeout.connect(
            self.update_simulated_telemetry
        )
        self.timer.start(1000)

    # =========================================================
    # Telemetry Update
    # =========================================================

    def update_simulated_telemetry(self):
        sample = self.telemetry_simulator.generate_sample()

        analysis = self.health_analyzer.analyze(sample)

        status = analysis["status"]
        alerts = analysis["alerts"]

        # ===== Update System Status =====

        self.status_label.setText(
            f"SYSTEM STATUS: {status}"
        )

        # ===== Update Alerts =====

        if alerts:
            self.alerts_message.setText(
                "\n".join(alerts)
            )
        else:
            self.alerts_message.setText(
                "No alerts"
            )

        # ===== Extract Telemetry =====

        cpu = sample["cpu"]
        ram = sample["ram"]
        stack = sample["stack"]
        heap = sample["heap"]
        temperature = sample["temperature"]
        current = sample["current"]
        speed = sample["speed"]

        # ===== Update Monitoring Cards =====

        self.cpu_value.setText(f"{cpu} %")
        self.ram_value.setText(f"{ram} %")
        self.stack_value.setText(f"{stack} %")
        self.heap_value.setText(f"{heap} KB")
        self.temperature_value.setText(
            f"{temperature} °C"
        )
        self.current_value.setText(
            f"{current:.2f} A"
        )
        self.speed_value.setText(
            f"{speed} RPM"
        )

        # ===== Store Telemetry =====

        self.cpu_data.append(cpu)
        self.ram_data.append(ram)
        self.stack_data.append(stack)
        self.heap_data.append(heap)
        self.temperature_data.append(temperature)
        self.current_data.append(current)
        self.speed_data.append(speed)

        # ===== Keep Last 60 Samples =====

        self.cpu_data = self.cpu_data[-self.max_points:]
        self.ram_data = self.ram_data[-self.max_points:]
        self.stack_data = self.stack_data[-self.max_points:]
        self.heap_data = self.heap_data[-self.max_points:]
        self.temperature_data = self.temperature_data[-self.max_points:]
        self.current_data = self.current_data[-self.max_points:]
        self.speed_data = self.speed_data[-self.max_points:]

        # ===== Update Graphs =====

        self.cpu_curve.setData(self.cpu_data)
        self.ram_curve.setData(self.ram_data)
        self.stack_curve.setData(self.stack_data)
        self.heap_curve.setData(self.heap_data)

        self.temperature_curve.setData(
            self.temperature_data
        )

        self.current_curve.setData(
            self.current_data
        )

        self.speed_curve.setData(
            self.speed_data
        )