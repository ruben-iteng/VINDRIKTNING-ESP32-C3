from enum import Enum
import logging
from typing import List

from faebryk.core.core import Module
from faebryk.core.util import get_all_nodes
from faebryk.library.Constant import Constant
from faebryk.library.DifferentialPair import DifferentialPair
from faebryk.library.Electrical import Electrical
from faebryk.library.ElectricLogic import ElectricLogic
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.LED import LED
from faebryk.library.PoweredLED import PoweredLED
from faebryk.library.PowerSwitch import PowerSwitch
from faebryk.library.Range import Range
from faebryk.library.UART_Base import UART_Base
from faebryk.library.I2C import I2C
from vindriktning_esp32_c3.library.BH1750FVI_TR import BH1750FVI_TR
from vindriktning_esp32_c3.library.Mounting_Hole import Mounting_Hole
from vindriktning_esp32_c3.library.SCD40 import SCD40
from faebryk.library.Resistor import Resistor
from vindriktning_esp32_c3.library.USB_C_PSU_Vertical import USB_C_PSU_Vertical
from faebryk.library.Capacitor import Capacitor
from faebryk.library.TBD import TBD
from faebryk.libs.units import k, m, n, u
from faebryk.libs.util import times
from vindriktning_esp32_c3.library.ME6211C33M5G_N import ME6211C33M5G_N
from vindriktning_esp32_c3.library.B4B_ZR_SM4_TF import B4B_ZR_SM4_TF
from vindriktning_esp32_c3.library.pf_74AHCT2G125 import pf_74AHCT2G125
from vindriktning_esp32_c3.library.pf_533984002 import pf_533984002
from vindriktning_esp32_c3.library.ESP32_C3_MINI_1 import ESP32_C3_MINI_1_VIND
from vindriktning_esp32_c3.library.HLK_LD2410B_P import HLK_LD2410B_P
from vindriktning_esp32_c3.library.XL_3528RGBW_WS2812B import XL_3528RGBW_WS2812B
from vindriktning_esp32_c3.picker import pick_component
from faebryk.library.can_bridge_defined import can_bridge_defined
from faebryk.core.util import connect_to_all_interfaces
from faebryk.library.has_defined_type_description import has_defined_type_description
from faebryk.library.MOSFET import MOSFET
from faebryk.library.Electrical import Electrical
from faebryk.core.core import LinkDirect

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

        self.NODEs = _NODEs(self)

        # internal connections
        self.NODEs.fan_power_switch.IFs.logic_in.connect(self.IFs.control_input)
        self.IFs.fan_output.connect_via(self.NODEs.fan_power_switch, self.IFs.power_in)

        self.IFs.power_in.connect_via(
            [self.NODEs.led, self.NODEs.fan_power_switch], self.IFs.power_in
        )

        self.add_trait(can_bridge_defined(self.IFs.power_in, self.IFs.fan_output))


