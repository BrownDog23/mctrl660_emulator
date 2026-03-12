# MCTRL660 Emulator – LOG (Append-Only)

⚠️ Questo file è APPEND-ONLY.
Non modificare righe precedenti.
Aggiungere sempre una nuova voce in fondo.

Formato voce:
YYYY-MM-DD HH:MM — [SESSION TAG] — Descrizione sintetica modifiche

---

2026-01-24 01:46 — INIT_ANALYSIS —
Analisi log NovaLCT (LCT.log / Mars.log). Identificato uso TCP 443 e protocollo 55AA + FE.

2026-02-18 16:30 — NETWORK_DEBUG_PHASE1 —
Test Wireshark su VirtualBox Host-Only (192.168.56.1). Nessuna risposta da emulatore su 443.

2026-02-18 18:10 — DISCOVERY_ANALYSIS —
Osservato traffico UDP 3702 (WS-Discovery), 1900 (SSDP), 6666. Nessuna risposta device-side.

2026-02-19 00:52 — TCP_TEST_SYN_ONLY —
NovaLCT tenta connessione TCP verso 192.168.0.10:443.
Solo SYN e retransmission. Nessun SYN/ACK.

2026-02-19 01:30 — ROUTING_ANALYSIS —
route print e tracert mostrano che 192.168.0.10 viene instradato verso gateway Wi-Fi.
Nessuna subnet locale 192.168.0.0/24 configurata.

2026-02-19 02:15 — PROJECT_RESTRUCTURE —
Creati documenti:
- STATE.md
- CAPTURE_NOTES.md
- LOG.md

Obiettivo formalizzato: emulare MCTRL660 completo (IP + TCP + 55AA protocol).

2026-02-19 23:10 — DESIGN_CORRECTION —
Chiarito che l’emulatore deve:
1. Esporre IP locale 192.168.0.10
2. Accettare TCP 443
3. Rispondere handshake 55AA valido
4. Gestire frame FE coerentemente

2026-02-21 23:55 — NETWORK_BIND_FAILURE_ANALYSIS —
Configurato TCP 443 e IP 192.168.0.10.
Bind fallisce con WinError 10049.
Diagnosi: IP assegnato a interfaccia "Ethernet 2" in stato Disconnected (AddressState Tentative).
Decisione: utilizzare Microsoft KM-TEST Loopback Adapter per creare subnet locale 192.168.0.0/24 attiva.

2026-02-22 00:40 — TLS_HANDSHAKE_OK_LEGACY —
Configurato IP 192.168.0.10 su Loopback (Ethernet 6) AddressState=Preferred. TCP 443 attivo.
Aggiunto TLS server-side su 443: NovaLCT usa TLSv1.0 con cipher ECDHE-RSA-AES256-SHA.
Per compatibilità: abilitati cipher legacy (ctx.set_ciphers("ALL:@SECLEVEL=0")).
Test SAN (subjectAltName=IP:192.168.0.10) non cambia comportamento: dopo handshake NovaLCT chiude (RX 0 bytes).
Prova server-first “probe” b"\x01\x02" provoca reset immediato (WinError 10054) → NovaLCT richiede frame applicativo valido.
Next step: inviare subito dopo handshake TLS il frame AA55 “connect successfully”
AA 55 00 00 00 FE 00 00 00 00 00 00 02 00 00 00 02 00 07 11 6F 56
e gestire ConnectionResetError senza crash; osservare RX > 0.


# LOG — Sessione TLS 443 Diagnostic

## Obiettivo
Verificare se NovaLCT comunica via TLS 443 con protocollo HEX.

## Test eseguiti
- CONNECT_OK_FRAME server-first
- REQUEST server-first
- Listen-first mode
- Client-first diagnostic recv
- Timeout variations

## Risultato definitivo
Log DIAG:

[TLS] Handshake OK
[DIAG] Client closed immediately after TLS handshake

Conclusione:
NovaLCT non utilizza 443/TLS per il protocollo di controllo.

