import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(message)s"
)

def log_packet(prefix, data):
    logging.debug(f"{prefix}: {data.hex()}")
    
def log_text(msg: str):
    logging.info(msg)
