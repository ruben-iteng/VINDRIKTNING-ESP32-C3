import logging

import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.core.util import connect_to_all_interfaces, get_all_nodes
from vindriktning_esp32_c3.library.BH1750FVI_TR import BH1750FVI_TR
from vindriktning_esp32_c3.library.ESP32_C3_MINI_1 import ESP32_C3_MINI_1
from vindriktning_esp32_c3.library.HLK_LD2410B_P import HLK_LD2410B_P
from vindriktning_esp32_c3.library.ME6211C33M5G_N import ME6211C33M5G_N
from vindriktning_esp32_c3.library.QWIIC import QWIIC
from vindriktning_esp32_c3.library.SCD40 import SCD40
from vindriktning_esp32_c3.library.USB_C_PSU_Vertical import USB_C_PSU_Vertical
from vindriktning_esp32_c3.modules.DigitalLED import DigitalLED
from vindriktning_esp32_c3.modules.IKEAVindriktningPMSensorInterface import (
    IKEAVindriktningPMSensorInterface,
)
from vindriktning_esp32_c3.modules.PCBMount import PCB_Mount

logger = logging.getLogger(__name__)


class Vindriktning_ESP32_C3(Module):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        class _IFs(Module.IFS()):
            pass

        self.IFs = _IFs(self)

        # components
        class _NODEs(Module.NODES()):
            pm_sensor = IKEAVindriktningPMSensorInterface()
            co2_sensor = SCD40()
            leds = DigitalLED(F.Constant(5), buffered=True)
            mcu = ESP32_C3_MINI_1()
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
        self.NODEs.co2_sensor.esphome.update_interval_s = F.Constant(
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
