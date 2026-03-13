NovaLCT_Emulator_Knowledge_Base.md
# NovaLCT Emulator – Knowledge Base

Progetto:
Emulatore software della sending card **Novastar MCTRL660**
per permettere a **NovaLCT** di funzionare senza hardware reale.
Protocollo analizzato tramite sniffing e reverse engineering.

---

# Architettura protocollo
Il controller comunica tramite:
1. UDP Discovery
2. TCP session controller
3. Protocollo binario tipo RS232 incapsulato su TCP

## Porte
UDP 3800  
TCP 5200

---

# Struttura pacchetto
Header request:
AA55

Header response:
55AA

Struttura:
head  
ack  
serial  
source  
destination  
deviceType  
port  
rcvIndex  
io (read/write)  
address (32 bit)  
length  
data  
crc16

CRC:
(sum(payload) + 0x5555) & 0xFFFF

---

# Device addressing
destination address (dst)
0x00 = sending card  
0x01+ = altri dispositivi nella catena

NovaLCT enumera i sender interrogando:
0x00000002
0x00000006
0x00000016
0x14000000

Model ID controller:
01 11

---

# Registri importanti

## Routing commands
0x02000011

Record 6 byte.
Formato osservato:
[group][a][b][c][x][y]

Example:
260311183435

---

## Commit routing
0x02000018

Payload:
00

---

# Screen tables lette da NovaLCT
0x02000000
0x02000100
0x02020020
0x08000000

Questi blocchi rappresentano la topologia dello schermo.

---

# Pipeline reale del controller
Sequenza osservata:
WRITE 0x02000011 (routing segment)
WRITE 0x02000011
WRITE 0x02000011
...
WRITE 0x02000018 (commit)
READ screen tables
---

# Architettura emulatore
## Routing command space
ROUTING_WRITES[]
Non memoria persistente.

---

## Topology model
SCREEN_WRITES[]
Interpretazione logica dei routing records.

---

## Controller readback blocks
CTRL_BLOCKS
0x02000000
0x02000100
0x02020020
0x08000000

---

# Milestones progetto
## Works_01 – Works_05
- TCP server base
- handshake protocol
- parsing pacchetti

---

## Works_06 – Works_08
- NovaLCT rileva controller
- UI Screen Connection appare

Problema:
Send to HW FAIL

---

## Works_09 – Works_13
Introduzione:
memory map multidimensionale
(dev, port, rcvIndex, dst, address)

Bug scoperto:
overlay memoria tra:
0x02000011
0x02000000
0x02000100

---

## Works_14
Fix:
separazione
routing command space
vs
controller readback memory

---

## Works_15
Tentativo di migliorare screen blocks.

Bug:
sending card = 20

Causa:
enumerazione sender troppo permissiva.

---

## Works_16
Fix enumerazione sender.

Regole:
dst=00 → sender reale
dst>=01 → timeout registri identity

Risultato:
sending card = 1

---

# Stato attuale progetto
sending card = 1
tiles >9 = KO
Send to HW = SI

Commit routing funziona.

NovaLCT invia:
WRITE 0x02000011
WRITE 0x02000018

---

# Root cause probabile
I blocchi screen sintetici non rappresentano correttamente la topologia reale.

Attualmente l'emulatore fa:
routing commands
→ packing quasi diretto
→ screen blocks

Il controller reale probabilmente fa:
routing commands
→ costruzione topology table
→ serializzazione controller blocks

---

# Prossima milestone

## Works_18
Implementare:
routing commands
→ topology model
→ screen table serializer

Rimuovere dai blocchi:
dst=FF
group
a/b/c

Usare solo dati topologici:
tile_index
chain_index
sender_port
route_word

---

# Obiettivo finale
sending card = 1
tiles >9 = OK
Send to HW = OK

NovaLCT deve poter configurare completamente la schermata senza hardware reale.

---

# File chiave progetto
Per riprendere lavoro in una nuova sessione caricare:
NovaLCT_Emulator_Knowledge_Base.md
tcp_server.py
state.md
log.md
Packet.ts
NovaStart_Protocol_file_RS232_V16.pdf
ultimo tcp5200 log

