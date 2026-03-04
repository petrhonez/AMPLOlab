# ui/config/cores.py
import json
import os
import tkinter as tk
from tkinter import colorchooser

from ui.config._base import make_config_window, _load_registry, _save_registry

# ── Temas predefinidos ────────────────────────────────────────────────────────

THEMES = {
    "ambar": {
        "label":    "🔥  Âmbar",
        "subtitle": "Retro quente — inspirado em terminais antigos",
        "colors": {
            "bg":                "#1a0f00",
            "fg":                "#ffcc66",
            "dim":               "#2e1f00",
            "topbar_border":     "#5c3d00",
            "focus":             "#ffaa00",
            "rest":              "#cc7700",
            "text_dim":          "#996633",
            "accent":            "#ff4400",
            "success":           "#aacc00",
            "current_highlight": "#ff8800",
        },
    },
    "matrix": {
        "label":    "👾  Terminal Matrix",
        "subtitle": "Escuro com verde neon — foco total",
        "colors": {
            "bg":                "#000000",
            "fg":                "#00ff41",
            "dim":               "#0a1a0a",
            "topbar_border":     "#003300",
            "focus":             "#00ff41",
            "rest":              "#00cc33",
            "text_dim":          "#006600",
            "accent":            "#ff0040",
            "success":           "#00ff88",
            "current_highlight": "#33ff66",
        },
    },
    "bluemoon": {
        "label":    "🌝  Blue Moon",
        "subtitle": "Calmo e frio — ótimo para sessões longas",
        "colors": {
            "bg":                "#050d1a",
            "fg":                "#cce0ff",
            "dim":               "#0d1e33",
            "topbar_border":     "#1a3a5c",
            "focus":             "#4da6ff",
            "rest":              "#0099cc",
            "text_dim":          "#4d7099",
            "accent":            "#ff4466",
            "success":           "#00ccaa",
            "current_highlight": "#66ccff",
        },
    },
    "seapearl": {
        "label":    "🐚  Sea Pearl",
        "subtitle": "Tema claro — rosado com azul esverdeado",
        "colors": {
            "bg":                "#f5f0f0",
            "fg":                "#2d3a3a",
            "dim":               "#e8dfe0",
            "topbar_border":     "#c9b8ba",
            "focus":             "#d4648a",
            "rest":              "#4aab9b",
            "text_dim":          "#8a7a7c",
            "accent":            "#cc3355",
            "success":           "#3a9e7e",
            "current_highlight": "#e07aa0",
        },
    },
}

COLOR_SLOTS = [
    ("Fundo",        "bg"),
    ("Texto",        "fg"),
    ("Superfície",   "dim"),
    ("Borda",        "topbar_border"),
    ("Foco",         "focus"),
    ("Descanso",     "rest"),
    ("Texto suave",  "text_dim"),
    ("Acento",       "accent"),
    ("Sucesso",      "success"),
    ("Em andamento", "current_highlight"),
]


def _default_config_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, '..', '..', 'config.json')


def _load_colors(fallback_colors: dict) -> dict:
    """Carrega as cores do registro central."""
    reg = _load_registry()
    return reg.get("colors", fallback_colors)


def _save_colors(colors_dict: dict, name: str = "Personalizado") -> None:
    """Salva as cores e o nome da paleta no registro central."""
    reg = _load_registry()
    reg["colors"] = colors_dict
    reg["palette_name"] = name
    _save_registry(reg)


