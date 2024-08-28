import logging

import faebryk.library._F as F
from faebryk.core.core import Module, Node
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
    def __init__(self) -> None:
        # TODO: move elsewhere
        def set_parameters_for_decoupling_capacitors(
            node: Node, capacitance: F.Constant, voltage: F.Constant
        ):
            for n in get_all_nodes(node):
                if n.has_trait(F.is_decoupled_nodes):
                    _capacitance = (
                        n.get_trait(F.is_decoupled_nodes)
                        .get_capacitor()
                        .PARAMs.capacitance
                    )
                    _voltage = (
                        node.get_trait(F.is_decoupled_nodes)
                        .get_capacitor()
                        .PARAMs.rated_voltage
                    )
                    if isinstance(_capacitance.get_most_narrow(), F.TBD):
                        _capacitance.merge(capacitance)
                    if isinstance(_voltage.get_most_narrow(), F.TBD):
                        _voltage.merge(voltage)

        def set_resistance_for_pull_resistors(node: Node, resistance: F.Constant):
            for n in get_all_nodes(node):
                if n.has_trait(F.ElectricLogic.has_pulls):
                    resistors = n.get_trait(F.ElectricLogic.has_pulls).get_pulls()
                    if resistors:
                        for r in resistors:
                            if r:
                                if isinstance(
                                    r.PARAMs.resistance.get_most_narrow(), F.TBD
                                ):
                                    r.PARAMs.resistance.merge(resistance)

        super().__init__()

        # ----------------------------------------
        #     modules, interfaces, parameters
        # ----------------------------------------

        class _IFs(Module.IFS()): ...

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            mcu_pcb = Vindriktning_ESP32_C3()
            particulate_sensor = F.PM1006()
            fan = F.Fan()

        self.NODEs = _NODEs(self)

        # ----------------------------------------
        #                aliasess
        # ----------------------------------------

        # ----------------------------------------
        #                net names
        # ----------------------------------------
        pcb = self.NODEs.mcu_pcb.NODEs
        nets = {
            "VBUS": pcb.usb_psu.NODEs.usb_connector.IFs.vbus.IFs.hv,
            "5V": pcb.usb_psu.IFs.power_out.IFs.hv,
            "3V3_MCU": pcb.ldo_mcu.IFs.power_out.IFs.hv,
            "3V3_PERIPHERAL": pcb.ldo_peripheral.IFs.power_out.IFs.hv,
            "GND": pcb.usb_psu.IFs.power_out.IFs.lv,
            "SDA": pcb.mcu.NODEs.esp32_c3_mini_1.NODEs.esp32_c3.IFs.i2c.IFs.sda.IFs.signal,  # noqa E501
            "SCL": pcb.mcu.NODEs.esp32_c3_mini_1.NODEs.esp32_c3.IFs.i2c.IFs.scl.IFs.signal,  # noqa E501
            "DSF_MCU_UART0_TX": pcb.mcu.IFs.uart.IFs.tx.IFs.signal,
            "DSF_MCU_UART0_RX": pcb.mcu.IFs.uart.IFs.rx.IFs.signal,
            "DSF_MCU_UART1_TX": pcb.mcu.NODEs.esp32_c3_mini_1.NODEs.esp32_c3.IFs.uart[
                1
            ].IFs.tx.IFs.signal,
            "DSF_MCU_UART1_RX": pcb.mcu.NODEs.esp32_c3_mini_1.NODEs.esp32_c3.IFs.uart[
                1
            ].IFs.rx.IFs.signal,
            "USF_PM_SENSOR_LEVEL_SHIFTER_TX": pcb.pm_sensor.NODEs.pm_sensor_level_shifter.IFs.voltage_b_bus.IFs.tx.IFs.signal,  # noqa E501
            "USF_PM_SENSOR_LEVEL_SHIFTER_RX": pcb.pm_sensor.NODEs.pm_sensor_level_shifter.IFs.voltage_b_bus.IFs.rx.IFs.signal,  # noqa E501
            "USB_DP": pcb.usb_psu.IFs.usb.IFs.usb_if.IFs.d.IFs.p,
            "USB_DN": pcb.usb_psu.IFs.usb.IFs.usb_if.IFs.d.IFs.n,
        }
        # rename all esp32_c3 gpio pin net names
        for i, gpio in enumerate(pcb.mcu.NODEs.esp32_c3_mini_1.IFs.gpio):
            if not gpio.has_trait(F.has_overriden_name_defined):
                nets[f"MCU_GPIO{i}"] = gpio.IFs.signal
        for net_name, mif in nets.items():
            net = F.Net()
            net.add_trait(F.has_overriden_name_defined(net_name))
            net.IFs.part_of.connect(mif)

        # ----------------------------------------
        #            parametrization
        # ----------------------------------------
        self.NODEs.particulate_sensor.esphome.update_interval_s = F.Constant(20 * P.s)

        for node in get_all_nodes(self):
            if isinstance(node, F.PoweredLED):
                node.NODEs.led.PARAMs.color.merge(F.LED.Color.RED)
                node.NODEs.led.PARAMs.brightness.merge(
                    TypicalLuminousIntensity.APPLICATION_LED_STANDBY.value.value
                )
        self.NODEs.mcu_pcb.NODEs.qwiic_fuse.PARAMs.fuse_type.merge(
            F.Fuse.FuseType.RESETTABLE
        )
        self.NODEs.mcu_pcb.NODEs.qwiic_fuse.PARAMs.trip_current.merge(
            F.Constant(550 * P.mA)
        )

        set_parameters_for_decoupling_capacitors(
            node=self,
            capacitance=F.Constant(100 * P.nF),
            voltage=F.Constant(10 * P.V),
        )

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        self.NODEs.particulate_sensor.IFs.data.connect(
            pcb.mcu.NODEs.esp32_c3_mini_1.NODEs.esp32_c3.IFs.uart[1]
        )

        # apply placement heuristics
        # LayoutHeuristicElectricalClosenessDecouplingCaps.add_to_all_suitable_modules(
        #    self
        # )
        # LayoutHeuristicElectricalClosenessPullResistors.add_to_all_suitable_modules(
        #    self
        # )
