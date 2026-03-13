=====================================================================
          NOVALCT SCREEN BLOCKS – PROBABLE INTERNAL STRUCTURE
=====================================================================

Scopo:
ricostruire il significato probabile dei blocchi letti da NovaLCT
dopo i routing commands e il commit.

Blocchi osservati:

    0x02000000
    0x02000100
    0x02020020
    0x08000000


=====================================================================
1. VISIONE GENERALE
=====================================================================

routing commands (0x02000011, 6 byte)
        │
        ▼
controller internal topology model
        │
        ├──► 0x02000000   main topology table
        ├──► 0x02000100   secondary / mirrored topology table
        ├──► 0x02020020   compact summary / validation block
        └──► 0x08000000   activation / presence bitmap


Ipotesi forte:

i routing records NON vengono copiati direttamente nei blocchi finali,
ma vengono prima trasformati in una tabella topologica interna.


=====================================================================
2. BLOCCO 0x02000000
=====================================================================

Dimensione osservata:
256 byte

Ruolo probabile:
MAIN SCREEN TOPOLOGY TABLE


Struttura ipotizzata:

Offset    Size    Significato probabile
--------------------------------------------------
0x00      1       controller_count_or_flag
0x01      1       block_type / version
0x02      1       dev
0x03      1       port
0x04      1       route_count / entry_count
0x05      1       fixed flag / mode
0x06      1       fixed flag
0x07      1       fixed flag
0x08      8       reserved / unknown
0x10      N*8     topology entries
...               zero padding


Esempio osservato (Works_16b):

0101000003200101
0000000000000000
343500ff03111826
345500ff03111826
351500ff03111826
...


Interpretazione attuale dei primi 8 byte:

01  = sender/controller visible count fixed at 1
01  = table type / version
00  = dev
00  = port
03  = route_count
20  = constant / mode
01  = flag
01  = flag


Problema:
la parte entries contiene ancora troppi elementi "raw-oriented":

3435 00 ff 03 11 18 26

cioè:
x y rcvIndex dst a b c group

Questo è probabilmente troppo vicino al command stream originale.


---------------------------------------------------------------------
2A. ENTRY PROBABILE REALE DI 0x02000000
---------------------------------------------------------------------

Entry size probabile:
8 byte

Possibile forma logica reale:

byte0   tile_index
byte1   sender_port
byte2   chain_index
byte3   output_group / segment_group
byte4   x_or_route_hi
byte5   y_or_route_lo
byte6   flags
byte7   reserved

Oppure:

byte0   tile_index
byte1   row
byte2   column
byte3   sender_port
byte4   chain_index
byte5   flags
byte6   reserved
byte7   reserved


Ipotesi forte:
NovaLCT si aspetta una lista di tile/logical nodes,
NON una copia decorata dei 6 byte raw.


=====================================================================
3. BLOCCO 0x02000100
=====================================================================

Dimensione osservata:
256 byte

Ruolo probabile:
SECONDARY TOPOLOGY TABLE
oppure
MIRROR / VALIDATION TABLE


Esempio osservato:

01a5000003200101
0000000000000000
26181103ff003534
26181103ff005534
26181103ff001535
...


Struttura ipotizzata:

Offset    Size    Significato probabile
--------------------------------------------------
0x00      1       controller_count_or_flag
0x01      1       table_signature / subtype
0x02      1       dev
0x03      1       port
0x04      1       route_count
0x05      1       fixed flag / mode
0x06      1       fixed flag
0x07      1       fixed flag
0x08      8       reserved / unknown
0x10      N*8     validation entries / mirrored entries
...               zero padding


Differenza rispetto a 0x02000000:

0x02000100 sembra essere una variante ordinata o specchiata
della stessa topologia.

Nel tuo emulatore attuale contiene l'entry invertita:

26181103ff003534

cioè reverse di:

343500ff03111826


Ipotesi forte:
0x02000100 non è semplicemente "reverse bytes",
ma una tabella parallela con campi diversi:

- maybe source-to-destination mapping
- maybe route validation sequence
- maybe chain traversal serialization


---------------------------------------------------------------------
3A. ENTRY PROBABILE REALE DI 0x02000100
---------------------------------------------------------------------

Entry size probabile:
8 byte

Possibile forma logica reale:

