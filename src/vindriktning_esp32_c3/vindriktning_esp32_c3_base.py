import logging

from faebryk.core.core import LinkDirect, Module
from faebryk.core.util import connect_to_all_interfaces, get_all_nodes
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.library.Capacitor import Capacitor
from faebryk.library.Constant import Constant
from faebryk.library.Diode import Diode
from faebryk.library.Electrical import Electrical
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.has_defined_type_description import has_defined_type_description
from faebryk.library.has_single_electric_reference_defined import (
    has_single_electric_reference_defined,
)
from faebryk.library.I2C import I2C
from faebryk.library.LED import LED
from faebryk.library.MOSFET import MOSFET
from faebryk.library.PoweredLED import PoweredLED
from faebryk.library.PowerSwitch import PowerSwitch
from faebryk.library.Range import Range
from faebryk.library.Resistor import Resistor
from faebryk.library.UART_Base import UART_Base
from faebryk.libs.units import k, m, n
from faebryk.libs.util import times
from vindriktning_esp32_c3.library.B4B_ZR_SM4_TF import B4B_ZR_SM4_TF
from vindriktning_esp32_c3.library.BH1750FVI_TR import BH1750FVI_TR
from vindriktning_esp32_c3.library.ESP32_C3_MINI_1 import ESP32_C3_MINI_1_VIND
from vindriktning_esp32_c3.library.HLK_LD2410B_P import HLK_LD2410B_P
from vindriktning_esp32_c3.library.ME6211C33M5G_N import ME6211C33M5G_N
from vindriktning_esp32_c3.library.Mounting_Hole import Mounting_Hole
from vindriktning_esp32_c3.library.pf_74AHCT2G125 import pf_74AHCT2G125
from vindriktning_esp32_c3.library.pf_533984002 import pf_533984002
from vindriktning_esp32_c3.library.QWIIC import QWIIC
from vindriktning_esp32_c3.library.SCD40 import SCD40
from vindriktning_esp32_c3.library.TXS0102DCUR import TXS0102DCUR
from vindriktning_esp32_c3.library.USB_C_PSU_Vertical import USB_C_PSU_Vertical
from vindriktning_esp32_c3.library.XL_3528RGBW_WS2812B import XL_3528RGBW_WS2812B
from vindriktning_esp32_c3.picker import pick_component

logger = logging.getLogger(__name__)


