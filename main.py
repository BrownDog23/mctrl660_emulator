import threading
from udp_server import start_udp
from tcp_server import start_tcp

if __name__ == "__main__":
    # Avvia UDP in un thread separato
    t_udp = threading.Thread(target=start_udp, daemon=True)
    t_udp.start()

    # Avvia TCP nel thread principale
    start_tcp()
