# ui/stats_mixin.py
import threading
import datetime
import tkinter as tk
from tkinter import ttk

from config import *
from ui.dialogs import CustomDialog


class StatsMixin:
    """Finalização de sessão, cálculo de estatísticas e tela de relatório."""

    # ── Fim de Sessão ────────────────────────────────────────────

    def finish_session(self):
        self.session_end_time = datetime.datetime.now()

        if self.current_break_start:
            end = self.session_end_time
            self.breaks_real.append({
                'index':    self.current_task_index - 1,
                'start':    self.current_break_start,
                'end':      end,
                'duration': int((end - self.current_break_start).total_seconds())
            })
            self.current_break_start = None

        if self.pause_start_timestamp:
            self.total_paused_time += (
                self.session_end_time - self.pause_start_timestamp
            ).total_seconds()
            self.pause_start_timestamp = None

        self.sound_manager.play_session_complete()

        stats              = self.calculate_session_statistics()
        efficiency         = self.stats_manager.calculate_session_focus_efficiency(stats)
        stats["efficiency"] = efficiency

        self.session_manager.save_session(self, stats)
        self.session_manager.clear_state()

        self.build_statistics_screen(stats)

    # ── Cálculo de Estatísticas ──────────────────────────────────

    def calculate_session_statistics(self):
        stats = {}
        sd = (self.session_end_time - self.session_start_time).total_seconds()
        stats['session_duration'] = sd

        tfp = sum(t.duration_seconds for t in self.tasks)
        tbp = (self.break_per_slot * (len(self.tasks) - 1)
               if len(self.tasks) > 1 else 0)
        stats['total_focus_planned']  = tfp
        stats['total_breaks_planned'] = tbp
        stats['total_planned']        = tfp + tbp

        tfr = sum(t.duration_seconds_real for t in self.tasks)
        tbr = sum(b.get('duration', 0) for b in self.breaks_real)
        stats['total_focus_real']    = tfr
        stats['total_breaks_real']   = tbr
        stats['total_activity_real'] = tfr + tbr
        stats['total_paused_time']   = self.total_paused_time

        stats['start'] = self.session_start_time.strftime("%H:%M:%S")
        stats['end']   = self.session_end_time.strftime("%H:%M:%S")

        stats['end_actual_str']    = stats['end']
        stats['end_planned_str']   = (self.planned_end_time.strftime("%H:%M:%S")
                                      if self.planned_end_time else "-")
        stats['total_actual_fmt']  = self.format_time_long(sd)
        stats['total_planned_fmt'] = self.format_time_long(tfp + tbp)

        efficiency = int(tfr / (sd - self.total_paused_time) * 100) if (sd - self.total_paused_time) > 0 else 0
        stats['efficiency'] = efficiency

        total_pct = int(sd / (tfp + tbp) * 100) if (tfp + tbp) > 0 else 0
        stats['total_percent_str'] = f"{total_pct}% do planejado"
        diff = (tfp + tbp) - sd
        stats['time_diff_str']   = ("+" if diff >= 0 else "") + self.format_time_long(abs(diff))
        stats['time_diff_color'] = COLORS['success'] if diff >= 0 else COLORS['accent']

        stats['focus_planned_fmt'] = self.format_time_long(tfp)
        stats['break_planned_fmt'] = self.format_time_long(tbp)
        stats['pause_time_fmt']    = self.format_time_long(self.total_paused_time)
        stats['focus_real_fmt']    = self.format_time_long(tfr)
        stats['break_real_fmt']    = self.format_time_long(tbr)
        
        # New: task completion percentages
        total_tasks = len(self.tasks)
        if total_tasks > 0:
            completed = sum(1 for t in self.tasks if t.status == "Concluída")
            abandoned = sum(1 for t in self.tasks if t.status == "Abandonada")
            stats['tasks_completed_pct'] = int(completed / total_tasks * 100)
            stats['tasks_abandoned_pct'] = int(abandoned / total_tasks * 100)
        else:
            stats['tasks_completed_pct'] = 0
            stats['tasks_abandoned_pct'] = 0

        return stats

    # ── Tela de Estatísticas ─────────────────────────────────────
    
    def build_statistics_screen(self, stats):
        self.clean_frame()
        bg = COLORS['bg']
        main_container = tk.Frame(self.root, bg=bg)
        main_container.pack(fill='both', expand=True)

        # Top bar (Simplificada)
        top_bar = tk.Frame(main_container, bg=COLORS['dim'], height=40)
        top_bar.pack(side='top', fill='x')
        top_bar.pack_propagate(False)

        tk.Button(top_bar, text="◀ VOLTAR",
                  command=self.build_planning_screen,
                  bg=COLORS['dim'], fg=COLORS['focus'],
                  font=("Inter", 9, "bold") if self._has_font("Inter") else ("Cascadia Code", 9, "bold"),
                  relief='flat', cursor='hand2', bd=0,
                  padx=12, pady=5).pack(side='left', padx=10, pady=2)

        tk.Frame(top_bar, bg=COLORS['dim']).pack(side='left', fill='x', expand=True)

        tk.Button(top_bar, text="📧 ENVIAR RELATÓRIO",
                  command=lambda: (
                      threading.Thread(
                          target=self.email_manager.send_daily_report,
                          daemon=True
                      ).start(),
                      CustomDialog.show_info(self.root, "Enviando",
                                             "Relatório sendo enviado em segundo plano.")
                  ),
                  bg=COLORS['rest'], fg='#000',
                  font=("Inter", 8, "bold") if self._has_font("Inter") else ("Cascadia Code", 8, "bold"),
                  relief='flat', cursor='hand2', bd=0,
                  padx=10, pady=5).pack(side='right', padx=5, pady=2)

        # Centralização do Bloco Único
        center_wrapper = tk.Frame(main_container, bg=bg)
        center_wrapper.place(relx=0.5, rely=0.5, anchor='center', relwidth=0.6, relheight=0.85)
        center_wrapper.grid_columnconfigure(0, weight=1)
        center_wrapper.grid_rowconfigure(0, weight=1)

        # Bloco Único (SBOX)
        stats_block = self._make_block(center_wrapper, "RESUMO DA SESSÃO", 0, 0)
        
        # Container Interno para as informações verticais
        scroll_container = tk.Frame(stats_block, bg=bg)
        scroll_container.pack(fill='both', expand=True, padx=20, pady=10)

        # 1. Métricas de Horário e Duração (Fonte Aumentada)
        metrics = [
            ("Começo", stats['start'], COLORS['fg']),
            ("Término", stats['end'], COLORS['fg']),
            ("Duração Total", stats['total_actual_fmt'], COLORS['rest']),
            ("Saldo (Planejado)", stats['time_diff_str'], stats['time_diff_color']),
        ]
        
        for label, val, col in metrics:
            self._add_stat_line(scroll_container, label, val, col, large=True)

        tk.Frame(scroll_container, bg=COLORS['dim'], height=1).pack(fill='x', pady=20)

        # 2. Detalhes de Tempo (Foco, Pausa, Descanso)
        details = [
            ("Tempo de Foco", stats['focus_real_fmt'], COLORS['focus']),
            ("Tempo de Pausa", stats['pause_time_fmt'], COLORS['current_highlight']),
            ("Tempo de Descanso", stats['break_real_fmt'], COLORS['rest']),
        ]
        for label, val, col in details:
            self._add_stat_line(scroll_container, label, val, col)

        tk.Frame(scroll_container, bg=COLORS['dim'], height=1).pack(fill='x', pady=20)

        # 3. Barras de Progresso Consolidadas
        sd_ = stats['session_duration']
        # O tempo de foco "real" das tarefas inclui as pausas globais.
        # Para a barra de progresso, mostramos o tempo de foco LÍQUIDO.
        net_focus = max(0, stats['total_focus_real'] - stats['total_paused_time'])
        
        fp_ = (net_focus / sd_ * 100) if sd_ > 0 else 0
        pp_ = (stats['total_paused_time'] / sd_ * 100) if sd_ > 0 else 0
        bp_ = (stats['total_breaks_real'] / sd_ * 100) if sd_ > 0 else 0
        
        self._draw_segmented_pb(scroll_container, "FLUXO DA SESSÃO", [
            (fp_, COLORS['focus'], f"FOCO {int(fp_)}%"),
            (pp_, COLORS['current_highlight'], f"PAUSA {int(pp_)}%"),
            (bp_, COLORS['rest'], f"DESC. {int(bp_)}%"),
        ])

        tk.Frame(scroll_container, bg=bg, height=20).pack()

        total_tasks = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == "Concluída")
        abandoned = sum(1 for t in self.tasks if t.status == "Abandonada")
        cp_ = (completed / total_tasks * 100) if total_tasks > 0 else 0
        ap_ = (abandoned / total_tasks * 100) if total_tasks > 0 else 0
        
        self._draw_segmented_pb(scroll_container, "CHECK DE TAREFAS", [
            (cp_, COLORS['success'], f"CONCLUÍDAS {int(cp_)}%"),
            (ap_, COLORS['accent'], f"ABANDONADAS {int(ap_)}%"),
        ])

    def _add_stat_line(self, parent, label, value, color, large=False):
        """Adiciona uma linha de estatística formatada com Inter ou fallback."""
        row = tk.Frame(parent, bg=COLORS['bg'])
        row.pack(fill='x', pady=6)
        
        main_size = 14 if large else 11
        val_size  = 18 if large else 14
        
        font_main = ("Inter", main_size) if self._has_font("Inter") else ("Cascadia Code", main_size-1)
        font_val  = ("Inter", val_size, "bold") if self._has_font("Inter") else ("Cascadia Code", val_size-1, "bold")
        
        tk.Label(row, text=label.upper(), font=font_main, bg=COLORS['bg'], fg=COLORS['text_dim']).pack(side='left')
        tk.Label(row, text=value, font=font_val, bg=COLORS['bg'], fg=color).pack(side='right')

    def _has_font(self, font_name):
        """Verifica se uma fonte está disponível no sistema."""
        from tkinter import font
        return font_name in font.families()

    def _draw_segmented_pb(self, parent, title, segments):
        """Desenha uma barra de progresso segmentada customizada."""
        canvas_h = 35
        container = tk.Frame(parent, bg=COLORS['bg'])
        container.pack(fill='x', pady=5)

        tk.Label(container, text=title, 
                 font=("Inter", 10, "bold") if self._has_font("Inter") else ("Cascadia Code", 9, "bold"),
                 bg=COLORS['bg'], fg=COLORS['text_dim']).pack(anchor='w', pady=(0, 5))
        
        canvas = tk.Canvas(container, height=canvas_h, bg=COLORS['dim'], highlightthickness=0)
        canvas.pack(fill='x', pady=(0, 10))
        
        def render_pb(e=None):
            canvas.delete("all")
            w = canvas.winfo_width()
            if w <= 1: return
            
            # Garante que a soma não exceda 100% por erro de arredondamento
            curr_x = 0
            for pct, color, label in segments:
                if pct <= 0: continue
                seg_w = (pct / 100) * w
                canvas.create_rectangle(curr_x, 0, curr_x + seg_w, canvas_h, fill=color, outline="")
                curr_x += seg_w
        
        canvas.bind("<Configure>", render_pb)
        
        # Legenda minimalista abaixo da barra
        legend_frame = tk.Frame(container, bg=COLORS['bg'])
        legend_frame.pack(fill='x')
        font_leg = ("Inter", 10) if self._has_font("Inter") else ("Cascadia Code", 9)
        
        for pct, color, label in segments:
            if pct <= 0: continue
            f = tk.Frame(legend_frame, bg=COLORS['bg'])
            f.pack(side='left', padx=(0, 25))
            tk.Label(f, text="■", fg=color, bg=COLORS['bg'], font=("Cascadia Code", 12)).pack(side='left')
            tk.Label(f, text=label, fg=COLORS['fg'], bg=COLORS['bg'], font=font_leg).pack(side='left', padx=5)

    # ── Widgets de Estatísticas ──────────────────────────────────

    def add_stat_row(self, parent, label, value, color=None):
        row = tk.Frame(parent, bg=COLORS['dim'])
        row.pack(pady=3)
        tk.Label(row, text=label, font=FONT_SMALL,
                 bg=COLORS['dim'], fg=COLORS['text_dim'],
                 anchor='w', width=30).pack(side='left', padx=10)
        tk.Label(row, text=value, font=("Cascadia Code", 11, "bold"),
                 bg=COLORS['dim'],
                 fg=color if color else COLORS['fg'],
                 anchor='e').pack(side='right', padx=10)

    def add_task_detail_extended(self, parent, number, task):
        color  = COLORS['success'] if task.status == "Concluída" else COLORS['accent']
        symbol = "✓" if task.status == "Concluída" else "✕"

        tc = tk.Frame(parent, bg=COLORS['bg'], bd=1, relief='solid')
        tc.pack(pady=3, padx=5)

        hr = tk.Frame(tc, bg=COLORS['bg'])
        hr.pack(padx=10, pady=5)
        tk.Label(hr, text=f"{symbol} #{number} [{task.weight}x]",
                 font=("Cascadia Code", 10, "bold"),
                 bg=COLORS['bg'], fg=color).pack(side='left', padx=5)
        tk.Label(hr, text=task.name.upper(), font=FONT_SMALL,
                 bg=COLORS['bg'], fg=COLORS['fg']).pack(side='left', padx=5, fill='x', expand=True)
        tk.Label(hr, text=task.status.upper(),
                 font=("Cascadia Code", 8, "bold"),
                 bg=COLORS['bg'], fg=color).pack(side='right', padx=5)

        tr = tk.Frame(tc, bg=COLORS['dim'])
        tr.pack(padx=5, pady=5)
        tk.Label(tr, text=f"Planejado: {self.format_time(task.duration_seconds)}",
                 font=("Cascadia Code", 9), bg=COLORS['dim'],
                 fg=COLORS['text_dim']).pack(side='left', padx=5)
        tk.Label(tr, text=f"Real: {self.format_time(task.duration_seconds_real)}",
                 font=("Cascadia Code", 9, "bold"),
                 bg=COLORS['dim'], fg=COLORS['focus']).pack(side='left', padx=5)

        diff  = task.duration_seconds_real - task.duration_seconds
        v_str = f"Variação: {'+' if diff >= 0 else ''}{self.format_time(abs(diff))}"
        v_col = COLORS['accent'] if diff > 0 else COLORS['success']
        tk.Label(tr, text=v_str, font=("Cascadia Code", 9),
                 bg=COLORS['dim'], fg=v_col).pack(side='right', padx=5)

    def draw_circular_chart(self, parent, focus_pct, break_pct, pause_pct):
        cf = tk.Frame(parent, bg=COLORS['dim'])
        cf.pack(fill='both', expand=True)

        sz = 250
        canvas = tk.Canvas(cf, width=sz, height=sz,
                           bg=COLORS['dim'], highlightthickness=0)
        canvas.pack(pady=10)

        cx, cy, r, inner = sz // 2, sz // 2, 100, 65
        start = 0
        for pct, color in [
            (focus_pct, COLORS['focus']),
            (break_pct, COLORS['rest']),
            (pause_pct, COLORS['current_highlight']),
        ]:
            ang = (pct / 100.0) * 360
            if ang > 0:
                canvas.create_arc(cx - r, cy - r, cx + r, cy + r,
                                  start=start, extent=ang,
                                  fill=color, outline=COLORS['bg'], width=2)
            start += ang

        canvas.create_oval(cx - inner, cy - inner, cx + inner, cy + inner,
                           fill=COLORS['dim'], outline=COLORS['dim'])
        canvas.create_text(cx, cy - 15, text=f"{focus_pct}% Foco",
                           font=("Cascadia Code", 10, "bold"), fill=COLORS['focus'])
        canvas.create_text(cx, cy + 5,  text=f"{break_pct}% Descanso",
                           font=("Cascadia Code", 10, "bold"), fill=COLORS['rest'])
        canvas.create_text(cx, cy + 25, text=f"{pause_pct}% Pausa",
                           font=("Cascadia Code", 10, "bold"), fill=COLORS['current_highlight'])

        lf = tk.Frame(parent, bg=COLORS['dim'])
        lf.pack(fill='x', pady=(10, 0))
        for text, color in [
            ("● Foco",     COLORS['focus']),
            ("● Descanso", COLORS['rest']),
            ("● Pausa",    COLORS['current_highlight']),
        ]:
            item = tk.Frame(lf, bg=COLORS['dim'])
            item.pack(side='left', padx=10, expand=True)
            tk.Label(item, text=text, font=("Cascadia Code", 9, "bold"),
                     bg=COLORS['dim'], fg=color).pack()

    # ── Tarefas no Relatório ─────────────────────────────────────

    def _add_task_report(self, parent, number, task):
        """Tarefa em formato de relatório com status editável."""
        from tkinter import ttk

        task_box = tk.Frame(parent, bg=COLORS['bg'], bd=1, relief='solid')
        task_box.pack(fill='x', pady=8)

        title_frame = tk.Frame(task_box, bg=COLORS['bg'])
        title_frame.pack(fill='x', padx=10, pady=8)

        color  = COLORS['success'] if task.status == "Concluída" else COLORS['accent']
        symbol = "✓" if task.status == "Concluída" else "✕"

        tk.Label(
            title_frame,
            text=f"{symbol} Tarefa {number}: {task.name.upper()} [{task.weight}x]",
            font=("Cascadia Code", 10, "bold"),
            bg=COLORS['bg'], fg=color
        ).pack(side='left', fill='x', expand=True)

        status_var   = tk.StringVar(value=task.status)
        status_combo = ttk.Combobox(title_frame, textvariable=status_var,
                                    values=["Concluída", "Abandonada", "Pendente"],
                                    state='readonly', width=12,
                                    font=("Cascadia Code", 8))
        status_combo.pack(side='right', padx=5)

        def _on_status_change(event=None):
            task.status = status_var.get()

        status_combo.bind('<<ComboboxSelected>>', _on_status_change)

        details_frame = tk.Frame(task_box, bg=COLORS['dim'])
        details_frame.pack(fill='x', padx=10, pady=(0, 8))

        self.add_stat_row(details_frame, "Foco:",    self.format_time(task.duration_seconds_real), COLORS['focus'])
        self.add_stat_row(details_frame, "Pausa:",   "0:00",                                       COLORS['current_highlight'])
        self.add_stat_row(details_frame, "Descanso:", "0:00",                                      COLORS['rest'])

    def _add_task_with_status_edit(self, parent, number, task):
        """Tarefa com opção de editar status."""
        from tkinter import ttk

        color  = COLORS['success'] if task.status == "Concluída" else COLORS['accent']
        symbol = "✓" if task.status == "Concluída" else "✕"

        tc = tk.Frame(parent, bg=COLORS['bg'], bd=1, relief='solid')
        tc.pack(pady=5, padx=5, fill='x')

        hr = tk.Frame(tc, bg=COLORS['bg'])
        hr.pack(padx=10, pady=8, fill='x')

        tk.Label(hr, text=f"{symbol} #{number} [{task.weight}x]",
                 font=("Cascadia Code", 10, "bold"),
                 bg=COLORS['bg'], fg=color).pack(side='left', padx=5)
        tk.Label(hr, text=task.name.upper(), font=FONT_SMALL,
                 bg=COLORS['bg'], fg=COLORS['fg']).pack(side='left', padx=5, fill='x', expand=True)

        status_var   = tk.StringVar(value=task.status)
        status_combo = ttk.Combobox(hr, textvariable=status_var,
                                    values=["Concluída", "Abandonada", "Pendente"],
                                    state='readonly', width=12,
                                    font=("Cascadia Code", 9))
        status_combo.pack(side='right', padx=5)

        def _on_status_change(event=None):
            task.status = status_var.get()
            sym_new = "✓" if task.status == "Concluída" else "✕"
            col_new = COLORS['success'] if task.status == "Concluída" else COLORS['accent']
            hr.winfo_children()[0].config(
                text=f"{sym_new} #{number} [{task.weight}x]", fg=col_new
            )

        status_combo.bind('<<ComboboxSelected>>', _on_status_change)

        tr = tk.Frame(tc, bg=COLORS['dim'])
        tr.pack(padx=10, pady=(0, 8), fill='x')

        tk.Label(tr, text=f"Planejado: {self.format_time(task.duration_seconds)}",
                 font=("Cascadia Code", 9), bg=COLORS['dim'],
                 fg=COLORS['text_dim']).pack(side='left', padx=5)
        tk.Label(tr, text=f"Real: {self.format_time(task.duration_seconds_real)}",
                 font=("Cascadia Code", 9, "bold"),
                 bg=COLORS['dim'], fg=COLORS['focus']).pack(side='left', padx=5)

        diff  = task.duration_seconds_real - task.duration_seconds
        v_str = f"Variação: {'+' if diff >= 0 else ''}{self.format_time(abs(diff))}"
        v_col = COLORS['accent'] if diff > 0 else COLORS['success']
        tk.Label(tr, text=v_str, font=("Cascadia Code", 9),
                 bg=COLORS['dim'], fg=v_col).pack(side='right', padx=5)

    def _save_stats(self):
        """Salva mudanças de status e mostra confirmação."""
        self.session_manager.save_state(self)
        CustomDialog.show_info(self.root, "Salvo", "Status das tarefas salvo com sucesso!")

    def log_event(self, tp, name, det):
        ts = datetime.datetime.now()
        self.session_log.append([
            ts.strftime("%Y-%m-%d"), ts.strftime("%H:%M:%S"), tp, name, det
        ])