## Decisione
Abbandonare 443/TLS.
Passare a TCP 5200 senza TLS.



# 03/03/2026
# Emulatore NovaLCT / MCTRL660

## LOG TECNICO – SESSIONE ATTUALE

---

## Setup di rete definitivo (laboratorio)

* PC Windows (NovaLCT): 192.168.0.10
* Raspberry (emulatore): 192.168.0.11 (IP statico permanente su eth0)
* Switch Ethernet dedicato
* WiFi disabilitato sul PC
* Comunicazione SSH funzionante

---

## Fase 1 – Discovery UDP/3800

### Verifica ricezione su Raspberry

Comando:

```
sudo tcpdump -ni eth0 udp port 3800 -vv
```

Risultato:

* Ricezione corretta di:
  192.168.0.10:3800 → 255.255.255.255:3800
  Payload: rqProMI:

Conclusione:

* Broadcast fisico correttamente ricevuto su rete reale.

---

## Fase 2 – Responder UDP funzionante

Script aggiornato:

* Bind su 0.0.0.0:3800
* Risposta unicast verso 192.168.0.10
* Broadcast subnet 192.168.0.255

Log esempio:

* RX rqProMI
* TX UNICAST rpProMI:App,0161
* TX BCAST(subnet)

Verifica tcpdump:

* Pacchetto in uscita 192.168.0.11:3800 → 192.168.0.10:3800
* Pacchetto in uscita 192.168.0.11:3800 → 192.168.0.255:3800

Conclusione:

* Discovery UDP 3800 COMPLETAMENTE OPERATIVO.

---

## Fase 3 – Connessione TCP/5200

Test server minimale su Raspberry.

Log connessioni reali da NovaLCT:

Connessione 1:

* RX 21 bytes:
  55aa00a7feff00000000010000000001010000fc57
* RX 20 bytes:
  55aa00b1fe000000000000000200000002000857
* Peer closed

Connessione 2:

* RX 21 bytes:
  55aa00effeff000000000100000000010100004458
* RX 20 bytes:
  55aa0024fe000000000000000200000002007b56
* Peer closed

Conclusione:

* NovaLCT parla per primo.
* In assenza di risposta valida, chiude la connessione.
* Protocollo confermato: COM-style su TCP.

---

## Fase 4 – Implementazione TCP Reply Specchio (in preparazione)

Creato nuovo server TCP 5200 con:

* Ricezione frame
* Reply con header invertito (55AA → AA55)
* Nessuna chiusura immediata della socket

Test da effettuare alla prossima sessione.

---

## Stato generale a fine sessione

✔ Discovery reale su rete fisica funzionante
✔ TCP 5200 intercettato su Raspberry
✔ Frame handshake acquisiti
✔ Ambiente di test stabile

Prossimo obiettivo:

* Far mantenere la connessione TCP a NovaLCT
* Costruire prima risposta valida protocollo 5200

---

Fine log sessione.


# LOG – Emulatore NovaLCT / MCTRL660
Data: 2026-03-03
Sessione: Raspberry + Switch Ethernet (separazione fisica PC/Device)

---

## 1️⃣ TOPOLOGIA TEST

PC Windows:
- IP: 192.168.0.10/24
- NovaLCT in esecuzione
- Wi-Fi disabilitata
- Interfaccia attiva: Ethernet 2

Raspberry Pi:
- IP statico: 192.168.0.11/24
- eth0 attiva
- SSH funzionante
- Emulator in esecuzione

Connessione:
PC ↔ Switch ↔ Raspberry

---

## 2️⃣ DISCOVERY UDP 3800

NovaLCT invia:
rqProMI:

Raspberry risponde:
rpProMI:App,0161

Verificato con:
- tcpdump su Raspberry
- Wireshark su Windows

Risultato:
✅ Discovery funzionante
NovaLCT riconosce il device e apre TCP 5200

---

## 3️⃣ TCP 5200 – SEQUENZA OSSERVATA

