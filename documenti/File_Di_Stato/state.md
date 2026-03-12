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

CURRENT PROJECT STATUS

Discovery layer
Status: WORKING

UDP discovery is functioning correctly and NovaLCT detects the virtual
controller.

---------------------------------------------------------------------

TCP protocol session
Status: WORKING

NovaLCT opens a stable TCP connection on port 5200.

Observed protocol flow:

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

Current visible result:
sending card = 1

Identity registers implemented and stable:

0x00000002
0x00000006
0x00000016
0x14000000

Only dst=00 is exposed as a valid sender identity.

---------------------------------------------------------------------

Routing commands
Status: WORKING

Routing records are received through:

0x02000011

Commit command:

0x02000018

These registers are correctly handled as commands and are no longer
written into generic memory.

Routing commands are parsed into logical topology data.

---------------------------------------------------------------------

Screen topology reconstruction
Status: PARTIALLY WORKING

The emulator synthesizes the following controller-level blocks:

0x02000000
0x02000100
0x02020020
0x08000000

These are rebuilt from routing entries and read back correctly by
NovaLCT.

Current situation:
- topology pipeline is functional
- NovaLCT reads the blocks successfully
- but topology is still not fully accepted

Observed result:
tiles > 9 = KO

This remains the main unresolved functional blocker.

---------------------------------------------------------------------

Receiving-card configuration flow
Status: PARTIALLY WORKING

Registers now handled:

0x02100000
0x05000000
0x05065000
0x05066000

Important finding:
NovaLCT writes a 256-byte blob to:

0x05066000

Observed header:

53535045ea030000

ASCII:
SSPE

This acts as a save/config marker and is now recognized by the emulator.

The emulator now generates non-zero semantic configuration state after
save marker acceptance.

---------------------------------------------------------------------

Save / persistence branch
Status: STABLE ENOUGH FOR CONTINUED WORK

A major milestone was achieved in this session.

Previous behaviour:
after save failure NovaLCT often entered fallback mode,
device count could jump from 1 to 20,
and the software showed:
"Please reconnect the device"

Current behaviour with Works_24:
- device remains visible
- device count stays at 1
- "Please reconnect the device" no longer appears

This means the save / persistence branch is significantly improved.

---------------------------------------------------------------------

Validation registers
Status: PARTIALLY UNDERSTOOD

Important validation-related registers observed:

0x0200000B
0x02000022
0x02000023
0x0200009D
0x02200117
0x03100109

Current strongest hypothesis:

0x02200117 is a key receiving-card configuration validity flag.

Problem:
during topology validation NovaLCT still sees 0x02200117 at the wrong
time / wrong state, so topology is likely rejected before the system is
considered fully configured.

---------------------------------------------------------------------

Current stable base
Status: Works_24

Works_24 is now the best current baseline because it preserves:

- device = 1
- no reconnect collapse
- no "Please reconnect the device"

while still allowing continued investigation of the topology-validation
problem.

Works_23 is NOT the correct base because it exposed configured state too
early and caused regression to fallback/re-enumeration.

---------------------------------------------------------------------

CURRENT PRIMARY BLOCKER

The remaining blocker is no longer generic save failure.

The remaining blocker is:

screen topology acceptance timing and validation semantics

Most likely centered around:
- 0x02200117
- relation between topology_count and config-valid state
- order in which NovaLCT expects these states to become valid

---------------------------------------------------------------------

NEXT INVESTIGATION TARGET

Works_25

Focus:
- keep Works_24 as baseline
- preserve:
  - device = 1
  - no reconnect
  - stable save flow
- refine timing of:
  0x02200117
- make receiving-card configuration become valid at the correct moment
  relative to topology validation, not too early and not too late

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