# ui/color_mixin.py
import os
import json
import tkinter as tk

from config import *
from ui.dialogs import CustomDialog


class ColorMixin:
    """Cores, fontes, página de customização e sistema de paletas."""

    # ── Página de Customização ──────────────────────────────────

    def _open_customization_page(self):
        self._show_customization_page()

    def _show_customization_page(self):
        """Constrói e exibe a página de customização (cores + paletas)."""
        for widget in self.root.winfo_children():
            widget.destroy()

        bg = COLORS['bg']

        topbar = tk.Frame(self.root, bg=COLORS['dim'], height=30)
        topbar.pack(fill='x')
        topbar.pack_propagate(False)

        tk.Button(
            topbar, text="◀ VOLTAR", command=self.build_planning_screen,
            font=("Cascadia Code", 9, "bold"),
            bg=COLORS['dim'], fg=COLORS['focus'],
            relief='flat', cursor='hand2', bd=0,
            padx=12, pady=6,
            activebackground=COLORS['focus'], activeforeground='#000'
        ).pack(side='left', padx=8, pady=2)

        tk.Label(topbar, text="PERSONALIZAR",
                 font=("Cascadia Code", 9),
                 bg=COLORS['dim'], fg=COLORS['text_dim']).pack(side='left', padx=8)

        main_frame = tk.Frame(self.root, bg=bg)
        main_frame.pack(fill='both', expand=True)

        center_frame = tk.Frame(main_frame, bg=bg)
        center_frame.place(relx=0.5, rely=0.5, anchor='center',
                           relwidth=0.9, relheight=0.95)

        self._build_customization_page(center_frame)

    def _build_customization_page(self, parent):
        """Constrói o conteúdo da página de customização."""
        from tkinter import colorchooser
        bg = COLORS['bg']

        COLOR_SLOTS = [
            ("🎨 Fundo",              'bg'),
            ("🎨 Texto Principal",    'fg'),
            ("📦 Superfície",         'dim'),
            ("🖼 Borda",              'topbar_border'),
            ("⭐ Foco (Destaque)",    'focus'),
            ("😴 Descanso",           'rest'),
            ("📝 Texto Secundário",   'text_dim'),
            ("⚠ Acento (Atenção)",   'accent'),
            ("✓ Sucesso",            'success'),
            ("▶ Em Andamento",       'current_highlight'),
        ]

        tk.Label(parent, text="PERSONALIZAR CORES",
                 font=("Cascadia Code", 15, "bold"),
                 bg=bg, fg=COLORS['focus']).pack(anchor='center', pady=(16, 16), padx=12)

        grid_f = tk.Frame(parent, bg=bg)
        grid_f.pack(fill='both', expand=False, padx=12, pady=0)

        self._color_swatches = {}

        for idx, (label, key) in enumerate(COLOR_SLOTS):
            row = idx // 2
            col = idx % 2

            cell = tk.Frame(grid_f, bg=COLORS['dim'], relief='solid', bd=1,
                            highlightthickness=0)
            cell.grid(row=row, column=col, sticky='ew', padx=3, pady=3)

            inner = tk.Frame(cell, bg=COLORS['dim'])
            inner.pack(fill='both', expand=True, padx=8, pady=8)

            swatch_frame = tk.Frame(inner, bg=COLORS['dim'])
            swatch_frame.pack(fill='x', pady=(0, 6))

            cv = tk.Canvas(swatch_frame, width=100, height=40, bg=COLORS['dim'],
                           highlightthickness=0, cursor='hand2', relief='flat', bd=0)
            cv.pack(side='left', padx=(0, 10), expand=True, fill='y')
            cv.create_rectangle(0, 0, 100, 40, fill=COLORS[key],
                                outline=COLORS['topbar_border'], width=2)
            self._color_swatches[key] = cv

            label_frame = tk.Frame(inner, bg=COLORS['dim'])
            label_frame.pack(fill='x')

            tk.Label(label_frame, text=label, font=("Cascadia Code", 11),
                     bg=COLORS['dim'], fg=COLORS['fg']).pack(anchor='w')

            hex_var = tk.StringVar(value=COLORS[key])
            tk.Label(label_frame, textvariable=hex_var,
                     font=("Cascadia Code", 10, "bold"),
                     bg=COLORS['dim'], fg=COLORS['text_dim']).pack(anchor='w')

            def _pick(k=key, canvas=cv, hex_label=hex_var):
                result = colorchooser.askcolor(color=COLORS[k],
                                               title=f"Cor: {k}", parent=self.root)
                if result and result[1]:
                    COLORS[k] = result[1]
                    canvas.delete('all')
                    canvas.create_rectangle(0, 0, 100, 40, fill=COLORS[k],
                                            outline=COLORS['topbar_border'], width=2)
                    hex_label.set(COLORS[k])
                    if k == 'bg':
                        self.root.configure(bg=COLORS['bg'])

            cv.bind('<Button-1>', lambda e, fn=_pick: fn())

        grid_f.columnconfigure(0, weight=1)
        grid_f.columnconfigure(1, weight=1)

        tk.Frame(parent, bg=COLORS['dim'], height=1).pack(fill='x', pady=(14, 10), padx=12)
        btn_apply = tk.Button(
            parent, text="🔄  APLICAR CORES",
            command=self._apply_and_refresh,
            bg=COLORS['dim'], fg=COLORS['focus'],
            font=("Cascadia Code", 13, "bold"),
            relief='flat', cursor='hand2',
            padx=14, pady=9,
            activebackground=COLORS['focus'], activeforeground='#000'
        )
        btn_apply.pack(pady=10)
        btn_apply.bind('<Enter>', lambda e: btn_apply.config(bg=COLORS['focus'], fg='#000'))
        btn_apply.bind('<Leave>', lambda e: btn_apply.config(bg=COLORS['dim'], fg=COLORS['focus']))

        tk.Frame(parent, bg=COLORS['dim'], height=1).pack(fill='x', pady=(14, 10), padx=12)
        tk.Label(parent, text="PALETAS SALVAS",
                 font=("Cascadia Code", 14, "bold"),
                 bg=bg, fg=COLORS['text_dim']).pack(anchor='center', pady=(0, 10), padx=12)

        palette_actions = tk.Frame(parent, bg=bg)
        palette_actions.pack(fill='x', pady=(0, 12), padx=12)

        btn_new = tk.Button(
            palette_actions, text="+ PALETA",
            command=self._create_palette,
            bg=COLORS['dim'], fg=COLORS['focus'],
            font=("Cascadia Code", 11, "bold"),
            relief='flat', cursor='hand2', padx=10, pady=6,
            activebackground=COLORS['focus'], activeforeground='#000'
        )
        btn_new.pack(side='left', padx=(0, 10))
        btn_new.bind('<Enter>', lambda e: btn_new.config(bg=COLORS['focus'], fg='#000'))
        btn_new.bind('<Leave>', lambda e: btn_new.config(bg=COLORS['dim'], fg=COLORS['focus']))

        btn_restore = tk.Button(
            palette_actions, text="↺ PADRÃO",
            command=self._restore_default_colors,
            bg=COLORS['dim'], fg=COLORS['rest'],
            font=("Cascadia Code", 11, "bold"),
            relief='flat', cursor='hand2', padx=10, pady=6,
            activebackground=COLORS['rest'], activeforeground='#000'
        )
        btn_restore.pack(side='left')
        btn_restore.bind('<Enter>', lambda e: btn_restore.config(bg=COLORS['rest'], fg='#000'))
        btn_restore.bind('<Leave>', lambda e: btn_restore.config(bg=COLORS['dim'], fg=COLORS['rest']))

        palettes = self._load_palettes()
        if palettes:
            for idx, palette in enumerate(palettes):
                self._draw_palette_item(parent, idx, palette.get('name', f'Paleta {idx+1}'), palette)
        else:
            tk.Label(parent, text="Nenhuma paleta salva",
                     font=("Cascadia Code", 12),
                     bg=bg, fg=COLORS['text_dim']).pack(anchor='center', pady=6, padx=12)

    # ── Bloco B — Color Picker ───────────────────────────────────

    def _build_block_b(self, parent):
        """Interface de cores no menu principal (10 swatches clicáveis)."""
        from tkinter import colorchooser
        bg = COLORS['bg']

        COLOR_SLOTS = [
            ("🎨 Fundo",              'bg'),
            ("🎨 Texto Principal",    'fg'),
            ("📦 Superfície",         'dim'),
            ("🖼 Borda",              'topbar_border'),
            ("⭐ Foco (Destaque)",    'focus'),
            ("😴 Descanso",           'rest'),
            ("📝 Texto Secundário",   'text_dim'),
            ("⚠ Acento (Atenção)",   'accent'),
            ("✓ Sucesso",            'success'),
            ("▶ Em Andamento",       'current_highlight'),
        ]

        tk.Label(parent, text="PERSONALIZAR CORES",
                 font=("Cascadia Code", 9, "bold"),
                 bg=bg, fg=COLORS['focus']).pack(anchor='w', pady=(0, 8))

        grid_f = tk.Frame(parent, bg=bg)
        grid_f.pack(fill='both', expand=True)

        self._color_swatches = {}

        for idx, (label, key) in enumerate(COLOR_SLOTS):
            row = idx // 2
            col = idx % 2

            cell = tk.Frame(grid_f, bg=COLORS['dim'], relief='solid', bd=1,
                            highlightthickness=0)
            cell.grid(row=row, column=col, sticky='ew', padx=2, pady=2)

            inner = tk.Frame(cell, bg=COLORS['dim'])
            inner.pack(fill='both', expand=True, padx=6, pady=6)

            swatch_frame = tk.Frame(inner, bg=COLORS['dim'])
            swatch_frame.pack(fill='x', pady=(0, 4))

            cv = tk.Canvas(swatch_frame, width=80, height=32, bg=COLORS['dim'],
                           highlightthickness=0, cursor='hand2', relief='flat', bd=0)
            cv.pack(side='left', padx=(0, 8), expand=True, fill='y')
            cv.create_rectangle(0, 0, 80, 32, fill=COLORS[key],
                                outline=COLORS['topbar_border'], width=2)
            self._color_swatches[key] = cv

            label_frame = tk.Frame(inner, bg=COLORS['dim'])
            label_frame.pack(fill='x')

            tk.Label(label_frame, text=label, font=("Cascadia Code", 8),
                     bg=COLORS['dim'], fg=COLORS['fg']).pack(anchor='w')

            hex_var = tk.StringVar(value=COLORS[key])
            tk.Label(label_frame, textvariable=hex_var,
                     font=("Cascadia Code", 7, "bold"),
                     bg=COLORS['dim'], fg=COLORS['text_dim']).pack(anchor='w')

            def _pick(k=key, canvas=cv, hex_label=hex_var):
                result = colorchooser.askcolor(color=COLORS[k],
                                               title=f"Cor: {k}", parent=self.root)
                if result and result[1]:
                    COLORS[k] = result[1]
                    canvas.delete('all')
                    canvas.create_rectangle(0, 0, 80, 32, fill=COLORS[k],
                                            outline=COLORS['topbar_border'], width=2)
                    hex_label.set(COLORS[k])
                    if k == 'bg':
                        self.root.configure(bg=COLORS['bg'])

            cv.bind('<Button-1>', lambda e, fn=_pick: fn())

        grid_f.columnconfigure(0, weight=1)
        grid_f.columnconfigure(1, weight=1)

        tk.Frame(parent, bg=COLORS['dim'], height=1).pack(fill='x', pady=(10, 6))
        btn_apply = tk.Button(
            parent, text="🔄  APLICAR CORES",
            command=self._apply_and_refresh,
            bg=COLORS['dim'], fg=COLORS['focus'],
            font=("Cascadia Code", 9, "bold"),
            relief='flat', cursor='hand2', padx=8, pady=5,
            activebackground=COLORS['focus'], activeforeground='#000'
        )
        btn_apply.pack(fill='x')
        btn_apply.bind('<Enter>', lambda e: btn_apply.config(bg=COLORS['focus'], fg='#000'))
        btn_apply.bind('<Leave>', lambda e: btn_apply.config(bg=COLORS['dim'], fg=COLORS['focus']))

        # Seção de paletas
        tk.Frame(parent, bg=COLORS['dim'], height=1).pack(fill='x', pady=(10, 6))
        tk.Label(parent, text="PALETAS SALVAS",
                 font=("Cascadia Code", 8),
                 bg=bg, fg=COLORS['text_dim']).pack(anchor='w', pady=(0, 6))

        palette_actions = tk.Frame(parent, bg=bg)
        palette_actions.pack(fill='x', pady=(0, 8))

        btn_new = tk.Button(
            palette_actions, text="+ PALETA",
            command=self._create_palette,
            bg=COLORS['dim'], fg=COLORS['focus'],
            font=("Cascadia Code", 8, "bold"),
            relief='flat', cursor='hand2', padx=6, pady=4,
            activebackground=COLORS['focus'], activeforeground='#000'
        )
        btn_new.pack(side='left', padx=(0, 6))
        btn_new.bind('<Enter>', lambda e: btn_new.config(bg=COLORS['focus'], fg='#000'))
        btn_new.bind('<Leave>', lambda e: btn_new.config(bg=COLORS['dim'], fg=COLORS['focus']))

        btn_restore = tk.Button(
            palette_actions, text="↺ PADRÃO",
            command=self._restore_default_colors,
            bg=COLORS['dim'], fg=COLORS['rest'],
            font=("Cascadia Code", 8, "bold"),
            relief='flat', cursor='hand2', padx=6, pady=4,
            activebackground=COLORS['rest'], activeforeground='#000'
        )
        btn_restore.pack(side='left')
        btn_restore.bind('<Enter>', lambda e: btn_restore.config(bg=COLORS['rest'], fg='#000'))
        btn_restore.bind('<Leave>', lambda e: btn_restore.config(bg=COLORS['dim'], fg=COLORS['rest']))

        palettes = self._load_palettes()
        if palettes:
            for idx, palette in enumerate(palettes):
                self._draw_palette_item(parent, idx, palette.get('name', f'Paleta {idx+1}'), palette)
        else:
            tk.Label(parent, text="Nenhuma paleta salva",
                     font=("Cascadia Code", 8),
                     bg=bg, fg=COLORS['text_dim']).pack(anchor='w', pady=2)

    # ── Aplicar / Carregar ───────────────────────────────────────

    def _apply_and_refresh(self):
        """Salva cores customizadas em config.json e reconstrói a tela."""
        try:
            cfg = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
            cfg['custom_colors'] = {k: COLORS[k] for k in COLORS}
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        self.root.configure(bg=COLORS['bg'])
        self.build_planning_screen()

    def _load_custom_colors(self):
        """Carrega cores salvas do config.json ao iniciar."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                for k, v in cfg.get('custom_colors', {}).items():
                    if k in COLORS:
                        COLORS[k] = v
        except Exception:
            pass

    def _get_default_colors(self):
        return {
            'bg':                '#0a0a0a',
            'fg':                '#ffffff',
            'dim':               '#222222',
            'topbar_border':     '#333333',
            'focus':             '#ffd700',
            'rest':              '#00bfff',
            'text_dim':          '#888888',
            'accent':            '#ff3333',
            'success':           '#32cd32',
            'current_highlight': '#ffa600',
        }

    # ── Sistema de Paletas ───────────────────────────────────────

    def _load_palettes(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f).get('palettes', [])
        except Exception:
            pass
        return []

    def _save_palettes(self, palettes):
        try:
            cfg = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
            cfg['palettes'] = palettes
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _create_palette(self):
        if len(self._load_palettes()) >= 3:
            CustomDialog.show_error(self.root, "Limite", "Máximo 3 paletas. Exclua uma antes.")
            return
        from tkinter import simpledialog
        nome = simpledialog.askstring("Nova Paleta", "Nome da paleta (máx 20 caracteres):",
                                      parent=self.root)
        if not nome or not nome.strip():
            return
        nome = nome.strip()[:20]
        palettes = self._load_palettes()
        palettes.append({"name": nome, "colors": {k: COLORS[k] for k in COLORS}})
        self._save_palettes(palettes)
        CustomDialog.show_info(self.root, "Sucesso", f"Paleta '{nome}' criada e salva!")
        self.build_planning_screen()

    def _apply_palette(self, palette_data):
        try:
            for k, v in palette_data.get('colors', {}).items():
                if k in COLORS:
                    COLORS[k] = v
            self.root.configure(bg=COLORS['bg'])
            self._apply_and_refresh()
            CustomDialog.show_info(self.root, "Paleta Aplicada",
                                   f"Paleta '{palette_data['name']}' aplicada com sucesso!")
        except Exception as e:
            CustomDialog.show_error(self.root, "Erro", f"Erro ao aplicar paleta: {e}")

    def _delete_palette(self, idx):
        palettes = self._load_palettes()
        if idx < len(palettes):
            name = palettes[idx]['name']
            palettes.pop(idx)
            self._save_palettes(palettes)
            CustomDialog.show_info(self.root, "Deletado", f"Paleta '{name}' excluída!")
            self.build_planning_screen()

    def _restore_default_colors(self):
        if not CustomDialog.ask_yes_no(self.root, "Restaurar Padrão",
                                       "Restaurar cores originais do app?"):
            return
        for k, v in self._get_default_colors().items():
            COLORS[k] = v
        self.root.configure(bg=COLORS['bg'])
        self._apply_and_refresh()
        CustomDialog.show_info(self.root, "Padrão Restaurado", "Cores padrão foram restauradas!")

    def _draw_palette_item(self, parent, idx, name, palette_data):
        """Desenha um item de paleta com preview das cores."""
        color_configs = {
            'bg':                {'width': 14, 'height': 26, 'border': 2},
            'fg':                {'width': 14, 'height': 26, 'border': 2},
            'dim':               {'width': 12, 'height': 24, 'border': 1},
            'topbar_border':     {'width': 12, 'height': 24, 'border': 1},
            'focus':             {'width': 16, 'height': 28, 'border': 3},
            'rest':              {'width': 12, 'height': 24, 'border': 1},
            'text_dim':          {'width': 10, 'height': 20, 'border': 1},
            'accent':            {'width': 14, 'height': 26, 'border': 2},
            'success':           {'width': 14, 'height': 26, 'border': 2},
            'current_highlight': {'width': 12, 'height': 24, 'border': 1},
        }
        color_keys = list(color_configs.keys())

        item_row = tk.Frame(parent, bg=COLORS['dim'], highlightthickness=1,
                            highlightbackground=COLORS['topbar_border'])
        item_row.pack(fill='x', pady=2)

        preview_frame = tk.Canvas(item_row, height=30, bg=COLORS['dim'],
                                  highlightthickness=0, cursor='hand2', relief='flat', bd=0)
        preview_frame.pack(side='left', padx=4, pady=2, fill='y')

        colors_list = palette_data.get('colors', {})
        x_offset = 0
        for color_key in color_keys:
            cfg = color_configs[color_key]
            w, h, border = cfg['width'], cfg['height'], cfg['border']
            color_hex = colors_list.get(color_key, '#333333')
            y_start = (30 - h) // 2
            preview_frame.create_rectangle(
                x_offset, y_start, x_offset + w, y_start + h,
                fill=color_hex, outline=COLORS['topbar_border'], width=border
            )
            x_offset += w + 2
        preview_frame.config(width=x_offset)

        tk.Label(item_row, text=f"  {idx+1}. {name}",
                 font=("Cascadia Code", 8),
                 bg=COLORS['dim'], fg=COLORS['fg']).pack(side='left', padx=6, pady=4)

        tk.Frame(item_row, bg=COLORS['dim']).pack(side='left', fill='x', expand=True)

        tk.Button(
            item_row, text="▶ Usar",
            command=lambda: self._apply_palette(palette_data),
            bg=COLORS['dim'], fg=COLORS['success'],
            font=("Cascadia Code", 7),
            relief='flat', cursor='hand2', padx=4, pady=2,
            activebackground=COLORS['success'], activeforeground='#000'
        ).pack(side='left', padx=(0, 2))

        tk.Button(
            item_row, text="✕",
            command=lambda idx_=idx: self._delete_palette(idx_),
            bg=COLORS['dim'], fg=COLORS['text_dim'],
            font=("Cascadia Code", 7, "bold"),
            relief='flat', cursor='hand2', padx=3, pady=2,
            activebackground=COLORS['accent'], activeforeground='#fff'
        ).pack(side='left', padx=(2, 6))

    # ── Página de Ajuda ──────────────────────────────────────────

    def _show_help_page(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        bg = COLORS['bg']

        topbar = tk.Frame(self.root, bg=COLORS['dim'], height=30)
        topbar.pack(fill='x')
        topbar.pack_propagate(False)

        tk.Button(
            topbar, text="◀ VOLTAR", command=self.build_planning_screen,
            font=("Cascadia Code", 9, "bold"),
            bg=COLORS['dim'], fg=COLORS['focus'],
            relief='flat', cursor='hand2', bd=0,
            padx=12, pady=6,
            activebackground=COLORS['focus'], activeforeground='#000'
        ).pack(side='left', padx=8, pady=2)

        tk.Label(topbar, text="INFORMAÇÕES",
                 font=("Cascadia Code", 9),
                 bg=COLORS['dim'], fg=COLORS['text_dim']).pack(side='left', padx=8)

        main_frame = tk.Frame(self.root, bg=bg)
        main_frame.pack(fill='both', expand=True)

        center_frame = tk.Frame(main_frame, bg=bg)
        center_frame.place(relx=0.5, rely=0.5, anchor='center',
                           relwidth=0.85, relheight=0.9)

        help_texts = [
            ("Amplo - Pomodoro Timer", "Versão 4.0"),
            ("🎯 Como Usar",
             "1. Configure o tempo de foco (padrão 25m)\n"
             "2. Clique em 'INICIAR' para começar\n"
             "3. Seu navegador abre ao final da sessão"),
            ("🎨 Personalizar Cores",
             "Clique no ícone 🎨 da sidebar para\n"
             "editar cores e gerenciar paletas"),
            ("💾 Salvar Paletas",
             "Crie paletas de cores e reutilize\n"
             "as suas combinações favoritas"),
            ("📊 Estatísticas",
             "Acompanhe sua produtividade\n"
             "no bloco central"),
        ]

        for title, content in help_texts:
            frame = tk.Frame(center_frame, bg=COLORS['dim'], highlightthickness=1,
                             highlightbackground=COLORS['topbar_border'])
            frame.pack(fill='x', pady=12)

            tk.Label(frame, text=title, font=("Cascadia Code", 14, "bold"),
                     bg=COLORS['dim'], fg=COLORS['focus']).pack(
                         anchor='center', padx=16, pady=(8, 4))

            tk.Label(frame, text=content, font=("Cascadia Code", 13),
                     bg=COLORS['dim'], fg=COLORS['text_dim'],
                     justify='center', wraplength=450).pack(
                         anchor='center', padx=16, pady=(4, 10))
