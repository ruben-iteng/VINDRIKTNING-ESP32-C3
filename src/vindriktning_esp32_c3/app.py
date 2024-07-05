import logging

import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.core.util import get_all_nodes
from vindriktning_esp32_c3.library.Fan import Fan
from vindriktning_esp32_c3.library.PM1006 import PM1006
from vindriktning_esp32_c3.vindriktning_esp32_c3_base import Vindriktning_ESP32_C3

logger = logging.getLogger(__name__)


class SmartVindrikting(Module):
    def __init__(self) -> None:
        super().__init__()

        # ----------------------------------------
        #     modules, interfaces, parameters
        # ----------------------------------------

        class _IFs(Module.IFS()): ...

        self.IFs = _IFs(self)

        class _NODEs(Module.NODES()):
            mcu_pcb = Vindriktning_ESP32_C3()
            particulate_sensor = PM1006()
            fan = Fan()

        self.NODEs = _NODEs(self)

        # ----------------------------------------
        #                aliasess
        # ----------------------------------------

        # ----------------------------------------
        #                net names
        # ----------------------------------------
        pcb = self.NODEs.mcu_pcb.NODEs
        nets = {
            "VBUS": pcb.usb_psu.IFs.power_out.IFs.hv,
            "3V3": pcb.ldo.IFs.power_out.IFs.hv,
            "GND": pcb.usb_psu.IFs.power_out.IFs.lv,
            "SDA": pcb.mcu.IFs.i2c.IFs.sda.IFs.signal,
            "SCL": pcb.mcu.IFs.i2c.IFs.scl.IFs.signal,
            "U0_TX": pcb.mcu.IFs.serial[0].IFs.tx.IFs.signal,
            "U0_RX": pcb.mcu.IFs.serial[0].IFs.rx.IFs.signal,
            "U1_TX": pcb.mcu.IFs.serial[1].IFs.tx.IFs.signal,
            "U1_RX": pcb.mcu.IFs.serial[1].IFs.rx.IFs.signal,
            "U1_TX_BHV": pcb.pm_sensor.NODEs.pm_sensor_level_shifter.IFs.voltage_a_bus.IFs.tx.IFs.signal,  # noqa E501
            "U1_RX_BHV": pcb.pm_sensor.NODEs.pm_sensor_level_shifter.IFs.voltage_b_bus.IFs.rx.IFs.signal,  # noqa E501
            "USB_DP": pcb.usb_psu.IFs.usb.IFs.d.IFs.p,
            "USB_DN": pcb.usb_psu.IFs.usb.IFs.d.IFs.n,
        }
        for net_name, mif in nets.items():
            net = F.Net()
            net.add_trait(F.has_overriden_name_defined(net_name))
            net.IFs.part_of.connect(mif)

        # ----------------------------------------
        #            parametrization
        # ----------------------------------------
        self.NODEs.particulate_sensor.esphome.update_interval_s = F.Constant(20)

        # pcb.pm_sensor.NODEs.uart_bus_voltage_dropper.NODEs.voltage_drop_resistors[
        #    0
        # ].PARAMs.resistance.merge(5.1e3)
        # pcb.pm_sensor.NODEs.uart_bus_voltage_dropper.NODEs.voltage_drop_resistors[
        #    1
        # ].PARAMs.resistance.merge(10e3)

        # ----------------------------------------
        #              connections
        # ----------------------------------------
        self.NODEs.particulate_sensor.IFs.data.connect(
            self.NODEs.mcu_pcb.NODEs.mcu.IFs.serial[1]
        )

        # ----------------------------------------
        #              specialize
        # ----------------------------------------

        for node in get_all_nodes(self):
            if node.has_trait(F.is_decoupled):
                # TODO do somewhere else
                capacitance = (
                    node.get_trait(F.is_decoupled).get_capacitor().PARAMs.capacitance
                )
                voltage = (
                    node.get_trait(F.is_decoupled).get_capacitor().PARAMs.rated_voltage
                )
                if isinstance(capacitance.get_most_narrow(), F.TBD):
                    capacitance.merge(100e-9)
                if isinstance(voltage.get_most_narrow(), F.TBD):
                    voltage.merge(10)
