import logging

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.core.util import connect_all_interfaces
from faebryk.libs.library import L
from faebryk.libs.units import P

from vindriktning_esp32_c3.modules.DigitalLED import DigitalLED
from vindriktning_esp32_c3.modules.IKEAVindriktningPMSensorInterface import (
    IKEAVindriktningPMSensorInterface,
)
from vindriktning_esp32_c3.modules.PCBMount import PCB_Mount

logger = logging.getLogger(__name__)


class Vindriktning_ESP32_C3(Module):
    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    pm_sensor: IKEAVindriktningPMSensorInterface
    co2_sensor: F.SCD40
    leds = L.f_field(DigitalLED)(5, buffered=True)
    mcu: F.ESP32_C3_MINI_1_Reference_Design
    pressence_sensor: F.HLK_LD2410B_P
    usb_psu: F.USB_C_PSU_Vertical
    lux_sensor: F.BH1750FVI_TR
    ldo_mcu: F.ME6211C33M5G_N
    ldo_peripheral: F.ME6211C33M5G_N
    pcb_mount: PCB_Mount
    qwiic_connector: F.QWIIC
    qwiic_fuse: F.Fuse

    # ----------------------------------------
    #                 traits
    # ----------------------------------------

    def __preinit__(self):
        # aliases
        gnd = self.usb_psu.power_out.lv

        # ------------------------------------
        #           connections
        # ------------------------------------
        # mcu has its own LDO
        self.ldo_mcu.power_out.connect(self.mcu.vdd3v3)
        # connect all 3.3V powers
        connect_all_interfaces(
            [
                self.ldo_peripheral.power_out,
                self.lux_sensor.power,
                self.pm_sensor.power_data,
                self.co2_sensor.power,
                self.leds.runtime_anon[0],
            ],
        )

        # connect qwiic connector via fuse to 3.3V
        self.qwiic_connector.power.hv.connect_via(
            self.qwiic_fuse, self.ldo_peripheral.power_out.hv
        )
        self.qwiic_connector.power.lv.connect(gnd)

        # connect all 5V powers
        connect_all_interfaces(
            [
                self.usb_psu.power_out,
                self.ldo_mcu.power_in,
                self.ldo_peripheral.power_in,
                self.pressence_sensor.power,
                self.leds.power,
                self.pm_sensor.power,
            ],
        )

        # pm sensor
        self.pm_sensor.uart.connect(self.mcu.esp32_c3_mini_1.esp32_c3.uart[1])
        # self.pm_sensor.uart.rx.connect(self.mcu.esp32_c3_mini_1.gpio[8])
        # self.pm_sensor.uart.tx.connect(self.mcu.esp32_c3_mini_1.gpio[9])
        self.pm_sensor.fan_enable.connect(self.mcu.esp32_c3_mini_1.gpio[7])

        # pressence sensor
        self.pressence_sensor.uart.connect(self.mcu.uart)
        self.pressence_sensor.out.connect(self.mcu.esp32_c3_mini_1.gpio[6])

        # I2C devices
        # connect_to_all_interfaces(
        #    self.mcu.esp32_c3_mini_1.esp32_c3.i2c,
        #    [
        #        self.co2_sensor.i2c,
        #        self.qwiic_connector.i2c,
        #        self.lux_sensor.i2c,
        #    ],
        # )
        self.mcu.esp32_c3_mini_1.esp32_c3.i2c.connect(
            self.co2_sensor.i2c, linkcls=F.ElectricLogic.LinkIsolatedReference
        )
        self.mcu.esp32_c3_mini_1.esp32_c3.i2c.connect(
            self.qwiic_connector.i2c, linkcls=F.ElectricLogic.LinkIsolatedReference
        )
        self.mcu.esp32_c3_mini_1.esp32_c3.i2c.connect(
            self.lux_sensor.i2c, linkcls=F.ElectricLogic.LinkIsolatedReference
        )

        # LEDs
        self.leds.data_in.connect(
            self.mcu.esp32_c3_mini_1.gpio[5],
            linkcls=F.ElectricLogic.LinkIsolatedReference,
        )

        # USB
        self.mcu.usb.connect(self.usb_psu.usb)

        # ------------------------------------
        #          parametrization
        # ------------------------------------
        # esphome settings
        default_update_interval = 1 * P.s
        self.pressence_sensor.esphome_config.throttle.merge(default_update_interval)
        self.lux_sensor.esphome_config.update_interval.merge(default_update_interval)
        self.leds.max_refresh_rate.merge(60 * P.Hz)
        self.co2_sensor.esphome_config.update_interval.merge(default_update_interval)
