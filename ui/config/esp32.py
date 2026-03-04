# ui/config/esp32.py
import tkinter as tk
import threading
import urllib.request
import os

from ui.config._base import make_config_window, _load_registry, _save_registry

# ── URL do pinout para decoração ──────────────────────────────────────────────
PINOUT_URL   = (
    "https://mischianti.org/wp-content/uploads/2024/01/"
    "ESP32-2432S028-CYD-v1.2-Mischianti-pinout-low.jpg"
)
PINOUT_CACHE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "_cyd_pinout.jpg"
)

# ── Specs da placa para fallback visual ───────────────────────────────────────
CYD_SPECS = [
    ("MCU",        "ESP32-WROOM-32  ·  dual-core 240 MHz"),
    ("Flash",      "32 Mbit  ·  DIO"),
    ("Display",    "2.8″  240×320 px  ILI9341  TFT resistivo"),
    ("Touch",      "XPT2046  SPI"),
    ("RGB LED",    "R→GPIO4  G→GPIO16  B→GPIO17"),
    ("SD Card",    "SPI VSPI"),
    ("Wi-Fi",      "802.11 b/g/n  2.4 GHz"),
    ("Bluetooth",  "4.2 + BLE"),
    ("USB-UART",   "CP2102 / CH340"),
    ("I/O livre",  "GPIO 21, 22, 27, 35  +  TX/RX"),
]


def _load_esp_config() -> dict:
    """Carrega config do ESP32 do registro central."""
    reg = _load_registry()
    return reg.get("esp32", {})


def _save_esp_config(data: dict) -> None:
    """Salva config do ESP32 no registro central."""
    reg = _load_registry()
    reg["esp32"] = data
    _save_registry(reg)