Ad ogni connessione NovaLCT invia SEMPRE:

1️⃣ Frame 21 byte:
55aa????feff00000000010000000001010000????57/58

2️⃣ Frame 20 byte:
55aa????fe00000000000000020000000200????56/57

Pattern costante:
- Primo frame contiene "feff"
- Secondo frame contiene "fe00"
- CRC variabile
- Lunghezza coerente (21B + 20B)

Dopo il secondo scambio:
NovaLCT chiude la connessione (FIN).

---

## 4️⃣ TEST A – Echo Identico

Server TCP:
- Risponde con lo stesso frame ricevuto (55aa… identico)

Risultato:
❌ NovaLCT chiude comunque la connessione
Nessun passo successivo

---

## 5️⃣ TEST B – CONNECT_OK_FRAME fisso

Server TCP:
- Risponde sempre con frame fisso:
aa55000000fe00000000000002000000020007116f56

Risultato:
❌ NovaLCT chiude comunque la connessione
Non prosegue oltre il secondo frame

---

## 6️⃣ CONCLUSIONE SESSIONE

Il problema NON è:
- rete
- discovery
- TCP handshake
- echo
- risposta generica

Il problema è:
⚠️ La risposta ai frame 21B e 20B deve essere strutturalmente coerente al comando ricevuto
⚠️ Probabile verifica CRC + campo comando/direzione

---

## 7️⃣ PROSSIMO STEP

- Parsing strutturale frame 55aa
- Verifica algoritmo CRC dal PDF RS232 V1.6
- Generazione risposta coerente ai comandi feff e fe00

Parola d'ordine ripartenza:
MCTRL660_STEP_NEXT


# Emulatore NovaLCT / MCTRL660
## LOG – Aggiornamento 2026-03-04

### 🔥 MILESTONE RAGGIUNTA

✔ UDP 3800 Discovery stabile (rqProMI / rpProMI:App,0161)
✔ TCP 5200 handshake stabile
✔ Checksum protocollo RS232 V1.6 corretto (sum bytes + 0x5555)
✔ ACK corretti con swap src/dst
✔ Model ID implementato su reg 0x00000002 (01 11)
✔ Timeout sugli indirizzi non emulati
✔ NovaLCT rileva correttamente "MCTRL660"
✔ Accesso completo alle finestre LEDwall
✔ Configurazione righe/colonne possibile
✔ Disegno collegamento mattonelle funzionante
✔ Sessione stabile (100+ frame RX/TX continui)

---

### ⚠ Problemi residui

1. "Send to Receiving Card" genera errore
2. Formato mattonelle anomalo (65x128)
3. Mancanza di coerenza completa tra WRITE e READ successivi
4. dst=0x01 attualmente risponde timeout (da correggere)

---

### 📡 Osservazioni traffico

- NovaLCT effettua polling esteso su:
  - 0x00000002 (Model ID)
  - 0x00000006
  - 0x00000016
  - 0x14000000 (blob 0x58)
  - 0x02000000
  - 0x02000100
  - 0x05000000
  - 0x05065000
  - 0x02100000
- WRITE osservate su:
  - 0x01000000
  - 0x02000011
  - Parameter Store (0x01000011)

---

### 🎯 Prossimo Step Pianificato

1. ALLOWED_DST = {0x00, 0x01, 0xFF}
2. Implementare memory-map stateful:
   - WRITE → salvare valore
   - READ → restituire valore scritto
3. Gestione corretta Parameter Store (0x01000011)
4. Consolidamento versione server v1.0 stable






#LOG aggiornamento 09/03/2026
# NovaLCT Emulator — Development Log

## Session summary

Major reverse engineering progress achieved.

NovaLCT communication sequence confirmed:

1. routing entries written via register
   0x02000011 (6 byte payload)

2. commit operation via
   0x02000018

3. NovaLCT then reads back configuration blocks:

