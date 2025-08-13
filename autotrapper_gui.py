import sys
import asyncio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QInputDialog, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject

import autotrapper_gravity

class AsyncWorker(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(object)

    def __init__(self, coro):
        super().__init__()
        self.coro = coro

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.coro)
        self.result.emit(result)
        self.finished.emit()

class AutoTrapperGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoTrapper Gravity Control")
        self.setGeometry(200, 200, 350, 250)

        self.layout = QVBoxLayout()
        self.status_label = QLabel("Status: Not connected")
        self.layout.addWidget(self.status_label)

        self.connect_btn = QPushButton("Connect to Server")
        self.connect_btn.clicked.connect(self.connect_to_server)
        self.layout.addWidget(self.connect_btn)

        self.set_laser_btn = QPushButton("Set Laser Power")
        self.set_laser_btn.clicked.connect(self.set_laser_power)
        self.set_laser_btn.setEnabled(False)
        self.layout.addWidget(self.set_laser_btn)

        self.set_pressure_btn = QPushButton("Set Pressure")
        self.set_pressure_btn.clicked.connect(self.set_pressure)
        self.set_pressure_btn.setEnabled(False)
        self.layout.addWidget(self.set_pressure_btn)

        self.mainloop_btn = QPushButton("Run Main Loop")
        self.mainloop_btn.clicked.connect(self.run_mainloop)
        self.mainloop_btn.setEnabled(False)
        self.layout.addWidget(self.mainloop_btn)

        self.setLayout(self.layout)
        self.reader = None
        self.writer = None

    def run_async(self, coro, callback=None):
        self.thread = QThread()
        self.worker = AsyncWorker(coro)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        if callback:
            self.worker.result.connect(callback)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def connect_to_server(self):
        self.status_label.setText("Status: Connecting...")
        def on_connected(result):
            self.reader, self.writer = result
            autotrapper_gravity.reader = self.reader
            autotrapper_gravity.writer = self.writer
            self.status_label.setText("Status: Connected")
            self.set_laser_btn.setEnabled(True)
            self.set_pressure_btn.setEnabled(True)
            self.mainloop_btn.setEnabled(True)
        self.run_async(autotrapper_gravity.connect_to_server(), on_connected)

    def set_laser_power(self):
        lpow, ok = QInputDialog.getDouble(self, "Set Laser Power", "Laser Power (dBm):", 0.0, -60.0, 10.0, 2)
        if ok:
            self.run_async(autotrapper_gravity.setlaserpower_trap(lpow), lambda _: self.status_label.setText(f"Laser power set to {lpow}"))

    def set_pressure(self):
        press, ok = QInputDialog.getDouble(self, "Set Pressure", "Pressure (Torr):", 0.0, 0.0, 10.0, 6)
        if not ok:
            return
        slowroughing, ok2 = QInputDialog.getItem(self, "Slow Roughing", "Use Slow Roughing?", ["No", "Yes"], 0, False)
        if ok2:
            use_slow = (slowroughing == "Yes")
            self.run_async(autotrapper_gravity.setpressure(press, slowroughing=use_slow), lambda _: self.status_label.setText(f"Pressure set to {press}"))

    def run_mainloop(self):
        self.status_label.setText("Running main loop...")
        self.run_async(autotrapper_gravity.mainloop(), lambda _: self.status_label.setText("Main loop finished"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = AutoTrapperGUI()
    gui.show()
    sys.exit(app.exec_())