class Fan_Controller(Module):
    """
    Module containing the hardware needed to controll a fan
    - LED indicator
    - MOSFET power switch
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power_in = ElectricPower()
            control_input = ElectricLogic()
            fan_output = ElectricPower()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            led = PoweredLED()
            fan_power_switch = PowerSwitch(lowside=True, normally_closed=False)
            flyback_protection_diode = Diode(forward_voltage=Constant(40))

        self.NODEs = _NODEs(self)

        # internal connections
        self.NODEs.fan_power_switch.IFs.logic_in.connect(self.IFs.control_input)
        self.IFs.fan_output.connect_via(self.NODEs.fan_power_switch, self.IFs.power_in)

        self.IFs.fan_output.NODEs.hv.connect(
            self.NODEs.flyback_protection_diode.IFs.annode
        )
        self.IFs.fan_output.NODEs.lv.connect(
            self.NODEs.flyback_protection_diode.IFs.cathode
        )

        self.IFs.power_in.connect_via(
            [self.NODEs.led, self.NODEs.fan_power_switch], self.IFs.power_in
        )

        self.add_trait(can_bridge_defined(self.IFs.power_in, self.IFs.fan_output))


class Ikea_Vindriktning_PM_Sensor(Module):
    """
    Module containing the hardware needed to connect to the fan and PM sensor
    in the IKEA VINDRIKTNING
      - Controllable FAN
        - Fan LED indicator
      - Level shifted UART
    """

    class PM1006_Connector(Module):
        def __init__(self) -> None:
            super().__init__()

            # interfaces
            class _IFs(Module.IFS()):
                power = ElectricPower()
                data = UART_Base()

            self.IFs = _IFs(self)

            # components
            class _NODEs(Module.NODES()):
                plug = B4B_ZR_SM4_TF()

            self.NODEs = _NODEs(self)

            # TODO
            self.NODEs.plug.IFs.pin[3].connect(self.IFs.power.NODEs.lv)
            self.NODEs.plug.IFs.pin[2].connect(self.IFs.power.NODEs.hv)
            self.NODEs.plug.IFs.pin[1].connect(
                self.IFs.data.NODEs.tx.NODEs.signal
            )  # connector out sensor in
            self.NODEs.plug.IFs.pin[0].connect(
                self.IFs.data.NODEs.rx.NODEs.signal
            )  # connector in sensor out

            ref = ElectricLogic.connect_all_module_references(self)
            self.add_trait(has_single_electric_reference_defined(ref))

    class Fan_Connector(Module):
        def __init__(self) -> None:
            super().__init__()

            class _IFs(Module.IFS()):
                power = ElectricPower()

            self.IFs = _IFs(self)

            class _NODEs(Module.NODES()):
                plug = pf_533984002()

            self.NODEs = _NODEs(self)

            self.NODEs.plug.IFs.pin[0].connect(self.IFs.power.NODEs.lv)
            self.NODEs.plug.IFs.pin[1].connect(self.IFs.power.NODEs.hv)

    # TODO move out of here
    class UART_Shifter(Module):
        def __init__(self) -> None:
            super().__init__()

            class _IFs(Module.IFS()):
                low_voltage_bus = UART_Base()
                high_voltage_bus = UART_Base()

            self.IFs = _IFs(self)

            class _NODEs(Module.NODES()):
                buffer = TXS0102DCUR()

            self.NODEs = _NODEs(self)

            self.IFs.low_voltage_bus.NODEs.tx.connect_via(
                self.NODEs.buffer.NODEs.shifters[0], self.IFs.high_voltage_bus.NODEs.tx
            )
            self.IFs.low_voltage_bus.NODEs.rx.connect_via(
                self.NODEs.buffer.NODEs.shifters[1], self.IFs.high_voltage_bus.NODEs.rx
            )

            self.add_trait(
                can_bridge_defined(self.IFs.low_voltage_bus, self.IFs.high_voltage_bus)
            )

    def __init__(self) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            power = ElectricPower()
            fan_enable = ElectricLogic()
            uart = UART_Base()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            fan_controller = Fan_Controller()
            fan_connector = self.Fan_Connector()
            pm_sensor_buffer = self.UART_Shifter()
            pm_sensor_connector = self.PM1006_Connector()

        self.NODEs = _NODEs(self)

        # fan
        self.IFs.power.connect_via(
            self.NODEs.fan_controller, self.NODEs.fan_connector.IFs.power
        )
        self.NODEs.fan_controller.IFs.control_input.connect(self.IFs.fan_enable)

        # pm1006
        self.IFs.uart.connect_via(
            self.NODEs.pm_sensor_buffer, self.NODEs.pm_sensor_connector.IFs.data
        )
        self.IFs.power.connect(self.NODEs.pm_sensor_connector.IFs.power)

        #
        self.IFs.power.add_constraint(ElectricPower.ConstraintVoltage(Constant(5)))


class CO2_Sensor(Module):
    """
    Sensirion SCD4x based NIR CO2 sensor
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = ElectricPower()
            i2c = I2C()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            scd4x = SCD40()
            decoupling_caps = [
                Capacitor(Constant(100 * n)),
                Capacitor(Constant(4700 * n)),
            ]
            pullup_resistors = times(2, lambda: Resistor(Constant(10 * k)))

        self.NODEs = _NODEs(self)

        # make internal connections
        # decoupling caps
        for de_cap in self.NODEs.decoupling_caps:
            self.IFs.power.NODEs.hv.connect_via(de_cap, self.IFs.power.NODEs.lv)

        # pullup resistors
        self.IFs.i2c.terminate(
            resistors=(self.NODEs.pullup_resistors[0], self.NODEs.pullup_resistors[1])
        )

        # co2 sensor
        self.NODEs.scd4x.IFs.power.connect(self.IFs.power)
        self.NODEs.scd4x.IFs.i2c.connect(self.IFs.i2c)

        #
        self.IFs.power.add_constraint(ElectricPower.ConstraintVoltage(Constant(3.3)))


