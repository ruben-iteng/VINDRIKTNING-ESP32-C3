import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.core.util import connect_all_interfaces
from faebryk.libs.units import P

from vindriktning_esp32_c3.modules.FanConnector import FanConnector
from vindriktning_esp32_c3.modules.FanController import FanController
from vindriktning_esp32_c3.modules.PM1006Connector import PM1006Connector


class IKEAVindriktningPMSensorInterface(Module):
    """
    Module containing the hardware needed to connect to the fan and PM sensor
    in the IKEA VINDRIKTNING
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
    fan_connector: FanConnector
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
        self.power.connect_via(self.fan_controller, self.fan_connector.power)
        self.fan_controller.control_input.connect(self.fan_enable)

        # pm1006
        connect_all_interfaces(
            [
                self.power,
                self.pm_sensor_level_shifter.voltage_b_power,
                self.pm_sensor_connector.power,
            ]
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
        self.power.voltage.merge(F.Range.from_center(5 * P.V, 0.2 * P.V))
        self.power_data.voltage.merge(F.Constant(3.3 * P.V))