- 0x02000000 (256 bytes)
- 0x02000100 (256 bytes)
- 0x02020020 (64 bytes)
- 0x08000000 (256 bytes)

Initial hypothesis assumed each write represented one tile.

Testing revealed this is incorrect.

Example log:

ROUTE WRITE reg=0x02000011 dst=FF data=260309002620
ROUTE WRITE reg=0x02000011 dst=FF data=260309002639
ROUTE WRITE reg=0x02000011 dst=FF data=260309002659

These writes represent routing segments rather than individual tiles.

Further analysis of Packet.ts exposed a critical missing dimension in the emulator:

- deviceType
- port
- rcvIndex

The emulator currently ignores rcvIndex and stores configuration globally.

This collapses multiple receiving cards into one memory map.

Consequences observed in NovaLCT:

- screen connection invalid after tile index 9
- Send to HW fails
- receiving card behaviour inconsistent

## Decision

Next development step:

Implement multi-dimensional memory map based on:

(deviceType, port, rcvIndex, dst, address)

Server version planned:

tcp_server.py Works_10

This should allow independent configuration per receiving card and unlock the remaining functionality.

## Status

Discovery: OK
TCP protocol: OK
Controller identity: OK
Sending card: OK
Screen connection: partial
Receiving chain emulation: pending

Project remains in reverse engineering phase.




# NovaLCT Emulator – development log
---
## 2026-03-10 – Works_12 / Works_13 investigation
Sessione di debugging mirata alla gestione delle **screen tables controller-level**.

Registri analizzati:
0x02000011
0x02000018
0x02000000
0x02000100
0x02020020
0x08000000

---

### Works_12
Implementato:
- controller screen blocks sintetici
- logging readback completo
- ricostruzione blocchi dopo commit.

Risultato:
sending card = 1
tile >9 = KO
failed to send data = SI
Log mostra che NovaLCT legge i registri screen **prima del commit**.

---

### Works_13
Aggiunto:
- seed iniziale dei blocchi screen
- rebuild su write routing
- rebuild su commit.
NovaLCT ora riceve dati non-zero nei readback iniziali.

---

### Problema osservato
Readback inconsistente.

Esempio:
block generated:
00260310021319
readback seen:
0026260310021319

Byte duplicato.

---

### Root cause identificata

Il server scrive i record di routing (`0x02000011`) nella stessa memoria utilizzata per i blocchi controller-level.
Questo crea **overlay della memoria** e corrompe i dati letti da NovaLCT.

---

### Conclusione tecnica

I registri:
0x02000011
0x02000018
devono essere trattati come **command registers**, non come memoria persistente.
La memoria dei blocchi screen deve essere generata separatamente.

---

### Prossimo step
Implementazione:
tcp_server.py – Works_14

con separazione:
routing command storage
vs
controller readback blocks

---

### Stato finale sessione

NovaLCT detect device: OK
sending card: 1
tile >9: KO
Send to HW: FAIL

Debug point identificato con precisione.
Sessione terminata con piano chiaro per Works_14.


---------------------------------------------------------------------
NovaLCT Emulator – Development Session Update
Date: 2026-03-11
Session: DEV SESSION 3
Reference keyword: MCTRL660_STEP_NEXT
---------------------------------------------------------------------

Current development phase:
Screen topology synthesis and hardware commit behaviour.

The emulator is now capable of completing the full initial communication
pipeline with NovaLCT:

Discovery → TCP connection → identity readback → routing commands → commit.

The NovaLCT software correctly detects a single sending card and
establishes a stable TCP/5200 session.

Recent development iterations:

Works_14
Separated routing command space from synthetic screen block memory.
This solved the previous memory overlay issue where writes to 0x02000011
corrupted controller readback blocks.

Works_15
Introduced semantic reconstruction of screen tables derived from routing
commands.

Works_16
Improved routing parsing and internal memory model stability.

Works_18
Reimplemented screen block serializer with simplified deterministic layout.

Works_19
Introduced two distinct semantic views of the topology:

