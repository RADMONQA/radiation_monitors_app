KPL/FK

FRAME DEFINITIONS FOR GSE (GEOCENTRIC SOLAR ECLIPTIC)
-----------------------------------------------------

This file defines a dynamic frame called GSE (Geocentric Solar Ecliptic).
The X-axis points from Earth to the Sun.
The Y-axis is in the ecliptic plane and points along Earth's orbital velocity.
The Z-axis is normal to the X-Y plane to complete a right-handed frame.

This frame is built using a parameterized TWO-VECTOR style definition.

\begindata

   FRAME_GSE                       =  98174937
   FRAME_98174937_NAME             = 'GSE'
   FRAME_98174937_CLASS            =  5
   FRAME_98174937_CLASS_ID         =  98174937
   FRAME_98174937_CENTER           =  399
   FRAME_98174937_RELATIVE         = 'J2000'
   FRAME_98174937_DEF_STYLE        = 'PARAMETERIZED'
   FRAME_98174937_FAMILY           = 'TWO-VECTOR'

   FRAME_98174937_PRI_AXIS         = 'X'
   FRAME_98174937_PRI_VECTOR_DEF   = 'OBSERVER_TARGET_POSITION'
   FRAME_98174937_PRI_OBSERVER     = 'EARTH'
   FRAME_98174937_PRI_TARGET       = 'SUN'
   FRAME_98174937_PRI_ABCORR       = 'NONE'

   FRAME_98174937_SEC_AXIS         = 'Y'
   FRAME_98174937_SEC_VECTOR_DEF   = 'OBSERVER_TARGET_VELOCITY'
   FRAME_98174937_SEC_OBSERVER     = 'EARTH'
   FRAME_98174937_SEC_TARGET       = 'SUN'
   FRAME_98174937_SEC_ABCORR       = 'NONE'
   FRAME_98174937_SEC_FRAME        = 'J2000'

\begintext

End of GSE frame definition.
