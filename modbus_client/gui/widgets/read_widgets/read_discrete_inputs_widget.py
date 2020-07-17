from modbus_client.gui.widgets.read_widgets.default_read_widget import DefaultRWidget


class ReadDiscreteInputsWidget(DefaultRWidget):

    def __init__(self):
        super(ReadDiscreteInputsWidget, self).__init__()
        self.count_constraint = (1, 2000)
        self.firstAddress.setToolTip(
            f"Address of the first discrete input.\nValue between {self.address_constraint[0]} and {self.address_constraint[1]}.")
        self.count.setToolTip(
            f"Number of discrete inputs to be read.\nValue between {self.count_constraint[0]} and {self.count_constraint[1]}.")
        self.layout.addRow("First input address: ", self.firstAddress)
        self.layout.addRow("Input count: ", self.count)
        self.setLayout(self.layout)
