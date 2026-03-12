NovaLCT Emulator Project
Target device: MCTRL660
Protocol: NovaLCT TCP control protocol (port 5200)

Current state reference:
MCTRL660_STEP_NEXT

---------------------------------------------------------------------

PROJECT OBJECTIVE

Reproduce the behaviour of a NovaStar MCTRL660 sending card in order
to allow NovaLCT to interact with an emulator exactly as it would
with the real hardware.

The emulator must support:

• device discovery
• controller identity
• routing configuration
• screen topology reconstruction
• hardware configuration commit

---------------------------------------------------------------------

CURRENT PROJECT STATUS

Discovery layer
Status: WORKING

UDP discovery is correctly implemented and NovaLCT detects the emulator.

---------------------------------------------------------------------

TCP protocol session
Status: WORKING

NovaLCT opens a TCP connection on port 5200.

Observed command pattern:

READ identity registers
WRITE routing commands
COMMIT configuration
READ screen topology blocks

Protocol framing (55AA / AA55) and checksum handling are stable.

---------------------------------------------------------------------

Controller identity
Status: WORKING

NovaLCT detects exactly one sending card.

sending card = 1

Identity registers implemented:

0x00000002
0x00000006
0x00000016
0x14000000

These registers correctly emulate an MCTRL660 controller.

---------------------------------------------------------------------

Routing commands
Status: WORKING

Routing commands are received through register:

0x02000011

Each command contains a 6-byte routing record.

Example:

260311183435

Routing entries are stored in a dedicated command space
and parsed into logical routing records.

Commit command:

0x02000018

Triggers reconstruction of controller screen blocks.

---------------------------------------------------------------------

Screen topology reconstruction
Status: PARTIALLY WORKING

Screen blocks currently generated:

0x02000000  (layout table)
0x02000100  (cascade table)
0x02020020  (summary table)
0x08000000  (presence map)

These blocks are synthesized from routing entries.

NovaLCT successfully reads the blocks and the emulator
rebuilds topology data dynamically.

However NovaLCT still rejects the configuration.

Current result:

tiles > 9 = KO

This indicates the topology serialization does not yet match
the exact structure expected by the real controller.

---------------------------------------------------------------------

Hardware commit
Status: NOT WORKING

Send to HW operation fails.

NovaLCT response:

Failed to send data

This likely indicates that additional metadata or validation
fields inside the topology blocks are missing or incorrect.

---------------------------------------------------------------------

Observed secondary behaviour

During testing the following behaviour was observed:

Send to HW → Failed
Receiving Card Save → Failed
Screen Connection Save → Failed

After these failures NovaLCT changes the detected device count:

1 → 20

Hypothesis:

NovaLCT may enter a fallback re-enumeration mode after persistent
configuration write failures.

Further logging is required to understand the protocol branch
executed in this situation.

---------------------------------------------------------------------

CURRENT PRIMARY BLOCKER

Exact structure of controller screen topology blocks.

The emulator must reproduce the same internal layout used by the
MCTRL660 controller when serializing topology data.

Without this NovaLCT refuses to commit the configuration.

---------------------------------------------------------------------

NEXT INVESTIGATION TARGETS

1. Refine screen topology block structure.

2. Investigate validation registers near:

0x02000000
0x0200000B
0x02000023
0x0200009D

3. Capture full protocol sequence during:

Send to HW
Receiving Card Save
Screen Connection Save

4. Analyze how NovaLCT validates topology before allowing commit.

---------------------------------------------------------------------

END STATE SNAPSHOT

Discovery             OK
TCP session           OK
Controller identity   OK
Routing commands      OK
Commit command        OK

Screen topology       NOT VALIDATED
Tiles > 9             FAIL
Send to HW            FAIL

---------------------------------------------------------------------