def open_ui(root, colors, fonts, app=None):

    # Cópia de trabalho — editamos aqui antes de aplicar
    working = {k: v for k, v in colors.items()}

    _, content = make_config_window(root, colors, "Cores e Temas", app=app)

    page = tk.Frame(content, bg=colors['bg'])
    page.pack(anchor='center', pady=30, padx=60, fill='x')

    selected_theme = tk.StringVar(value="custom")

    # ── Layout em duas colunas ────────────────────────────────────
    columns = tk.Frame(page, bg=colors['bg'])
    columns.pack(fill='x')
    columns.columnconfigure(0, weight=2)
    columns.columnconfigure(1, weight=3)

    left  = tk.Frame(columns, bg=colors['bg'])
    left.grid(row=0, column=0, sticky='nsew', padx=(0, 16))

    right = tk.Frame(columns, bg=colors['bg'])
    right.grid(row=0, column=1, sticky='nsew')

    # ════════════════════════════════════════════════════
    # COLUNA ESQUERDA — cards de tema
    # ════════════════════════════════════════════════════
    tk.Label(left, text="TEMAS",
             font=("Cascadia Code", 9, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(0, 8))

    theme_cards = {}

    def _select_theme(key: str):
        selected_theme.set(key)
        if key in THEMES and THEMES[key]["colors"]:
            for k, v in THEMES[key]["colors"].items():
                working[k] = v
        _update_preview()
        _refresh_swatches()
        _update_cards()
        custom_panel.pack(fill='x', pady=(10, 0)) if key == "custom" else custom_panel.pack_forget()

    def _update_cards():
        sel = selected_theme.get()
        for k, card in theme_cards.items():
            active = (k == sel)
            card.config(highlightbackground=working.get('focus', colors['focus'])
                        if active else colors['topbar_border'],
                        highlightthickness=2 if active else 1)

    # Cards dos temas predefinidos
    for key, data in THEMES.items():
        card = tk.Frame(left, bg=colors['dim'],
                        highlightthickness=1,
                        highlightbackground=colors['topbar_border'],
                        cursor='hand2')
        card.pack(fill='x', pady=3)
        card.bind('<Button-1>', lambda e, k=key: _select_theme(k))

        inn = tk.Frame(card, bg=colors['dim'])
        inn.pack(fill='x', padx=12, pady=8)
        inn.bind('<Button-1>', lambda e, k=key: _select_theme(k))

        tk.Label(inn, text=data["label"],
                 font=("Cascadia Code", 11, "bold"),
                 bg=colors['dim'], fg=colors['fg'],
                 cursor='hand2').pack(anchor='w')

        tk.Label(inn, text=data["subtitle"],
                 font=("Cascadia Code", 8),
                 bg=colors['dim'], fg=colors['text_dim'],
                 cursor='hand2').pack(anchor='w', pady=(2, 0))

        # Mini strip de cores
        strip = tk.Frame(inn, bg=colors['dim'])
        strip.pack(anchor='w', pady=(6, 0))
        for slot_key in ["bg", "focus", "rest", "accent", "success"]:
            c = data["colors"][slot_key]
            tk.Frame(strip, bg=c, width=18, height=14).pack(side='left', padx=1)

        theme_cards[key] = card

    # Card "Custom"
    custom_card = tk.Frame(left, bg=colors['dim'],
                           highlightthickness=1,
                           highlightbackground=colors['topbar_border'],
                           cursor='hand2')
    custom_card.pack(fill='x', pady=3)
    custom_card.bind('<Button-1>', lambda e: _select_theme("custom"))

    inn_c = tk.Frame(custom_card, bg=colors['dim'])
    inn_c.pack(fill='x', padx=12, pady=8)
    inn_c.bind('<Button-1>', lambda e: _select_theme("custom"))

    tk.Label(inn_c, text="🎨  Personalizado",
             font=("Cascadia Code", 11, "bold"),
             bg=colors['dim'], fg=colors['fg'],
             cursor='hand2').pack(anchor='w')
    tk.Label(inn_c, text="Defina suas próprias cores",
             font=("Cascadia Code", 8),
             bg=colors['dim'], fg=colors['text_dim'],
             cursor='hand2').pack(anchor='w', pady=(2, 0))

    theme_cards["custom"] = custom_card

    # ════════════════════════════════════════════════════
    # COLUNA DIREITA — preview + painel custom
    # ════════════════════════════════════════════════════
    tk.Label(right, text="PREVIEW",
             font=("Cascadia Code", 9, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(0, 8))

    preview_box = tk.Frame(right, bg=colors['bg'],
                           highlightthickness=1,
                           highlightbackground=colors['topbar_border'])
    preview_box.pack(fill='x')

    def _update_preview():
        for w in preview_box.winfo_children():
            w.destroy()

        bg_  = working.get('bg', '#000')
        dim_ = working.get('dim', '#222')

        # Topbar
        tb = tk.Frame(preview_box, bg=working.get('topbar_border', '#333'), height=20)
        tb.pack(fill='x')
        tb.pack_propagate(False)
        tk.Label(tb, text="● AMPLO",
                 font=("Cascadia Code", 7, "bold"),
                 bg=working.get('topbar_border', '#333'),
                 fg=working.get('focus', '#ffd700')).pack(side='left', padx=8)
        tk.Label(tb, text="✕",
                 font=("Cascadia Code", 7),
                 bg=working.get('topbar_border', '#333'),
                 fg=working.get('text_dim', '#888')).pack(side='right', padx=8)

        # Corpo
        body = tk.Frame(preview_box, bg=bg_)
        body.pack(fill='both', expand=True, padx=10, pady=10)

        # Sidebar mini
        side_mini = tk.Frame(body, bg=dim_, width=22)
        side_mini.pack(side='left', fill='y', padx=(0, 8))
        side_mini.pack_propagate(False)
        for icon in ["⚙", "🎨", "🔊"]:
            tk.Label(side_mini, text=icon, font=("Cascadia Code", 7),
                     bg=dim_, fg=working.get('text_dim', '#888')).pack(pady=4)

        # Área principal
        main = tk.Frame(body, bg=bg_)
        main.pack(side='left', fill='both', expand=True)

        tk.Label(main, text="14:30",
                 font=("Cascadia Code", 28, "bold"),
                 bg=bg_, fg=working.get('fg', '#fff')).pack(anchor='w')

        tk.Label(main, text="FOCO: Tarefa Principal",
                 font=("Cascadia Code", 7),
                 bg=bg_, fg=working.get('focus', '#ffd700')).pack(anchor='w')

        # Bloco de tarefas
        bloco = tk.Frame(main, bg=dim_,
                         highlightthickness=1,
                         highlightbackground=working.get('topbar_border', '#333'))
        bloco.pack(fill='x', pady=(6, 4))

        tk.Label(bloco, text="▶  Tarefa ativa",
                 font=("Cascadia Code", 7, "bold"),
                 bg=dim_,
                 fg=working.get('current_highlight', '#ffa600')).pack(
                     anchor='w', padx=6, pady=(4, 1))
        tk.Label(bloco, text="○  Próxima tarefa",
                 font=("Cascadia Code", 7),
                 bg=dim_,
                 fg=working.get('text_dim', '#888')).pack(
                     anchor='w', padx=6, pady=(1, 4))

        # Botões mini
        btn_row_m = tk.Frame(main, bg=bg_)
        btn_row_m.pack(anchor='w', pady=(2, 0))
        for txt, ckey in [("✓ Concluir", 'success'), ("✕ Abandonar", 'accent'), ("⏸", 'focus')]:
            b_m = tk.Frame(btn_row_m, bg=working.get(ckey, '#888'), padx=4, pady=2)
            b_m.pack(side='left', padx=2)
            tk.Label(b_m, text=txt, font=("Cascadia Code", 6),
                     bg=working.get(ckey, '#888'),
                     fg=bg_).pack()

    _update_preview()

    # ── Painel custom (oculto por padrão) ─────────────────────────
    custom_panel = tk.Frame(right, bg=colors['bg'])

    tk.Label(custom_panel, text="PERSONALIZAR CORES",
             font=("Cascadia Code", 9, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(12, 8))

    swatch_refs = {}   # key → (canvas, hex_var)

    grid_f = tk.Frame(custom_panel, bg=colors['bg'])
    grid_f.pack(fill='x')
    grid_f.columnconfigure(0, weight=1)
    grid_f.columnconfigure(1, weight=1)

    for idx, (label, key) in enumerate(COLOR_SLOTS):
        cell = tk.Frame(grid_f, bg=colors['dim'],
                        highlightthickness=1,
                        highlightbackground=colors['topbar_border'])
        cell.grid(row=idx // 2, column=idx % 2, sticky='ew', padx=2, pady=2)

        cin = tk.Frame(cell, bg=colors['dim'])
        cin.pack(fill='x', padx=6, pady=5)

        cv = tk.Canvas(cin, width=34, height=20,
                       bg=colors['dim'], highlightthickness=0, cursor='hand2')
        cv.pack(side='left', padx=(0, 6))
        cv.create_rectangle(1, 1, 33, 19,
                            fill=working.get(key, '#000000'),
                            outline=colors['topbar_border'], width=1)

        txt_f = tk.Frame(cin, bg=colors['dim'])
        txt_f.pack(side='left')

        tk.Label(txt_f, text=label,
                 font=("Cascadia Code", 8),
                 bg=colors['dim'], fg=colors['fg']).pack(anchor='w')

        hex_var = tk.StringVar(value=working.get(key, '#000000'))
        tk.Label(txt_f, textvariable=hex_var,
                 font=("Cascadia Code", 7),
                 bg=colors['dim'], fg=colors['text_dim']).pack(anchor='w')

        swatch_refs[key] = (cv, hex_var)

        def _pick(k=key, canvas=cv, hv=hex_var):
            result = colorchooser.askcolor(
                color=working.get(k, '#000000'),
                title=f"Cor: {k}", parent=root)
            if result and result[1]:
                working[k] = result[1]
                canvas.delete('all')
                canvas.create_rectangle(1, 1, 33, 19,
                                        fill=result[1],
                                        outline=colors['topbar_border'], width=1)
                hv.set(result[1])
                _update_preview()

        cv.bind('<Button-1>', lambda e, fn=_pick: fn())

    def _refresh_swatches():
        for key, (cv, hv) in swatch_refs.items():
            c = working.get(key, '#000000')
            cv.delete('all')
            cv.create_rectangle(1, 1, 33, 19,
                                fill=c,
                                outline=colors['topbar_border'], width=1)
            hv.set(c)

    # ════════════════════════════════════════════════════
    # BOTÕES DE AÇÃO
    # ════════════════════════════════════════════════════
    tk.Frame(page, bg=colors['topbar_border'], height=1).pack(fill='x', pady=(20, 12))

    btn_row = tk.Frame(page, bg=colors['bg'])
    btn_row.pack(fill='x')

    def _save():
        # Sincroniza working -> colors global
        for k, v in working.items():
            if k in colors:
                colors[k] = v
        
        sel = selected_theme.get()
        name = THEMES[sel]["label"] if sel in THEMES else "Personalizado"
        _save_colors(dict(colors), name)
        root.configure(bg=colors['bg'])
        
        btn_save.config(text="✓  Salvo!")
        root.after(1200, lambda: btn_save.config(text="💾  Salvar"))

    def _apply_and_close():
        # Sincroniza working -> colors global
        for k, v in working.items():
            if k in colors:
                colors[k] = v
        
        sel = selected_theme.get()
        name = THEMES[sel]["label"] if sel in THEMES else "Personalizado"
        _save_colors(dict(colors), name)
        root.configure(bg=colors['bg'])
        if app is not None:
            app.build_planning_screen()

    # Botão Aplicar e Voltar (à esquerda)
    btn_apply = tk.Button(btn_row, text="🎨  Aplicar e Voltar",
                          command=_apply_and_close,
                          bg=colors['dim'], fg=colors['focus'],
                          font=("Cascadia Code", 11, "bold"),
                          relief='flat', cursor='hand2',
                          padx=16, pady=8,
                          activebackground=colors['focus'],
                          activeforeground='#000')
    btn_apply.pack(side='left')

    # Botão Salvar (à direita)
    btn_save = tk.Button(btn_row, text="💾  Salvar",
                         command=_save,
                         bg=colors['focus'], fg='#000',
                         font=("Cascadia Code", 11, "bold"),
                         relief='flat', cursor='hand2',
                         padx=16, pady=8,
                         activebackground=colors['success'],
                         activeforeground='#000')
    btn_save.pack(side='right')

    _update_cards()
