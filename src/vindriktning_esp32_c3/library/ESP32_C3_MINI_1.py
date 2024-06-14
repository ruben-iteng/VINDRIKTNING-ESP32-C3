import logging

import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.core.util import connect_to_all_interfaces, get_parameter_max
from faebryk.libs.units import k, n, u
from faebryk.libs.util import times

logger = logging.getLogger(__name__)


class ESP32_C3_MINI_1_VIND(Module):
    """ESP32-C3-MINI-1 with only Vindrikting project relevant interfaces"""

    def __init__(self) -> None:
        super().__init__()

        class _NODEs(Module.NODES()):
            en_rc_capacitor = F.Capacitor()
            # en_rc_resistor = F.Resistor()
            # boot_resistors = times(2, F.Resistor)
            # TODO make a debounced switch
            switches = times(2, F.Switch(F.Electrical))
            debounce_capacitors = times(2, F.Capacitor)
            debounce_resistors = times(2, F.Resistor)

        self.NODEs = _NODEs(self)

        class _IFs(Module.IFS()):
            gnd = times(22, F.Electrical)
            pwr3v3 = F.ElectricPower()
            usb = F.USB2_0()
            i2c = F.I2C()
            gpio = times(22, F.ElectricLogic)  # 11-19 not connected
            enable = F.ElectricLogic()
            serial = times(2, F.UART_Base)
            boot_mode = F.ElectricLogic()

        self.IFs = _IFs(self)

        self.NODEs.en_rc_capacitor.PARAMs.capacitance.merge(F.Constant(1 * u))
        # self.NODEs.en_rc_resistor.PARAMs.resistance.merge(F.Constant(10 * k))
        for cap in self.NODEs.debounce_capacitors:
            cap.PARAMs.capacitance.merge(F.Constant(100 * n))
        for res in self.NODEs.debounce_resistors:
            res.PARAMs.resistance.merge(F.Constant(10 * k))

        x = self.IFs

        # https://www.espressif.com/sites/default/files/documentation/esp32-c3_technical_reference_manual_en.pdf#uart
        for ser in x.serial:
            ser.PARAMs.baud.merge(F.Range(0, 5000000))

        # connect all logic references
        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(F.has_single_electric_reference_defined(ref))

        self.pinmap_default = {
            "1": x.gnd[0],
            "2": x.gnd[1],
            "3": x.pwr3v3.IFs.hv,
            "5": x.gpio[2].IFs.signal,
            "6": x.gpio[3].IFs.signal,
            "8": x.enable.IFs.signal,
            "11": x.gnd[2],
            "12": x.gpio[0].IFs.signal,
            "13": x.gpio[1].IFs.signal,
            "14": x.gnd[3],
            "16": x.gpio[10].IFs.signal,
            "18": x.gpio[4].IFs.signal,
            "19": x.gpio[5].IFs.signal,
            "20": x.gpio[6].IFs.signal,
            "21": x.gpio[7].IFs.signal,
            "22": x.gpio[8].IFs.signal,
            "23": x.gpio[9].IFs.signal,
            # 24 is missing #TODO
            "26": x.usb.IFs.d.IFs.n,
            "27": x.usb.IFs.d.IFs.p,
            "30": x.gpio[20].IFs.signal,
            "31": x.gpio[21].IFs.signal,
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

        self.add_trait(F.can_attach_to_footprint_via_pinmap(self.pinmap))

        # set constraints
        self.IFs.pwr3v3.PARAMs.voltage.merge(F.Range(3.0, 3.6))

        # connect all grounds to eachother and power
        connect_to_all_interfaces(self.IFs.pwr3v3.IFs.lv, self.IFs.gnd)

        # connect power decoupling caps
        self.IFs.pwr3v3.get_trait(F.can_be_decoupled).decouple()
        # TODO: should be 100nF + 10uF

        # rc delay circuit on enable pin for startup delay
        # https://www.espressif.com/sites/default/files/russianDocumentation/esp32-c3-mini-1_datasheet_en.pdf page 24  # noqa E501
        self.IFs.enable.IFs.signal.connect_via(
            self.NODEs.en_rc_capacitor, self.IFs.pwr3v3.IFs.lv
        )
        self.IFs.enable.get_trait(F.ElectricLogic.can_be_pulled).pull(
            up=True
        )  # TODO: en_rc_resistor

        # set default boot mode to "SPI Boot mode" (gpio = N.C. or HIGH)
        # https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf page 25  # noqa E501
        self.IFs.gpio[8].get_trait(F.ElectricLogic.can_be_pulled).pull(
            up=True
        )  # boot_resistors[0]
        self.IFs.gpio[2].get_trait(F.ElectricLogic.can_be_pulled).pull(
            up=True
        )  # boot_resistors[1]
        self.IFs.gpio[9].connect(
            self.IFs.boot_mode
        )  # ESP32-c3 defaults to pull-up at boot = SPI-Boot

        # boot and enable switches
        for i, switch in enumerate(self.NODEs.switches):
            if i:
                self.IFs.enable.IFs.signal.connect_via(
                    [self.NODEs.debounce_resistors[i], switch],
                    self.IFs.pwr3v3.IFs.lv,
                )
            else:
                self.IFs.boot_mode.IFs.signal.connect_via(
                    [self.NODEs.debounce_resistors[i], switch],
                    self.IFs.pwr3v3.IFs.lv,
                )
            switch.IFs.unnamed[0].connect_via(
                self.NODEs.debounce_capacitors[i], switch.IFs.unnamed[1]
            )

        self.add_trait(F.has_designator_prefix_defined("U"))

        self.add_trait(
            F.has_datasheet_defined(
                "https://www.espressif.com/sites/default/files/russianDocumentation/esp32-c3-mini-1_datasheet_en.pdf"
            )
        )
        # self.add_trait(F.has_datasheet_defined("https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf"))

        # set mux states
        # UART 1
        self.set_mux(x.gpio[20], self.IFs.serial[1].IFs.rx)
        self.set_mux(x.gpio[21], self.IFs.serial[1].IFs.tx)
        # UART 0
        self.set_mux(x.gpio[0], self.IFs.serial[0].IFs.rx)
        self.set_mux(x.gpio[1], self.IFs.serial[0].IFs.tx)

        # F.I2C
        self.set_mux(x.gpio[4], self.IFs.i2c.IFs.scl)
        self.set_mux(x.gpio[5], self.IFs.i2c.IFs.sda)

        class _uart_esphome_config(F.has_esphome_config.impl()):
            def get_config(self_) -> dict:
                assert isinstance(self, ESP32_C3_MINI_1_VIND)
                obj = self_.get_obj()
                assert isinstance(obj, F.UART_Base)
                config = {
                    "uart": [
                        {
                            "id": obj.get_trait(F.is_esphome_bus).get_bus_id(),
                            "baud_rate": get_parameter_max(obj.PARAMs.baud),
                        }
                    ]
                }

                try:
                    config["uart"][0]["rx_pin"] = self.get_mux_pin(obj.IFs.rx)[1]
                except IndexError:
                    ...

                try:
                    config["uart"][0]["tx_pin"] = self.get_mux_pin(obj.IFs.tx)[1]
                except IndexError:
                    ...

                # if no rx/tx pin is set, then not in use
                if set(config["uart"][0].keys()).isdisjoint({"rx_pin", "tx_pin"}):
                    return {}

                return config

        class _i2c_esphome_config(F.has_esphome_config.impl()):
            def get_config(self_) -> dict:
                assert isinstance(self, ESP32_C3_MINI_1_VIND)
                obj = self_.get_obj()
                assert isinstance(obj, F.I2C)

                try:
                    sda = self.get_mux_pin(obj.IFs.sda)[1]
                    scl = self.get_mux_pin(obj.IFs.scl)[1]
                except IndexError:
                    # Not in use if pinmux is not set
                    return {}

                config = {
                    "i2c": [
                        {
                            "id": obj.get_trait(F.is_esphome_bus).get_bus_id(),
                            "frequency": int(get_parameter_max(obj.PARAMs.frequency)),
                            "sda": sda,
                            "scl": scl,
                        }
                    ]
                }

                return config

        for serial in self.IFs.serial:
            serial.add_trait(
                F.is_esphome_bus_defined(f"uart_{self.IFs.serial.index(serial)}")
            )
            serial.add_trait(_uart_esphome_config())

        for i, gpio in enumerate(self.IFs.gpio):
            gpio.add_trait(F.is_esphome_bus_defined(f"GPIO{i}"))

        self.IFs.i2c.add_trait(F.is_esphome_bus_defined("i2c_0"))
        self.IFs.i2c.add_trait(_i2c_esphome_config())
        self.IFs.i2c.PARAMs.frequency.merge(
            F.Set(
                [
                    F.I2C.define_max_frequency_capability(speed)
                    for speed in [
                        F.I2C.SpeedMode.low_speed,
                        F.I2C.SpeedMode.standard_speed,
                    ]
                ]
                + [
                    F.Range(10 * k, 800 * k)
                ],  # TODO: should be range 200k-800k, but breaks parameter merge
            )
        )

        self.add_trait(
            F.has_esphome_config_defined(
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
    def set_mux(self, gpio: F.ElectricLogic, target: F.ElectricLogic):
        """Careful not checked"""

        pin, _ = self.get_mux_pin(gpio)
        self.pinmap[pin] = target.IFs.signal

    def get_mux_pin(self, target: F.ElectricLogic) -> tuple[str, int]:
        """Returns pin & gpio number"""

        pin = [k for k, v in self.pinmap.items() if v == target.IFs.signal][0]
        gpio = self.pinmap_default[pin]
        gpio_index = [i for i, g in enumerate(self.IFs.gpio) if g.IFs.signal == gpio][0]

        return pin, gpio_index
