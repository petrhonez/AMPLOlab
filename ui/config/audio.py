# ui/config/audio.py
import tkinter as tk

from ._base import make_config_window, _load_registry, _save_registry

SOUND_ENABLED_KEY = "sound_enabled"
SOUND_STYLE_KEY   = "sound_style"
DEFAULT_STYLE     = "leve"


def _load_audio_config() -> dict:
    """Carrega config de áudio do registro central."""
    reg = _load_registry()
    cfg = reg.get("audio", {})
    return {
        "enabled": cfg.get(SOUND_ENABLED_KEY, True),
        "style":   cfg.get(SOUND_STYLE_KEY, DEFAULT_STYLE),
    }


def _save_audio_config(enabled: bool, style: str) -> None:
    """Salva config de áudio no registro central."""
    reg = _load_registry()
    reg["audio"] = {
        SOUND_ENABLED_KEY: enabled,
        SOUND_STYLE_KEY:   style
    }
    _save_registry(reg)


def open_ui(root, colors, fonts, app=None):
    """Abre a janela de configuração de áudio."""

    # Config atual
    cfg = _load_audio_config()
    curr_enabled = cfg["enabled"]
    curr_style   = cfg["style"]

    _, content = make_config_window(root, colors, "Configurações de Áudio", app=app)

    page = tk.Frame(content, bg=colors['bg'])
    page.pack(anchor='center', pady=30, padx=80, fill='x')

    sound_enabled = tk.BooleanVar(value=curr_enabled)
    sound_style   = tk.StringVar(value=curr_style)

    # ── Seção: Som Geral ─────────────────────────────────────────
    tk.Label(page, text="SOM",
             font=("Cascadia Code", 9, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(0, 8))

    toggle_box = tk.Frame(page, bg=colors['dim'],
                          highlightthickness=1,
                          highlightbackground=colors['topbar_border'])
    toggle_box.pack(fill='x', pady=(0, 20))

    toggle_inner = tk.Frame(toggle_box, bg=colors['dim'])
    toggle_inner.pack(fill='x', padx=14, pady=12)

    # Canvas checkbox customizado
    cv = tk.Canvas(toggle_inner, width=20, height=20,
                   bg=colors['dim'], highlightthickness=0, cursor='hand2')
    cv.pack(side='left', padx=(0, 10))

    def _draw_check():
        cv.delete('all')
        cv.create_rectangle(1, 1, 19, 19,
                            outline=colors['topbar_border'], width=1,
                            fill=colors['bg'])
        if sound_enabled.get():
            cv.create_text(10, 10, text="✓",
                           font=("Cascadia Code", 12, "bold"),
                           fill=colors['focus'])
        _sync_to_app()

    def _toggle_sound():
        sound_enabled.set(not sound_enabled.get())
        _draw_check()

    cv.bind('<Button-1>', lambda e: _toggle_sound())

    lbl_toggle = tk.Label(toggle_inner,
                          text="🔊  Efeitos sonoros ativos",
                          font=("Cascadia Code", 11),
                          bg=colors['dim'], fg=colors['fg'],
                          cursor='hand2')
    lbl_toggle.pack(side='left')
    lbl_toggle.bind('<Button-1>', lambda e: _toggle_sound())

    lbl_status = tk.Label(toggle_inner, text="",
                          font=("Cascadia Code", 9),
                          bg=colors['dim'], fg=colors['text_dim'])
    lbl_status.pack(side='right', padx=6)

    def _sync_to_app():
        """Atualiza o SoundManager ao vivo se o app estiver disponível."""
        enabled = sound_enabled.get()
        lbl_status.config(text="ON" if enabled else "OFF",
                          fg=colors['success'] if enabled else colors['accent'])
        if app is not None and hasattr(app, 'sound_manager'):
            app.sound_manager.enabled = enabled

    _draw_check()   # inicializa visual

    # ── Separador ─────────────────────────────────────────────────
    tk.Frame(page, bg=colors['topbar_border'], height=1).pack(fill='x', pady=(4, 16))

    # ── Seção: Estilo de Aviso ────────────────────────────────────
    tk.Label(page, text="ESTILO DE AVISO FINAL",
             font=("Cascadia Code", 9, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(0, 8))

    STYLES = [
        (
            "leve",
            "🌿  Leve",
            "Um aviso suave aos 10 segundos finais",
            "Discreto — não interrompe o raciocínio",
        ),
        (
            "rigido",
            "⚡  Rígido",
            "5 bipes nos últimos 5 segundos, volume alto",
            "Intenso — garante que você vai notar",
        ),
        (
            "critico",
            "🚨  Crítico",
            "Bipa a cada segundo (10s finais), bipa ao pausar/retomar",
            "Máximo foco — contagem regressiva total",
        ),
    ]

    style_refs = {}   # key → (card_frame, desc_label)

    def _select_style(key: str):
        sound_style.set(key)
        _update_style_cards()

    def _update_style_cards():
        sel = sound_style.get()
        for key, (card, _) in style_refs.items():
            active = (key == sel)
            card.config(highlightbackground=colors['focus']
                        if active else colors['topbar_border'])

    for key, title, subtitle, note in STYLES:
        card = tk.Frame(page, bg=colors['dim'],
                        highlightthickness=2,
                        highlightbackground=colors['topbar_border'],
                        cursor='hand2')
        card.pack(fill='x', pady=4)
        card.bind('<Button-1>', lambda e, k=key: _select_style(k))

        inner = tk.Frame(card, bg=colors['dim'])
        inner.pack(fill='x', padx=14, pady=10)
        inner.bind('<Button-1>', lambda e, k=key: _select_style(k))

        header = tk.Frame(inner, bg=colors['dim'])
        header.pack(fill='x')
        header.bind('<Button-1>', lambda e, k=key: _select_style(k))

        tk.Label(header, text=title,
                 font=("Cascadia Code", 12, "bold"),
                 bg=colors['dim'], fg=colors['fg'],
                 cursor='hand2').pack(side='left')
        tk.Label(header, text=subtitle,
                 font=("Cascadia Code", 8),
                 bg=colors['dim'], fg=colors['text_dim'],
                 cursor='hand2').pack(side='left', padx=12, pady=(3, 0))

        # Botão preview
        btn_preview = tk.Button(
            header, text="▶ Ouvir",
            font=("Cascadia Code", 8),
            bg=colors['dim'], fg=colors['rest'],
            relief='flat', cursor='hand2',
            padx=8, pady=3, bd=0,
            activebackground=colors['rest'],
            activeforeground='#000',
            command=lambda k=key: _preview(k)
        )
        btn_preview.pack(side='right', padx=4)
        btn_preview.bind('<Enter>', lambda e, b=btn_preview: b.config(
            bg=colors['rest'], fg='#000'))
        btn_preview.bind('<Leave>', lambda e, b=btn_preview: b.config(
            bg=colors['dim'], fg=colors['rest']))

        note_lbl = tk.Label(inner, text=note,
                            font=("Cascadia Code", 8),
                            bg=colors['dim'], fg=colors['text_dim'],
                            cursor='hand2')
        note_lbl.pack(anchor='w', pady=(4, 0))
        note_lbl.bind('<Button-1>', lambda e, k=key: _select_style(k))

        style_refs[key] = (card, note_lbl)

    _update_style_cards()

    # ── Preview ───────────────────────────────────────────────────
    def _preview(style_key: str):
        if app is None or not hasattr(app, 'sound_manager'):
            return
        sm = app.sound_manager
        if style_key == "leve":
            sm.play_break_warning()
        elif style_key == "rigido":
            sm.play_break_warning_rigid()
        elif style_key == "critico":
            sm.play_tick()

    # ── Separador ─────────────────────────────────────────────────
    tk.Frame(page, bg=colors['topbar_border'], height=1).pack(fill='x', pady=(16, 12))

    # ── Botão Salvar ──────────────────────────────────────────────
    def _save():
        enabled = sound_enabled.get()
        style   = sound_style.get()
        _save_audio_config(enabled, style)

        # Atualiza o SoundManager ao vivo
        if app is not None and hasattr(app, 'sound_manager'):
            app.sound_manager.enabled     = enabled
            app.sound_manager.style       = style

        btn_save.config(text="✓  Salvo!")
        root.after(1200, lambda: btn_save.config(text="💾  Salvar"))

    btn_save = tk.Button(page, text="💾  Salvar",
                         command=_save,
                         bg=colors['focus'], fg='#000',
                         font=("Cascadia Code", 11, "bold"),
                         relief='flat', cursor='hand2',
                         padx=16, pady=8,
                         activebackground=colors['success'],
                         activeforeground='#000')
    btn_save.pack(anchor='e')