class LevelBuffer(Module):
    """
    Logic buffer using a 74HCT1G125 single gate buffer
      - Enable pin active by default
    """

    def __init__(self, enabled: bool = True) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            logic_in = ElectricLogic()
            logic_out = ElectricLogic()
            enable = ElectricLogic()
            power = ElectricPower()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            buffer = pf_74AHCT2G125()
            decoupling_cap = Capacitor(Constant(100 * n))

        self.NODEs = _NODEs(self)

        # connect power
        self.IFs.power.connect(self.NODEs.buffer.IFs.power)

        # connect decouple capacitor
        self.IFs.power.decouple(self.NODEs.decoupling_cap)

        # connect logic
        self.NODEs.buffer.IFs.a.connect(self.IFs.logic_in)
        self.NODEs.buffer.IFs.y.connect(self.IFs.logic_out)

        # connect enable pin to power.lv to enable the buffer
        self.NODEs.buffer.IFs.oe.connect(self.IFs.enable)
        if enabled:
            self.NODEs.buffer.IFs.oe.NODEs.signal.connect(self.IFs.power.NODEs.lv)

        # Add bridge trait
        self.add_trait(can_bridge_defined(self.IFs.logic_in, self.IFs.logic_out))


class digitalLED(Module):
    """
    Create a string of WS2812B RGBW LEDs with optional signal level translator
    """

    class DecoupledDigitalLED(Module):
        def __init__(self, led_class) -> None:
            super().__init__()

            class _IFs(Module.IFS()):
                data_in = ElectricLogic()
                data_out = ElectricLogic()
                power = ElectricPower()

            self.IFs = _IFs(self)

            class _NODEs(Module.NODES()):
                led = led_class()
                decoupling_cap = Capacitor(capacitance=Constant(100 * n))

            self.NODEs = _NODEs(self)

            self.IFs.power.decouple(self.NODEs.decoupling_cap)
            self.IFs.data_in.connect_via(self.NODEs.led, self.IFs.data_out)

            self.IFs.power.connect(self.NODEs.led.IFs.power)

            # Add bridge trait
            self.add_trait(can_bridge_defined(self.IFs.data_in, self.IFs.data_out))

    def __init__(self, pixels: int, buffered: bool = True) -> None:
        super().__init__()

        self.pixels = pixels
        self.buffered = buffered

        class _IFs(Module.IFS()):
            data_in = ElectricLogic()
            power = ElectricPower()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            if buffered:
                buffer = LevelBuffer()
            leds = times(pixels, lambda: self.DecoupledDigitalLED(XL_3528RGBW_WS2812B))

        self.NODEs = _NODEs(self)

        di = ElectricLogic()

        # connect power
        for led in self.NODEs.leds:
            led.IFs.power.connect(self.IFs.power)

        # connect all LEDs in series
        di.connect_via(self.NODEs.leds)

        # put buffer in between if needed
        if buffered:
            self.IFs.data_in.connect_via(self.NODEs.buffer, di)
        else:
            self.IFs.data_in.connect(di)


