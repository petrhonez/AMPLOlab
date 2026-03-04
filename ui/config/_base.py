import tkinter as tk
import json
import os

REGISTRO_FILE = "c_registro.json"

def _load_registry() -> dict:
    """Carrega o arquivo de registro central c_registro.json."""
    try:
        if os.path.exists(REGISTRO_FILE):
            with open(REGISTRO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_registry(data: dict) -> None:
    """Salva o arquivo de registro central c_registro.json."""
    try:
        with open(REGISTRO_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def make_config_window(root, colors, title: str, width=None, height=None, app=None, scrollable=True):
    """Renderiza a página de config em tela cheia no root (sem Toplevel)."""

    for widget in root.winfo_children():
        widget.destroy()

    # ── Topbar ────────────────────────────────────────────────────
    topbar = tk.Frame(root, bg=colors['dim'], height=40)
    topbar.pack(fill='x')
    topbar.pack_propagate(False)

    def _go_back():
        if app is not None:
            app.build_planning_screen()

    tk.Button(
        topbar, text="◀  VOLTAR",
        command=_go_back,
        font=("Cascadia Code", 9, "bold"),
        bg=colors['dim'], fg=colors['focus'],
        relief='flat', cursor='hand2', bd=0,
        padx=14, pady=8,
        activebackground=colors['focus'],
        activeforeground='#000'
    ).pack(side='left', padx=6, pady=4)

    tk.Label(
        topbar, text=title.upper(),
        font=("Cascadia Code", 9),
        bg=colors['dim'], fg=colors['text_dim']
    ).pack(side='left', padx=6)

    # ── Área de conteúdo ───────────────────────────────
    if scrollable:
        canvas = tk.Canvas(root, bg=colors['bg'], highlightthickness=0)
        
        # A scrollbar foi removida visualmente (sem pack), mas o canvas ainda pode rolar via mousewheel
        canvas.pack(side='left', fill='both', expand=True)

        content = tk.Frame(canvas, bg=colors['bg'])
        canvas_window = canvas.create_window((0, 0), window=content, anchor='nw')

        def _on_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))

        def _on_canvas_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)

        content.bind('<Configure>', _on_configure)
        canvas.bind('<Configure>', _on_canvas_resize)

        def _on_mousewheel(event):
            if hasattr(event, 'delta'):
                canvas.yview_scroll(-1 if event.delta > 0 else 1, 'units')
            elif hasattr(event, 'num'):
                canvas.yview_scroll(-1 if event.num == 4 else 1, 'units')

        canvas.bind('<MouseWheel>', _on_mousewheel)
        canvas.bind('<Button-4>',   _on_mousewheel)
        canvas.bind('<Button-5>',   _on_mousewheel)
    else:
        content = tk.Frame(root, bg=colors['bg'])
        content.pack(fill='both', expand=True)

    return root, content