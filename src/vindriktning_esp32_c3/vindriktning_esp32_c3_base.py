import logging

import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.core.util import (
    connect_all_interfaces,
    connect_to_all_interfaces,
)
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
            co2_sensor = F.SCD40()
            leds = DigitalLED(F.Constant(5), buffered=True)
            mcu = F.ESP32_C3_MINI_1_Reference_Design()
            pressence_sensor = F.HLK_LD2410B_P()
            usb_psu = F.USB_C_PSU_Vertical()
            lux_sensor = F.BH1750FVI_TR()
            ldo_mcu = F.ME6211C33M5G_N()
            ldo_peripheral = F.ME6211C33M5G_N()
            pcb_mount = PCB_Mount()
            qwiic_connector = F.QWIIC()
            qwiic_fuse = F.Fuse()

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

        # aliases
        gnd = self.NODEs.usb_psu.IFs.power_out.IFs.lv

        # connections
        # mcu has its own LDO
        self.NODEs.ldo_mcu.IFs.power_out.connect(self.NODEs.mcu.IFs.vdd3v3)
        # connect all 3.3V powers
        connect_all_interfaces(
            [
                self.NODEs.ldo_peripheral.IFs.power_out,
                self.NODEs.lux_sensor.IFs.power,
                self.NODEs.pm_sensor.IFs.power_data,
                self.NODEs.co2_sensor.IFs.power,
                self.NODEs.leds.IFs.power_data,
            ],
        )

        # connect qwiic connector via fuse to 3.3V
        self.NODEs.qwiic_connector.IFs.power.IFs.hv.connect_via(
            self.NODEs.qwiic_fuse, self.NODEs.ldo_peripheral.IFs.power_out.IFs.hv
        )
        self.NODEs.qwiic_connector.IFs.power.IFs.lv.connect(gnd)

        # connect all 5V powers
        connect_all_interfaces(
            [
                self.NODEs.usb_psu.IFs.power_out,
                self.NODEs.ldo_mcu.IFs.power_in,
                self.NODEs.ldo_peripheral.IFs.power_in,
                self.NODEs.pressence_sensor.IFs.power,
                self.NODEs.leds.IFs.power,
                self.NODEs.pm_sensor.IFs.power,
            ],
        )

        # pm sensor
        self.NODEs.pm_sensor.IFs.uart.connect(
            self.NODEs.mcu.NODEs.esp32_c3_mini_1.NODEs.esp32_c3.IFs.uart[1]
        )
        # self.NODEs.pm_sensor.IFs.uart.IFs.rx.connect(self.NODEs.mcu.NODEs.esp32_c3_mini_1.IFs.gpio[8]) # noqa E501
        # self.NODEs.pm_sensor.IFs.uart.IFs.tx.connect(self.NODEs.mcu.NODEs.esp32_c3_mini_1.IFs.gpio[9]) # noqa E501
        self.NODEs.pm_sensor.IFs.fan_enable.connect(
            self.NODEs.mcu.NODEs.esp32_c3_mini_1.IFs.gpio[7]
        )

        # pressence sensor
        self.NODEs.pressence_sensor.IFs.uart.connect(self.NODEs.mcu.IFs.uart)
        self.NODEs.pressence_sensor.IFs.out.connect(
            self.NODEs.mcu.NODEs.esp32_c3_mini_1.IFs.gpio[6]
        )

        # I2C devices
        connect_to_all_interfaces(
            self.NODEs.mcu.NODEs.esp32_c3_mini_1.NODEs.esp32_c3.IFs.i2c,
            [
                self.NODEs.co2_sensor.IFs.i2c,
                self.NODEs.qwiic_connector.IFs.i2c,
                self.NODEs.lux_sensor.IFs.i2c,
            ],
        )

        # LEDs
        self.NODEs.leds.IFs.data_in.connect(
            self.NODEs.mcu.NODEs.esp32_c3_mini_1.IFs.gpio[5]
        )

        # USB
        self.NODEs.mcu.IFs.usb.connect(self.NODEs.usb_psu.IFs.usb)

        # function

        # fill parameters
        # cmps = get_all_nodes(self)
        # for cmp in cmps:
        #    # logger.warn(f"{str(cmp.get_full_name).split('|')[2].split('>')[0]}")
        #    if isinstance(cmp, F.PowerSwitchMOSFET):
        #        cmp.NODEs.pull_resistor.PARAMs.resistance.merge(F.Constant(100e3))
        #    if isinstance(cmp, F.PoweredLED):
        #        cmp.NODEs.led.PARAMs.color.merge(F.LED.Color.RED)
        #        cmp.NODEs.led.PARAMs.brightness.merge(
        #            TypicalLuminousIntensity.APPLICATION_LED_STANDBY.value.value
        #        )
        #    if isinstance(cmp, F.LED):
        #        cmp.add_trait(F.has_designator_prefix_defined("D"))
        #    if isinstance(cmp, F.MOSFET):
        #        cmp.add_trait(F.has_designator_prefix_defined("Q"))
        # self.NODEs.qwiic_fuse.PARAMs.fuse_type.merge(F.Fuse.FuseType.RESETTABLE)
        # self.NODEs.qwiic_fuse.PARAMs.trip_current.merge(F.Constant(0.550))
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