---

---

## NovaLCT Fail-Save Behaviour Observation

During emulator testing a previously undocumented behaviour of NovaLCT was observed.

Test sequence:

1. Enter the "Receiving Card" section
2. Load a .rcfgx receiving card configuration
3. Open "Screen Connection"
4. Create routing with approximately 15 tiles
5. Execute "Send to HW" → Result: Failed to send data
6. Return to "Receiving Card"
7. Press "Save" → Result: Failed to send data
8. Return to "Screen Connection"
9. Press "Save" → Result: Failed to send data

Unexpected result:

After the second save failure the number of detected devices changed from:

1 → 20

Interpretation:

This suggests that NovaLCT may enter a fallback or re-enumeration mode after persistent configuration failures.

Possible internal behaviour:

Send to HW → fail
      │
      ▼
Receiving Card Save → fail
      │
      ▼
Screen Connection Save → fail
      │
      ▼
NovaLCT invalidates current topology
      │
      ▼
Controller / device re-enumeration

Hypothesis:

After configuration write failure NovaLCT may:

• reset internal topology state  
• rescan controller identity registers  
• rebuild the device list  

This behaviour could temporarily reproduce the historical bug where multiple sending cards are detected.

Further logging during this sequence will be required to confirm which registers or commands are involved.

---

## Project Status Snapshot

Current emulator status:
UDP Discovery                OK
TCP/5200 session             OK
Sender identity              OK
Routing command parsing      OK
Commit handling              OK

Screen topology validation   NOT YET SOLVED
Tiles > 9 configuration      FAIL
Send to HW                   FAIL

Next investigation areas:
• screen block structure refinement  
• validation registers around 0x02000000 range  
• behaviour during "Send to HW" and configuration persistence

---

---

# UPDATE — Emulator Development (Works_26 → Works_33)

## Background

After stabilizing the controller session and screen block synthesis
in Works_24, additional investigations were performed to understand
why NovaLCT rejects routing configurations beyond tile index 9.

Observed behaviour:

sending card = 1
tiles > 9 = KO
Send to HW = NO


## Validation Register Experiments

The following registers were suspected as topology validation gates:

0x0200009D
0x02200117
0x0200000B
0x02000022
0x02000023

Multiple emulator builds attempted to force these values
during routing and commit phases.

Results:

forcing 0x0200009D → no behavioural change
forcing 0x02200117 → no behavioural change

Conclusion:

These registers are **not the primary acceptance gate**
for screen topology.


## Topology Probe Behaviour

Analysis of routing traffic revealed that NovaLCT performs
a progressive topology probe.

Typical sequence observed:

READ screen blocks
WRITE route entry
WRITE route entry
READ validation registers
WRITE route entry
WRITE route entry
COMMIT


Baseline emulator behaviour:

route writes accepted: 2
NovaLCT aborts session


Experimental builds modifying screen block structure produced:

route writes accepted: 4
NovaLCT aborts session


Interpretation:

NovaLCT evaluates the internal consistency of the topology
generated from the first routing entries.


## Screen Block Synthesis

Controller readback blocks involved:

0x02000000
0x02000100
0x02020020
0x08000000

These blocks are not simple memory storage but are
generated representations of the routing topology.

They likely encode:

- cabinet geometry
- cascade order
- sender port mapping
- receiving card index
- tile coordinate system


## Key Insight

The emulator is no longer blocked by register validation.

The current blocker is:

**topology representation inside screen blocks.**


## Current Project Status

Discovery UDP: OK  
TCP session: OK  
Controller detection: OK  
Sending card: OK  

Topology acceptance: PARTIAL


Observed limitation:

tiles beyond index 9 rejected


## Next Development Direction

Improve topology synthesis model
used to generate controller screen blocks.

Focus area:

first cabinets used by NovaLCT
as topology validation probe.


---

# Parola di ripartenza
MCTRL660_STEP_NEXT


