=====================================================================
                NOVALCT CONTROLLER PROTOCOL FLOW
=====================================================================

NovaLCT Software
      │
      │
      ▼
+--------------------------------------------------------------+
| 1. DISCOVERY PHASE                                           |
|    UDP /3800                                                 |
+--------------------------------------------------------------+

NovaLCT  ──►  Broadcast discovery request

    rqProMI
    (who is there?)

Device Emulator  ──►  rpProMI
    response with:
        device type
        IP
        controller capability

Result:
NovaLCT lists the controller in the device list


      │
      ▼
+--------------------------------------------------------------+
| 2. TCP SESSION START                                         |
|    TCP /5200                                                 |
+--------------------------------------------------------------+

NovaLCT  ──►  open TCP connection

Protocol type:
RS232-like binary protocol encapsulated in TCP


Packet format:

    Request
    ------------------------------------
    AA55                header
    ack                 always 00
    serial
    source
    destination
    deviceType
    port
    rcvIndex
    io (read/write)
    reserved
    address (32 bit)
    length
    data
    CRC16


    Response
    ------------------------------------
    55AA
    ack code
    serial
    destination
    source
    deviceType
    port
    rcvIndex
    io
    reserved
    address
    length
    data
    CRC16



CRC16 algorithm

    crc = (sum(bytes) + 0x5555) & 0xFFFF

      │
      ▼
+--------------------------------------------------------------+
| 3. DEVICE ENUMERATION                                        |
+--------------------------------------------------------------+

NovaLCT enumerates possible sending cards

Loop over destination address:
dst = 00
dst = 01
dst = 02
...

For each dst NovaLCT reads identity registers:
READ 0x00000002  (Model ID)
READ 0x00000006
READ 0x00000016
READ 0x14000000

Controller response example:
0x00000002 → 01 11

Meaning:
01 11 = controller model family
(MCTRL / MSD family)

Result in NovaLCT UI:
Sending Card = N

Emulator requirement:
Only dst=00 must answer identity registers
dst>=01 must timeout or return ACK error

      │
      ▼
+--------------------------------------------------------------+
| 4. INITIAL SCREEN STATE QUERY                                |
+--------------------------------------------------------------+

Before sending routing commands NovaLCT reads screen state
READ 0x02000000
READ 0x02000100
READ 0x02020020
READ 0x08000000


These registers represent:
controller screen topology tables

If the controller returns invalid data
NovaLCT refuses screen configuration.

      │
      ▼
+--------------------------------------------------------------+
| 5. ROUTING COMMAND STREAM                                    |
+--------------------------------------------------------------+

When user builds screen connection in UI
NovaLCT sends routing commands.

WRITE 0x02000011
Payload length = 6 bytes

Observed structure
[group][a][b][c][x][y]

Example:
260311183435

Interpretation hypothesis:
group = command type
a/b/c = routing parameters
x/y = coordinate or routing word

Multiple commands are sent sequentially:
WRITE 0x02000011
WRITE 0x02000011
WRITE 0x02000011
...
Emulator stores commands in
ROUTING_WRITES[]

      │
      ▼
+--------------------------------------------------------------+
| 6. ROUTING COMMIT                                            |
+--------------------------------------------------------------+

After sending routing segments NovaLCT sends:
WRITE 0x02000018
Payload:
00
Meaning:
Apply routing configuration


Controller must now build screen tables.

      │
      ▼
+--------------------------------------------------------------+
| 7. CONTROLLER SCREEN TABLE GENERATION                        |
+--------------------------------------------------------------+

Controller converts routing commands into topology model
routing commands
        │
        ▼
topology model
        │
        ▼
controller screen blocks

Registers used:
0x02000000
0x02000100
0x02020020
0x08000000

These represent:
screen topology
receiving card chain
tile mapping


Emulator currently synthesizes blocks.

      │
      ▼
+--------------------------------------------------------------+
| 8. SCREEN VALIDATION BY NOVALCT                              |
+--------------------------------------------------------------+

NovaLCT reads again:
READ 0x02000000
READ 0x02000100
READ 0x02020020
READ 0x08000000

If data is valid:
Tiles appear in UI
Screen connection succeeds

If invalid:
tiles > 9 fail
Send to HW fails

      │
      ▼
+--------------------------------------------------------------+
| 9. HARDWARE CONFIGURATION PHASE                              |
+--------------------------------------------------------------+

When user presses:
Send to HW

NovaLCT writes configuration data
to receiving cards via controller.

