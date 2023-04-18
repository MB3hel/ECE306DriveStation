"""
Copyright 2021 Marcus Behel

This file is part of ECE306-DriveStation.

ArPiRobot-DriveStation is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ArPiRobot-DriveStation is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with ECE306-DriveStation.  If not, see <https://www.gnu.org/licenses/>. 
"""

from PySide6.QtCore import QTime, QTimer, Qt
from PySide6.QtGui import QCloseEvent, QFontDatabase, QIntValidator
from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtNetwork import QAbstractSocket, QHostAddress, QTcpSocket, QUdpSocket
import sdl2
from gamepad import GamepadManager
from ui_drive_station import Ui_DriveStationWindow


class DriveStationWindow(QMainWindow):
    ############################################################################
    # UI stuff
    ############################################################################

    def __init__(self, parent = None) -> None:
        super().__init__(parent=parent)

        # UI Setup
        self.ui = Ui_DriveStationWindow()
        self.ui.setupUi(self)
        self.ui.txt_log.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.ui.txt_port.setValidator(QIntValidator(0, 65535, self))
        self.ui.txt_send_rate.setValidator(QIntValidator(1, 10000, self))

        # TCP client socket object(s)
        self.tcp_socket_timer = QTimer(self)
        self.tcp_socket = QTcpSocket(self)
        self.udp_socket = QUdpSocket(self)
        self.udp_alive = False

        # Gamepad data
        self.gamepad_manager = GamepadManager(mappings_file=":/gamecontrollerdb.txt")
        self.send_data_timer = QTimer(self)
        self.update_gamepad_ui_timer = QTimer(self)

        # On some systems, progress bars will only repaint progress bar every several pixels, leading to choppy motion
        # To fix this, force a repaint to happen every time the value changes
        self.force_instant_pbar_updates()

        # Signal / slot setup
        self.ui.btn_connect.clicked.connect(self.connect_clicked)
        self.ui.btn_disconnect.clicked.connect(self.disconnect_clicked)
        self.ui.btn_clear_log.clicked.connect(lambda: self.ui.txt_log.setPlainText(""))
        self.ui.txt_send_rate.editingFinished.connect(self.send_rate_changed)

        self.tcp_socket.connected.connect(self.network_connected)
        self.tcp_socket.disconnected.connect(self.network_disconnected)
        self.tcp_socket.readyRead.connect(self.network_read_ready)
        self.udp_socket.readyRead.connect(self.network_read_ready)
        self.tcp_socket.errorOccurred.connect(self.network_error)

        self.tcp_socket_timer.timeout.connect(self.network_connect_timeout)

        self.gamepad_manager.connected.connect(self.gamepad_connected)
        self.gamepad_manager.disconnected.connect(self.gamepad_disconnected)

        self.send_data_timer.timeout.connect(self.send_gamepad_data)

        self.update_gamepad_ui_timer.timeout.connect(self.update_gamepad_indicators)

        # Start things
        self.gamepad_manager.start()
        self.send_data_timer.start(int(self.ui.txt_send_rate.text()))
        self.update_gamepad_ui_timer.start(16)   # ~60FPS
    
    def force_instant_pbar_updates(self):
        self.ui.pbar_lx.valueChanged.connect(self.ui.pbar_lx.update)
        self.ui.pbar_ly.valueChanged.connect(self.ui.pbar_ly.update)
        self.ui.pbar_rx.valueChanged.connect(self.ui.pbar_rx.update)
        self.ui.pbar_ry.valueChanged.connect(self.ui.pbar_ry.update)
        self.ui.pbar_a.valueChanged.connect(self.ui.pbar_a.update)
        self.ui.pbar_b.valueChanged.connect(self.ui.pbar_b.update)
        self.ui.pbar_x.valueChanged.connect(self.ui.pbar_x.update)
        self.ui.pbar_y.valueChanged.connect(self.ui.pbar_y.update)

    def ui_state_connecting(self):
        self.ui.txt_ip.setEnabled(False)
        self.ui.txt_port.setEnabled(False)
        self.ui.btn_connect.setEnabled(False)
        self.ui.btn_disconnect.setEnabled(False)
        self.ui.cbo_mode.setEnabled(False)
    
    def ui_state_connected(self):
        self.ui.txt_ip.setEnabled(False)
        self.ui.txt_port.setEnabled(False)
        self.ui.btn_connect.setEnabled(False)
        self.ui.btn_disconnect.setEnabled(True)
        self.ui.cbo_mode.setEnabled(False)

    def ui_state_disconnected(self):
        self.ui.txt_ip.setEnabled(True)
        self.ui.txt_port.setEnabled(True)
        self.ui.btn_connect.setEnabled(True)
        self.ui.btn_disconnect.setEnabled(False)
        self.ui.cbo_mode.setEnabled(True)
        

    ############################################################################
    # UI event slots
    ############################################################################

    def connect_clicked(self):
        ip = QHostAddress()

        if not ip.setAddress(self.ui.txt_ip.text()):
            self.log("DS", "Invalid IP address.")
            return

        try:
            port = int(self.ui.txt_port.text())
            if(port > 65535):
                raise Exception("Invalid port number")
        except:
            # Invalid port
            self.log("DS", "Invalid port number.")
            return

        if self.ui.cbo_mode.currentText() == "TCP":
            self.log("DS", f"Connecting to {ip.toString()}:{port}...")
            self.ui_state_connecting()
            self.tcp_socket.connectToHost(ip, port)
            self.tcp_socket_timer.start(5000)
        else:
            self.log("DS", "WARNING using UDP. Concept of a connection is meaningless.")
            self.log("DS", f"Connecting to {ip.toString()}:{port}...")
            self.udp_alive = True
            self.network_connected()

    def disconnect_clicked(self):
        if self.ui.cbo_mode.currentText() == "TCP":
            self.tcp_socket.disconnectFromHost()
        else:
            self.udp_alive = False
            self.network_disconnected()

    def send_rate_changed(self):
        rate = int(self.ui.txt_send_rate.text())
        self.send_data_timer.stop()
        self.send_data_timer.start(rate)

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        res = QMessageBox.question(self, "Exit Confirmation", 
            "Are you sure you want to exit?", QMessageBox.Yes | QMessageBox.No)
        if(res == QMessageBox.Yes):
            event.accept()

    ############################################################################
    # Networking slots
    ############################################################################

    def network_connect_timeout(self):
        self.log("DS", "Connect timed out.")
        self.tcp_socket_timer.stop()
        self.tcp_socket.disconnectFromHost()
        self.ui_state_disconnected()

    def network_connected(self):
        self.tcp_socket_timer.stop()
        self.log("DS", "Connected.")
        self.ui_state_connected()

    def network_disconnected(self):
        self.log("DS", "Disconnected.")
        self.ui_state_disconnected()
    
    def network_error(self, socket_error: QAbstractSocket.SocketError):
        if socket_error == QAbstractSocket.SocketError.RemoteHostClosedError:
            # Only applies for TCP
            self.log("DS", "Connection lost.")

    def network_read_ready(self):
        if self.ui.cbo_mode.currentText() == "TCP":
            self.log("Car", bytes(self.tcp_socket.readAll()).decode())
        elif self.udp_alive:
            datagram = self.udp_socket.receiveDatagram()
            if(datagram.senderAddress().isEqual(QHostAddress(self.ui.txt_ip.text()))):
                self.log("Car", bytes(datagram.data()).decode())

    def network_send_to_car(self, msg: bytearray):
        if self.ui.cbo_mode.currentText() == "TCP":
            if self.tcp_socket.state() == QAbstractSocket.SocketState.ConnectedState:
                self.tcp_socket.write(msg)
        elif self.udp_alive:
            self.udp_socket.writeDatagram(msg, QHostAddress(self.ui.txt_ip.text()), int(self.ui.txt_port.text()))

    ############################################################################
    # Gamepad slots
    ############################################################################

    def gamepad_connected(self, device_id: int, device_name: str):
        self.ui.cbo_controllers.addItem(device_name, device_id)

    def gamepad_disconnected(self, device_id: int):
        for i in range(self.ui.cbo_controllers.count()):
            curr_id = self.ui.cbo_controllers.itemData(i, Qt.UserRole)
            if(curr_id == device_id):
                self.ui.cbo_controllers.removeItem(i)
    
    def update_gamepad_indicators(self):
        self.gamepad_manager.update()

        selected_idx = self.ui.cbo_controllers.currentIndex()
        dev_id = self.ui.cbo_controllers.itemData(selected_idx) if selected_idx != -1 else -1

        # First, update what is shown on the progress bars
        if selected_idx == -1:
            self.ui.pbar_lx.setValue(0)
            self.ui.pbar_ly.setValue(0)
            self.ui.pbar_rx.setValue(0)
            self.ui.pbar_ry.setValue(0)
            self.ui.pbar_a.setValue(0)
            self.ui.pbar_b.setValue(0)
            self.ui.pbar_x.setValue(0)
            self.ui.pbar_y.setValue(0)
        else:
            self.ui.pbar_lx.setValue(self.gamepad_manager.get_axis(dev_id, sdl2.SDL_CONTROLLER_AXIS_LEFTX))
            self.ui.pbar_ly.setValue(self.gamepad_manager.get_axis(dev_id, sdl2.SDL_CONTROLLER_AXIS_LEFTY))
            self.ui.pbar_rx.setValue(self.gamepad_manager.get_axis(dev_id, sdl2.SDL_CONTROLLER_AXIS_RIGHTX))
            self.ui.pbar_ry.setValue(self.gamepad_manager.get_axis(dev_id, sdl2.SDL_CONTROLLER_AXIS_RIGHTY))
            self.ui.pbar_a.setValue(1 if self.gamepad_manager.get_button(dev_id, sdl2.SDL_CONTROLLER_BUTTON_A) else 0)
            self.ui.pbar_b.setValue(1 if self.gamepad_manager.get_button(dev_id, sdl2.SDL_CONTROLLER_BUTTON_B) else 0)
            self.ui.pbar_x.setValue(1 if self.gamepad_manager.get_button(dev_id, sdl2.SDL_CONTROLLER_BUTTON_X) else 0)
            self.ui.pbar_y.setValue(1 if self.gamepad_manager.get_button(dev_id, sdl2.SDL_CONTROLLER_BUTTON_Y) else 0)

    def send_gamepad_data(self):
        # Already done at a faster rate in update_gamepad_indicators
        # self.gamepad_manager.update()

        selected_idx = self.ui.cbo_controllers.currentIndex()
        dev_id = self.ui.cbo_controllers.itemData(selected_idx) if selected_idx != -1 else -1 

        # Note: the car's data processing is very primitive. 
        # YOU CANNOT SEND A NEWLINE OR CARRIAGE RETURN!
        # ASCII 10 and ASCII 13

        # Data format:
        # ^[KEY]C[LX][LY][RX][RY][A][B][X][Y]
        #   Each axis's (LX, LY, RX, RY) value is sent as a single character
        #   Value is from 32 to 95 (64 values) where 32 = -100% and 95 = 100%
        #   0% = 64 = ASCII @
        #   
        #   Each button's value is sent as a single character
        #   T = True = Pressed. F = False = Not Pressed

        data = bytearray()
        data.extend(b'^')
        data.extend(self.ui.txt_key.text().encode())
        data.extend(b'C')

        if(selected_idx == -1):
            # Send zero data
            data.extend(b'@@@@FFFF')
        else:
            # Send actual data
            data.append(self.encode_axis_value(self.gamepad_manager.get_axis(dev_id, sdl2.SDL_CONTROLLER_AXIS_LEFTX)))
            data.append(self.encode_axis_value(self.gamepad_manager.get_axis(dev_id, sdl2.SDL_CONTROLLER_AXIS_LEFTY)))
            data.append(self.encode_axis_value(self.gamepad_manager.get_axis(dev_id, sdl2.SDL_CONTROLLER_AXIS_RIGHTX)))
            data.append(self.encode_axis_value(self.gamepad_manager.get_axis(dev_id, sdl2.SDL_CONTROLLER_AXIS_RIGHTY)))
            data.extend(b'T' if self.gamepad_manager.get_button(dev_id, sdl2.SDL_CONTROLLER_BUTTON_A) else b'F')
            data.extend(b'T' if self.gamepad_manager.get_button(dev_id, sdl2.SDL_CONTROLLER_BUTTON_B) else b'F')
            data.extend(b'T' if self.gamepad_manager.get_button(dev_id, sdl2.SDL_CONTROLLER_BUTTON_X) else b'F')
            data.extend(b'T' if self.gamepad_manager.get_button(dev_id, sdl2.SDL_CONTROLLER_BUTTON_Y) else b'F')

        self.network_send_to_car(data)

    ############################################################################
    # Helper functions
    ############################################################################

    def encode_axis_value(self, axis_val: int)->int:
        # Convert axis value [-32768, 32767] to encoded version [32, 96]
        axis_val += 32768       # Convert to unsigned [0, 655365]
        axis_val >>= 10         # Bitshift division down to 6 bits [0, 64]
        axis_val += 32          # Linear shift [32, 96]
        return axis_val

    def log(self, src: str, msg: str):
        self.ui.txt_log.setPlainText(f"{self.ui.txt_log.toPlainText()}[{src}]: {msg}\n")
        self.ui.txt_log.verticalScrollBar().setValue(self.ui.txt_log.verticalScrollBar().maximum())