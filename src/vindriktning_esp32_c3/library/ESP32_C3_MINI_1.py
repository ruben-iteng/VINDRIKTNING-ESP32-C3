import logging

from faebryk.core.core import Module, ModuleInterface, ModuleInterfaceTrait
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.Capacitor import Capacitor
from faebryk.library.Electrical import Electrical
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_datasheet_defined import has_datasheet_defined
from faebryk.library.has_defined_type_description import has_defined_type_description
from faebryk.library.has_esphome_config import (
    has_esphome_config_defined,
    is_esphome_bus,
    has_esphome_config,
)
from faebryk.library.TBD import TBD
from faebryk.library.Constant import Constant
from faebryk.library.UART_Base import UART_Base
from faebryk.library.USB2_0 import USB2_0
from faebryk.libs.util import times

logger = logging.getLogger(__name__)


class ESP32_C3_MINI_1_VIND(Module):
    """ESP32-C3-MINI-1 with only Vindrikting project relevant interfaces"""

    def __init__(self) -> None:
        super().__init__()

        class _NODEs(Module.NODES()):
            decoupling_cap = Capacitor(TBD())

        self.NODEs = _NODEs(self)

        class _IFs(Module.IFS()):
            gnd = times(22, Electrical)
            pwr3v3 = ElectricPower()
            usb = USB2_0()
            gpio = times(22, ElectricLogic)  # 11-19 not connected
            enable = ElectricLogic()
            serial = times(2, UART_Base)

        self.IFs = _IFs(self)

        x = self.IFs

        self.pinmap_default = {
            "1": x.gnd[0],
            "2": x.gnd[1],
            "3": x.pwr3v3.NODEs.hv,
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
            "30": x.gpio[20].NODEs.signal,
            "31": x.gpio[21].NODEs.signal,
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
        self.pinmap = dict(self.pinmap_default)

        self.add_trait(can_attach_to_footprint_via_pinmap(self.pinmap))

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

        self.IFs.pwr3v3.decouple(self.NODEs.decoupling_cap)

        self.add_trait(has_defined_type_description("U"))

        self.add_trait(
            has_datasheet_defined(
                "https://www.espressif.com/sites/default/files/russianDocumentation/esp32-c3-mini-1_datasheet_en.pdf"
            )
        )
        # self.add_trait(has_datasheet_defined("https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf"))

        self.set_mux(x.gpio[20], self.IFs.serial[1].NODEs.rx)
        self.set_mux(x.gpio[21], self.IFs.serial[1].NODEs.tx)

        class _uart_esphome_config(has_esphome_config.impl()):
            def get_config(self_) -> dict:
                assert isinstance(self, ESP32_C3_MINI_1_VIND)
                obj = self_.get_obj()
                assert isinstance(obj, UART_Base)
                index = self.IFs.serial.index(obj)

                config = {
                    "uart": [
                        {
                            "id": f"uart_{index}",
                            "baud_rate": obj.baud,
                        }
                    ]
                }

                try:
                    config["uart"][0]["rx_pin"] = self.get_mux_pin(obj.NODEs.rx)[1]
                except IndexError:
                    ...

                try:
                    config["uart"][0]["tx_pin"] = self.get_mux_pin(obj.NODEs.tx)[1]
                except IndexError:
                    ...

                # if no rx/tx pin is set, then not in use
                if set(config["uart"][0].keys()).isdisjoint({"rx_pin", "tx_pin"}):
                    return {}

                return config

        for serial in self.IFs.serial:
            serial.add_trait(is_esphome_bus.impl()())
            serial.add_trait(_uart_esphome_config())

        self.add_trait(
            has_esphome_config_defined(
                {
                    "esp32": {
                        "board": "Espressif ESP32-C3-DevKitM-1",
                        "variant": "esp32c3",
                        "framework": {
                            "type": "esp-idf",
                            "version": "recommended",
                        },
                    },
                }
            )
        )

    # very simple mux that uses pinmap
    def set_mux(self, gpio: ElectricLogic, target: ElectricLogic):
        """Careful not checked"""

        pin, _ = self.get_mux_pin(gpio)
        self.pinmap[pin] = target.NODEs.signal

    def get_mux_pin(self, target: ElectricLogic) -> tuple[str, int]:
        """Returns pin & gpio number"""

        pin = [k for k, v in self.pinmap.items() if v == target.NODEs.signal][0]
        gpio = self.pinmap_default[pin]
        gpio_index = [i for i, g in enumerate(self.IFs.gpio) if g.NODEs.signal == gpio][
            0
        ]

        return pin, gpio_index
