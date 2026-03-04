# ui/app.py
import tkinter as tk
import json
import datetime
import os
import sys
import platform
import ctypes

from config import *
from models.task import Task
from services.audio import SoundManager
from services.sessions import SessionManager, StatisticsManager
from services.email_svc import EmailManager, EmailScheduler
from ui.dialogs import CustomDialog
from ui.config._base import _load_registry

# ── Mixins ──────────────────────────────────────────────────────
from ui.color_mixin   import ColorMixin
from ui.planning_mixin import PlanningMixin
from ui.timer_mixin   import TimerMixin
from ui.stats_mixin   import StatsMixin
from ui.topbar_mixin  import TopbarMixin
from ui.utility_mixin import UtilityMixin


class AmploApp(
    ColorMixin,
    PlanningMixin,
    TimerMixin,
    StatsMixin,
    TopbarMixin,
    UtilityMixin,
):
    """
    Controlador principal da interface.
    Gerencia as telas, o loop do relógio e as interações do usuário.
    A lógica está dividida nos mixins importados acima.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Amplo")

        # Serviços
        self.sound_manager   = SoundManager()
        self.stats_manager   = StatisticsManager()
        self.session_manager = SessionManager()
        self.email_manager   = EmailManager(self.session_manager)
        self.scheduler       = EmailScheduler(self.email_manager)
        self.scheduler.start()

        self.root.configure(bg=COLORS['bg'])
        self.root.attributes('-fullscreen', True)

        # ── Estado do cronômetro ──────────────────────────────
        self.tasks               = []
        self.current_task_index  = 0
        self.is_break            = False
        self.timer_running       = False
        self.timer_after_id      = None
        self.clock_after_id      = None
        self.time_left           = 0
        self.break_per_slot      = 0

        # ── Topbar / mapa ─────────────────────────────────────
        self.topbar_visible         = False
        self.topbar_frame           = None
        self.timeline_blocks        = []
        self.topbar_opened_by_pause = False

        # ── Tempo e estatísticas ──────────────────────────────
        self.session_start_time    = None
        self.session_end_time      = None
        self.planned_end_time      = None
        self.total_paused_time     = 0.0
        self.pause_start_timestamp = None
        self.breaks_real           = []
        self.current_break_start   = None

        # ── Sistema de confirmação integrado ──────────────────
        self.in_confirmation_screen  = False
        self.confirmation_type       = None      # "success" | "skip" | "abort"
        self.confirmation_start_time = None
        self._confirm_pause_start    = None

        # ── UI vars — checkboxes bloco A ──────────────────────
        self.sound_enabled  = tk.BooleanVar(value=True)
        self.esp32_enabled  = tk.BooleanVar(value=False)
        self.lamp_enabled   = tk.BooleanVar(value=False)
        self.record_enabled = tk.BooleanVar(value=True)

        # ── Paletas / temas ───────────────────────────────────
        self.theme_idx   = 0
        self.palette_idx = 0
        self.rgb_idx     = 0

        # ── Log e navegação de menu ───────────────────────────
        self.session_log            = []
        self.menu_buttons           = []
        self.selected_button_index  = 0

        # ── Sistema de blink para navegação ───────────────────
        self._blink_state    = False
        self._blink_after_id = None
        self._blink_speed    = 400       # ms entre alternâncias
        self._nav_items      = []
        self._nav_index      = 0

        self.prevent_sleep()


        # Carrega configuração do registro central (c_registro.json)
        reg = _load_registry()

        # 1. Cores
        loaded_colors = reg.get("colors", {})
        for k, v in loaded_colors.items():
            if k in COLORS:
                COLORS[k] = v

        # 2. Áudio
        audio_cfg = reg.get("audio", {})
        self.sound_manager.enabled = audio_cfg.get("sound_enabled", True)
        self.sound_manager.style   = audio_cfg.get("sound_style", "leve")


        # 4. Modos
        self.focus_percent = reg.get("focus_percent", 80) / 100.0

        # 4. App Config (config.json)
        self._load_app_config()

        self._check_state_recovery()

    def _load_app_config(self):
        """Carrega configurações do app_config em config.json."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cfg = data.get("app_config", {})
                    self.sound_enabled.set(cfg.get("sound_enabled", True))
                    self.esp32_enabled.set(cfg.get("esp32_enabled", False))
                    self.lamp_enabled.set(cfg.get("lamp_enabled", False))
                    self.record_enabled.set(cfg.get("record_enabled", True))
                    
                    # Sincroniza estado inicial do sound_manager
                    self.sound_manager.enabled = self.sound_enabled.get()
        except Exception as e:
            print(f"Erro ao carregar config.json: {e}")

    def _save_app_config(self):
        """Salva o estado atual dos checkboxes em config.json."""
        try:
            data = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            if "app_config" not in data:
                data["app_config"] = {}
                
            data["app_config"].update({
                "sound_enabled":  self.sound_enabled.get(),
                "esp32_enabled":  self.esp32_enabled.get(),
                "lamp_enabled":   self.lamp_enabled.get(),
                "record_enabled": self.record_enabled.get(),
            })
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar config.json: {e}")

    # ── Inicialização ────────────────────────────────────────────

    def prevent_sleep(self):
        if platform.system() == 'Windows':
            try:
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)
            except Exception:
                pass

    def _check_state_recovery(self):
        """Verifica se há sessão interrompida e oferece recuperação."""
        state = self.session_manager.load_state()
        if state:
            if CustomDialog.ask_yes_no(
                self.root,
                "Sessão Interrompida",
                f"Uma sessão iniciada às {state['session_start'][11:16]} foi interrompida.\n\n"
                "Deseja retomar de onde parou?"
            ):
                self._restore_session(state)
                return
            else:
                self.session_manager.clear_state()
        self.build_planning_screen()

    def _restore_session(self, state: dict):
        """Reconstrói o estado da sessão a partir do JSON salvo."""
        self.tasks              = self.session_manager.restore_tasks(state)
        self.current_task_index = state["current_task_index"]
        self.is_break           = state["is_break"]
        self.time_left          = state["time_left"]
        self.total_paused_time  = state["total_paused_time"]
        self.break_per_slot     = state["break_per_slot"]
        self.session_start_time = datetime.datetime.fromisoformat(state["session_start"])
        self.planned_end_time   = (
            datetime.datetime.fromisoformat(state["planned_end"])
            if state.get("planned_end") else None
        )
        self.breaks_real = [
            {
                "index":    b["index"],
                "start":    datetime.datetime.fromisoformat(b["start"]),
                "end":      datetime.datetime.fromisoformat(b["end"]),
                "duration": b["duration"],
            }
            for b in state.get("breaks_real", [])
        ]

        if self.is_break:
            self.setup_timer_ui("PAUSA REGENERATIVA", COLORS['rest'])
        else:
            current = self.tasks[self.current_task_index]
            self.setup_timer_ui(f"FOCO: {current.name.upper()}", COLORS['focus'])

        self.timer_running = True
        self.run_timer()

    # ── Limpeza de Frame ─────────────────────────────────────────

    def clean_frame(self):
        if self.timer_after_id:
            self.root.after_cancel(self.timer_after_id)
            self.timer_after_id = None
        if self.clock_after_id:
            self.root.after_cancel(self.clock_after_id)
            self.clock_after_id = None
        if self._blink_after_id:
            self.root.after_cancel(self._blink_after_id)
            self._blink_after_id = None

        self.timer_running = False

        keys_to_unbind = [
            'p', '<space>', 'm', 'Up', 'Down', 'Left', 'Right', '<Return>',
            '<Escape>', '<Control-Return>',
            '<Control-a>', '<Control-A>',
            '<Control-x>', '<Control-X>',
        ]
        for key in keys_to_unbind:
            try:
                self.root.unbind(key)
            except Exception:
                pass

        for w in self.root.winfo_children():
            w.destroy()

        self.topbar_frame    = None
        self.topbar_visible  = False
        self.timeline_blocks = []
        self.menu_buttons    = []

    # ── Menu Principal ───────────────────────────────────────────

    def build_planning_screen(self):
        self.clean_frame()
        self.entries_tasks = []
        self._nav_items    = []
        self._nav_index    = 0

        bg = COLORS['bg']

        outer = tk.Frame(self.root, bg=bg)
        outer.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        grid = tk.Frame(outer, bg=bg)
        grid.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        # Sidebar (~5%) | Conteúdo (~95%)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=19)
        grid.rowconfigure(0, weight=1)

        self._build_sidebar(grid)

        content_grid = tk.Frame(grid, bg=bg)
        content_grid.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)

        content_grid.columnconfigure(0, weight=10)
        content_grid.columnconfigure(1, weight=10)
        content_grid.rowconfigure(0, weight=1)
        content_grid.rowconfigure(1, weight=1)

        frm_c = self._make_block(content_grid, "",        0, 0, rowspan=2)
        self._build_block_c(frm_c)

        frm_d = self._make_block(content_grid, "SESSÃO",  0, 1)
        self._build_block_d(frm_d)

        frm_e = self._make_block(content_grid, "TAREFAS", 1, 1)
        self._build_block_e(frm_e)

        # Botão ✕ flutuante (acima do outer)
        btn_close = tk.Button(
            self.root, text="✕", command=lambda: sys.exit(),
            bg=COLORS['bg'], fg=COLORS['text_dim'],
            font=(BASE_FONT, 11, "bold"),
            relief='flat', cursor='hand2', padx=10, pady=6,
            activebackground=COLORS['accent'], activeforeground='#fff',
            bd=0
        )
        btn_close.place(relx=1.0, rely=0.0, anchor='ne', x=-6, y=6)
        btn_close.lift()
        self.sidebar_buttons.append(btn_close)

        self.update_menu_clock()
        self._setup_nav_keys()

    # ── Sidebar ──────────────────────────────────────────────────

    def _build_sidebar(self, parent):
        """Sidebar vertical com botões de configuração."""
        bg     = COLORS['bg']
        border = COLORS['topbar_border']

        sidebar = tk.Frame(parent, bg=border, width=70)
        sidebar.grid(row=0, column=0, sticky='nsew')
        sidebar.pack_propagate(False)

        inner = tk.Frame(sidebar, bg=bg)
        inner.pack(fill='both', expand=True, padx=3, pady=3)

        tk.Label(inner, text="CFG",
                 font=(BASE_FONT, 7, "bold"),
                 bg=bg, fg=COLORS['text_dim']).pack(pady=(8, 4))

        config_pages = [
            ("📋", "Registros", "registros"),
            ("🎨", "Cores",     "cores"),
            ("🔊", "Áudio",     "audio"),
            ("📨", "E-mail",    "email"),
            ("📡", "Esp32",     "esp32"),
            ("⚙️",  "Modos",     "modos"),
        ]
        self.sidebar_buttons = []

        for emoji, label, page in config_pages:
            btn = tk.Button(
                inner, text=emoji,
                font=(BASE_FONT, 18),
                bg=bg, fg=COLORS['text_dim'],
                relief='flat', cursor='hand2',
                padx=8, pady=10, bd=0,
                activebackground=bg, activeforeground=COLORS['focus'],
                command=lambda p=page: self._open_config_page(p)
            )
            self.sidebar_buttons.append(btn)

            tip = tk.Label(inner, text=label,
                           font=(BASE_FONT, 6),
                           bg=bg, fg=COLORS['text_dim'])

            def _enter(e, b=btn, t=tip):
                b.config(fg=COLORS['focus'])
                t.pack(fill='x')

            def _leave(e, b=btn, t=tip):
                b.config(fg=COLORS['text_dim'])
                t.pack_forget()

            btn.bind('<Enter>', _enter)
            btn.bind('<Leave>', _leave)
            btn.pack(fill='x', pady=1)

        tk.Frame(inner, bg=COLORS['dim'], height=1).pack(
            fill='x', pady=(8, 4), side='bottom')

        tk.Button(
            inner, text="✕",
            font=(BASE_FONT, 14, "bold"),
            bg=bg, fg=COLORS['text_dim'],
            relief='flat', cursor='hand2',
            padx=8, pady=8, bd=0,
            activebackground=COLORS['accent'], activeforeground='#fff',
            command=lambda: sys.exit()
        ).pack(fill='x', pady=2, side='bottom')

    def _open_config_page(self, page: str):
        import importlib
        try:
            self.clean_frame()   # ← limpa tela antes de renderizar
            module = importlib.import_module(f'ui.config.{page}')
            
            # Tenta open_ui (novo padrão) ou open (antigo)
            opener = getattr(module, 'open_ui', getattr(module, 'open', None))
            if opener:
                opener(self.root, COLORS, {
                    'clock':  FONT_CLOCK,
                    'date':   FONT_DATE,
                    'main':   FONT_MAIN,
                    'small':  FONT_SMALL,
                    'topbar': FONT_TOPBAR,
                    'stats':  FONT_STATS,
                }, self)
            else:
                self.build_planning_screen()
        except ModuleNotFoundError:
            self.build_planning_screen()   # volta ao menu se página não existe
        except Exception as exc:
            CustomDialog.show_error(self.root, "Erro", str(exc))
            self.build_planning_screen()

    # ── Fábrica de Bloco ─────────────────────────────────────────

    def _make_block(self, parent, title, row, col, rowspan=1):
        """Cria um bloco visual com borda e título."""
        bg     = COLORS['bg']
        border = COLORS['topbar_border']

        outer = tk.Frame(parent, bg=border)
        outer.grid(row=row, column=col, rowspan=rowspan,
                   sticky='nsew', padx=4, pady=4)

        if title:
            header = tk.Frame(outer, bg=COLORS['dim'], height=24)
            header.pack(fill='x')
            header.pack_propagate(False)
            tk.Label(header, text=title, font=(BASE_FONT, 9),
                     bg=COLORS['dim'], fg=COLORS['text_dim']).pack(
                         side='left', padx=10, pady=4)
            tk.Frame(outer, bg=border, height=1).pack(fill='x')

        inner = tk.Frame(outer, bg=bg)
        inner.pack(fill='both', expand=True, padx=10, pady=8)
        return inner
