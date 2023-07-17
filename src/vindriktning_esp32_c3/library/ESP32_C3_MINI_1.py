import logging

from faebryk.core.core import Module
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.Capacitor import Capacitor
from faebryk.library.Electrical import Electrical
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_defined_type_description import has_defined_type_description
from faebryk.library.TBD import TBD
from faebryk.library.UART_Base import UART_Base
from faebryk.library.USB2_0 import USB2_0
from faebryk.libs.util import times

logger = logging.getLogger(__name__)


class ESP32_C3_MINI_1(Module):
    def __init__(self) -> None:
        super().__init__()

        class _NODEs(Module.NODES()):
            decoupling_cap = Capacitor(TBD())

        self.NODEs = _NODEs(self)

        class _IFs(Module.IFS()):
            gnd = times(21, Electrical)
            pwr3v3 = Electrical()
            power = ElectricPower()
            usb = USB2_0()
            gpio = times(11, ElectricLogic)
            enable = ElectricLogic()
            serial = UART_Base()

        self.IFs = _IFs(self)

        x = self.IFs
        self.add_trait(
            can_attach_to_footprint_via_pinmap(
                {
                    "1": x.gnd[0],
                    "2": x.gnd[1],
                    "3": x.pwr3v3,
                    "5": x.gpio[2].NODEs.signal,
                    "6": x.gpio[3].NODEs.signal,
                    "8": x.enable.NODEs.signal,
                    "11": x.gnd[2],
                    "12": x.gpio[0].NODEs.signal,
                    "13": x.gpio[1].NODEs.signal,
                    "14": x.gnd[3],
                    "16": x.gpio[10].NODEs.signal,
                    "18": x.gpio[4].NODEs.signal,
                    "19": x.gpio[5].NODEs.signal,
                    "20": x.gpio[6].NODEs.signal,
                    "21": x.gpio[7].NODEs.signal,
                    "22": x.gpio[8].NODEs.signal,
                    "23": x.gpio[9].NODEs.signal,
                    "26": x.usb.NODEs.d.NODEs.n,
                    "27": x.usb.NODEs.d.NODEs.p,
                    "30": x.serial.NODEs.rx.NODEs.signal,
                    "31": x.serial.NODEs.tx.NODEs.signal,
                    "36": x.gnd[4],
                    "37": x.gnd[5],
                    "38": x.gnd[6],
                    "39": x.gnd[7],
                    "40": x.gnd[8],
                    "41": x.gnd[9],
                    "42": x.gnd[10],
                    "43": x.gnd[11],
                    "44": x.gnd[12],
                    "45": x.gnd[13],
                    "46": x.gnd[14],
                    "47": x.gnd[15],
                    "48": x.gnd[16],
                    "49": x.gnd[17],
                    "50": x.gnd[18],
                    "51": x.gnd[19],
                    "52": x.gnd[20],
                    "53": x.gnd[21],
                }
            )
        )

        # connect_all_interfaces(
        #    list(
        #        [e.NODEs.reference for e in self.IFs.gpio]
        #        + [
        #            self.IFs.power,
        #            self.IFs.nwc.NODEs.reference,
        #            self.IFs.data.NODEs.sda.NODEs.reference,
        #        ]
        #    )
        # )

        self.IFs.power.decouple(self.NODEs.decoupling_cap)

        self.add_trait(has_defined_type_description("U"))
