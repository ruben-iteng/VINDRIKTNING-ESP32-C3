import faebryk.library._F as F
from faebryk.core.module import Module
from faebryk.libs.units import P
from faebryk.libs.library import L
from vindriktning.blocks.FanController import FanController
from vindriktning.components.PM1006Connector import PM1006Connector


class PM1006Interface(Module):
    """
    Module containing the hardware needed to connect to the fan and PM1006 particulate
    matter sensor (used in the IKEA VINDRIKTNING).
      - Controllable FAN
        - Fan LED indicator
      - Level shifted UART
    """

    # ----------------------------------------
    #     modules, interfaces, parameters
    # ----------------------------------------
    power: F.ElectricPower
    power_data: F.ElectricPower
    fan_enable: F.ElectricLogic
    uart: F.UART_Base

    fan_controller: FanController
    pm_sensor_level_shifter: F.TXS0102DCUR_UART
    pm_sensor_connector: PM1006Connector

    # ----------------------------------------
    #                 traits
    # ----------------------------------------

    def __preinit__(self):
        # ------------------------------------
        #           connections
        # ------------------------------------
        # fan
        self.fan_controller.control_input.connect(self.fan_enable)

        # pm1006
        self.power.connect(
            self.pm_sensor_level_shifter.voltage_b_power,
            self.pm_sensor_connector.power,
        )
        self.power_data.connect(self.pm_sensor_level_shifter.voltage_a_power)

        # uart
        # TODO: connect shallow
        # self.uart.connect_via(
        #    self.pm_sensor_level_shifter,
        #    self.pm_sensor_connector.data,
        #    linkcls=self.uart.__class__._LinkDirectShallow,
        # )
        self.uart.connect(self.pm_sensor_level_shifter.voltage_a_bus)
        self.pm_sensor_connector.data.connect(
            self.pm_sensor_level_shifter.voltage_b_bus
        )

        # -------------------------------
        #    parametrization
        # ------------------------------
        self.power.voltage.constrain_subset(L.Range.from_center_rel(5 * P.V, 0.05))
        self.power_data.voltage.constrain_subset(
            L.Range.from_center_rel(3.3 * P.V, 0.05)
        )
        self.pm_sensor_level_shifter.buffer.add(
            F.has_explicit_part.by_supplier(
                "C53434",
                pinmap={
                    "1": self.pm_sensor_level_shifter.buffer.shifters[1].io_b.line,
                    "2": self.pm_sensor_level_shifter.buffer.voltage_a_power.lv,
                    "3": self.pm_sensor_level_shifter.buffer.voltage_a_power.hv,
                    "4": self.pm_sensor_level_shifter.buffer.shifters[1].io_a.line,
                    "5": self.pm_sensor_level_shifter.buffer.shifters[0].io_a.line,
                    "6": self.pm_sensor_level_shifter.buffer.n_oe.line,
                    "7": self.pm_sensor_level_shifter.buffer.voltage_b_power.hv,
                    "8": self.pm_sensor_level_shifter.buffer.shifters[0].io_b.line,
                },
            )
        )
