===========================================================
1. MODELLO DI BASE DEL DISPOSITIVO
===========================================================

LINSN
-----
- Sending card
- Receiving card
- Configurazione salvata in flash
- Configurazione runtime in RAM

NOVASTAR (osservato)
--------------------
- Sending card (controller)
- Receiving card (rcvIndex)
- memoria runtime (blocchi 0x02000000 ecc.)
- commit/save (0x02000018 + SSPE)

IMPLICAZIONE PER L'EMULATORE
----------------------------
Serve mantenere:

state_runtime_topology
state_runtime_registers
state_flash_parameters
state_commit_status


===========================================================
2. SCRITTURA PARAMETRI
===========================================================

LINSN
-----
WriteMemory(address, data)

con:
StartX
StartY
Width
Height
CardMode
MaxWidth
MaxHeight

NOVASTAR (osservato)
--------------------
Write register:

0x02000011   route record
0x02000018   commit

blocchi sintetizzati:

0x02000000
0x02000100
0x02020020
0x08000000

IPOTESI
-------
I blocchi sintetizzati rappresentano:

layout geometry
cascade order
port topology
device descriptor


===========================================================
3. ROUTING / TOPOLOGIA
===========================================================

LINSN
-----
Display topology costruita tramite:

StartX
StartY
Width
Height
scan chain order

NOVASTAR
--------
routing record:

0x02000011

campi osservati:

layout_x
layout_y
sender_port
cascade_order
tile_index

IPOTESI
-------
NovaLCT usa i primi cabinet per verificare:

geometria plausibile
ordine cascata coerente
coerenza layout ↔ cascade



===========================================================
4. STATO DI VALIDAZIONE
===========================================================

LINSN
-----
device state machine:

RAM state
FLASH state
PARAMETER STORE

NOVASTAR
--------
registri letti frequentemente:

0x0200000B
0x02000022
0x02000023
0x02200117
0x0200009D

OSSERVAZIONE
------------
Non sono il gate principale
ma fanno parte della state machine.


===========================================================
5. SAVE / PERSISTENZA
===========================================================

LINSN
-----
write flash
checksum
commit

NOVASTAR
--------
save marker osservato:

0x05066000 = "SSPE"

poi:

0x0200009D = 01

IPOTESI
-------
NovaLCT verifica:

config salvata
config runtime coerente
topology valida


===========================================================
6. PROBE INIZIALE DELLA TOPOLOGIA
===========================================================

OSSERVAZIONE DAI LOG
--------------------

NovaLCT:

route1
validation read
route2
commit
abort

oppure (mirror_minimal):

route1
route2
route3
route4
commit
abort

INTERPRETAZIONE
---------------

NovaLCT usa i primi cabinet come:

topology probe



===========================================================
7. BLOCCO PIÙ SOSPETTO
===========================================================

BLOCCHI SINTETICI

0x02000000
0x02000100
0x02020020
0x08000000

FUNZIONE PROBABILE

02000000 → layout table
02000100 → cascade table
02020020 → summary / count
08000000 → device descriptors


===========================================================
8. DIREZIONE DI SVILUPPO DELL'EMULATORE
===========================================================

FASE 1 (fatta)
--------------
validation registers

FASE 2 (attuale)
----------------
topology block synthesis

FASE 3 (probabile)
------------------
geometry model

screen_width
screen_height
cabinet positions
chain validation

------------

Sintesi operativa
La retroingegneria Linsn suggerisce che:

topologia display
=
geometria
+
ordine cascata
+
config receiving card
+
stato persistente