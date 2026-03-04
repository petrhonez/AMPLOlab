# ui/config/email.py
import tkinter as tk
from tkinter import ttk
import json
import threading
import os

from ui.config._base import make_config_window
from ui.dialogs import CustomDialog

CONFIG_FILE = "config.json"

def _load_email_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("email", {})
    except Exception:
        pass
    return {
        "enabled": False,
        "sender": "seu_email@gmail.com",
        "password": "",
        "recipient": "destino@email.com",
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587
    }

def _save_email_config(email_cfg):
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        data["email"] = email_cfg
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar config.json: {e}")
        return False

def open_ui(root, colors, fonts, app=None):
    email_cfg = _load_email_config()

    _, content = make_config_window(root, colors, "Configuração de E-mail", app=app)

    page = tk.Frame(content, bg=colors['bg'])
    page.pack(anchor='center', pady=30, padx=60, fill='x')

    # Variables
    enabled_var = tk.BooleanVar(value=bool(email_cfg.get("enabled", False)))
    sender_var = tk.StringVar(value=str(email_cfg.get("sender", "")))
    pass_var = tk.StringVar(value=str(email_cfg.get("password", "")))
    dest_var = tk.StringVar(value=str(email_cfg.get("recipient", "")))
    host_var = tk.StringVar(value=str(email_cfg.get("smtp_host", "smtp.gmail.com")))
    port_var = tk.StringVar(value=str(email_cfg.get("smtp_port", "587")))

    # Layout: Form Left, Preview Right
    columns = tk.Frame(page, bg=colors['bg'])
    columns.pack(fill='x')
    columns.columnconfigure(0, weight=1)
    columns.columnconfigure(1, weight=1)

    left = tk.Frame(columns, bg=colors['bg'])
    left.grid(row=0, column=0, sticky='nsew', padx=(0, 20))

    right = tk.Frame(columns, bg=colors['bg'])
    right.grid(row=0, column=1, sticky='nsew')

    # --- LEFT COLUMN: Form ---
    tk.Label(left, text="SETTINGS", font=("Cascadia Code", 9, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(0, 10))

    def _make_field(parent, label, var, show=None):
        f = tk.Frame(parent, bg=colors['bg'])
        f.pack(fill='x', pady=5)
        tk.Label(f, text=label.upper(), font=("Cascadia Code", 8),
                 bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w')
        e = tk.Entry(f, textvariable=var, font=("Cascadia Code", 10),
                     bg=colors['dim'], fg=colors['fg'],
                     insertbackground=colors['focus'], relief='flat', show=show)
        e.pack(fill='x', pady=(2, 0), ipady=4)
        return e

    cb_enabled = tk.Checkbutton(
        left, text="Ativar Envio de Relatórios",
        variable=enabled_var,
        font=("Cascadia Code", 10, "bold"),
        bg=colors['bg'], fg=colors['fg'],
        selectcolor=colors['dim'], activebackground=colors['bg'],
        activeforeground=colors['focus'], cursor='hand2'
    )
    cb_enabled.pack(anchor='w', pady=(0, 15))

    _make_field(left, "E-mail de Origem (Gmail preferred)", sender_var)
    _make_field(left, "Senha de Aplicativo", pass_var, show="*")
    _make_field(left, "E-mail de Destino", dest_var)
    
    # Advanced / SMTP
    tk.Label(left, text="SMTP ADVANCED", font=("Cascadia Code", 7, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(15, 5))
    
    smtp_row = tk.Frame(left, bg=colors['bg'])
    smtp_row.pack(fill='x')
    
    tk.Label(smtp_row, text="HOST", font=("Cascadia Code", 7), bg=colors['bg'], fg=colors['text_dim']).pack(side='left')
    tk.Entry(smtp_row, textvariable=host_var, width=20, font=("Cascadia Code", 8),
             bg=colors['dim'], fg=colors['fg'], relief='flat').pack(side='left', padx=5)
    
    tk.Label(smtp_row, text="PORT", font=("Cascadia Code", 7), bg=colors['bg'], fg=colors['text_dim']).pack(side='left', padx=(10,0))
    tk.Entry(smtp_row, textvariable=port_var, width=5, font=("Cascadia Code", 8),
             bg=colors['dim'], fg=colors['fg'], relief='flat').pack(side='left', padx=5)

    # --- RIGHT COLUMN: Preview ---
    tk.Label(right, text="EMAIL PREVIEW (DAILY REPORT STYLE)", font=("Cascadia Code", 9, "bold"),
             bg=colors['bg'], fg=colors['text_dim']).pack(anchor='w', pady=(0, 10))

    preview_container = tk.Frame(right, bg='#0a0a0a', bd=1, relief='solid', highlightbackground=colors['topbar_border'], highlightthickness=1)
    preview_container.pack(fill='both', expand=True)

    # Mini Email Header
    head = tk.Frame(preview_container, bg='#1a1a1a')
    head.pack(fill='x', padx=10, pady=10)
    tk.Label(head, text="Assunto: 📊 Amplo — Relatório 04/03/2026", font=("Inter", 9, "bold"), bg='#1a1a1a', fg='#ffd700').pack(anchor='w')

    # Mini Email Body (Simplified simulation of services/email_svc.py HTML)
    body = tk.Frame(preview_container, bg='#0a0a0a')
    body.pack(fill='both', expand=True, padx=20, pady=10)

    tk.Label(body, text="🎯 Relatório de Foco — 04/03/2026", font=("Inter", 11, "bold"), bg='#0a0a0a', fg='#32cd32').pack(anchor='w', pady=(0, 15))

    # Session Summary Box
    sbox = tk.Frame(body, bg='#1a1a1a', bd=1, relief='solid', padx=15, pady=15)
    sbox.pack(fill='x', pady=5)
    
    tk.Label(sbox, text="Sessão #1 (08:30 – 10:45)", font=("Inter", 9, "bold"), bg='#1a1a1a', fg='#ffd700').pack(anchor='w', pady=(0, 10))
    
    metrics = tk.Frame(sbox, bg='#1a1a1a')
    metrics.pack(fill='x')
    
    def _add_mini_metric(p, l, v, c):
        f = tk.Frame(p, bg='#1a1a1a')
        f.pack(side='left', expand=True)
        tk.Label(f, text=l, font=("Inter", 7), bg='#1a1a1a', fg='#888').pack()
        tk.Label(f, text=v, font=("Inter", 10, "bold"), bg='#1a1a1a', fg=c).pack()

    _add_mini_metric(metrics, "DURAÇÃO", "02:15:00", "#fff")
    _add_mini_metric(metrics, "GANHO", "+05:12", "#32cd32")
    _add_mini_metric(metrics, "EFICIÊNCIA", "88%", "#32cd32")

    # Progress Bars (Segmented pattern)
    tk.Label(sbox, text="PROGRESSO DA SESSÃO", font=("Inter", 7, "bold"), bg='#1a1a1a', fg='#888').pack(anchor='w', pady=(15, 2))
    pb_sessao = tk.Frame(sbox, bg='#333', height=12)
    pb_sessao.pack(fill='x', pady=2)
    tk.Frame(pb_sessao, bg='#ffd700', width=100).pack(side='left', fill='y') # Focus
    tk.Frame(pb_sessao, bg='#ffa600', width=20).pack(side='left', fill='y')  # Pause
    tk.Frame(pb_sessao, bg='#00bfff', width=30).pack(side='left', fill='y')  # Break

    tk.Label(sbox, text="CHECK DE TAREFAS", font=("Inter", 7, "bold"), bg='#1a1a1a', fg='#888').pack(anchor='w', pady=(10, 2))
    pb_tasks = tk.Frame(sbox, bg='#333', height=12)
    pb_tasks.pack(fill='x', pady=2)
    tk.Frame(pb_tasks, bg='#32cd32', width=120).pack(side='left', fill='y') # Completed
    tk.Frame(pb_tasks, bg='#ff3333', width=30).pack(side='left', fill='y')  # Abandoned

    tk.Label(body, text="Amplo — gerado automaticamente", font=("Inter", 7), bg='#0a0a0a', fg='#444').pack(anchor='w', pady=(20, 0))

    # --- ACTION BUTTONS ---
    tk.Frame(page, bg=colors['topbar_border'], height=1).pack(fill='x', pady=(30, 15))
    
    btn_row = tk.Frame(page, bg=colors['bg'])
    btn_row.pack(fill='x')

    def _save():
        try:
            new_cfg = {
                "enabled":   enabled_var.get(),
                "sender":    sender_var.get().strip(),
                "password":  pass_var.get().strip(),
                "recipient": dest_var.get().strip(),
                "smtp_host": host_var.get().strip(),
                "smtp_port": int(port_var.get().strip())
            }
            if _save_email_config(new_cfg):
                btn_save.config(text="✓ SALVO!", bg=colors['success'])
                root.after(2000, lambda: btn_save.config(text="💾 SALVAR", bg=colors['focus']))
            else:
                CustomDialog.show_error(root, "Erro", "Falha ao salvar configuração.")
        except ValueError:
            CustomDialog.show_error(root, "Erro", "Porta SMTP deve ser um número.")

    def _test():
        if not sender_var.get() or not pass_var.get() or not dest_var.get():
            CustomDialog.show_error(root, "Erro", "Preencha origem, senha e destino para testar.")
            return
            
        btn_test.config(text="⌛ ENVIANDO...", state='disabled')
        
        def run_test():
            # First save current view state to registry so service picks it up
            _save()
            if app and hasattr(app, 'email_manager'):
                success, msg = app.email_manager.send_test_email()
            else:
                success, msg = (False, "Gerenciador de e-mail não disponível.")
            
            def finalize():
                btn_test.config(text="📧 ENVIAR TESTE", state='normal')
                if success:
                    CustomDialog.show_info(root, "Sucesso", msg)
                else:
                    CustomDialog.show_error(root, "Falha", msg)
            
            root.after(0, finalize)

        threading.Thread(target=run_test, daemon=True).start()

    btn_test = tk.Button(btn_row, text="📧 ENVIAR TESTE",
                         command=_test,
                         bg=colors['dim'], fg=colors['focus'],
                         font=("Cascadia Code", 10, "bold"),
                         relief='flat', cursor='hand2',
                         padx=15, pady=8, activebackground=colors['focus'], activeforeground='#000')
    btn_test.pack(side='left')

    btn_save = tk.Button(btn_row, text="💾 SALVAR",
                         command=_save,
                         bg=colors['focus'], fg='#000',
                         font=("Cascadia Code", 10, "bold"),
                         relief='flat', cursor='hand2',
                         padx=25, pady=8, activebackground=colors['success'], activeforeground='#000')
    btn_save.pack(side='right')

    return content
