from faebryk.core.core import Module
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.Constant import Constant
from faebryk.library.Resistor import Resistor
from faebryk.library.UART_Base import UART_Base
from faebryk.libs.util import times


class UARTVoltageDropper(Module):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            uart_in = UART_Base()
            uart_out = UART_Base()

        self.IFs = _IFs(self)

        # voltage_drop = Constant(0.5)  # abs(
        # voltage_drop = abs(
        #   self.IFs.uart_in.get_trait(
        #       has_single_electric_reference
        #   ).get_reference().ConstraintVoltage
        #   - self.IFs.uart_out.get_trait(
        #       has_single_electric_reference
        #   ).get_reference()
        # )

        # TODO get from somewhere
        # current = Constant(0.001282)

        # components
        class _NODEs(Module.NODES()):
            voltage_drop_resistors = times(2, Resistor)

        self.NODEs = _NODEs(self)

        for res in self.NODEs.voltage_drop_resistors:
            res.PARAMs.resistance.merge(Constant(390))

        # TODO: set value for resistor in self.NODEs.voltage_drop_resistors:

        # connect uarts togerther on high level (signal only, not electrical)
        # TODO this breaks the electric connection with the resistors
        # self.IFs.uart_in.connect(
        #    self.IFs.uart_out,
        #    linkcls=LinkDirectShallow(
        #        lambda link, gif: not isinstance(gif.node, Electrical)
        #    ),
        # )

        # electrically connect via resistors
        # self.IFs.uart_in.IFs.rx.connect_via(
        #    self.NODEs.voltage_drop_resistors[0], self.IFs.uart_out.IFs.tx
        # )
        self.IFs.uart_in.IFs.rx.IFs.signal.connect(
            self.NODEs.voltage_drop_resistors[0].IFs.unnamed[0]
        )
        self.IFs.uart_out.IFs.tx.IFs.signal.connect(
            self.NODEs.voltage_drop_resistors[0].IFs.unnamed[1]
        )

        # self.IFs.uart_in.IFs.tx.connect_via(
        #    self.NODEs.voltage_drop_resistors[1], self.IFs.uart_out.IFs.rx
        # )
        self.IFs.uart_in.IFs.tx.IFs.signal.connect(
            self.NODEs.voltage_drop_resistors[1].IFs.unnamed[0]
        )
        self.IFs.uart_out.IFs.rx.IFs.signal.connect(
            self.NODEs.voltage_drop_resistors[1].IFs.unnamed[1]
        )

        self.add_trait(can_bridge_defined(self.IFs.uart_in, self.IFs.uart_out))
