# ui/config/modos.py
import tkinter as tk

from ui.config._base import make_config_window, _load_registry, _save_registry

# Chave usada no registro
FOCUS_PCT_KEY = "focus_percent"
DEFAULT_FOCUS_PCT = 80

# Templates pré-definidos: (nome, emoji, pct_foco, descrição)
TEMPLATES = [
    ("Tranquilo",   "🌿", 60, "Mais descanso — ideal para dias longos ou tarefas criativas"),
    ("Equilibrado", "⚖️", 70, "Balanceado — boa produtividade sem exigir muito"),
    ("Focado",      "🎯", 80, "Padrão Pomodoro — máximo foco com pausas curtas"),
    ("Adrenalina",  "⚡", 90, "Modo sprint — pouco descanso, máxima intensidade"),
]


def _load_focus_pct() -> int:
    """Lê o percentual salvo no registro central."""
    reg = _load_registry()
    return int(reg.get(FOCUS_PCT_KEY, DEFAULT_FOCUS_PCT))


def _save_focus_pct(pct: int) -> None:
    """Salva o percentual no registro central."""
    reg = _load_registry()
    reg[FOCUS_PCT_KEY] = pct
    _save_registry(reg)


def open_ui(root, colors, fonts, app=None):
    """Abre a janela de configuração de modos."""

    # Valor atual
    current_pct = tk.IntVar(value=_load_focus_pct())

    win, content = make_config_window(root, colors, "Modos de Sessão", app=app)

    page = tk.Frame(content, bg=colors['bg'])
    page.pack(anchor='center', pady=24, padx=60, fill='x')

    # ── Título ───────────────────────────────────────────────────────────────
    tk.Label(page, text="EQUILÍBRIO DA SESSÃO",
             font=("Cascadia Code", 9, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(0, 6))

    # ── Slider Customizado ───────────────────────────────────────────────────
    slider_frame = tk.Frame(page, bg=colors['dim'],
                            highlightthickness=1,
                            highlightbackground=colors['topbar_border'])
    slider_frame.pack(fill='x', pady=(0, 24))

    sf_inner = tk.Frame(slider_frame, bg=colors['dim'])
    sf_inner.pack(fill='x', padx=20, pady=20)

    # Info e Valor
    top_row = tk.Frame(sf_inner, bg=colors['dim'])
    top_row.pack(fill='x')

    tk.Label(top_row, text="PERCENTUAL DE FOCO",
             font=("Cascadia Code", 10, "bold"),
             bg=colors['dim'], fg=colors['fg']).pack(side='left')

    val_lbl = tk.Label(top_row, text=f"{current_pct.get()}%",
                       font=("Cascadia Code", 14, "bold"),
                       bg=colors['dim'], fg=colors['focus'])
    val_lbl.pack(side='right')

    # O Slider em si (Canvas para ser mais bonito)
    slider_canvas = tk.Canvas(sf_inner, height=40, bg=colors['dim'],
                              highlightthickness=0, cursor='hand2')
    slider_canvas.pack(fill='x', pady=(14, 4))

    def _update_slider_display(event=None):
        w = slider_canvas.winfo_width()
        if w < 10: return
        h = 40
        slider_canvas.delete('all')

        # Trilho (bg)
        slider_canvas.create_rectangle(0, h//2-4, w, h//2+4,
                                       fill=colors['topbar_border'], outline="")

        # Parte preenchida (foco)
        pct = current_pct.get()
        fill_w = (pct / 100.0) * w
        slider_canvas.create_rectangle(0, h//2-4, fill_w, h//2+4,
                                       fill=colors['focus'], outline="")

        # Marcadores de 0, 25, 50, 75, 100
        for i in range(0, 101, 25):
            x = (i / 100.0) * w
            slider_canvas.create_line(x, h//2-8, x, h//2+8, fill=colors['text_dim'])

        # O "Handle" (círculo)
        slider_canvas.create_oval(fill_w-10, h//2-10, fill_w+10, h//2+10,
                                  fill=colors['fg'], outline=colors['focus'], width=2)

        val_lbl.config(text=f"{pct}%")
        _update_template_buttons()

    def _on_click(event):
        w = slider_canvas.winfo_width()
        new_pct = int((event.x / w) * 100)
        new_pct = max(10, min(95, new_pct))  # limita entre 10% e 95%
        current_pct.set(new_pct)
        _update_slider_display()

    slider_canvas.bind('<B1-Motion>', _on_click)
    slider_canvas.bind('<Button-1>', _on_click)

    # ── Templates (Botões Rápidos) ──────────────────────────────────────────
    tk.Label(page, text="OU SELECIONE UM PERFIL",
             font=("Cascadia Code", 9, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(0, 8))

    template_btns = []

    def _select_template(pct):
        current_pct.set(pct)
        _update_slider_display()

    for name, emoji, pct, desc in TEMPLATES:
        row = tk.Frame(page, bg=colors['dim'],
                       highlightthickness=1,
                       highlightbackground=colors['topbar_border'],
                       cursor='hand2')
        row.pack(fill='x', pady=3)

        inner = tk.Frame(row, bg=colors['dim'])
        inner.pack(fill='x', padx=14, pady=10)

        tk.Label(inner, text=f"{emoji} {name}",
                 font=("Cascadia Code", 11, "bold"),
                 bg=colors['dim'], fg=colors['fg'],
                 cursor='hand2').pack(side='left')

        tk.Label(inner, text=desc,
                 font=("Cascadia Code", 8),
                 bg=colors['dim'], fg=colors['text_dim'],
                 cursor='hand2').pack(side='left', padx=15)

        p_lbl = tk.Label(inner, text=f"{pct}%",
                         font=("Cascadia Code", 10, "bold"),
                         bg=colors['dim'], fg=colors['text_dim'])
        p_lbl.pack(side='right')

        # Bindings para clicar na linha toda
        for w in [row, inner]:
            w.bind('<Button-1>', lambda e, p=pct: _select_template(p))

        template_btns.append((pct, row, p_lbl))

    def _update_template_buttons():
        """Destaca a linha do template que corresponde ao valor atual."""
        pct = current_pct.get()
        for t_pct, row_frame, pct_lbl in template_btns:
            active = (t_pct == pct)
            row_frame.config(
                highlightbackground=colors['focus'] if active else colors['topbar_border']
            )
            pct_lbl.config(
                fg=colors['focus'] if active else colors['text_dim']
            )

    # Inicializa display
    _update_slider_display()
    root.after(50, _update_slider_display)

    # ── Botão Salvar ─────────────────────────────────────────────────────────
    tk.Frame(page, bg=colors['topbar_border'], height=1).pack(fill='x', pady=(16, 12))

    def _save():
        pct = current_pct.get()
        _save_focus_pct(pct)
        if app is not None:
            app.focus_percent = pct / 100.0
        btn_save.config(text="✓  Salvo!")
        root.after(1200, lambda: btn_save.config(text="💾  Salvar"))

    btn_save = tk.Button(
        page, text="💾  Salvar",
        command=_save,
        bg=colors['focus'], fg='#000',
        font=("Cascadia Code", 11, "bold"),
        relief='flat', cursor='hand2',
        padx=16, pady=8,
        activebackground=colors['success'],
        activeforeground='#000'
    )
    btn_save.pack(anchor='e', pady=(0, 10))