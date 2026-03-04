# ui/topbar_mixin.py
import tkinter as tk

from config import *


class TopbarMixin:
    """Mapa de progresso (topbar deslizante) com timeline horizontal."""

    # ── Toggle ───────────────────────────────────────────────────

    def toggle_topbar(self, event=None):
        if self.topbar_visible:
            self.hide_topbar()
        else:
            self.show_topbar()

    # ── Mostrar / Esconder ───────────────────────────────────────

    def show_topbar(self):
        if self.topbar_frame:
            self.topbar_frame.lift()
            self.topbar_visible = True
            return

        h  = 140
        sw = self.root.winfo_screenwidth()

        self.topbar_frame = tk.Frame(
            self.root, bg=COLORS['dim'],
            width=sw, height=h, bd=2, relief='solid',
            highlightbackground=COLORS['topbar_border'],
            highlightthickness=2
        )
        self.topbar_frame.place(x=0, y=-h)
        self.topbar_frame.pack_propagate(False)

        # Header
        header = tk.Frame(self.topbar_frame, bg=COLORS['topbar_border'], height=35)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text="MAPA DE PROGRESSO",
                 font=("Cascadia Code", 11, "bold"),
                 bg=COLORS['topbar_border'],
                 fg=COLORS['focus']).pack(side='left', padx=10, pady=8)

        tk.Button(header, text="✕", command=self.hide_topbar,
                  bg=COLORS['accent'], fg=COLORS['fg'],
                  font=("Arial", 12, "bold"), relief='flat',
                  padx=10, pady=0, cursor='hand2').pack(side='right', padx=10)

        # Container do timeline
        tc = tk.Frame(self.topbar_frame, bg=COLORS['dim'])
        tc.pack(fill='both', expand=True, padx=10, pady=10)

        self.build_horizontal_timeline(tc)
        self.animate_topbar_in(h)
        self.topbar_visible = True

    def hide_topbar(self):
        if not self.topbar_frame:
            return
        self.topbar_opened_by_pause = False
        self.animate_topbar_out(140)
        self.topbar_visible = False

    # ── Animações ────────────────────────────────────────────────

    def animate_topbar_in(self, h, step=0):
        if step < h:
            self.topbar_frame.place(y=-h + step)
            self.root.after(5, lambda: self.animate_topbar_in(h, step + 10))
        else:
            self.topbar_frame.place(y=0)

    def animate_topbar_out(self, h, step=0):
        if step < h:
            self.topbar_frame.place(y=-step)
            self.root.after(5, lambda: self.animate_topbar_out(h, step + 10))
        else:
            self.topbar_frame.place(y=-h)
            self.root.after(
                100,
                lambda: self.topbar_frame.destroy() if self.topbar_frame else None
            )
            self.topbar_frame = None

    # ── Timeline Horizontal ──────────────────────────────────────

    def build_horizontal_timeline(self, parent):
        self.timeline_blocks = []

        bf = tk.Frame(parent, bg=COLORS['dim'], height=60)
        bf.pack(pady=(0, 5))

        screen_w          = self.root.winfo_screenwidth()
        max_timeline_width = min(screen_w - 80, 1600)

        total_time   = (sum(t.duration_seconds for t in self.tasks)
                        + self.break_per_slot * (len(self.tasks) - 1))
        total_blocks = len(self.tasks) + max(0, len(self.tasks) - 1)

        padding_per_block = 5
        total_padding     = padding_per_block * total_blocks
        available_width   = max_timeline_width - total_padding
        pps               = available_width / total_time if total_time > 0 else 1
        min_block_width   = 40

        for i, task in enumerate(self.tasks):
            tw      = max(min_block_width, int(task.duration_seconds * pps))
            bc      = self.get_task_color(i)
            is_curr = (i == self.current_task_index and not self.is_break)

            tb = tk.Frame(
                bf, bg=bc, width=tw, height=60,
                bd=2 if is_curr else 1,
                relief='solid',
                highlightbackground=COLORS['current_highlight'] if is_curr else COLORS['topbar_border'],
                highlightthickness=3 if is_curr else 1
            )
            tb.pack(side='left', padx=padding_per_block // 2)
            tb.pack_propagate(False)

            if is_curr:
                tk.Label(tb, text="▶", font=("Arial", 12, "bold"),
                         bg=bc, fg=COLORS['current_highlight']).pack(pady=2)

            max_name_len = max(6, (tw - 20) // 6)
            name = (task.name
                    if len(task.name) <= max_name_len
                    else task.name[:max(3, max_name_len - 3)] + "..")

            tk.Label(tb, text=f"{name.upper()} [{task.weight}x]",
                     font=FONT_TOPBAR, bg=bc, fg=COLORS['fg'],
                     wraplength=max(30, tw - 10)).pack(expand=True)

            tk.Label(tb, text=self.format_time(task.duration_seconds),
                     font=("Cascadia Code", 7), bg=bc,
                     fg=COLORS['text_dim']).pack(pady=(0, 2))

            self.timeline_blocks.append((tb, i, 'task'))

            # Break entre tarefas (exceto após a última)
            if i < len(self.tasks) - 1:
                bw     = max(min_block_width, int(self.break_per_slot * pps))
                is_brk = (i == self.current_task_index and self.is_break)

                bb = tk.Frame(
                    bf,
                    bg=COLORS['rest'] if is_brk else COLORS['dim'],
                    width=bw, height=60,
                    bd=2 if is_brk else 1, relief='solid',
                    highlightbackground=COLORS['current_highlight'] if is_brk else COLORS['topbar_border'],
                    highlightthickness=3 if is_brk else 1
                )
                bb.pack(side='left', padx=padding_per_block // 2)
                bb.pack_propagate(False)

                if is_brk:
                    tk.Label(bb, text="▶", font=("Arial", 12, "bold"),
                             bg=bb['bg'], fg=COLORS['current_highlight']).pack(pady=2)

                tk.Label(bb, text="PAUSA", font=FONT_TOPBAR,
                         bg=bb['bg'], fg=COLORS['fg']).pack(expand=True)

                tk.Label(bb, text=self.format_time(int(self.break_per_slot)),
                         font=("Cascadia Code", 7),
                         bg=bb['bg'], fg=COLORS['text_dim']).pack(pady=(0, 2))

                self.timeline_blocks.append((bb, i, 'break'))

        self.build_legend(parent)

    def build_legend(self, parent):
        lf = tk.Frame(parent, bg=COLORS['dim'])
        lf.pack(side='bottom')

        for text, color in [
            ("✓ Concluída",  COLORS['success']),
            ("✕ Abandonada", COLORS['accent']),
            ("▶ Atual",      COLORS['current_highlight']),
            ("○ Pendente",   COLORS['dim']),
        ]:
            item = tk.Frame(lf, bg=COLORS['dim'])
            item.pack(side='left', padx=10)
            tk.Frame(item, bg=color, width=12, height=12, bd=1, relief='solid').pack(
                side='left', padx=(0, 5))
            tk.Label(item, text=text, font=("Cascadia Code", 7),
                     bg=COLORS['dim'], fg=COLORS['text_dim']).pack(side='left')

    # ── Cor e Atualização dos Blocos ─────────────────────────────

    def get_task_color(self, idx):
        task = self.tasks[idx]
        if idx == self.current_task_index and not self.is_break:
            return COLORS['current_highlight']
        if task.status == "Concluída":
            return COLORS['success']
        elif task.status != "Pendente":
            return COLORS['accent']
        return COLORS['dim']

    def update_timeline_block(self, task_index):
        for block, idx, btype in self.timeline_blocks:
            if btype == 'task' and idx == task_index:
                nc = self.get_task_color(task_index)
                block.config(bg=nc)
                for w in block.winfo_children():
                    w.config(bg=nc)
