# Minimal PQT decay definitions added on top of the SM UFO base.

from __future__ import absolute_import
from .object_library import all_decays, Decay
from . import particles as P


Decay_S = Decay(name = 'Decay_S',
                particle = P.S,
                partial_widths = {(P.Z,P.Z):'sint**2*MZ**3/(16.*cmath.pi*vev**2)',
                                  (P.W__minus__,P.W__plus__):'sint**2*MW**3/(8.*cmath.pi*vev**2)'})

Decay_H2 = Decay(name = 'Decay_H2',
                 particle = P.H2,
                 partial_widths = {(P.Z,P.Z):'cost**2*MZ**3/(16.*cmath.pi*vev**2)',
                                   (P.W__minus__,P.W__plus__):'cost**2*MW**3/(8.*cmath.pi*vev**2)'})