class Vindriktning_ESP32_C3(Module):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            pass

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            pm_sensor = Ikea_Vindriktning_PM_Sensor()
            co2_sensor = CO2_Sensor()
            leds = digitalLED(5, buffered=True)
            mcu = ESP32_C3_MINI_1_VIND()
            pressence_sensor = HLK_LD2410B_P()
            usb_psu = USB_C_PSU_Vertical()
            lux_sensor = BH1750FVI_TR()
            ldo = ME6211C33M5G_N()
            mounting_holes = times(3, lambda: Mounting_Hole(diameter=2.0))
            qwiic_connector = QWIIC()

        self.NODEs = _NODEs(self)

        # esphome settings
        default_update_interval_s = 1
        self.NODEs.pressence_sensor.esphome.throttle_ms = Constant(
            default_update_interval_s * 1000
        )  # ms
        self.NODEs.lux_sensor.esphome.update_interval_s = Constant(
            default_update_interval_s
        )
        self.NODEs.co2_sensor.NODEs.scd4x.esphome.update_interval_s = Constant(
            default_update_interval_s
        )

        # connections
        # power
        connect_to_all_interfaces(
            self.NODEs.ldo.IFs.power_out,
            [
                self.NODEs.mcu.IFs.pwr3v3,
                self.NODEs.qwiic_connector.IFs.power,
                self.NODEs.lux_sensor.IFs.power,
            ],
        )
        connect_to_all_interfaces(
            self.NODEs.usb_psu.IFs.power_out,
            [
                self.NODEs.ldo.IFs.power_in,
                self.NODEs.pressence_sensor.IFs.power,
                self.NODEs.leds.IFs.power,
                self.NODEs.pm_sensor.IFs.power,
            ],
        )

        # pm sensor
        self.NODEs.pm_sensor.IFs.uart.connect(self.NODEs.mcu.IFs.serial[1])
        # self.NODEs.pm_sensor.IFs.uart.NODEs.rx.connect(self.NODEs.mcu.IFs.gpio[8])
        # self.NODEs.pm_sensor.IFs.uart.NODEs.tx.connect(self.NODEs.mcu.IFs.gpio[9])
        self.NODEs.pm_sensor.IFs.fan_enable.connect(self.NODEs.mcu.IFs.gpio[7])

        # pressence sensor
        self.NODEs.pressence_sensor.IFs.uart.connect(self.NODEs.mcu.IFs.serial[0])
        self.NODEs.pressence_sensor.IFs.out.connect(self.NODEs.mcu.IFs.gpio[6])

        # I2C devices
        connect_to_all_interfaces(
            self.NODEs.mcu.IFs.i2c,
            [
                self.NODEs.co2_sensor.IFs.i2c,
                self.NODEs.qwiic_connector.IFs.i2c,
                self.NODEs.lux_sensor.IFs.i2c,
            ],
        )

        # LEDs
        self.NODEs.leds.IFs.data_in.connect(self.NODEs.mcu.IFs.gpio[5])

        # USB
        self.NODEs.mcu.IFs.usb.connect(self.NODEs.usb_psu.IFs.usb)

        # TODO connect references

        # function

        # fill parameters
        cmps = get_all_nodes(self)
        for cmp in cmps:
            # logger.warn(f"{str(cmp.get_full_name).split('|')[2].split('>')[0]}")
            if isinstance(cmp, PowerSwitch):
                powerswitch = cmp
                powerswitch.NODEs.pull_resistor.set_resistance(Constant(100 * k))
            if isinstance(cmp, BH1750FVI_TR):
                for r in cmp.NODEs.i2c_termination_resistors:
                    r.set_resistance(Constant(10 * k))
            if isinstance(cmp, PoweredLED):
                cmp.NODEs.led.set_forward_parameters(
                    voltage_V=Constant(2), current_A=Constant(10 * m)
                )
                R_led = cmp.NODEs.led.get_trait(
                    LED.has_calculatable_needed_series_resistance
                ).get_needed_series_resistance_ohm(5)
                # Take higher resistance for dimmer LED
                R_led_dim = Range(R_led.value * 2, R_led.value * 4)
                cmp.NODEs.current_limiting_resistor.set_resistance(R_led_dim)
            if isinstance(cmp, LED):
                cmp.add_trait(has_defined_type_description("D"))
            if isinstance(cmp, MOSFET):
                cmp.add_trait(has_defined_type_description("Q"))

        # footprints
        for cmp in cmps:
            if not isinstance(cmp, Module):
                continue
            pick_component(cmp)

        # Check for electrical connections util
        def get_connections(mif: Electrical):
            return [
                other
                for link in mif.GIFs.connected.connections
                for other in link.get_connections()
                if isinstance(link, LinkDirect)
                and other is not mif.GIFs.connected
                and isinstance(other.node, Electrical)
            ]

        # easy ERC
        for cmp in cmps:
            if not isinstance(cmp, Module):
                continue
            for interface in cmp.IFs.get_all():
                if isinstance(interface, Electrical):
                    if not get_connections(interface):
                        logger.warn(f"{interface} is not connected!")
