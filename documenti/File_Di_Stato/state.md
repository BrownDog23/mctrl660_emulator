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

CURRENT PROJECT STATUS (2026-03-16)

Discovery layer
Status: WORKING

UDP discovery is fully functional and NovaLCT reliably detects
the virtual controller.

---------------------------------------------------------------------

TCP protocol session
Status: WORKING

NovaLCT opens a stable TCP connection on port 5200.

Confirmed protocol flow:

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

Implemented identity registers:

0x00000002
0x00000006
0x00000016
0x14000000

Only dst=00 is exposed as valid controller identity.

---------------------------------------------------------------------

Routing commands
Status: WORKING

Routing entries are received through:

0x02000011

Commit command:

0x02000018

These are correctly handled as command registers and are no longer
written into generic persistent memory.

Routing commands are parsed into an internal topology structure.

---------------------------------------------------------------------

Save / persistence branch
Status: STABLE

Receiving-card configuration save handling is stable enough
for continued work.

Implemented registers:

0x02100000
0x05000000
0x05065000
0x05066000

Observed save/config marker:

0x05066000
header: 53535045ea030000
ASCII: SSPE

Current behaviour:
- device remains visible
- device count stays at 1
- "Please reconnect the device" no longer appears

This branch is no longer the main blocker.

---------------------------------------------------------------------

Validation registers
Status: INVESTIGATED / NOT PRIMARY BLOCKER

Registers tested:

0x0200000B
0x02000022
0x02000023
0x0200009D
0x02200117
0x03100109

Experimental forcing and timing adjustments showed that:

- 0x0200009D is not the primary topology gate
- 0x02200117 is not the primary topology gate

These registers participate in the protocol state,
but they do not by themselves explain routing rejection.

---------------------------------------------------------------------

Screen topology reconstruction
Status: PARTIALLY WORKING

The emulator synthesizes controller-level screen blocks:

0x02000000
0x02000100
0x02020020
0x08000000

NovaLCT reads these blocks successfully,
but still rejects topology during early routing validation.

Observed result:
tiles > 9 = KO
Send to HW = Failed

---------------------------------------------------------------------

Best experimental branch

Works_33 is currently the best experimental branch.

Observed behaviour with Works_33:
NovaLCT accepted routing up to 5 route writes before aborting.

This is the strongest improvement observed so far.

Works_34b / Works_35 / Works_36 / Works_37 / Works_38 /
Works_39 / Works_40 did not improve over Works_33 and were
mainly useful for excluding incorrect hypotheses.

---------------------------------------------------------------------

Important exclusions

The following are now considered excluded as main isolated causes:

- validation registers alone
- 0x08000000 alone
- 0x02000100 alone
- simple extension of W33 byte patterns
- cabinet sorting as the sole blocker

---------------------------------------------------------------------

Current main blocker

The remaining blocker is the semantic interpretation
of the routing payload and the topology model derived from it.

In other words:

NovaLCT is rejecting the combined topology coherence
of the synthesized screen blocks.

This is no longer a simple byte-patching problem.

---------------------------------------------------------------------

NEXT INVESTIGATION TARGET

Start a new reverse engineering phase focused on:

route payload semantics

Main fields to understand:

- x
- y
- c
- tile_index
- cascade_order
- layout_x
- layout_y

Goal:
derive the true topological model expected by NovaLCT,
then regenerate all 4 controller-level screen blocks
from that semantic model.

---------------------------------------------------------------------

Recommended working reference

Stable base:
Works_24

Best experimental branch:
Works_33

Next work should begin from:
- Works_24 for stability
- Works_33 for topology-probe reference

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