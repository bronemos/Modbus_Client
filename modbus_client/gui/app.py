import sys

from modbus_client.gui.style.custom_elements import *
from modbus_client.gui.widgets import *
from modbus_client.gui.widgets import RequestWidget
from modbus_client.resources.codes import Codes


class Application(QMainWindow):
    connected = False
    transaction_id = 0

    def __init__(self, state_manager, parent=None):
        QMainWindow.__init__(self, parent)

        self.state_manager = state_manager
        self.state_manager.update.connect(self.update_gui)

        self.mainWidget = QWidget()

        self.HomeWidget = HomeWidget()
        self.HomeWidget.connect_button.clicked.connect(self._connect_disconnect)
        self.HomeWidget.historian_button.clicked.connect(self._switch_to_historian)
        self.HomeWidget.live_button.clicked.connect(self._switch_to_live)

        layout = QVBoxLayout()
        layout.addWidget(self.HomeWidget)

        self.reqWidget = RequestWidget('manual')
        self.reqWidget.setEnabled(self.connected)
        self.reqWidget.sendButton.clicked.connect(self._validate_and_queue)

        self.resWidget = QGroupBox('RESPONSE')
        self.resWidget.setEnabled(self.connected)
        self.res_message = QLabel()
        self.res_message.setAlignment(Qt.AlignCenter)
        reslayout = QVBoxLayout()
        reslayout.addWidget(self.res_message)
        self.resWidget.setAlignment(Qt.AlignCenter)
        self.resWidget.setLayout(reslayout)

        self.requestLogWidget = RequestLogWidget()

        self.responseLogWidget = ResponseLogWidget()

        self.mainScrollWidget = QScrollArea()
        self.mainScrollWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.mainScrollWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.mainScrollWidget.setWidgetResizable(True)

        self.reqresWidget = QWidget()
        reqresLayout = QGridLayout()
        reqresLayout.setRowStretch(0, 1)
        reqresLayout.setRowStretch(1, 1)
        reqresLayout.setColumnStretch(0, 1)
        reqresLayout.setColumnStretch(1, 1)
        reqresLayout.setRowMinimumHeight(0, 200)
        reqresLayout.setRowMinimumHeight(1, 500)
        reqresLayout.addWidget(self.reqWidget, 0, 0, 1, 1)
        reqresLayout.addWidget(self.resWidget, 0, 1, 1, -1)
        reqresLayout.addWidget(self.requestLogWidget, 1, 0, -1, 1)
        reqresLayout.addWidget(self.responseLogWidget, 1, 1, -1, -1)
        self.reqresWidget.setLayout(reqresLayout)

        self.mainScrollWidget.setWidget(self.reqresWidget)
        self.historianWidget = HistorianWidget()
        self.liveViewWidget = LiveViewWidget(self.state_manager.req_queue)

        self.centerWidget = QStackedWidget()
        self.centerWidget.addWidget(self.mainScrollWidget)
        self.centerWidget.addWidget(self.historianWidget)
        self.centerWidget.addWidget(self.liveViewWidget)

        layout.addWidget(self.centerWidget)

        self.mainWidget.setLayout(layout)
        self.setCentralWidget(self.mainWidget)

    def _connect_disconnect(self):
        if not self.connected:
            self.HomeWidget.connect_button.setEnabled(self.connected)
            self.reqWidget.setEnabled(self.connected)
            self.resWidget.setEnabled(self.connected)
            self.HomeWidget.connect_button.setText('Connecting...')
            self.HomeWidget.indicator.setMovie(self.HomeWidget.connecting_movie)
            self.state_manager.run_loop()
        else:
            self.state_manager.req_queue.put('DC')
            self.update_gui('DC')

    def _switch_to_historian(self):
        if self.centerWidget.currentWidget() != self.historianWidget:
            self.historianWidget.load(self.state_manager.db)
            self.centerWidget.setCurrentWidget(self.historianWidget)
        else:
            self.centerWidget.setCurrentWidget(self.mainScrollWidget)

    def _switch_to_live(self):
        if self.centerWidget.currentWidget() != self.liveViewWidget:
            self.centerWidget.setCurrentWidget(self.liveViewWidget)
        else:
            self.centerWidget.setCurrentWidget(self.mainScrollWidget)

    def _validate_and_queue(self):
        try:
            unit_address = int(self.reqWidget.unitAddress.text())
        except ValueError:
            ErrorDialog(self, 'Incorrect unit address value.')
            return

        if not self.reqWidget.stackedRequestWidget.currentWidget().validate_input(self):
            return

        message = self.reqWidget.stackedRequestWidget.currentWidget().generate_message(self.transaction_id, unit_address)
        self.requestLogWidget.update_log(message)

        print(message)
        self.transaction_id += 1
        self.state_manager.req_queue.put(message)

    def update_gui(self, message):
        print('this is msg', message)
        if message == 'ACK':
            self.connected = True
            self.HomeWidget.connect_button.setEnabled(True)
            self.reqWidget.setEnabled(self.connected)
            self.resWidget.setEnabled(self.connected)
            self.HomeWidget.connect_button.setText('Disconnect')
            self.HomeWidget.indicator.setMovie(self.HomeWidget.connected_movie)
            self.liveViewWidget.counter.start()
            return
        elif message == 'DC' or message == 1000:
            self.connected = False
            self.HomeWidget.connect_button.setEnabled(True)
            self.reqWidget.setEnabled(self.connected)
            self.resWidget.setEnabled(self.connected)
            self.HomeWidget.connect_button.setText('Connect')
            self.HomeWidget.indicator.setMovie(self.HomeWidget.disconnected_movie)
            self.liveViewWidget.counter.requestInterruption()
            return
        self.responseLogWidget.update_log(message)
        current_selection = getattr(Codes, self.reqWidget.dropdown.currentText().replace(' ', '_')).value
        if current_selection == 1:
            self.res_message.setText(f"Coils set are: {','.join(message['set_list'])}" if len(message['set_list'])
                                     else 'No coils are set')
        elif current_selection == 2:
            self.res_message.setText(
                f"Discrete inputs status: {','.join(message['set_list'])}" if len(message['set_list'])
                else 'No discrete inputs are set.')
        elif current_selection == 3:
            self.res_message.setText(f"Holding registers data: {','.join(message['register_data'])}")
        elif current_selection == 4:
            self.res_message.setText(f"Input registers data: {','.join(message['register_data'])}")


def run_gui(state_manager):
    app = QApplication()
    app.setApplicationDisplayName('Modbus Client GUI')
    app.setStyle('fusion')
    mainWindow = Application(state_manager)
    p = mainWindow.palette()
    p.setColor(mainWindow.backgroundRole(), Qt.white)
    mainWindow.setPalette(p)
    mainWindow.setMinimumSize(1400, 800)
    mainWindow.show()
    sys.exit(app.exec_())