byte0   chain_index
byte1   sender_port
byte2   tile_index
byte3   reserved / flags
byte4   route_hi
byte5   route_lo
byte6   reserved
byte7   reserved

Oppure:

byte0   upstream_node
byte1   downstream_node
byte2   sender_port
byte3   chain_index
byte4   flags
byte5   flags
byte6   reserved
byte7   reserved


Ipotesi:
0x02000000 e 0x02000100 sono due viste della stessa topologia:

- table A = layout order
- table B = chain order


=====================================================================
4. BLOCCO 0x02020020
=====================================================================

Dimensione osservata:
64 byte

Ruolo probabile:
COMPACT SUMMARY / QUICK VALIDATION BLOCK


Esempio osservato:

0100000300000000
3435ff00
3455ff00
3515ff00
...


Struttura ipotizzata:

Offset    Size    Significato probabile
--------------------------------------------------
0x00      1       controller_count_or_flag
0x01      1       dev
0x02      1       port
0x03      1       route_count
0x04      4       reserved / mode / checksum seed?
0x08      N*4     compact per-entry summary
...               zero padding


Attualmente l'emulatore usa:

x y dst rcvIndex

Questo è ancora troppo vicino al routing raw.

Più probabile invece:

entry compact 4 byte:

byte0   tile_index
byte1   sender_port
byte2   chain_index
byte3   flags

Oppure:

byte0   route_hi
byte1   route_lo
byte2   logical_order
byte3   enable


Ruolo probabile nel software:
NovaLCT può usarlo come verifica rapida per capire:

- quanti nodi esistono
- ordine minimo della catena
- quali tile sono attivi


Ipotesi forte:
questo blocco è un "digest" della topologia,
non la topologia completa.


=====================================================================
5. BLOCCO 0x08000000
=====================================================================

Dimensione osservata:
256 byte

Ruolo probabile:
ACTIVATION MAP / PRESENCE BITMAP / ENABLE TABLE


Esempio osservato con 3 entries:

0101010000000000...


Interpretazione attuale:
ogni byte iniziale = 1 per tile attivo


Struttura ipotizzata:

Offset    Size    Significato probabile
--------------------------------------------------
0x00      N       active tile bitmap / enable bytes
...               zero padding


Ipotesi 1:
1 byte per tile

byte[i] = 01  -> tile presente
byte[i] = 00  -> tile assente


Ipotesi 2:
bitmap per gruppi di 8 tile

bit0 = tile0
bit1 = tile1
...


Dai log attuali sembra più probabile la forma semplice:

un byte per tile attivo


Ruolo probabile:
NovaLCT lo usa per decidere rapidamente
se la topologia è "popolata" oppure vuota.


=====================================================================
6. RELAZIONE TRA I BLOCCHI
=====================================================================

+---------------------------------------------------------------+
| 0x02000000                                                    |
| Topologia principale                                          |
| "layout order"                                                |
+---------------------------------------------------------------+

+---------------------------------------------------------------+
| 0x02000100                                                    |
| Topologia secondaria                                          |
| "chain order" / "validation order"                            |
+---------------------------------------------------------------+

+---------------------------------------------------------------+
| 0x02020020                                                    |
| Riassunto compatto                                            |
| count / compact nodes / fast validation                       |
+---------------------------------------------------------------+

+---------------------------------------------------------------+
| 0x08000000                                                    |
| Presence / activation map                                     |
| quali tile sono presenti                                      |
+---------------------------------------------------------------+


NovaLCT probabilmente fa una validazione di coerenza:

    if
        count(0x02000000) matches
        count(0x02000100) matches
        summary(0x02020020) coherent
        active_map(0x08000000) coherent
    then
        accept topology
    else
        reject topology


=====================================================================
7. PERCHÉ tiles > 9 FALLISCE
=====================================================================

Ipotesi tecnica più forte:

NON è un problema di quantità pura.

È un problema di coerenza semantica tra i blocchi.


Possibili cause:

1. 0x02000000 contiene ancora campi raw-oriented
   (dst=FF, group, a/b/c)

2. 0x02000100 è costruito come semplice reverse bytes
   invece di una vera tabella secondaria

3. 0x02020020 è troppo povero e non rappresenta davvero
   la summary chain

