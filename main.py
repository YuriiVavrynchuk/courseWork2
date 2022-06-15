import glob
import sys
import threading

import serial
import mysql.connector

from datetime import datetime
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi

current_measurement_state = {
    'Potency': 0,
    'Temperature': 0,
    "Fire": False,
    "Smoke": False
}

is_active_led1 = False
is_active_led2 = False
is_active_led3 = False

global serial_ports
global current_serial_port


def get_serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def swap_bool(controller):
    return not controller


def get_temperature():
    if not current_serial_port.is_open:
        current_serial_port.open()
    current_serial_port.write(b'7')
    value = float(str(current_serial_port.readline())[2:-1])
    current_serial_port.close()
    return value


def get_potency():
    if not current_serial_port.is_open:
        current_serial_port.open()
    current_serial_port.write(b'8')
    value = int(str(current_serial_port.readline())[2:-1])
    current_serial_port.close()
    return value


def get_fire():
    if not current_serial_port.is_open:
        current_serial_port.open()
    current_serial_port.write(b'f')
    value = bool(int(str(current_serial_port.readline())[2:-1]))
    current_serial_port.close()
    return value


def get_smoke():
    if not current_serial_port.is_open:
        current_serial_port.open()
    current_serial_port.write(b's')
    value = bool(int(str(current_serial_port.readline())[2:-1]))
    current_serial_port.close()
    return value


def run_motor():
    try:
        if not current_serial_port.is_open:
            current_serial_port.open()
        current_serial_port.write(b'4')
        current_serial_port.close()
    except:
        print("Port is busy now. Wait untill data will be transmitted.")


def stop_motor():
    if not current_serial_port.is_open:
        current_serial_port.open()
    current_serial_port.write(b'6')
    current_serial_port.close()


def get_measurements():
    global current_measurement_state
    try:
        return {
            "Potency": get_potency(),
            "Temperature": get_temperature(),
            "Fire": get_fire(),
            "Smoke": get_smoke()
        }
    except:
        print("Port is busy now. Wait untill data will be transmitted.")
        return current_measurement_state


def update_measurements():
    global current_measurement_state
    current_measurement_state = get_measurements()


def post_mesurements(database, query_template, measurements):
    cursor = database.cursor()
    cursor.executemany(query_template, measurements)
    database.commit()


class Window(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("GUI.ui", self)
        self.setFixedSize(self.size())

        self.is_active_comport = False

        self.database = database
        self.query_template = "INSERT INTO `cursova`.`house_state` (`time`, `potency`, `temperature`, `is_fire`, " \
                              "`is_smoke`) VALUES (%s, %s, %s, %s, %s); "
        self.portcomboBox.addItems(serial_ports)
        self.portcomboBox.activated[str].connect(self.get_combobox_result)

        self.left_mottor_button.clicked.connect(run_motor)
        self.off_mottor_button.clicked.connect(stop_motor)

        self.get_report_button.clicked.connect(self.get_database_mesurements)

        self._update_timer = QtCore.QTimer()
        self._update_timer.timeout.connect(self.update_measurements_outputs)
        self._update_timer.start(10000)  # milliseconds

    def update_measurements_outputs(self):
        global current_measurement_state

        if self.is_active_comport:
            self.potency_text.setPlainText("Potency:\n" + str(current_measurement_state["Potency"]) + "W")
            self.temperature_text.setPlainText("Temperature:\n" + str(current_measurement_state["Temperature"]) + "K")

            if current_measurement_state["Fire"]:
                self.fire_flag.setStyleSheet("QWidget { background-color : rgb(255, 1, 1); }")
            else:
                self.fire_flag.setStyleSheet("QWidget { background-color :  rgb(85, 255, 0); }")

            if current_measurement_state["Smoke"]:
                self.smoke_flag.setStyleSheet("QWidget { background-color : rgb(255, 1, 1); }")
            else:
                self.smoke_flag.setStyleSheet("QWidget { background-color :  rgb(85, 255, 0); }")

            current_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            post_mesurements(self.database, self.query_template,
                             [(current_time,) + tuple(value for key, value in current_measurement_state.items())])

    def get_combobox_result(self):
        global current_serial_port
        current_serial_port = serial.Serial(self.portcomboBox.currentText(), 9600, timeout=2)

        self.is_active_comport = True
        timer.start()

    def closeEvent(self, event):
        timer.cancel()

    def get_database_mesurements(self):
        cursor = self.database.cursor()
        cursor.execute("select * from house_state order by id desc limit 5;")
        result = cursor.fetchall()
        header = ("Time", "Potency", "Temperature", "Fire alarm", "Smoke alarm")
        result = [header] + result
        final_text = str()
        for element in result:
            final_text = final_text + str(element) + "\n"
        self.get_report_text.setText(final_text)
        return result


class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
            print(' ')


timer = RepeatTimer(1, update_measurements)


def main():
    global serial_ports
    global database

    serial_ports = get_serial_ports()

    database = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database="cursova"
    )

    app = QApplication([])
    window = Window()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
