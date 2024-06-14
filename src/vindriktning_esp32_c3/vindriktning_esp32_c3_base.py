import logging

import faebryk.library._F as F
from faebryk.core.core import Module, Parameter
from faebryk.core.util import connect_to_all_interfaces, get_all_nodes
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

logger = logging.getLogger(__name__)


class Fan_Controller(Module):
    """
    Module containing the hardware needed to controll a fan
    - F.LED indicator
    - F.MOSFET power switch
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power_in = F.ElectricPower()
            control_input = F.ElectricLogic()
            fan_output = F.ElectricPower()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            led = F.PoweredLED()
            fan_power_switch = F.PowerSwitchMOSFET(lowside=True, normally_closed=False)
            flyback_protection_diode = F.Diode()

        self.NODEs = _NODEs(self)

        self.NODEs.flyback_protection_diode.PARAMs.forward_voltage.merge(F.Constant(40))

        # internal connections
        self.NODEs.fan_power_switch.IFs.logic_in.connect(self.IFs.control_input)
        self.IFs.fan_output.connect_via(self.NODEs.fan_power_switch, self.IFs.power_in)

        self.IFs.fan_output.IFs.hv.connect(
            self.NODEs.flyback_protection_diode.IFs.anode
        )
        self.IFs.fan_output.IFs.lv.connect(
            self.NODEs.flyback_protection_diode.IFs.cathode
        )

        self.IFs.power_in.IFs.hv.connect_via(
            [self.NODEs.led, self.NODEs.fan_power_switch], self.IFs.power_in.IFs.lv
        )

        self.add_trait(F.can_bridge_defined(self.IFs.power_in, self.IFs.fan_output))


class Ikea_Vindriktning_PM_Sensor(Module):
    """
    Module containing the hardware needed to connect to the fan and PM sensor
    in the IKEA VINDRIKTNING
      - Controllable FAN
        - Fan F.LED indicator
      - Level shifted UART
    """

    class UART_Voltage_Dropper(Module):
        def __init__(self) -> None:
            super().__init__()

            # interfaces
            class _IFs(Module.IFS()):
                uart_in = F.UART_Base()
                uart_out = F.UART_Base()

            self.IFs = _IFs(self)

            # voltage_drop = F.Constant(0.5)  # abs(
            # voltage_drop = abs(
            #   self.IFs.uart_in.get_trait(
            #       has_single_electric_reference
            #   ).get_reference().ConstraintVoltage
            #   - self.IFs.uart_out.get_trait(
            #       has_single_electric_reference
            #   ).get_reference()
            # )

            # TODO get from somewhere
            # current = F.Constant(0.001282)

            # components
            class _NODEs(Module.NODES()):
                voltage_drop_resistors = times(2, F.Resistor)

            self.NODEs = _NODEs(self)

            for res in self.NODEs.voltage_drop_resistors:
                res.PARAMs.resistance.merge(F.Constant(390))

            # TODO: set value for resistor in self.NODEs.voltage_drop_resistors:

            # connect uarts togerther on high level (signal only, not electrical)
            # TODO this breaks the electric connection with the resistors
            # self.IFs.uart_in.connect(
            #    self.IFs.uart_out,
            #    linkcls=LinkDirectShallow(
            #        lambda link, gif: not isinstance(gif.node, F.Electrical)
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

            self.add_trait(F.can_bridge_defined(self.IFs.uart_in, self.IFs.uart_out))

    class PM1006_Connector(Module):
        def __init__(self) -> None:
            super().__init__()

            # interfaces
            class _IFs(Module.IFS()):
                power = F.ElectricPower()
                data = F.UART_Base()

            self.IFs = _IFs(self)

            # components
            class _NODEs(Module.NODES()):
                plug = B4B_ZR_SM4_TF()

            self.NODEs = _NODEs(self)

            # TODO
            self.NODEs.plug.IFs.pin[3].connect(self.IFs.power.IFs.lv)
            self.NODEs.plug.IFs.pin[2].connect(self.IFs.power.IFs.hv)
            self.NODEs.plug.IFs.pin[1].connect(
                self.IFs.data.IFs.tx.IFs.signal
            )  # connector out sensor in
            self.NODEs.plug.IFs.pin[0].connect(
                self.IFs.data.IFs.rx.IFs.signal
            )  # connector in sensor out

            ref = F.ElectricLogic.connect_all_module_references(self)
            self.add_trait(F.has_single_electric_reference_defined(ref))

    class Fan_Connector(Module):
        def __init__(self) -> None:
            super().__init__()

            class _IFs(Module.IFS()):
                power = F.ElectricPower()

            self.IFs = _IFs(self)

            class _NODEs(Module.NODES()):
                plug = pf_533984002()

            self.NODEs = _NODEs(self)

            self.NODEs.plug.IFs.pin[0].connect(self.IFs.power.IFs.lv)
            self.NODEs.plug.IFs.pin[1].connect(self.IFs.power.IFs.hv)

    # TODO move out of here
    class UART_Shifter(Module):
        def __init__(self) -> None:
            super().__init__()

            class _IFs(Module.IFS()):
                low_voltage_bus = F.UART_Base()
                high_voltage_bus = F.UART_Base()

            self.IFs = _IFs(self)

            class _NODEs(Module.NODES()):
                buffer = TXS0102DCUR()

            self.NODEs = _NODEs(self)

            # TODO check connection
            self.IFs.low_voltage_bus.IFs.tx.connect_via(
                self.NODEs.buffer.NODEs.shifters[0], self.IFs.high_voltage_bus.IFs.tx
            )
            self.IFs.low_voltage_bus.IFs.rx.connect_via(
                self.NODEs.buffer.NODEs.shifters[1], self.IFs.high_voltage_bus.IFs.rx
            )

            self.add_trait(
                F.can_bridge_defined(
                    self.IFs.low_voltage_bus, self.IFs.high_voltage_bus
                )
            )

    def __init__(self) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            power = F.ElectricPower()
            power_data = F.ElectricPower()
            fan_enable = F.ElectricLogic()
            uart = F.UART_Base()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            fan_controller = Fan_Controller()
            fan_connector = self.Fan_Connector()
            pm_sensor_buffer = self.UART_Shifter()
            pm_sensor_connector = self.PM1006_Connector()
            uart_bus_voltage_dropper = self.UART_Voltage_Dropper()

        self.NODEs = _NODEs(self)

        # fan
        self.IFs.power.connect_via(
            self.NODEs.fan_controller, self.NODEs.fan_connector.IFs.power
        )
        self.NODEs.fan_controller.IFs.control_input.connect(self.IFs.fan_enable)

        # pm1006
        # self.IFs.uart.connect_via(
        #    [self.NODEs.pm_sensor_buffer, self.NODEs.uart_bus_voltage_dropper],
        #    self.NODEs.pm_sensor_connector.IFs.data,
        # )
        self.IFs.uart.connect(self.NODEs.pm_sensor_buffer.IFs.low_voltage_bus)
        self.NODEs.pm_sensor_buffer.IFs.high_voltage_bus.connect(
            self.NODEs.uart_bus_voltage_dropper.IFs.uart_in
        )
        self.NODEs.uart_bus_voltage_dropper.IFs.uart_out.connect(
            self.NODEs.pm_sensor_connector.IFs.data
        )
        # TODO this connects VBUS with 3V3
        # self.NODEs.pm_sensor_buffer.NODEs.buffer.IFs.high_voltage_power.connect(
        #    self.IFs.power
        # )
        # self.NODEs.pm_sensor_buffer.NODEs.buffer.IFs.low_voltage_power.connect(
        #    self.IFs.power_data
        # )
        self.IFs.power.connect(self.NODEs.pm_sensor_connector.IFs.power)

        # set constraints
        self.IFs.power_data.PARAMs.voltage.merge(F.Constant(3.3))
        # self.IFs.power.PARAMs.voltage.merge(F.Constant(5))


class CO2_Sensor(Module):
    """
    Sensirion SCD4x based NIR CO2 sensor
    """

    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            power = F.ElectricPower()
            i2c = F.I2C()

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            scd4x = SCD40()

        self.NODEs = _NODEs(self)

        self.IFs.power.get_trait(F.can_be_decoupled).decouple()

        # pullup resistors
        # for r in self.NODEs.pullup_resistors:
        #    assert isinstance(
        #        r.PARAMs.resistance.get_most_narrow(), F.Constant
        #    ), f"r={r.PARAMs.resistance}"

        self.IFs.i2c.terminate()

        # co2 sensor
        self.NODEs.scd4x.IFs.power.connect(self.IFs.power)
        self.NODEs.scd4x.IFs.i2c.connect(self.IFs.i2c)

        #
        self.IFs.power.PARAMs.voltage.merge(F.Constant(3.3))


class LevelBuffer(Module):
    """
    Logic buffer using a 74HCT1G125 single gate buffer
      - Enable pin active by default
    """

    def __init__(self, enabled: bool = True) -> None:
        super().__init__()

        class _IFs(Module.IFS()):
            logic_in = F.ElectricLogic()
            logic_out = F.ElectricLogic()
            enable = F.ElectricLogic()
            power = F.ElectricPower()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            buffer = pf_74AHCT2G125()

        self.NODEs = _NODEs(self)

        # connect power
        self.IFs.power.connect(self.NODEs.buffer.IFs.power)

        # connect decouple capacitor
        self.IFs.power.get_trait(F.can_be_decoupled).decouple()

        # connect logic
        self.NODEs.buffer.IFs.a.connect(self.IFs.logic_in)
        self.NODEs.buffer.IFs.y.connect(self.IFs.logic_out)

        # connect enable pin to power.lv to enable the buffer
        self.NODEs.buffer.IFs.oe.connect(self.IFs.enable)
        if enabled:
            self.NODEs.buffer.IFs.oe.IFs.signal.connect(self.IFs.power.IFs.lv)

        # connect all logic references
        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(F.has_single_electric_reference_defined(ref))

        # Add bridge trait
        self.add_trait(F.can_bridge_defined(self.IFs.logic_in, self.IFs.logic_out))


class digitalLED(Module):
    """
    Create a string of WS2812B RGBW F.LEDs with optional signal level translator
    """

    class _digitalLED_esphome_config(F.has_esphome_config.impl()):
        def get_config(self) -> dict:
            obj = self.get_obj()
            assert isinstance(obj, digitalLED)
            assert isinstance(
                obj.max_refresh_rate_hz, F.Constant
            ), "No update interval set!"

            gpio = F.is_esphome_bus.find_connected_bus(obj.IFs.data_in)

            return {
                "sensor": [
                    {
                        "platform": "esp32_rmt_led_strip",
                        "name": "F.LED string",
                        "rgb_order": "GRB",
                        "pin": gpio.get_trait(F.is_esphome_bus).get_bus_id(),
                        "num_leds": len(obj.NODEs.leds),
                        "rmt_channel": 0,
                        "chipset": "SK6812",
                        "is_rgbw": False,
                        "max_refresh_rate": f"{obj.max_refresh_rate_hz.value}s",
                    }
                ]
            }

    class DecoupledDigitalLED(Module):
        def __init__(self, led_class) -> None:
            super().__init__()

            class _IFs(Module.IFS()):
                data_in = F.ElectricLogic()
                data_out = F.ElectricLogic()
                power = F.ElectricPower()

            self.IFs = _IFs(self)

            class _NODEs(Module.NODES()):
                led = led_class()

            self.NODEs = _NODEs(self)

            self.IFs.power.get_trait(F.can_be_decoupled).decouple()
            self.IFs.data_in.connect_via(self.NODEs.led, self.IFs.data_out)

            self.IFs.power.connect(self.NODEs.led.IFs.power)

            # connect all logic references
            ref = F.ElectricLogic.connect_all_module_references(self)
            self.add_trait(F.has_single_electric_reference_defined(ref))

            # Add bridge trait
            self.add_trait(F.can_bridge_defined(self.IFs.data_in, self.IFs.data_out))

    def __init__(self, pixels: Parameter, buffered: bool = True) -> None:
        super().__init__()

        assert isinstance(pixels, F.Constant)

        self.pixels = pixels
        self.buffered = buffered

        class _IFs(Module.IFS()):
            data_in = F.ElectricLogic()
            power = F.ElectricPower()

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            if buffered:
                buffer = LevelBuffer()
            leds = times(
                self.pixels.value, lambda: self.DecoupledDigitalLED(XL_3528RGBW_WS2812B)
            )

        self.NODEs = _NODEs(self)

        di = F.ElectricLogic()

        # connect power
        for led in self.NODEs.leds:
            led.IFs.power.connect(self.IFs.power)

        # connect all F.LEDs in series
        di.connect_via(self.NODEs.leds)

        # put buffer in between if needed
        if buffered:
            self.IFs.data_in.connect_via(self.NODEs.buffer, di)
        else:
            self.IFs.data_in.connect(di)

        # connect all logic references
        ref = F.ElectricLogic.connect_all_module_references(self)
        self.add_trait(F.has_single_electric_reference_defined(ref))

        # esphome
        self.esphome = self._digitalLED_esphome_config()
        self.add_trait(self.esphome)

        self.max_refresh_rate_hz: Parameter = F.TBD()


class PCB_Mount(Module):
    """
    Mounting holes and features for the PCB
    """

    def __init__(self, enabled: bool = True) -> None:
        super().__init__()

        class _IFs(Module.IFS()): ...

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            screw_holes = times(3, lambda: Mounting_Hole(diameter=F.Constant(2.1)))

        self.NODEs = _NODEs(self)


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
            leds = digitalLED(F.Constant(5), buffered=True)
            mcu = ESP32_C3_MINI_1_VIND()
            pressence_sensor = HLK_LD2410B_P()
            usb_psu = USB_C_PSU_Vertical()
            lux_sensor = BH1750FVI_TR()
            ldo = ME6211C33M5G_N()
            pcb_mount = PCB_Mount()
            qwiic_connector = QWIIC()

        self.NODEs = _NODEs(self)

        # esphome settings
        default_update_interval_s = 1
        self.NODEs.pressence_sensor.esphome.throttle_ms = F.Constant(
            default_update_interval_s * 1000
        )  # ms
        self.NODEs.lux_sensor.esphome.update_interval_s = F.Constant(
            default_update_interval_s
        )
        self.NODEs.leds.max_refresh_rate_hz = F.Constant(60)
        self.NODEs.co2_sensor.NODEs.scd4x.esphome.update_interval_s = F.Constant(
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
                self.NODEs.pm_sensor.IFs.power_data,
                self.NODEs.co2_sensor.IFs.power,
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
        # self.NODEs.pm_sensor.IFs.uart.IFs.rx.connect(self.NODEs.mcu.IFs.gpio[8])
        # self.NODEs.pm_sensor.IFs.uart.IFs.tx.connect(self.NODEs.mcu.IFs.gpio[9])
        self.NODEs.pm_sensor.IFs.fan_enable.connect(self.NODEs.mcu.IFs.gpio[7])

        # pressence sensor
        self.NODEs.pressence_sensor.IFs.uart.connect(self.NODEs.mcu.IFs.serial[0])
        self.NODEs.pressence_sensor.IFs.out.connect(self.NODEs.mcu.IFs.gpio[6])

        # F.I2C devices
        connect_to_all_interfaces(
            self.NODEs.mcu.IFs.i2c,
            [
                self.NODEs.co2_sensor.IFs.i2c,
                self.NODEs.qwiic_connector.IFs.i2c,
                self.NODEs.lux_sensor.IFs.i2c,
            ],
        )

        # F.LEDs
        self.NODEs.leds.IFs.data_in.connect(self.NODEs.mcu.IFs.gpio[5])

        # USB
        self.NODEs.mcu.IFs.usb.connect(self.NODEs.usb_psu.IFs.usb)

        # function

        # fill parameters
        cmps = get_all_nodes(self)
        for cmp in cmps:
            # logger.warn(f"{str(cmp.get_full_name).split('|')[2].split('>')[0]}")
            if isinstance(cmp, F.PowerSwitchMOSFET):
                cmp.NODEs.pull_resistor.PARAMs.resistance.merge(F.Constant(100e3))
            if isinstance(cmp, F.PoweredLED):
                cmp.NODEs.led.PARAMs.forward_voltage.merge(F.Constant(2))
                # cmp.NODEs.led.PARAMs.current.merge(F.Constant(10 * m))
                cmp.NODEs.led.PARAMs.color.merge(F.LED.Color.RED)
            if isinstance(cmp, F.LED):
                cmp.add_trait(F.has_designator_prefix_defined("D"))
            if isinstance(cmp, F.MOSFET):
                cmp.add_trait(F.has_designator_prefix_defined("Q"))

        # Check for electrical connections util
        # def get_connections(mif: F.Electrical):
        #    return [
        #        other
        #        for link in mif.GIFs.connected.connections
        #        for other in link.get_connections()
        #        if isinstance(link, LinkDirect)
        #        and other is not mif.GIFs.connected
        #        and isinstance(other.node, F.Electrical)
        #    ]

        # easy ERC
        # for cmp in cmps:
        #    if not isinstance(cmp, Module):
        #        continue
        #    for interface in cmp.IFs.get_all():
        #        if isinstance(interface, F.Electrical):
        #            if not get_connections(interface):
        #                logger.warn(f"ERC: {interface} is not connected!")
