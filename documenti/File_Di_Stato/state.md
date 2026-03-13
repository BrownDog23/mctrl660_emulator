NovaLCT Emulator Project
Target device: MCTRL660
Protocol: NovaLCT TCP control protocol (port 5200)

Current state reference:
MCTRL660_STEP_NEXT

---------------------------------------------------------------------

PROJECT OBJECTIVE

Emulate a NovaStar MCTRL660 sending card closely enough that NovaLCT
can interact with the emulator as if it were real hardware.

The emulator must support:

- discovery
- controller identity
- routing configuration
- screen topology reconstruction
- receiving-card configuration flow
- save / hardware commit flow

---------------------------------------------------------------------

CURRENT PROJECT STATUS (2026-03-13)

Discovery layer
Status: WORKING

UDP discovery is fully functional and NovaLCT reliably detects
the virtual controller.

---------------------------------------------------------------------

TCP protocol session
Status: WORKING

NovaLCT opens a stable TCP connection on port 5200.

Protocol flow confirmed:

identity reads
routing writes
commit
screen topology reads
receiving-card validation reads
save/config writes

Packet framing and checksum handling are stable.

---------------------------------------------------------------------

Controller identity
Status: WORKING

NovaLCT detects exactly one sending card.

Observed result:
sending card = 1

Identity registers implemented:

0x00000002
0x00000006
0x00000016
0x14000000

Only dst=00 is exposed as controller identity.

---------------------------------------------------------------------

Routing command handling
Status: WORKING

Routing entries are received through:

0x02000011

Commit command:

0x02000018

These registers are treated as command registers
and are not written to persistent memory.

Routing commands are parsed into an internal topology model.

---------------------------------------------------------------------

Screen topology reconstruction
Status: PARTIALLY WORKING

The emulator synthesizes controller-level screen blocks:

0x02000000
0x02000100
0x02020020
0x08000000

These blocks are reconstructed from routing entries and
read back correctly by NovaLCT.

However the topology is still rejected during validation.

Observed result:

tiles > 9 = KO

This remains the primary functional blocker.

---------------------------------------------------------------------

Receiving-card configuration flow
Status: PARTIALLY WORKING

Registers implemented:

0x02100000
0x05000000
0x05065000
0x05066000

NovaLCT writes a 256-byte blob to:

0x05066000

Observed header:

53535045ea030000

ASCII:
SSPE

This is interpreted as a configuration save marker and
is now recognized by the emulator.

---------------------------------------------------------------------

Save / persistence branch
Status: STABLE

Earlier versions triggered a fallback mode where NovaLCT
re-enumerated devices and temporarily showed:

device count = 20
"Please reconnect the device"

With Works_24 and later versions:

device remains visible
device count stays at 1
no reconnect message appears

This branch is now considered stable enough for further work.

---------------------------------------------------------------------

Validation registers
Status: INVESTIGATED

Registers examined:

0x0200009D
0x02200117
0x0200000B
0x02000022
0x02000023

Experiments forcing these registers during routing
did not change NovaLCT behaviour.

Conclusion:

Topology acceptance is not controlled solely by these registers.

---------------------------------------------------------------------

Topology probe behaviour

Experimental builds modifying the representation of early
screen topology blocks revealed an important pattern.

Baseline topology synthesis:

NovaLCT accepts only two routing entries.

Modified synthesis ("mirror_minimal"):

NovaLCT continues routing up to four entries.

Interpretation:

NovaLCT performs an incremental topology validation using
the first cabinets as a probe before accepting the full routing.

---------------------------------------------------------------------

Current baseline

Works_24 remains the stable reference implementation.

Later experimental builds investigate topology synthesis
without breaking the stability achieved in Works_24.

---------------------------------------------------------------------

CURRENT PRIMARY BLOCKER

Screen topology acceptance by NovaLCT.

Symptoms:

tiles > 9 = KO
Send to HW = Failed

Most likely cause:

incorrect internal structure of controller screen blocks.

---------------------------------------------------------------------

NEXT INVESTIGATION TARGET

Improve topology synthesis model used to generate:

0x02000000
0x02000100
0x02020020
0x08000000

Focus on the structure of the first cabinets which NovaLCT
appears to use as a topology validation probe.

---------------------------------------------------------------------

END STATE SNAPSHOT

Discovery                 OK
TCP session               OK
Controller identity       OK
Routing commands          OK
Commit command            OK
Save/persistence branch   STABLE
Device visibility         STABLE (device = 1)

Tiles > 9                 FAIL
Send to HW                FAIL
Topology acceptance       NOT YET SOLVED

---------------------------------------------------------------------