4. 0x08000000 è corretto solo come "presence",
   ma non basta se gli altri blocchi non concordano


=====================================================================
8. MODELLO DI SERIALIZZAZIONE PIÙ CREDIBILE
=====================================================================

routing commands
    │
    ▼
parse_route_record()
    │
    ▼
TOPOLOGY_STATE = [
    {
        tile_index,
        sender_port,
        chain_index,
        route_word,
        x,
        y
    }
]
    │
    ├──► serialize_main_table()      -> 0x02000000
    ├──► serialize_chain_table()     -> 0x02000100
    ├──► serialize_summary_table()   -> 0x02020020
    └──► serialize_presence_map()    -> 0x08000000


Questo è probabilmente molto più vicino al comportamento reale
del controller.


=====================================================================
9. IPOTESI OPERATIVA PER WORKS_18
=====================================================================

Rimuovere dai blocchi finali:

- dst
- group
- a
- b
- c


Conservare nel topology model solo:

- tile_index
- sender_port
- chain_index
- route_word
- x
- y


Esempio entry proposta per 0x02000000:

byte0   tile_index
byte1   sender_port
byte2   chain_index
byte3   0x00
byte4   x
byte5   y
byte6   0x00
byte7   0x00


Esempio entry proposta per 0x02000100:

byte0   chain_index
byte1   tile_index
byte2   sender_port
byte3   0x00
byte4   x
byte5   y
byte6   0x00
byte7   0x00


Esempio entry proposta per 0x02020020:

byte0   tile_index
byte1   sender_port
byte2   chain_index
byte3   0x01


Esempio 0x08000000:

byte[i] = 0x01 se tile i presente
byte[i] = 0x00 altrimenti


=====================================================================
10. STATO ATTUALE DEL REVERSE ENGINEERING
=====================================================================

Confermato:

- 0x02000011 = routing command stream
- 0x02000018 = commit
- 0x02000000 / 0x02000100 / 0x02020020 / 0x08000000
  = blocchi controller-level di topologia
- sender identity ormai corretta
- sending card = 1 corretto


Ancora ignoto:

- formato esatto delle entries nei blocchi
- relazione precisa tra table A e table B
- significato reale di x/y rispetto ai tile
- eventuali campi row/column nascosti


=====================================================================
11. CONCLUSIONE
=====================================================================

Il problema residuo NON è più:

- rete
- TCP
- checksum
- identity
- commit

Il problema residuo è:

RICOSTRUIRE IL FORMATO SEMANTICO DELLE SCREEN TABLES


Obiettivo:

routing commands
    │
    ▼
topology model corretto
    │
    ▼
screen blocks coerenti
    │
    ▼
tiles > 9 OK
Send to HW OK

=====================================================================


---

# New Findings — Screen Block Behaviour (Works_26 → Works_33)

## Observation

NovaLCT reads controller screen blocks during
screen routing operations.

Registers involved:

0x02000000
0x02000100
0x02020020
0x08000000


These reads occur **before routing commit**.


## Behaviour During Routing

Routing commands are written through:

0x02000011

Followed by:

0x02000018 (commit)


However NovaLCT already reads screen blocks
before commit.


## Experimental Variations

Different synthesis strategies were tested.

### Baseline

Standard topology reconstruction.

Observed behaviour:

routing accepted: 2 entries


### Mirror Minimal

Simplified replication of early cabinet structure.

Observed behaviour:

routing accepted: 4 entries


### Zero Tail

Remaining entries filled with zeros.

Observed behaviour:

routing accepted: 2 entries


## Interpretation

NovaLCT validates topology incrementally.

The first cabinets appear to function as a
**topology probe**.

NovaLCT likely verifies:

geometry coherence  
cascade continuity  
cabinet ordering  


## Hypothesis

Screen blocks may contain a compact representation
of the topology model.

Possible structure:

02000000 → cabinet layout table  
02000100 → cascade chain table  
02020020 → topology summary  
08000000 → device presence / descriptors


## Implication for Emulator

The emulator must generate screen blocks
based on a coherent internal topology model.

Direct memory mirroring is insufficient.


## Current Focus

Improve the structure of the first cabinets
inside the synthesized screen blocks.

This should allow NovaLCT to accept
routing tables larger than 9 tiles.


================================================================