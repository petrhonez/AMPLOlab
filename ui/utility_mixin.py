# ui/utility_mixin.py
import os
import shutil
import threading
import tkinter as tk

import config as _cfg
from config import *
from ui.dialogs import CustomDialog


class UtilityMixin:
    """Utilitários gerais: hover em botões, e-mail, limpeza de histórico,
    formatação de tempo e tela de confirmação integrada."""

    # ── Hover em Botões ──────────────────────────────────────────

    def add_button_hover_effect(self, button, hover_color):
        orig = button.cget('fg')
        button.bind('<Enter>', lambda e: button.config(fg=hover_color))
        button.bind('<Leave>', lambda e: button.config(fg=orig))

    # ── E-mail e Histórico ───────────────────────────────────────

    def _manual_send_email(self):
        cfg = self.email_manager._load_config()
        if not cfg.get("enabled", False):
            CustomDialog.show_info(
                self.root, "E-mail desativado",
                f"Para ativar o e-mail, edite o arquivo:\n{CONFIG_FILE}\n\n"
                'Defina "enabled": true e preencha as credenciais.'
            )
            return
        threading.Thread(target=self.email_manager.send_daily_report,
                         daemon=True).start()
        CustomDialog.show_info(self.root, "Enviando",
                               "Relatório sendo enviado em segundo plano.")

    def clear_reports(self):
        if not CustomDialog.ask_yes_no(
            self.root, "Confirmar Limpeza",
            "Deseja excluir todo o histórico?\nEsta ação não pode ser desfeita."
        ):
            return
        try:
            if os.path.exists(LOG_STATISTICS):
                os.remove(LOG_STATISTICS)
            if os.path.exists(SESSION_DIR):
                shutil.rmtree(SESSION_DIR)
            os.makedirs(SESSION_DIR, exist_ok=True)
            CustomDialog.show_info(self.root, "Sucesso", "Histórico excluído com sucesso!")
            self.build_planning_screen()
        except Exception as e:
            CustomDialog.show_error(self.root, "Erro", str(e))

    # ── Formatação de Tempo ──────────────────────────────────────

    def format_time(self, seconds):
        return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

    def format_time_long(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    # ── Tela de Confirmação Integrada ────────────────────────────

    def show_confirmation_screen(
        self,
        title: str,
        message: str,
        callback_yes,
        callback_no,
        confirm_type: str = "generic",
    ):
        """Exibe uma sobreposição de confirmação sobre a tela atual.

        Parâmetros
        ----------
        title        : Título exibido na caixa.
        message      : Mensagem de confirmação.
        callback_yes : Callable executado se o usuário confirmar.
        callback_no  : Callable executado se o usuário cancelar.
        confirm_type : "success", "skip", "abort" ou "generic" — afeta a cor do botão sim.
        """
        if self.in_confirmation_screen:
            return

        self.in_confirmation_screen = True
        self.confirmation_type      = confirm_type
        self.confirmation_start_time = __import__('datetime').datetime.now()

        # Registra tempo de pausa enquanto confirmação está aberta
        if self.timer_running and not self.is_break:
            if self.timer_after_id:
                self.root.after_cancel(self.timer_after_id)
            self._confirm_pause_start = __import__('datetime').datetime.now()
        else:
            self._confirm_pause_start = None

        # Cores por tipo
        color_map = {
            "success": COLORS['success'],
            "skip":    COLORS['accent'],
            "abort":   COLORS['accent'],
            "generic": COLORS['focus'],
        }
        yes_color = color_map.get(confirm_type, COLORS['focus'])

        # Overlay semi-transparente
        overlay = tk.Frame(self.root, bg=COLORS['bg'])
        overlay.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        # Caixa de diálogo centralizada
        box = tk.Frame(overlay, bg=COLORS['dim'],
                       highlightthickness=2,
                       highlightbackground=COLORS['topbar_border'])
        box.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(box, text=title,
                 font=(_cfg.BASE_FONT, 18, "bold"),
                 bg=COLORS['dim'], fg=yes_color).pack(padx=40, pady=(30, 10))

        tk.Label(box, text=message,
                 font=(_cfg.BASE_FONT, 13),
                 bg=COLORS['dim'], fg=COLORS['fg'],
                 justify='center', wraplength=480).pack(padx=40, pady=(0, 24))

        btn_row = tk.Frame(box, bg=COLORS['dim'])
        btn_row.pack(padx=40, pady=(0, 30))

        def _yes():
            self._close_confirmation(overlay)
            callback_yes()

        def _no():
            self._close_confirmation(overlay)
            callback_no()

        tk.Button(
            btn_row, text="✓  SIM",
            command=_yes,
            bg=yes_color, fg='#000',
            font=(_cfg.BASE_FONT, 13, "bold"),
            relief='flat', cursor='hand2',
            padx=20, pady=10,
            activebackground=COLORS['topbar_border'],
            activeforeground=yes_color,
        ).pack(side='left', padx=(0, 16))

        tk.Button(
            btn_row, text="✕  NÃO",
            command=_no,
            bg=COLORS['dim'], fg=COLORS['text_dim'],
            font=(_cfg.BASE_FONT, 13, "bold"),
            relief='flat', cursor='hand2',
            padx=20, pady=10,
            highlightthickness=1,
            highlightbackground=COLORS['topbar_border'],
            activebackground=COLORS['topbar_border'],
        ).pack(side='left')

        # Atalhos de teclado para a caixa de confirmação
        self.root.bind('<Return>',  lambda e: _yes())
        self.root.bind('<Escape>',  lambda e: _no())

    def _close_confirmation(self, overlay):
        """Fecha o overlay de confirmação e restaura o estado."""
        # Contabiliza o tempo pausado pela confirmação
        if self._confirm_pause_start is not None:
            import datetime
            paused = (datetime.datetime.now() - self._confirm_pause_start).total_seconds()
            self.total_paused_time += paused
            self._confirm_pause_start = None

        overlay.destroy()
        self.in_confirmation_screen = False
        self.confirmation_type      = None

        # Restaura atalhos normais do cronômetro se ainda estiver rodando
        if hasattr(self, 'lbl_timer'):
            self.root.bind('p',              self.toggle_pause)
            self.root.bind('<space>',        self.toggle_pause)
            self.root.bind('<Return>',       lambda e: None)
            self.root.bind('<Escape>',       lambda e: None)
            self.root.bind('<Control-Return>', self.handle_success)
            self.root.bind('<Control-a>',    self.handle_skip)
            self.root.bind('<Control-A>',    self.handle_skip)
            self.root.bind('<Control-x>',    self.emergency_trigger)
            self.root.bind('<Control-X>',    self.emergency_trigger)

            # Retoma o timer se estava rodando
            if self.timer_running:
                self.run_timer()