Examples:
gamma
brightness
panel parameters
scan mode
calibration tables

These writes propagate through
controller → receiving card chain.

      │
      ▼
+--------------------------------------------------------------+
| 10. NORMAL OPERATION                                         |
+--------------------------------------------------------------+

Controller forwards video data
and manages receiving cards.



Emulator goal:
simulate enough controller behavior
so NovaLCT accepts full configuration.


=====================================================================
CURRENT PROJECT STATE
=====================================================================

Discovery        OK
TCP session      OK
Sender identity  OK
sending card = 1

Remaining problem:
screen topology synthesis

Current result:
tiles > 9 = KO
Send to HW = FAIL

Next milestone:

WORKS_18
routing commands
        │
        ▼
topology model
        │
        ▼
correct screen tables


## Error Handling Branch (Observed Behaviour)

During emulator testing NovaLCT showed a secondary behaviour path when configuration writes fail.

Discovery
   │
   ▼
TCP Connection (5200)
   │
   ▼
Identity Reads
   │
   ▼
Routing Commands (0x02000011)
   │
   ▼
Commit (0x02000018)
   │
   ▼
Screen Tables Readback
   │
   ▼
Send to HW
   │
   ├── SUCCESS
   │        │
   │        ▼
   │   Normal operation
   │
   └── FAILURE
            │
            ▼
      Save Attempt
            │
            ▼
      Internal Validation
            │
            ▼
      Possible Re-Enumeration
            │
            ▼
      Device list rebuild

This behaviour suggests NovaLCT may attempt a fallback rescan procedure when configuration persistence fails.


=====================================================================
NEW FINDINGS FROM EMULATOR DEVELOPMENT
=====================================================================

These findings refine the understanding of the topology validation
phase inside NovaLCT.

------------------------------------------------------------
A. TOPOLOGY PROBE MECHANISM
------------------------------------------------------------

NovaLCT does not immediately send the full routing table.

Instead it performs a progressive probe:

route1
validation read
route2
validation read
commit
possible abort

Observed behaviour:

baseline emulator
    route_writes = 2
    commit
    connection reset by NovaLCT

mirror_minimal experiment
    route_writes = 4
    commit
    connection reset

Conclusion:

NovaLCT performs a topology plausibility check on
the first cabinets before continuing.


------------------------------------------------------------
B. VALIDATION REGISTERS ARE NOT PRIMARY GATE
------------------------------------------------------------

Registers tested:

0x0200009D
0x02200117
0x0200000B
0x02000022
0x02000023

Experiments forcing these registers showed:

forcing 0200009D → no change
forcing 02200117 → no change

Conclusion:

Validation registers are secondary indicators,
not the main topology acceptance gate.


------------------------------------------------------------
C. SCREEN BLOCK STRUCTURE MATTERS
------------------------------------------------------------

Blocks synthesized by controller:

0x02000000
0x02000100
0x02020020
0x08000000

These blocks are generated from routing commands.

Experiments modifying the representation of the
first cabinets changed NovaLCT behaviour:

baseline
    abort after 2 cabinets

mirror_minimal
    abort after 4 cabinets

zero_tail
    abort after 2 cabinets

Conclusion:

NovaLCT evaluates the internal coherence
of these blocks during topology construction.


------------------------------------------------------------
D. LIKELY INTERNAL CONTROLLER MODEL
------------------------------------------------------------

Routing commands
        │
        ▼
internal topology model
        │
        ▼
controller screen blocks
        │
        ▼
NovaLCT validation


Possible internal fields:

cabinet geometry
cascade order
sender port mapping
chain length
tile coordinates


------------------------------------------------------------
E. CURRENT WORKING HYPOTHESIS
------------------------------------------------------------

NovaLCT performs progressive validation:

1) receive first routing commands
2) reconstruct topology
3) verify cabinet geometry coherence
4) continue routing if valid

Failure occurs when the generated topology
is inconsistent with NovaLCT expectations.


------------------------------------------------------------
F. CURRENT PROJECT STATUS
------------------------------------------------------------

Discovery                    OK
TCP session                  OK
Identity enumeration         OK
Sending card detected        OK

Topology synthesis           PARTIAL

Observed behaviour:

tiles > 9                    FAIL
Send to HW                   FAIL

However:

routing acceptance improved
from 2 cabinets → 4 cabinets
using simplified topology model.


Next investigation direction:

improve topology synthesis model
for the first cabinets.