0x02000000 → layout table
0x02000100 → cascade table
0x02020020 → topology summary
0x08000000 → presence map

The controller now reconstructs screen blocks from logical routing entries.

Observed behaviour:

NovaLCT correctly recognizes:

sending card = 1

However the following issues remain unresolved:

tiles > 9 = KO
Send to HW = Failed to send data

NovaLCT still rejects the generated screen topology during validation.

Additional observation during manual testing:

After repeated configuration write failures the NovaLCT device count
unexpectedly changes from:

1 → 20

This occurs after the sequence:

Send to HW → Failed
Receiving Card → Save → Failed
Screen Connection → Save → Failed

Hypothesis:

NovaLCT may enter a fallback re-enumeration mode after persistent
configuration failures, temporarily invalidating the active topology
and triggering a device list rebuild.

This behaviour requires further logging to determine which registers
or protocol branches are involved.

Current conclusion:

Protocol handshake and routing command handling are fully functional.
The remaining blocker is the exact structure and validation metadata
expected inside the screen topology blocks.

Next investigation targets:

• screen topology serialization
• validation registers near 0x02000000 range
• behaviour during Send to HW and configuration persistence
• possible re-enumeration logic triggered by Save failures

End of session.
---------------------------------------------------------------------

---------------------------------------------------------------------
NovaLCT Emulator – Development Session Update
Date: 2026-03-13
Session: DEV SESSION 4
Reference keyword: MCTRL660_STEP_NEXT
---------------------------------------------------------------------

Current development phase:
Receiving-card configuration validation and post-save device stability.

During this session the emulator progressed beyond the previous
"device disappears / reconnect required" failure mode.

Main development path tested:

Works_20
Added explicit storage for receiving-card related registers:
0x02100000
0x05000000
0x05065000
0x05066000

Added first validation register handling and RCFG logging.

Result:
NovaLCT still failed Send to HW.
Save operation wrote 0x05066000 but the device remained logically
unconfigured.

Key observation:
0x05066000 write contained a 256-byte blob beginning with:

53535045ea030000

ASCII:
SSPE

This appears to be a save/config marker rather than a full rich panel
configuration block.

Works_21
Added semantic effect for 0x05066000 save marker.
After receiving the SSPE marker, the emulator generated non-zero
configuration state for:
0x05000000
0x02100000
0x05065000

Result:
Device no longer stayed completely empty after save.
However NovaLCT still reset the session and re-entered fallback mode.

Works_22
Improved post-save readback coherence.

Result:
Major improvement.
After save:
- device remains visible
- device count stays at 1
- "Please reconnect the device" no longer appears

This was the first stable version of the save/persistence branch.

Works_23
Attempted to expose configuration-valid state too early by forcing
0x02200117 and related config markers during early validation.

Result:
Regression.
NovaLCT returned to:
- device = 20
- reconnect/fallback behaviour
- "Please reconnect the device"

Conclusion:
Configuration-valid state must NOT be exposed too early.

Works_24
Rebased on Works_22 and changed logic so that the receiving-card
configuration becomes valid only when the following conditions are
coherent:

- save marker received (0x05066000 / SSPE)
- topology is non-empty
- config blocks are non-zero

Result:
Stable again.

Observed final behaviour with Works_24:
device = 1
no "Please reconnect the device"

This confirms that the save / persistence branch is now much healthier
than before.

Remaining issues:
tiles > 9 = KO
Send to HW = Failed

Important technical conclusion:
The save/reconnect problem is now mostly under control.
The remaining blocker is the timing and semantics of topology validation,
especially around register:

0x02200117

Current best hypothesis:
NovaLCT validates the screen topology while 0x02200117 is still 00.
This likely causes topology rejection even though the device now remains
connected and stable.

Direction for next step:
Works_25 should focus on the timing of 0x02200117 and related
topology-validation semantics, without breaking the new stability
achieved in Works_24.

End of session.
---------------------------------------------------------------------