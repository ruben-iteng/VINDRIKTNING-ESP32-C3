import logging

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.core.parameter import Parameter

# from faebryk.exporters.pcb.layout.heuristic_decoupling import (
#    LayoutHeuristicElectricalClosenessDecouplingCaps,
# )
# from faebryk.exporters.pcb.layout.heuristic_pulls import (
#    LayoutHeuristicElectricalClosenessPullResistors,
# )
from faebryk.libs.brightness import TypicalLuminousIntensity
from faebryk.libs.units import P

from vindriktning_esp32_c3.util import get_decoupling_caps
from vindriktning_esp32_c3.vindriktning_esp32_c3_base import Vindriktning_ESP32_C3

logger = logging.getLogger(__name__)


class SmartVindrikting(Module):
    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------

    mcu_pcb: Vindriktning_ESP32_C3
    particulate_sensor: F.PM1006
    fan: F.Fan

    def __preinit__(self):
        # ----------------------------------------
        #                aliasess
        # ----------------------------------------

        # ----------------------------------------
        #                net names
        # ----------------------------------------
        pcb = self.mcu_pcb
        nets = {
            "VBUS": pcb.usb_psu.usb_connector.vbus.hv,
            "5V": pcb.usb_psu.power_out.hv,
            "3V3_MCU": pcb.ldo_mcu.power_out.hv,
            "3V3_PERIPHERAL": pcb.ldo_peripheral.power_out.hv,
            "GND": pcb.usb_psu.power_out.lv,
            "SDA": pcb.mcu.esp32_c3_mini_1.esp32_c3.i2c.sda.signal,
            "SCL": pcb.mcu.esp32_c3_mini_1.esp32_c3.i2c.scl.signal,
            "DSF_MCU_UART0_TX": pcb.mcu.uart.tx.signal,
            "DSF_MCU_UART0_RX": pcb.mcu.uart.rx.signal,
            "DSF_MCU_UART1_TX": pcb.mcu.esp32_c3_mini_1.esp32_c3.uart[1].tx.signal,
            "DSF_MCU_UART1_RX": pcb.mcu.esp32_c3_mini_1.esp32_c3.uart[1].rx.signal,
            "USF_PM_SENSOR_LEVEL_SHIFTER_TX": pcb.pm_sensor.pm_sensor_level_shifter.voltage_b_bus.tx.signal,  # noqa E501
            "USF_PM_SENSOR_LEVEL_SHIFTER_RX": pcb.pm_sensor.pm_sensor_level_shifter.voltage_b_bus.rx.signal,  # noqa E501
            "USB_DP": pcb.usb_psu.usb.usb_if.d.p,
            "USB_DN": pcb.usb_psu.usb.usb_if.d.n,
            "USB_CC1": pcb.usb_psu.usb_connector.cc1,
            "USB_CC2": pcb.usb_psu.usb_connector.cc2,
            "FAN_OUT-": pcb.pm_sensor.fan_connector.power.lv,
            "CHIP_EN": pcb.mcu.esp32_c3_mini_1.chip_enable.signal,
        }
        # rename all esp32_c3 gpio pin net names
        for i, gpio in enumerate(pcb.mcu.esp32_c3_mini_1.gpio):
            if not gpio.has_trait(F.has_overriden_name_defined):
                if i not in [18, 19, 20, 21, 7, 8, 2, 3]:
                    nets[f"MCU_GPIO{i}"] = gpio.signal

        for net_name, mif in nets.items():
            F.Net.with_name(net_name).part_of.connect(mif)

        # ----------------------------------------
        #            parametrization
        # ----------------------------------------
        self.particulate_sensor.esphome_config.update_interval.merge(20 * P.s)

        for node in self.get_children(direct_only=False, types=F.PoweredLED):
            node.led.color.merge(F.LED.Color.RED)
            node.led.brightness.merge(
                TypicalLuminousIntensity.APPLICATION_LED_STANDBY.value.value
            )
        self.mcu_pcb.qwiic_fuse.fuse_type.merge(F.Fuse.FuseType.RESETTABLE)
        self.mcu_pcb.qwiic_fuse.trip_current.merge(F.Constant(550 * P.mA))

        for c in get_decoupling_caps(self):
            c.capacitance.merge(
                F.Range.from_center(100 * P.nF, 50 * P.nF),
            )
            try:
                c.rated_voltage.merge(
                    F.Range.lower_bound(10 * P.V),
                )
            except Parameter.MergeException:
                ...

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        self.particulate_sensor.data.connect(pcb.mcu.esp32_c3_mini_1.esp32_c3.uart[1])
        self.fan.power.connect(self.mcu_pcb.pm_sensor.fan_connector.power)

        # apply placement heuristics
        # LayoutHeuristicElectricalClosenessDecouplingCaps.add_to_all_suitable_modules(
        #    self
        # )
        # LayoutHeuristicElectricalClosenessPullResistors.add_to_all_suitable_modules(
        #    self
        # )
