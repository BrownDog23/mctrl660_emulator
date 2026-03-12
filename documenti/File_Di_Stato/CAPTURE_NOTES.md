# MCTRL660 Emulator – CAPTURE NOTES

## 1️⃣ Ambiente di Test

- Sistema: Windows (NovaLCT gira su host, NON in VM)
- VirtualBox installato
- 192.168.56.1 = VirtualBox Host-Only (NON usato per emulazione)
- Wi-Fi attivo: 10.44.41.218 / 255.255.255.0
- Gateway Wi-Fi: 10.44.41.185
- IP target emulatore configurato in NovaLCT: 192.168.0.10 (IP fittizio)

---

## 2️⃣ Wireshark – Filtri Utilizzati

### Connessione TCP verso IP target

ip.addr == 192.168.0.10


### Discovery WS-Discovery

udp.port == 3702


### SSDP / UPnP

udp.port == 1900


### Broadcast generico

udp and ip.dst == 255.255.255.255


---

## 3️⃣ Risultati Osservati

### TCP 443 verso 192.168.0.10

- Solo pacchetti:
  - SYN
  - TCP Retransmission
- Nessun:
  - SYN/ACK
  - RST
  - Risposta ICMP

Interpretazione:
NovaLCT tenta connessione TCP 443 verso l’IP configurato.

---

### ICMP Ping verso 192.168.0.10

- Echo request inviato
- Nessuna risposta

---

### UDP osservati

- UDP 3702 (WS-Discovery)
- UDP 1900 (SSDP)
- UDP 6666 (porta usata da NovaLCT)

Nessuna risposta proveniente da dispositivo reale.

---

## 4️⃣ netstat significativo

Durante “Search/Detect/Connect”:


TCP 10.44.41.218:xxxxx → 192.168.0.10:443 SYN_SENT


NovaLCT usa:
- TCP 443
- UDP 3702
- UDP 1900
- UDP 6666

---

## 5️⃣ route print significativo

Non esiste rotta locale per:


192.168.0.0 / 255.255.255.0


Quindi Windows instrada verso gateway Wi-Fi.

---

## 6️⃣ tracert 192.168.0.10

1° hop → 10.44.41.185 (gateway Wi-Fi)
Poi instradamento interno rete (192.168.15.x, 192.168.255.x)
Nessun raggiungimento target.

---

# 🎯 Expected Behavior Emulator

L’emulatore deve:

1. Esporre un IP locale nella subnet 192.168.0.0/24
2. Accettare connessione TCP su porta 443
3. Rispondere al primo frame ricevuto da NovaLCT
4. Inviare risposta 55AA valida
5. Rispondere coerentemente ai comandi FE successivi

---

# 🔬 Obiettivo Tecnico

Simulare completamente:

- Livello IP locale (192.168.0.10)
- Handshake TCP corretto
- Protocollo applicativo NovaStar (55AA + FE)

Senza hardware reale.