class Ikea_Vindriktning_PM_Sensor(Module):
    """
    Module containing the hardware needed to connect to the fan and PM sensor
    in the IKEA VINDRIKTNING
      - Controllable FAN
      - Level shifted UART
      - Fan LED indicator
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power_5v_in = ElectricPower()
            power_3v3_in = ElectricPower()
            fan_enable = ElectricLogic()
            uart = UART_Base()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            fan_controller = Fan_Controller()
            fan_connector = pf_533984002()
            pm_sensor_connector = B4B_ZR_SM4_TF()
            pm_sernsor_buffers = times(2, LevelBuffer)  # 0=tx, 1=rx

        self.NODEs = _NODEs(self)

        # aliasses
        tx = 0
        rx = 1

        # TODO ^that or this?
        class RxTx(Enum):
            TX = 0
            RX = 1

        gnd = self.IFs.power_5v_in.NODEs.lv
        v_5V = self.IFs.power_5v_in.NODEs.hv
        v_3V3 = self.IFs.power_3v3_in.NODEs.hv

        # make internal connections
        # fan connector
        self.NODEs.fan_connector.IFs.pin[0].connect_via(self.NODEs.fan_controller, gnd)
        self.NODEs.fan_connector.IFs.pin[1].connect(v_5V)
        self.NODEs.fan_controller.IFs.control_input.connect(self.IFs.fan_enable)

        # tx buffer to 5v power (mcu 3v3 > sensor 5v)
        self.NODEs.pm_sernsor_buffers[tx].IFs.power.connect(self.IFs.power_5v_in)
        # rx buffer to 3v3 power (mcu 3v3 < sensor 5v)
        self.NODEs.pm_sernsor_buffers[RxTx.RX.value].IFs.power.connect(
            self.IFs.power_3v3_in
        )

        # pm sensor connector to buffers
        self.NODEs.pm_sensor_connector.IFs.pin[3].connect(gnd)
        self.NODEs.pm_sensor_connector.IFs.pin[2].connect(v_5V)
        self.NODEs.pm_sensor_connector.IFs.pin[1].connect_via(
            self.NODEs.pm_sernsor_buffers[rx],
            self.IFs.uart.NODEs.rx.NODEs.signal,
        )
        self.NODEs.pm_sensor_connector.IFs.pin[0].connect_via(
            self.NODEs.pm_sernsor_buffers[RxTx.TX.value],
            self.IFs.uart.NODEs.tx.NODEs.signal,
        )


class CO2_Sensor(Module):
    """
    Sensirion SCD4x based NIR CO2 sensor
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power_3v3_in = ElectricPower()
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

        # alliases
        gnd = self.IFs.power_3v3_in.NODEs.lv
        v_3V = self.IFs.power_3v3_in.NODEs.hv
        scl = self.NODEs.scd4x.IFs.i2c.NODEs.scl
        sda = self.NODEs.scd4x.IFs.i2c.NODEs.sda

        # make internal connections
        # decoupling caps
        for de_cap in self.NODEs.decoupling_caps:
            v_3V.connect_via(de_cap, gnd)

        # pullup resistors
        # TODO self.NODEs.scd4x.IFs.i2c.NODEs.scl.connect_to_electric
        self.NODEs.scd4x.IFs.i2c.NODEs.scl.pull_up(self.NODEs.pullup_resistors[0])
        self.NODEs.scd4x.IFs.i2c.NODEs.sda.pull_up(self.NODEs.pullup_resistors[1])

        # co2 sensor
        self.NODEs.scd4x.IFs.power.NODEs.lv.connect(gnd)
        self.NODEs.scd4x.IFs.power.NODEs.hv.connect(v_3V)
        self.NODEs.scd4x.IFs.i2c.NODEs.scl.connect(scl)
        self.NODEs.scd4x.IFs.i2c.NODEs.sda.connect(sda)


class LevelBuffer(Module):
    """
    Logic buffer using a 74HCT1G125 single gate buffer
      - Enable pin active by default
    """

    def __init__(self) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            logic_in = ElectricLogic()
            logic_out = ElectricLogic()
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

        # connect enable pin to power.lv to always enable the buffer
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
            psu = USB_C_PSU_Vertical()
            lux_sensor = BH1750FVI_TR()
            ldo = ME6211C33M5G_N()
            mounting_holes = times(3, lambda: Mounting_Hole(diameter=2.0))

        self.NODEs = _NODEs(self)

        # connections
        # power
        connect_to_all_interfaces(
            self.NODEs.ldo.IFs.power_out,
            [
                self.NODEs.mcu.IFs.pwr3v3,
                self.NODEs.pm_sensor.IFs.power_3v3_in,
            ],
        )
        connect_to_all_interfaces(
            self.NODEs.psu.IFs.power_out,
            [
                self.NODEs.ldo.IFs.power_in,
                self.NODEs.pressence_sensor.IFs.power,
                self.NODEs.leds.IFs.power,
                self.NODEs.pm_sensor.IFs.power_5v_in,
            ],
        )

        # sensors
        self.NODEs.pressence_sensor.IFs.uart.connect(self.NODEs.mcu.IFs.serial[0])
        self.NODEs.pressence_sensor.IFs.out.connect(self.NODEs.mcu.IFs.gpio[6])
        self.NODEs.pm_sensor.IFs.uart.NODEs.rx.connect(self.NODEs.mcu.IFs.gpio[8])
        self.NODEs.pm_sensor.IFs.uart.NODEs.tx.connect(self.NODEs.mcu.IFs.gpio[9])
        self.NODEs.pm_sensor.IFs.fan_enable.connect(self.NODEs.mcu.IFs.gpio[7])

        # LEDs
        self.NODEs.leds.IFs.data_in.connect(self.NODEs.mcu.IFs.gpio[5])

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
            if isinstance(cmp, Capacitor):
                capacitor = cmp
                if isinstance(capacitor.capacitance, TBD):
                    logger.warn(
                        f"Found capacitor with TBD value at {capacitor.get_full_name}"
                    )
                    placeholder_capacitance = Constant(100 * n)
                    capacitor.set_capacitance(placeholder_capacitance)
                    logger.warn(
                        f"Set capacitor value to {placeholder_capacitance.value:.2E}F"
                    )
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
