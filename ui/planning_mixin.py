# ui/planning_mixin.py
import datetime
import tkinter as tk
import json
import os
from tkinter import ttk

from config import *
from ui.dialogs import CustomDialog
from ui.config._base import _load_registry


class PlanningMixin:
    """Blocos de planejamento (A/C/D/E), relógio do menu, navegação por teclas
    e validações de entrada."""

    # ── Bloco A — Controles e Checkboxes ─────────────────────────

    def _build_block_a(self, parent):
        bg = COLORS['bg']

        checks = [
            ("🔊", "SOM ATIVO",        self.sound_enabled,  self.toggle_sound),
            ("📡", "CONEXÃO ESP32",    self.esp32_enabled,  self._save_app_config),
            ("💡", "LÂMPADA RGB",      self.lamp_enabled,   self._save_app_config),
            ("📝", "REGISTRAR SESSÃO", self.record_enabled, self._save_app_config),
        ]

        for emoji, label, var, cmd in checks:
            row = tk.Frame(parent, bg=bg)
            row.pack(fill='x', pady=4)

            cv = tk.Canvas(row, width=18, height=18, bg=bg,
                           highlightthickness=0, cursor='hand2')
            cv.pack(side='left', padx=(0, 8))

            def _draw_check(canvas=cv, variable=var):
                canvas.delete('all')
                canvas.create_rectangle(1, 1, 17, 17,
                                        outline=COLORS['topbar_border'], width=1,
                                        fill=COLORS['dim'])
                if variable.get():
                    canvas.create_text(9, 9, text="✓",
                                       font=("Cascadia Code", 11, "bold"),
                                       fill=COLORS['focus'])

            def _toggle(variable=var, redraw=_draw_check, callback=cmd):
                variable.set(not variable.get())
                redraw()
                if callback:
                    callback()

            cv.bind('<Button-1>', lambda e, fn=_toggle: fn())
            _draw_check()

            lbl = tk.Label(row, text=f"{emoji}  {label}",
                           font=("Cascadia Code", 9),
                           bg=bg, fg=COLORS['fg'], cursor='hand2')
            lbl.pack(side='left')
            lbl.bind('<Button-1>', lambda e, fn=_toggle: fn())

        tk.Frame(parent, bg=COLORS['dim'], height=1).pack(fill='x', pady=(10, 6))

        util_row = tk.Frame(parent, bg=bg)
        util_row.pack(fill='x')

        def _mk_util_btn(parent_f, text, cmd, hover_color):
            b = tk.Button(
                parent_f, text=text, command=cmd,
                bg=COLORS['dim'], fg=COLORS['text_dim'],
                font=("Cascadia Code", 8), relief='flat',
                cursor='hand2', padx=6, pady=4,
                activebackground=COLORS['dim']
            )
            b.pack(fill='x', pady=2)
            b.bind('<Enter>', lambda e, btn=b, c=hover_color: btn.config(fg=c))
            b.bind('<Leave>', lambda e, btn=b: btn.config(fg=COLORS['text_dim']))
            return b

        _mk_util_btn(parent, "✉  ENVIAR RELATÓRIO",  self._manual_send_email, COLORS['rest'])
        _mk_util_btn(parent, "🗑  LIMPAR HISTÓRICO",  self.clear_reports,       COLORS['accent'])

    # ── Bloco C — Central (Relógio + Gráfico) ────────────────────

    def _build_block_c(self, parent):
        bg = COLORS['bg']

        center_frame = tk.Frame(parent, bg=bg)
        center_frame.pack(fill='both', expand=True, pady=10)

        moon_emoji, _ = self.get_moon_phase()

        self.lbl_real_date = tk.Label(
            center_frame, text="",
            font=("Cascadia Code", 60),
            bg=bg, fg=COLORS['text_dim']
        )
        self.lbl_real_date.pack(pady=(0, 150))

        self.lbl_real_clock = tk.Label(
            center_frame, text="00:00:00",
            font=("Cascadia Code", 170, "bold"),
            bg=bg, fg=COLORS['fg']
        )
        self.lbl_real_clock.pack(pady=(6, 80))

        tk.Label(center_frame, text="EFICIÊNCIA — ÚLTIMA SEMANA",
                 font=("Cascadia Code", 8),
                 bg=bg, fg=COLORS['text_dim']).pack(pady=(0, 4))
        self._draw_mini_graph(center_frame)

    def _draw_mini_graph(self, parent):
        """Gráfico de linha compacto para o bloco central."""
        bg   = COLORS['bg']
        data = self.stats_manager.get_weekly_focus_efficiency()
        days = ['D', '2', '3', '4', '5', '6', 'S']
        effs = [data[i] for i in range(7)]
        today_idx = (datetime.datetime.now().weekday() + 1) % 7

        W, H = 1000, 280
        ml, mr, mt, mb = 28, 8, 8, 22
        aw = W - ml - mr
        ah = H - mt - mb

        cv = tk.Canvas(parent, width=W, height=H, bg=bg, highlightthickness=0)
        cv.pack(pady=4)

        cv.create_line(ml, mt, ml, H - mb, fill=COLORS['dim'], width=1)
        cv.create_line(ml, H - mb, W - mr, H - mb, fill=COLORS['dim'], width=1)

        for pct in [50, 100]:
            y = H - mb - (pct / 100) * ah
            cv.create_text(ml - 3, y, text=f"{pct}",
                           font=("Cascadia Code", 6),
                           fill=COLORS['text_dim'], anchor='e')

        pts = []
        for i, eff in enumerate(effs):
            x = ml + (i / 6) * aw
            y = H - mb - (eff / 100) * ah if eff > 0 else H - mb
            pts.append((x, y))

        for i in range(len(pts) - 1):
            cv.create_line(*pts[i], *pts[i + 1],
                           fill=COLORS['focus'], width=3, smooth=True)

        for i, (x, y) in enumerate(pts):
            col = COLORS['current_highlight'] if i == today_idx else COLORS['focus']
            r = 4
            cv.create_oval(x - r, y - r, x + r, y + r,
                           fill=col, outline=bg, width=2)
            cv.create_text(x, H - mb + 8, text=days[i],
                           font=("Cascadia Code", 7),
                           fill=col if i == today_idx else COLORS['text_dim'],
                           anchor='n')

    # ── Bloco D — Sessão ─────────────────────────────────────────

    def _build_block_d(self, parent):
        bg = COLORS['bg']

        tk.Label(parent, text="FINALIZAR EM",
                 font=("Cascadia Code", 9),
                 bg=bg, fg=COLORS['text_dim']).pack(anchor='w', pady=(16, 0))

        default_end = (datetime.datetime.now() +
                       datetime.timedelta(hours=2)).strftime("%H:%M")
        self.entry_end_time = tk.Entry(
            parent, bg=COLORS['dim'], fg=COLORS['fg'],
            font=("Cascadia Code", 22, "bold"),
            width=7, insertbackground=COLORS['focus'],
            bd=0, justify='center',
            relief='flat',
            highlightthickness=1,
            highlightbackground=COLORS['topbar_border'],
            highlightcolor=COLORS['focus']
        )
        self.entry_end_time.insert(0, default_end)
        self.entry_end_time.pack(pady=(12, 16), fill='x')
        self._setup_time_entry_validation(self.entry_end_time)

        tk.Label(parent, text="DURAÇÃO RÁPIDA",
                 font=("Cascadia Code", 8),
                 bg=bg, fg=COLORS['text_dim']).pack(anchor='w', pady=(16, 4))

        durations = [
            ("05m", 5), ("10m", 10), ("20m", 20), ("30m", 30),
            ("50m", 50), ("01h", 60), ("90m", 90), ("02h", 120)
        ]

        row1 = tk.Frame(parent, bg=bg)
        row1.pack(fill='x', pady=(0, 18))
        row2 = tk.Frame(parent, bg=bg)
        row2.pack(fill='x', pady=(0, 30))

        for i, (label, minutes) in enumerate(durations):
            target_row = row1 if i < 4 else row2
            b = tk.Button(
                target_row, text=label,
                command=lambda m=minutes: self._set_quick_time(m),
                bg=COLORS['dim'], fg=COLORS['text_dim'],
                font=("Cascadia Code", 9, "bold"),
                relief='flat', cursor='hand2', padx=6, pady=5,
                activebackground=COLORS['focus'], activeforeground='#000'
            )
            b.pack(side='left', padx=(0, 4), fill='x', expand=True)
            b.bind('<Enter>', lambda e, btn=b: btn.config(
                bg=COLORS['topbar_border'], fg=COLORS['focus']))
            b.bind('<Leave>', lambda e, btn=b: btn.config(
                bg=COLORS['dim'], fg=COLORS['text_dim']))

        tk.Frame(parent, bg=COLORS['dim'], height=1).pack(fill='x', pady=(70, 4)) # precisa centralizar e abaixar
        reg = _load_registry()
        mode_val  = f"{reg.get('focus_percent', 80)}%"
        audio_val = reg.get('audio', {}).get('sound_style', 'leve').upper()
        color_val = reg.get('palette_name', 'PADRÃO').upper()
        
        # Carrega status do e-mail de config.json
        email_val = "INATIVO"
        try:
            if os.path.exists("config.json"):
                with open("config.json", 'r', encoding='utf-8') as f:
                    c_json = json.load(f)
                    if c_json.get("email", {}).get("enabled", False):
                        email_val = "ATIVO"
        except Exception:
            pass

        tk.Label(
            parent,
            text=f" CONFIGURAÇÃO ATIVA: Modo {mode_val} | Áudio {audio_val} | Cores {color_val} | E-mail {email_val}",
            font=("Cascadia Code", 10, "italic"),
            bg=bg, fg=COLORS['text_dim'],
            wraplength=700, justify='left'
        ).pack(anchor='w', pady=(18, 0))

    # ── Bloco E — Tarefas ────────────────────────────────────────

    def _build_block_e(self, parent):
        bg = COLORS['bg']

        self.task_list_frame = tk.Frame(parent, bg=bg)
        self.task_list_frame.pack(fill='both', expand=True)

        self.add_task_row()

        tk.Frame(parent, bg=COLORS['dim'], height=1).pack(fill='x', pady=(6, 4))

        actions = tk.Frame(parent, bg=bg)
        actions.pack(fill='x')

        self._btn_add_task = tk.Button(
            actions, text="+ TAREFA",
            command=self.add_task_row,
            bg=COLORS['dim'], fg=COLORS['fg'],
            font=("Cascadia Code", 9, "bold"),
            relief='flat', cursor='hand2',
            padx=8, pady=5,
            activebackground=COLORS['focus'], activeforeground='#000',
            highlightthickness=2, highlightbackground=COLORS['dim'], bd=0
        )
        self._btn_add_task.pack(side='left')

        self._btn_start = tk.Button(
            actions,
            text="▶   INICIAR FOCO",
            command=self.calculate_schedule,
            bg=COLORS['focus'], fg='#000000',
            font=("Cascadia Code", 11, "bold"),
            relief='flat', cursor='hand2',
            padx=16, pady=5,
            activebackground=COLORS['rest'], activeforeground='#000',
            highlightthickness=2,
            highlightbackground=COLORS['focus'],
            highlightcolor=COLORS['rest'],
            bd=0
        )
        self._btn_start.pack(side='right')

    # ── Linha de Tarefa ──────────────────────────────────────────

    def add_task_row(self):
        """Linha de tarefa: [entry] [1x][2x][3x] [✕]."""
        bg  = COLORS['bg']
        row = tk.Frame(self.task_list_frame, bg=bg)
        row.pack(fill='x', pady=2)

        e = tk.Entry(
            row, bg=COLORS['dim'], fg=COLORS['fg'],
            font=("Cascadia Code", 10),
            width=22, insertbackground=COLORS['focus'],
            bd=0, relief='flat',
            highlightthickness=2,
            highlightbackground=COLORS['dim'],
            highlightcolor=COLORS['focus']
        )
        e.pack(side='left', padx=(0, 6), ipady=3)
        self._setup_task_name_validation(e)

        w = tk.IntVar(value=1)
        weight_btns = []

        def _update_weight_colors():
            for val, btn in weight_btns:
                active = (w.get() == val)
                btn.config(
                    bg=COLORS['focus'] if active else COLORS['dim'],
                    fg='#000' if active else COLORS['text_dim']
                )

        for val, label in [(1, "1x"), (2, "2x"), (3, "3x")]:
            btn = tk.Button(
                row, text=label,
                font=("Cascadia Code", 8, "bold"),
                bg=COLORS['dim'], fg=COLORS['text_dim'],
                relief='flat', cursor='hand2',
                padx=5, pady=3,
                activebackground=COLORS['focus'], activeforeground='#000'
            )
            btn.pack(side='left', padx=1)
            weight_btns.append((val, btn))

            def _pick(v=val, variable=w, upd=_update_weight_colors):
                variable.set(v)
                upd()

            btn.config(command=_pick)

        _update_weight_colors()

        entry_ref = (e, w)
        self.entries_tasks.append(entry_ref)

        def _remove(r=row, ref=entry_ref):
            r.destroy()
            if ref in self.entries_tasks:
                self.entries_tasks.remove(ref)
            self._rebuild_nav_list()

        tk.Button(
            row, text="✕", command=_remove,
            bg=bg, fg=COLORS['text_dim'],
            font=("Cascadia Code", 9), relief='flat', cursor='hand2',
            padx=4, pady=3,
            activebackground=bg, activeforeground=COLORS['accent']
        ).pack(side='left', padx=(4, 0))

        e.focus_set()

        if hasattr(self, '_nav_items'):
            self._rebuild_nav_list()

    # ── Navegação por Teclas de Seta ─────────────────────────────

    def _setup_nav_keys(self):
        self._rebuild_nav_list()
        self.root.bind('<Up>',    self._nav_prev)
        self.root.bind('<Down>',  self._nav_next)
        self.root.bind('<Return>', self._nav_activate)

    def _rebuild_nav_list(self):
        """Reconstrói a lista navegável: horário → entries → + TAREFA → INICIAR → sidebar."""
        self._nav_items = []

        # 1. Caixa de tempo
        if hasattr(self, 'entry_end_time') and self.entry_end_time.winfo_exists():
            self._nav_items.append(('entry', self.entry_end_time))

        # 2. Caixa de nome da tarefa
        for entry, _ in self.entries_tasks:
            if entry.winfo_exists():
                self._nav_items.append(('entry', entry))

        # 3. +tarefa
        if hasattr(self, '_btn_add_task') and self._btn_add_task.winfo_exists():
            self._nav_items.append(('button', self._btn_add_task))

        # 4. Iniciar
        if hasattr(self, '_btn_start') and self._btn_start.winfo_exists():
            self._nav_items.append(('button', self._btn_start))

        # 5. Sidebar
        if hasattr(self, 'sidebar_buttons'):
            for btn in self.sidebar_buttons:
                if btn.winfo_exists():
                    self._nav_items.append(('button', btn))

        if self._nav_index >= len(self._nav_items):
            self._nav_index = 0

        self._nav_draw_highlight()

    def _nav_draw_highlight(self):
        self._stop_blink()
        for i, (kind, widget) in enumerate(self._nav_items):
            try:
                if not widget.winfo_exists():
                    continue
                if i == self._nav_index:
                    if kind == 'button':
                        widget.config(bg=COLORS['focus'], fg='#000000', relief='sunken')
                    else:
                        widget.config(highlightthickness=2,
                                      highlightbackground=COLORS['focus'],
                                      highlightcolor=COLORS['focus'])
                else:
                    if kind == 'button':
                        widget.config(bg=COLORS['dim'], fg=COLORS['fg'], relief='flat')
                    else:
                        widget.config(highlightthickness=2,
                                      highlightbackground=COLORS['topbar_border'],
                                      highlightcolor=COLORS['topbar_border'])
            except tk.TclError:
                pass
        self._start_blink()

    def _nav_prev(self, event=None):
        if not self._nav_items:
            return
        self._nav_index = (self._nav_index - 1) % len(self._nav_items)
        self._nav_draw_highlight()
        self._nav_focus_current()

    def _nav_next(self, event=None):
        if not self._nav_items:
            return
        self._nav_index = (self._nav_index + 1) % len(self._nav_items)
        self._nav_draw_highlight()
        self._nav_focus_current()

    def _nav_focus_current(self):
        if not self._nav_items:
            return
        kind, widget = self._nav_items[self._nav_index]
        try:
            if kind == 'entry' and widget.winfo_exists():
                widget.focus_set()
        except tk.TclError:
            pass

    def _nav_activate(self, event=None):
        if not self._nav_items:
            return
        kind, widget = self._nav_items[self._nav_index]
        try:
            if not widget.winfo_exists():
                return
            if kind == 'button':
                widget.invoke()
            elif kind == 'entry':
                widget.focus_set()
        except tk.TclError:
            pass

    # ── Navegação de Menu (esquerda/direita) ─────────────────────

    def navigate_menu_left(self, event=None):
        self.selected_button_index = (self.selected_button_index - 1) % len(self.menu_buttons)
        self.highlight_selected_button()

    def navigate_menu_right(self, event=None):
        self.selected_button_index = (self.selected_button_index + 1) % len(self.menu_buttons)
        self.highlight_selected_button()

    def activate_selected_button(self, event=None):
        if self.menu_buttons:
            self.menu_buttons[self.selected_button_index].invoke()

    def highlight_selected_button(self):
        for i, btn in enumerate(self.menu_buttons):
            if i == self.selected_button_index:
                btn.config(relief='solid', bd=2,
                           highlightbackground=COLORS['focus'], highlightthickness=2)
            else:
                btn.config(relief='flat', bd=0, highlightthickness=0)

    # ── Relógio do Menu ──────────────────────────────────────────

    def update_menu_clock(self):
        now = datetime.datetime.now()
        dias_abrev = ["2ª", "3ª", "4ª", "5ª", "6ª", "S", "D"]
        moon_emoji, _ = self.get_moon_phase()
        try:
            if self.lbl_real_clock.winfo_exists():
                self.lbl_real_clock.config(text=now.strftime("%H:%M:%S"))
            if self.lbl_real_date.winfo_exists():
                date_str = (f"{dias_abrev[now.weekday()]} {moon_emoji} "
                            f"{now.day:02d}/{now.month:02d}/{now.year}")
                self.lbl_real_date.config(text=date_str)
        except tk.TclError:
            return
        self.clock_after_id = self.root.after(1000, self.update_menu_clock)

    def get_moon_phase(self):
        """Calcula fase lunar por ciclo sinódico."""
        ref   = datetime.datetime(2000, 1, 6, 18, 14)
        now   = datetime.datetime.now()
        cycle = 29.53058867 * 24 * 3600
        pct   = ((now - ref).total_seconds() % cycle) / cycle

        phases = [
            (0.000, "◯", ""), (0.075, "☽", ""),
            (0.250, "◑", ""), (0.375, "◗", ""),
            (0.500, "◉", ""), (0.625, "◖", ""),
            (0.750, "◐", ""), (0.875, "☾", ""),
        ]
        for threshold, emoji, name in reversed(phases):
            if pct >= threshold:
                return emoji, name
        return "🌑", "Lua Nova"

    def toggle_sound(self):
        self.sound_manager.enabled = self.sound_enabled.get()
        if self.sound_manager.enabled:
            self.sound_manager.play_task_completed()

    def _set_quick_time(self, minutes: int):
        t = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        self.entry_end_time.delete(0, 'end')
        self.entry_end_time.insert(0, t.strftime("%H:%M"))

    # ── Sistema de Blink para Navegação ──────────────────────────

    def _stop_blink(self):
        if self._blink_after_id:
            self.root.after_cancel(self._blink_after_id)
            self._blink_after_id = None
        self._blink_state = False

    def _start_blink(self):
        self._stop_blink()
        self._blink_toggle()

    def _blink_toggle(self):
        if not self._nav_items or self._nav_index >= len(self._nav_items):
            return
        kind, widget = self._nav_items[self._nav_index]
        try:
            if not widget.winfo_exists():
                return
            if self._blink_state:
                if kind == 'button':
                    widget.config(bg=COLORS['focus'], fg='#000000')
                else:
                    widget.config(highlightthickness=2,
                                  highlightbackground=COLORS['focus'],
                                  highlightcolor=COLORS['focus'])
            else:
                if kind == 'button':
                    widget.config(bg=COLORS['dim'], fg=COLORS['fg'])
                else:
                    widget.config(highlightthickness=2,
                                  highlightbackground=COLORS['topbar_border'],
                                  highlightcolor=COLORS['focus'])
            self._blink_state = not self._blink_state
            self._blink_after_id = self.root.after(self._blink_speed, self._blink_toggle)
        except tk.TclError:
            pass

    # ── Validações de Entrada ────────────────────────────────────

    def _validate_time_input(self, value):
        clean = ''.join(c for c in value if c.isdigit())
        if len(clean) > 4:
            return False
        if len(clean) <= 2:
            return True
        return clean[:2] + ':' + clean[2:]

    def _validate_task_name(self, value):
        allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_')
        return all(c in allowed for c in value)

    def _setup_time_entry_validation(self, entry_widget):
        def on_time_change(*args):
            value = entry_widget.get()
            clean = ''.join(c for c in value if c.isdigit() or c == ':')
            if len(clean) > 5:
                clean = clean[:5]
            if ':' not in clean and len(clean) >= 3:
                clean = clean[:2] + ':' + clean[2:]
            if clean != value:
                entry_widget.delete(0, 'end')
                entry_widget.insert(0, clean)
        entry_widget.bind('<KeyRelease>', on_time_change)

    def _setup_task_name_validation(self, entry_widget):
        def on_name_change(*args):
            value = entry_widget.get()
            clean = ''.join(c for c in value if c.isalnum() or c in ' -_')
            if clean != value:
                entry_widget.delete(0, 'end')
                entry_widget.insert(0, clean)
        entry_widget.bind('<KeyRelease>', on_name_change)