def open_ui(root, colors, fonts, app=None):
    """Abre a janela de configuração do ESP32."""

    saved = _load_esp_config()

    _, content = make_config_window(root, colors, "ESP32 CYD — Controle", app=app)

    page = tk.Frame(content, bg=colors['bg'])
    page.pack(anchor='center', pady=24, padx=60, fill='x')

    # ════════════════════════════════════════════════════
    # LAYOUT: esquerda (controles) | direita (pinout)
    # ════════════════════════════════════════════════════
    cols = tk.Frame(page, bg=colors['bg'])
    cols.pack(fill='x')
    cols.columnconfigure(0, weight=2)
    cols.columnconfigure(1, weight=3)

    left  = tk.Frame(cols, bg=colors['bg'])
    left.grid(row=0, column=0, sticky='nsew', padx=(0, 20))

    right = tk.Frame(cols, bg=colors['bg'])
    right.grid(row=0, column=1, sticky='nsew')

    # ════════════════════════════════════════════════════
    # ESQUERDA — configuração e testes
    # ════════════════════════════════════════════════════

    tk.Label(left, text="CONEXÃO MQTT",
             font=("Cascadia Code", 9, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(0, 8))

    conn_box = tk.Frame(left, bg=colors['dim'],
                        highlightthickness=1,
                        highlightbackground=colors['topbar_border'])
    conn_box.pack(fill='x', pady=(0, 16))

    cb = tk.Frame(conn_box, bg=colors['dim'])
    cb.pack(fill='x', padx=14, pady=12)

    # Broker
    tk.Label(cb, text="Broker IP",
             font=("Cascadia Code", 8),
             bg=colors['dim'], fg=colors['text_dim']).pack(anchor='w')

    broker_var = tk.StringVar(value=saved.get("broker", "192.168.1.100"))
    broker_entry = tk.Entry(cb, textvariable=broker_var,
                            font=("Cascadia Code", 10),
                            bg=colors['bg'], fg=colors['fg'],
                            insertbackground=colors['focus'],
                            relief='flat', bd=4)
    broker_entry.pack(fill='x', pady=(2, 8))

    # Porta
    tk.Label(cb, text="Porta",
             font=("Cascadia Code", 8),
             bg=colors['dim'], fg=colors['text_dim']).pack(anchor='w')

    port_var = tk.StringVar(value=saved.get("port", "1883"))
    tk.Entry(cb, textvariable=port_var,
             font=("Cascadia Code", 10),
             bg=colors['bg'], fg=colors['fg'],
             insertbackground=colors['focus'],
             relief='flat', bd=4, width=10).pack(anchor='w', pady=(2, 8))

    # Status da conexão
    status_var  = tk.StringVar(value="⬤  não conectado")
    status_lbl  = tk.Label(cb, textvariable=status_var,
                           font=("Cascadia Code", 9),
                           bg=colors['dim'], fg=colors['accent'])
    status_lbl.pack(anchor='w', pady=(4, 0))

    def _connect():
        status_var.set("⬤  aguardando implementação MQTT...")
        status_lbl.config(fg=colors['focus'])

    tk.Button(cb, text="🔌  Conectar",
              command=_connect,
              font=("Cascadia Code", 9, "bold"),
              bg=colors['topbar_border'], fg=colors['fg'],
              relief='flat', cursor='hand2',
              padx=10, pady=5).pack(anchor='w', pady=(10, 0))

    # ── Separador ─────────────────────────────────────
    tk.Frame(left, bg=colors['topbar_border'], height=1).pack(
        fill='x', pady=(0, 14))

    # ── Testes manuais ─────────────────────────────────
    tk.Label(left, text="TESTES MANUAIS",
             font=("Cascadia Code", 9, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(0, 8))

    log_lines = []

    def _log(msg: str):
        log_lines.append(msg)
        if len(log_lines) > 6:
            log_lines.pop(0)
        log_box.config(state='normal')
        log_box.delete('1.0', 'end')
        log_box.insert('end', '\n'.join(log_lines))
        log_box.config(state='disabled')

    # Botão Hello World
    def _send_hello():
        _log("→ enviando: hello world")
        try:
            from services.esp32_svc import send_display_text
            send_display_text("hello world")
            _log("✓ enviado ao display")
        except ImportError:
            _log("⚠ esp32_svc ainda não implementado")
        except Exception as e:
            _log(f"✕ erro: {e}")

    btn_style = dict(
        font=("Cascadia Code", 10, "bold"),
        relief='flat', cursor='hand2',
        padx=12, pady=7, bd=0,
    )

    hw_btn = tk.Button(left, text="📺  Hello World  (display)",
                       command=_send_hello,
                       bg=colors['dim'], fg=colors['focus'],
                       activebackground=colors['focus'],
                       activeforeground='#000',
                       **btn_style)
    hw_btn.pack(fill='x', pady=3)

    # Botão Lâmpada RGB IR
    def _send_lamp():
        _log("→ enviando: acender lâmpada RGB via IR NEC")
        try:
            from services.esp32_svc import send_ir_command
            send_ir_command("lamp_on")
            _log("✓ comando IR enviado")
        except ImportError:
            _log("⚠ esp32_svc ainda não implementado")
        except Exception as e:
            _log(f"✕ erro: {e}")

    lamp_btn = tk.Button(left, text="💡  Acender Lâmpada  (IR NEC)",
                         command=_send_lamp,
                         bg=colors['dim'], fg=colors['rest'],
                         activebackground=colors['rest'],
                         activeforeground='#000',
                         **btn_style)
    lamp_btn.pack(fill='x', pady=3)

    # Hover
    for btn, hc in [(hw_btn, colors['focus']), (lamp_btn, colors['rest'])]:
        btn.bind('<Enter>', lambda e, b=btn, c=hc: b.config(bg=c, fg='#000'))
        btn.bind('<Leave>', lambda e, b=btn, c=hc,
                 orig=colors['dim']: b.config(bg=orig, fg=c))

    # Log de saída
    tk.Label(left, text="LOG",
             font=("Cascadia Code", 8),
             bg=colors['bg'], fg=colors['text_dim']).pack(
                 anchor='w', pady=(12, 2))

    log_box = tk.Text(left, height=5,
                      font=("Cascadia Code", 8),
                      bg=colors['dim'], fg=colors['text_dim'],
                      insertbackground=colors['focus'],
                      relief='flat', bd=4, state='disabled',
                      wrap='word')
    log_box.pack(fill='x')
    _log("pronto — nenhum comando enviado")

    # ── Salvar ─────────────────────────────────────────
    tk.Frame(left, bg=colors['topbar_border'], height=1).pack(
        fill='x', pady=(16, 10))

    def _save():
        _save_esp_config({
            "broker": broker_var.get().strip(),
            "port":   port_var.get().strip(),
        })
        btn_save.config(text="✓  Salvo!")
        root.after(1200, lambda: btn_save.config(text="💾  Salvar"))

    btn_save = tk.Button(left, text="💾  Salvar",
                         command=_save,
                         bg=colors['focus'], fg='#000',
                         font=("Cascadia Code", 11, "bold"),
                         relief='flat', cursor='hand2',
                         padx=14, pady=7,
                         activebackground=colors['success'],
                         activeforeground='#000')
    btn_save.pack(anchor='e')

    # ════════════════════════════════════════════════════
    # DIREITA — imagem do pinout (download + fallback)
    # ════════════════════════════════════════════════════

    tk.Label(right, text="ESP32-2432S028  ·  CYD  PINOUT",
             font=("Cascadia Code", 9, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(0, 8))

    img_frame = tk.Frame(right, bg=colors['dim'],
                         highlightthickness=1,
                         highlightbackground=colors['topbar_border'])
    img_frame.pack(fill='x')

    img_label = tk.Label(img_frame, bg=colors['dim'],
                         text="⏳  carregando imagem...",
                         font=("Cascadia Code", 9),
                         fg=colors['text_dim'])
    img_label.pack(padx=8, pady=8)

    def _load_image():
        try:
            from PIL import Image, ImageTk
            if not os.path.exists(PINOUT_CACHE):
                urllib.request.urlretrieve(PINOUT_URL, PINOUT_CACHE)
            img = Image.open(PINOUT_CACHE)
            max_w = 460
            ratio = max_w / img.width
            img   = img.resize((max_w, int(img.height * ratio)), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            img_label.config(image=photo, text="")
            img_label._photo = photo
        except Exception:
            _show_specs_fallback()

    def _show_specs_fallback():
        for w in img_frame.winfo_children():
            w.destroy()

        tk.Label(img_frame, text="📋  Especificações  ESP32-2432S028R",
                 font=("Cascadia Code", 9, "bold"),
                 bg=colors['dim'], fg=colors['focus']).pack(
                     anchor='w', padx=12, pady=(10, 6))

        tk.Frame(img_frame, bg=colors['topbar_border'], height=1).pack(
            fill='x', padx=12)

        for label, value in CYD_SPECS:
            row = tk.Frame(img_frame, bg=colors['dim'])
            row.pack(fill='x', padx=12, pady=2)
            tk.Label(row, text=f"{label:<12}",
                     font=("Cascadia Code", 8, "bold"),
                     bg=colors['dim'], fg=colors['text_dim'],
                     width=14, anchor='w').pack(side='left')
            tk.Label(row, text=value,
                     font=("Cascadia Code", 8),
                     bg=colors['dim'], fg=colors['fg']).pack(side='left')

        tk.Label(img_frame,
                 text="instale Pillow para ver o pinout:  pip install pillow",
                 font=("Cascadia Code", 7),
                 bg=colors['dim'], fg=colors['text_dim']).pack(
                     anchor='w', padx=12, pady=(8, 10))

    threading.Thread(target=_load_image, daemon=True).start()

    tk.Label(right,
             text="fonte: mischianti.org  ·  randomnerdtutorials.com",
             font=("Cascadia Code", 7),
             bg=colors['bg'], fg=colors['text_dim']).pack(
                 anchor='w', pady=(6, 0))