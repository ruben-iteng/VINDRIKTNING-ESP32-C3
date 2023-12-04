import logging
from typing import Any

from faebryk.core.core import Module
from faebryk.core.util import connect_to_all_interfaces, get_parameter_max
from faebryk.library.can_attach_to_footprint_via_pinmap import (
    can_attach_to_footprint_via_pinmap,
)
from faebryk.library.Capacitor import Capacitor
from faebryk.library.Constant import Constant
from faebryk.library.Electrical import Electrical
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_datasheet_defined import has_datasheet_defined
from faebryk.library.has_defined_type_description import has_defined_type_description
from faebryk.library.has_esphome_config import (
    has_esphome_config,
    has_esphome_config_defined,
    is_esphome_bus,
    is_esphome_bus_defined,
)
from faebryk.library.has_single_electric_reference_defined import (
    has_single_electric_reference_defined,
)
from faebryk.library.I2C import I2C
from faebryk.library.Range import Range
from faebryk.library.Resistor import Resistor
from faebryk.library.Set import Set
from faebryk.library.Switch import Switch
from faebryk.library.UART_Base import UART_Base
from faebryk.library.USB2_0 import USB2_0
from faebryk.libs.units import k, n, u
from faebryk.libs.util import times

logger = logging.getLogger(__name__)


class ESP32_C3_MINI_1_VIND(Module):
    """ESP32-C3-MINI-1 with only Vindrikting project relevant interfaces"""

    def __init__(self) -> None:
        super().__init__()

        class _NODEs(Module.NODES()):
            pwr_3v3_decoupling_caps = [
                Capacitor(Constant(100 * n)),
                Capacitor(Constant(10 * u)),
            ]
            en_rc_capacitor = Capacitor(Constant(1 * u))
            en_rc_resesitor = Resistor(Constant(10 * k))
            boot_resistors = times(2, lambda: Resistor(Constant(10 * k)))
            # TODO make a debounced switch
            switches = times(2, lambda: Switch(Electrical)())
            debounce_capacitors = times(2, lambda: Capacitor(Constant(100 * n)))
            debounce_resistors = times(2, lambda: Resistor(Constant(10 * k)))

        self.NODEs = _NODEs(self)

        class _IFs(Module.IFS()):
            gnd = times(22, Electrical)
            pwr3v3 = ElectricPower()
            usb = USB2_0()
            i2c = I2C()
            gpio = times(22, ElectricLogic)  # 11-19 not connected
            enable = ElectricLogic()
            serial = times(2, UART_Base)
            boot_mode = ElectricLogic()

        self.IFs = _IFs(self)

        x = self.IFs

        # connect all logic references
        ref = ElectricLogic.connect_all_module_references(self)
        self.add_trait(has_single_electric_reference_defined(ref))

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
            # 24 is missing #TODO
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

        # connect all grounds to eachother and power
        connect_to_all_interfaces(self.IFs.pwr3v3.NODEs.lv, self.IFs.gnd)

        # connect power decoupling caps
        for cap in self.NODEs.pwr_3v3_decoupling_caps:
            self.IFs.pwr3v3.decouple(cap)

        # rc delay circuit on enable pin for startup delay
        # https://www.espressif.com/sites/default/files/russianDocumentation/esp32-c3-mini-1_datasheet_en.pdf page 24
        self.IFs.enable.NODEs.signal.connect_via(
            self.NODEs.en_rc_capacitor, self.IFs.pwr3v3.NODEs.lv
        )
        self.IFs.enable.pull_up(self.NODEs.en_rc_resesitor)

        # set default boot mode to "SPI Boot mode" (gpio = N.C. or HIGH)
        # https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf page 25
        self.IFs.gpio[8].pull_up(self.NODEs.boot_resistors[0])
        self.IFs.gpio[2].pull_up(self.NODEs.boot_resistors[1])
        self.IFs.gpio[9].connect(
            self.IFs.boot_mode
        )  # ESP32-c3 defaults to pull-up at boot = SPI-Boot

        # boot and enable switches
        for i, switch in enumerate(self.NODEs.switches):
            self.IFs.enable.NODEs.signal.connect_via(
                [self.NODEs.debounce_resistors[i], switch],
                self.IFs.pwr3v3.NODEs.lv,
            )
            switch.IFs.unnamed[0].connect_via(
                self.NODEs.debounce_capacitors[i], switch.IFs.unnamed[1]
            )

        self.add_trait(has_defined_type_description("U"))

        self.add_trait(
            has_datasheet_defined(
                "https://www.espressif.com/sites/default/files/russianDocumentation/esp32-c3-mini-1_datasheet_en.pdf"
            )
        )
        # self.add_trait(has_datasheet_defined("https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf"))

        # set mux states
        # UART 1
        self.set_mux(x.gpio[20], self.IFs.serial[1].NODEs.rx)
        self.set_mux(x.gpio[21], self.IFs.serial[1].NODEs.tx)
        # UART 0
        self.set_mux(x.gpio[0], self.IFs.serial[0].NODEs.rx)
        self.set_mux(x.gpio[1], self.IFs.serial[0].NODEs.tx)

        # I2C
        self.set_mux(x.gpio[4], self.IFs.i2c.NODEs.scl)
        self.set_mux(x.gpio[5], self.IFs.i2c.NODEs.sda)

        class _uart_esphome_config(has_esphome_config.impl()):
            def get_config(self_) -> dict:
                assert isinstance(self, ESP32_C3_MINI_1_VIND)
                obj = self_.get_obj()
                assert isinstance(obj, UART_Base)

                config = {
                    "uart": [
                        {
                            "id": obj.get_trait(is_esphome_bus).get_bus_id(),
                            "baud_rate": get_parameter_max(obj.baud),
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

        class _i2c_esphome_config(has_esphome_config.impl()):
            def get_config(self_) -> dict:
                assert isinstance(self, ESP32_C3_MINI_1_VIND)
                obj = self_.get_obj()
                assert isinstance(obj, I2C)

                try:
                    sda = self.get_mux_pin(obj.NODEs.sda)[1]
                    scl = self.get_mux_pin(obj.NODEs.scl)[1]
                except IndexError:
                    # Not in use if pinmux is not set
                    return {}

                config = {
                    "i2c": [
                        {
                            "id": obj.get_trait(is_esphome_bus).get_bus_id(),
                            "frequency": int(get_parameter_max(obj.frequency)),
                            "sda": sda,
                            "scl": scl,
                        }
                    ]
                }

                return config

        for serial in self.IFs.serial:
            serial.add_trait(
                is_esphome_bus_defined(f"uart_{self.IFs.serial.index(serial)}")
            )
            serial.add_trait(_uart_esphome_config())

        for i, gpio in enumerate(self.IFs.gpio):
            gpio.add_trait(is_esphome_bus_defined(f"GPIO{i}"))

        self.IFs.i2c.add_trait(is_esphome_bus_defined("i2c_0"))
        self.IFs.i2c.add_trait(_i2c_esphome_config())
        self.IFs.i2c.set_frequency(
            Set(
                [
                    I2C.define_max_frequency_capability(speed)
                    for speed in [
                        I2C.SpeedMode.low_speed,
                        I2C.SpeedMode.standard_speed,
                    ]
                ]
                + [Range(200 * k, 800 * k)],
            )
        )

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
