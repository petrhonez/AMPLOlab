# services/esp32_svc.py
"""
Serviço de integração com o ESP32 CYD via MQTT.

ARQUITETURA FUTURA:
    Tópicos publicados pelo Amplo:
        focusboss/state    → "focus" | "break" | "rest" | "idle"
        focusboss/display  → texto para o display TFT
        focusboss/lamp     → "color:R,G,B" | "lamp_off" | "ir:<hex>"

    Cores da lâmpada por estado:
        focus  → âmbar    R=255 G=100 B=0
        break  → azul     R=0   G=80  B=200
        rest   → verde    R=0   G=180 B=60
        idle   → apagado

    O ESP32 escuta "focusboss/state" e confirma em "focusboss/ack".
    IR NEC via GPIO para lâmpadas RGB externas.

    Dependência futura: pip install paho-mqtt
"""

_client = None


class MQTTClient:
    def __init__(self, broker="192.168.1.100", port=1883):
        self.broker    = broker
        self.port      = port
        self.connected = False

    def connect(self):
        # TODO: paho-mqtt — client.connect(broker, port)
        raise NotImplementedError("MQTT não implementado")

    def publish(self, topic: str, payload: str):
        # TODO: client.publish(topic, payload)
        raise NotImplementedError("MQTT não implementado")


def send_state(state: str) -> None:
    """Chamado por timer_mixin ao iniciar/terminar ciclos."""
    # TODO: get_client().publish("focusboss/state", state)
    print(f"[esp32_svc] send_state: {state}")


def send_display_text(text: str) -> None:
    """Chamado pelo botão de teste em ui/config/esp32.py."""
    # TODO: get_client().publish("focusboss/display", text)
    print(f"[esp32_svc] display: '{text}'")


def send_ir_command(command: str) -> None:
    """command: 'lamp_on' | 'lamp_off' | 'color:R,G,B'"""
    # TODO: get_client().publish("focusboss/lamp", command)
    print(f"[esp32_svc] ir: '{command}'")


def send_color_for_state(state: str) -> None:
    """Converte estado → cor e envia via IR."""
    color_map = {
        "focus": "color:255,100,0",
        "break": "color:0,80,200",
        "rest":  "color:0,180,60",
        "idle":  "lamp_off",
    }
    send_ir_command(color_map.get(state, "lamp_off"))