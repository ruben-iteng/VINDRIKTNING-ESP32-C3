# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.core import Module, Parameter
from faebryk.libs.util import times
from vindriktning_esp32_c3.library.Inductor import Inductor


class LC_Filter(Module):
    """
    Pi type LC filter
    #TODO: make into universal LC filter or filter module
    """

    def __init__(self, inductance: Parameter, capacitance: Parameter):
        super().__init__()

        # Interfaces
        class _IFs(Module.IFS()):
            power = F.ElectricPower()
            signal_in = F.Electrical()
            signal_out = F.Electrical()

        self.IFs = _IFs(self)

        # Components
        class _NODEs(Module.NODES()):
            inductor = Inductor(inductance)
            capacitor = times(2, lambda: F.Capacitor(capacitance))

        self.NODEs = _NODEs(self)

        for cap in self.NODEs.capacitor:
            cap.PARAMs.capacitance.merge(capacitance)

        # Connections
        self.IFs.signal_in.connect_via(self.NODEs.inductor, self.IFs.signal_out)
        self.IFs.signal_in.connect_via(self.NODEs.capacitor[0], self.IFs.power.IFs.lv)
        self.IFs.signal_out.connect_via(self.NODEs.capacitor[1], self.IFs.power.IFs.lv)

        # traits
        self.add_trait(F.can_bridge_defined(self.IFs.signal_in, self.IFs.signal_out))
