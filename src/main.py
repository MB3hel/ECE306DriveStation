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

import sys
from contextlib import redirect_stdout

from PySide6.QtWidgets import QApplication, QStyleFactory
from drive_station import DriveStationWindow

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.mbehel.ece306-drivestation")
except AttributeError:
    pass

app = QApplication(sys.argv)
ds = DriveStationWindow()
ds.show()
app.exec()