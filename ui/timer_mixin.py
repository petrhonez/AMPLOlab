# ui/timer_mixin.py
import datetime
import tkinter as tk

import config as _cfg
from config import *
from ui.dialogs import CustomDialog
from ui.config.modos import _load_focus_pct


class TimerMixin:
    """Cálculo de schedule, controle do cronômetro, teclas de atalho e botões."""

    # ── Cálculo de Schedule ──────────────────────────────────────

    def calculate_schedule(self):
        try:
            raw = self.entry_end_time.get().strip()
            if ":" in raw:
                h, m = raw.split(":")
                raw = f"{int(h):02d}:{int(m):02d}"
            end_time = datetime.datetime.strptime(raw, "%H:%M")
            now      = datetime.datetime.now()
            target   = now.replace(hour=end_time.hour, minute=end_time.minute, second=0)
            if target <= now:
                target += datetime.timedelta(days=1)

            total_sec   = (target - now).total_seconds()
            valid_tasks = [
                __import__('models.task', fromlist=['Task']).Task(e.get().strip(), w.get())
                for e, w in self.entries_tasks if e.get().strip()
            ]
            if not valid_tasks:
                return

            self.tasks          = valid_tasks
            focus_ratio         = getattr(self, 'focus_percent', None)
            if focus_ratio is None:
                focus_ratio = _load_focus_pct(CONFIG_FILE) / 100.0
            rest_ratio          = 1.0 - focus_ratio

            work_sec            = total_sec * focus_ratio
            self.break_per_slot = (total_sec * rest_ratio) / len(self.tasks)
        
            total_w             = sum(t.weight for t in self.tasks)

            self.session_start_time    = now
            self.planned_end_time      = target
            self.total_paused_time     = 0.0
            self.pause_start_timestamp = None
            self.breaks_real           = []
            self.current_break_start   = None

            current_time = now
            for i, t in enumerate(self.tasks):
                t.duration_seconds = int((t.weight / total_w) * work_sec)
                t.start_time       = current_time
                current_time      += datetime.timedelta(seconds=t.duration_seconds)
                if i < len(self.tasks) - 1:
                    current_time += datetime.timedelta(seconds=int(self.break_per_slot))

            self.current_task_index = 0
            self.time_left          = self.tasks[0].duration_seconds
            self.is_break           = False
            self.session_manager.save_state(self)

            self.start_task_cycle()
        except Exception as ex:
            CustomDialog.show_error(self.root, "Erro", f"Formato HH:MM inválido.\n{ex}")

    # ── Ciclos de Tarefa e Pausa ─────────────────────────────────

    def start_task_cycle(self):
        self.is_break  = False
        current        = self.tasks[self.current_task_index]
        current.start_time_real = datetime.datetime.now()
        self.time_left = current.duration_seconds
        self.setup_timer_ui(f"FOCO: {current.name.upper()}", COLORS['focus'])
        self.timer_running = True
        self.sound_manager.play_task_start()
        self.session_manager.save_state(self)
        self.run_timer()

    def start_break_cycle(self):
        self.is_break            = True
        self.current_break_start = datetime.datetime.now()
        self.time_left           = int(self.break_per_slot)
        self.setup_timer_ui("PAUSA REGENERATIVA", COLORS['rest'])
        self.timer_running       = True
        self.sound_manager.play_break_start()
        self.session_manager.save_state(self)
        self.run_timer()

    # ── Interface do Cronômetro ──────────────────────────────────

    def setup_timer_ui(self, title, color, subtitle=""):
        self.clean_frame()
        container = tk.Frame(self.root, bg=COLORS['bg'])
        container.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        center_frame = tk.Frame(container, bg=COLORS['bg'])
        center_frame.place(relx=.5, rely=.5, anchor='center')

        tk.Label(center_frame, text=title, font=FONT_MAIN,
                 bg=COLORS['bg'], fg=color).pack(pady=10)

        self.lbl_timer = tk.Label(
            center_frame,
            text=self.format_time(self.time_left),
            font=(_cfg.BASE_FONT, 300, "bold"),
            bg=COLORS['bg'], fg=color
        )
        self.lbl_timer.pack(pady=20)

        if subtitle:
            tk.Label(center_frame, text=subtitle, font=FONT_SMALL,
                     bg=COLORS['bg'], fg=COLORS['fg']).pack()

        instr = "---" if not self.is_break else "-||-"
        tk.Label(self.root, text=instr, font=(_cfg.BASE_FONT, 10),
                 bg=COLORS['bg'], fg=COLORS['text_dim']).pack(side='bottom', pady=30)

        self.build_timer_buttons()

        # Atalhos de teclado
        self.root.bind('p',              self.toggle_pause)
        self.root.bind('<space>',        self.toggle_pause)
        self.root.bind('m',              self.toggle_topbar)
        self.root.bind('<Control-Return>', self.handle_success)
        self.root.bind('<Control-q>', self.handle_success)
        self.root.bind('<Control-Q>', self.handle_success)
        self.root.bind('<Control-a>',    self.handle_skip)
        self.root.bind('<Control-A>',    self.handle_skip)
        self.root.bind('<Control-x>',    self.emergency_trigger)
        self.root.bind('<Control-X>',    self.emergency_trigger)

    def build_timer_buttons(self):
        buttons_frame = tk.Frame(self.root, bg=COLORS['bg'])
        buttons_frame.pack(side='bottom', pady=15)

        btn_style = {
            'font': FONT_BUTTON_SMALL,
            'bg':   COLORS['dim'],
            'fg':   COLORS['text_dim'],
            'relief': 'flat', 'bd': 0,
            'padx': 8, 'pady': 4, 'cursor': 'hand2',
            'activebackground': COLORS['topbar_border'],
        }

        if not self.is_break:
            b_ok = tk.Button(buttons_frame, text="✓ Concluir",
                             command=lambda: self.handle_success(None), **btn_style)
            b_ok.pack(side='left', padx=10)
            self.add_button_hover_effect(b_ok, COLORS['success'])

            b_ab = tk.Button(buttons_frame, text="✕ Abandonar",
                             command=lambda: self.handle_skip(None), **btn_style)
            b_ab.pack(side='left', padx=10)
            self.add_button_hover_effect(b_ab, COLORS['accent'])

            b_pa = tk.Button(
                buttons_frame,
                text="⏸ Pausar" if self.timer_running else "▶ Retomar",
                command=lambda: self.toggle_pause(None), **btn_style
            )
            b_pa.pack(side='left', padx=10)
            self.add_button_hover_effect(b_pa, COLORS['focus'])
            self.btn_pause_ref = b_pa
        else:
            b_sk = tk.Button(buttons_frame, text="⏭ Pular Pausa",
                             command=lambda: self.handle_success(None), **btn_style)
            b_sk.pack(side='left', padx=10)
            self.add_button_hover_effect(b_sk, COLORS['rest'])

        b_mp = tk.Button(buttons_frame, text="🗺 Mapa",
                         command=lambda: self.toggle_topbar(None), **btn_style)
        b_mp.pack(side='left', padx=10)
        self.add_button_hover_effect(b_mp, COLORS['focus'])

        b_ex = tk.Button(buttons_frame, text="⚠ Sair",
                         command=lambda: self.emergency_trigger(None), **btn_style)
        b_ex.pack(side='left', padx=10)
        self.add_button_hover_effect(b_ex, COLORS['accent'])

    # ── Loop do Cronômetro ───────────────────────────────────────

    def run_timer(self):
        if self.timer_after_id:
            self.root.after_cancel(self.timer_after_id)

        if self.timer_running and self.time_left > 0:
            self.lbl_timer.config(text=self.format_time(self.time_left))
            
            style = getattr(self.sound_manager, 'style', 'leve')
            if style == 'critico' and 1 <= self.time_left <= 10:
                self.sound_manager.play_tick()

            if self.is_break:
                if style == 'rigido' and self.time_left in (5, 4, 3, 2, 1):
                    self.sound_manager.play_break_warning_rigid()
                elif style == 'leve' and self.time_left == 10:
                    self.sound_manager.play_break_warning()

            self.time_left -= 1
            self.timer_after_id = self.root.after(1000, self.run_timer)
        elif self.timer_running and self.time_left <= 0:
            self.auto_transition()

    # ── Transições Automáticas ───────────────────────────────────

    def auto_transition(self):
        """Transição automática quando o tempo esgota (sem confirmação)."""
        if not self.is_break:
            self.sound_manager.play_time_exhausted()
            self.timer_running = False
            task = self.tasks[self.current_task_index]
            task.end_time_real = datetime.datetime.now()
            task.calculate_real_duration()
            task.status = "Concluída"
            self.log_event("TAREFA", task.name, "Concluída (tempo esgotado)")
            self.sound_manager.play_task_completed()
            if self.topbar_visible:
                self.update_timeline_block(self.current_task_index)
            self.trigger_rest_or_finish()
        else:
            if self.current_break_start:
                end = datetime.datetime.now()
                self.breaks_real.append({
                    'index':    self.current_task_index,
                    'start':    self.current_break_start,
                    'end':      end,
                    'duration': int((end - self.current_break_start).total_seconds())
                })
                self.current_break_start = None
            self.skip_rest()

    def trigger_rest_or_finish(self):
        """Decide se inicia um descanso ou finaliza a sessão."""
        has_next_task = self.current_task_index < len(self.tasks) - 1
        if has_next_task:
            self.is_break = True
            self.start_break_cycle()
        else:
            self.is_break = False
            self.show_summary_screen()

    def skip_rest(self):
        self.timer_running = False
        if self.current_break_start:
            end = datetime.datetime.now()
            self.breaks_real.append({
                'index':    self.current_task_index,
                'start':    self.current_break_start,
                'end':      end,
                'duration': int((end - self.current_break_start).total_seconds())
            })
            self.current_break_start = None
        self.current_task_index += 1
        if self.current_task_index < len(self.tasks):
            self.start_task_cycle()
        else:
            self.finish_session()

    # ── Ações do Usuário ─────────────────────────────────────────

    def handle_success(self, event=None):
        """Conclui a tarefa/pausa imediatamente (Ctrl+Enter)."""
        if not self.is_break:
            task = self.tasks[self.current_task_index]
            task.end_time_real = datetime.datetime.now()
            task.calculate_real_duration()
            task.status = "Concluída"
            self.log_event("TAREFA", task.name, "Concluída")
            self.sound_manager.play_task_completed()
            if self.topbar_visible:
                self.update_timeline_block(self.current_task_index)
            self.trigger_rest_or_finish()
        else:
            self.skip_rest()

    def handle_skip(self, event=None):
        """Pede confirmação para abandonar a tarefa (Ctrl+A)."""
        if self.in_confirmation_screen:
            return
        if not self.is_break:
            task = self.tasks[self.current_task_index]

            def _on_yes():
                task.end_time_real = datetime.datetime.now()
                task.calculate_real_duration()
                task.status = "Abandonada"
                self.log_event("TAREFA", task.name, "Abandonada")
                self.sound_manager.play_task_abandoned()
                if self.topbar_visible:
                    self.update_timeline_block(self.current_task_index)
                self.trigger_rest_or_finish()

            self.show_confirmation_screen(
                "Abandonar Tarefa",
                f'Deseja realmente abandonar "{task.name}"?',
                _on_yes, lambda: None, "skip"
            )
        else:
            self.skip_rest()

    def emergency_trigger(self, event=None):
        """Pede confirmação para abortar a sessão e voltar ao menu (Ctrl+X)."""
        if self.in_confirmation_screen:
            return

        def _on_yes():
            self.sound_manager.play_emergency_abort()
            self.session_manager.clear_state()
            self.build_planning_screen()

        self.show_confirmation_screen(
            "Abortar Sessão?",
            "Deseja realmente voltar ao menu?\nO progresso desta sessão será perdido.",
            _on_yes, lambda: None, "abort"
        )

    # ── Pausa ────────────────────────────────────────────────────

    def toggle_pause(self, event=None):
        if self.is_break:
            return
        self.timer_running = not self.timer_running
        if not self.timer_running:
            if self.timer_after_id:
                self.root.after_cancel(self.timer_after_id)
            self.lbl_timer.config(fg=COLORS['dim'])
            self.sound_manager.play_pause()
            self.pause_start_timestamp = datetime.datetime.now()
            if hasattr(self, 'btn_pause_ref'):
                self.btn_pause_ref.config(text="▶ Retomar")
            self.topbar_opened_by_pause = True
            self.show_topbar()
        else:
            self.lbl_timer.config(fg=COLORS['focus'])
            self.sound_manager.play_resume()
            if self.pause_start_timestamp:
                self.total_paused_time += (
                    datetime.datetime.now() - self.pause_start_timestamp
                ).total_seconds()
                self.pause_start_timestamp = None
            if hasattr(self, 'btn_pause_ref'):
                self.btn_pause_ref.config(text="⏸ Pausar")
            if self.topbar_opened_by_pause and self.topbar_visible:
                self.hide_topbar()
                self.topbar_opened_by_pause = False
            self.run_timer()

    # ── Compatibilidade de nome ──────────────────────────────────

    def show_summary_screen(self):
        """Alias para finish_session (chamado por trigger_rest_or_finish)."""
        self.finish_session()
