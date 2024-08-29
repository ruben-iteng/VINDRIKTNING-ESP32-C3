# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

import faebryk.library._F as F
from faebryk.core.core import Module
from faebryk.libs.library import L
from faebryk.libs.units import P, Quantity


class LC_Filter(Module):
    """
    Pi type LC filter
    #TODO: make into universal LC filter or filter module
    """

    inductance: F.TBD[Quantity]
    capacitance: F.TBD[Quantity]

    # Interfaces
    power: F.ElectricPower
    signal_in: F.Electrical
    signal_out: F.Electrical

    # Components
    inductor = L.f_field(F.Inductor)
    capacitor = L.list_field(2, F.Capacitor)

    def __preinit__(self):
        for cap in self.capacitor:
            cap.capacitance.merge(self.capacitance)

        # Connections
        self.signal_in.connect_via(self.inductor, self.signal_out)
        self.signal_in.connect_via(self.capacitor[0], self.power.lv)
        self.signal_out.connect_via(self.capacitor[1], self.power.lv)

    @L.rt_field
    def can_bridge(self):
        return F.can_bridge_defined(self.signal_in, self.signal_out)
