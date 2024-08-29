import logging

import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.core.node import Node
from faebryk.core.util import get_all_nodes

# from faebryk.exporters.pcb.layout.heuristic_decoupling import (
#    LayoutHeuristicElectricalClosenessDecouplingCaps,
# )
# from faebryk.exporters.pcb.layout.heuristic_pulls import (
#    LayoutHeuristicElectricalClosenessPullResistors,
# )
from faebryk.libs.brightness import TypicalLuminousIntensity
from faebryk.libs.units import P

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
        # TODO: move elsewhere
        def set_parameters_for_decoupling_capacitors(
            node: Node, capacitance: F.Constant, voltage: F.Constant
        ):
            decoupling_caps = {
                c.get_trait(F.is_decoupled).get_capacitor()
                for c in self.get_children(
                    direct_only=False, f_filter=lambda x: x.has_trait(F.is_decoupled)
                )
            }

            for c in decoupling_caps:
                if isinstance(c.capacitance.get_most_narrow(), F.TBD):
                    c.capacitance.merge(capacitance)
                if isinstance(c.voltage.get_most_narrow(), F.TBD):
                    c.voltage.merge(voltage)

        # ----------------------------------------
        #                aliasess
        # ----------------------------------------

        # ----------------------------------------
        #                net names
        # ----------------------------------------
        pcb = self.mcu_pcb.NODEs
        nets = {
            "VBUS": pcb.usb_psu.usb_connector.vbus.hv,
            "5V": pcb.usb_psu.power_out.hv,
            "3V3_MCU": pcb.ldo_mcu.power_out.hv,
            "3V3_PERIPHERAL": pcb.ldo_peripheral.power_out.hv,
            "GND": pcb.usb_psu.power_out.lv,
            "SDA": pcb.mcu.esp32_c3_mini_1.esp32_c3.i2c.sda.signal,  # noqa E501
            "SCL": pcb.mcu.esp32_c3_mini_1.esp32_c3.i2c.scl.signal,  # noqa E501
            "DSF_MCU_UART0_TX": pcb.mcu.uart.tx.signal,
            "DSF_MCU_UART0_RX": pcb.mcu.uart.rx.signal,
            "DSF_MCU_UART1_TX": pcb.mcu.esp32_c3_mini_1.esp32_c3.uart[1].tx.signal,
            "DSF_MCU_UART1_RX": pcb.mcu.esp32_c3_mini_1.esp32_c3.uart[1].rx.signal,
            "USF_PM_SENSOR_LEVEL_SHIFTER_TX": pcb.pm_sensor.pm_sensor_level_shifter.voltage_b_bus.tx.signal,  # noqa E501
            "USF_PM_SENSOR_LEVEL_SHIFTER_RX": pcb.pm_sensor.pm_sensor_level_shifter.voltage_b_bus.rx.signal,  # noqa E501
            "USB_DP": pcb.usb_psu.usb.usb_if.d.p,
            "USB_DN": pcb.usb_psu.usb.usb_if.d.n,
        }
        # rename all esp32_c3 gpio pin net names
        for i, gpio in enumerate(pcb.mcu.esp32_c3_mini_1.gpio):
            if not gpio.has_trait(F.has_overriden_name_defined):
                nets[f"MCU_GPIO{i}"] = gpio.signal
        for net_name, mif in nets.items():
            net = F.Net()
            net.add_trait(F.has_overriden_name_defined(net_name))
            net.part_of.connect(mif)

        # ----------------------------------------
        #            parametrization
        # ----------------------------------------
        self.particulate_sensor.esphome.update_interval_s = F.Constant(20 * P.s)

        for node in get_all_nodes(self):
            if isinstance(node, F.PoweredLED):
                node.led.color.merge(F.LED.Color.RED)
                node.led.brightness.merge(
                    TypicalLuminousIntensity.APPLICATION_LED_STANDBY.value.value
                )
        self.mcu_pcb.qwiic_fuse.fuse_type.merge(F.Fuse.FuseType.RESETTABLE)
        self.mcu_pcb.qwiic_fuse.trip_current.merge(F.Constant(550 * P.mA))

        set_parameters_for_decoupling_capacitors(
            node=self,
            capacitance=F.Constant(100 * P.nF),
            voltage=F.Constant(10 * P.V),
        )

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        self.particulate_sensor.data.connect(pcb.mcu.esp32_c3_mini_1.esp32_c3.uart[1])

        # apply placement heuristics
        # LayoutHeuristicElectricalClosenessDecouplingCaps.add_to_all_suitable_modules(
        #    self
        # )
        # LayoutHeuristicElectricalClosenessPullResistors.add_to_all_suitable_modules(
        #    self
        # )
