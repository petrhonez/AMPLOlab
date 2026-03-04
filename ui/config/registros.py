# ui/config/registros.py
import tkinter as tk
import os
import json
import datetime
from ui.config._base import make_config_window
from config import SESSION_DIR
from ui.dialogs import CustomDialog

def open_ui(root, colors, fonts, app=None):
    _, content = make_config_window(root, colors, "Registros de Sessões", app=app, scrollable=False)

    # Fonte base
    font_main = fonts.get("main", ("Cascadia Code", 20, "bold"))
    font_small = fonts.get("small", ("Cascadia Code", 11))
    font_topbar = ("Cascadia Code", 9)

    page = tk.Frame(content, bg=colors['bg'])
    page.pack(fill='both', expand=True, padx=40, pady=20)

    # ── Cabeçalho ──────────────────────────────────────────────
    header = tk.Frame(page, bg=colors['bg'])
    header.pack(fill='x', pady=(5, 10))
    tk.Label(header, text="🕒  Histórico de Atividades", 
             font=font_main, bg=colors['bg'], fg=colors['fg']).pack(side='left')

    def _delete_all():
        if not os.path.exists(SESSION_DIR) or not os.listdir(SESSION_DIR): return
        if CustomDialog.ask_yes_no(root, "Excluir Tudo", "Atenção: Isso vai excluir TODOS os seus registros permanentemente. Deseja continuar?"):
            for f in os.listdir(SESSION_DIR):
                path = os.path.join(SESSION_DIR, f)
                try: os.remove(path)
                except: pass
            if app:
                app._open_config_page("registros")

    tk.Button(header, text="🗑 Excluir Todos",
              command=_delete_all,
              bg=colors['bg'], fg=colors['accent'],
              font=("Cascadia Code", 10, "bold"),
              relief='flat', cursor='hand2',
              padx=10, pady=4,
              activebackground=colors['dim'],
              activeforeground=colors['accent']).pack(side='right')

    # ── Layout de 2 Colunas ────────────────────────────────────
    main_area = tk.Frame(page, bg=colors['bg'])
    main_area.pack(fill='both', expand=True)

    # Coluna Esquerda: Lista de Registros (Peso 2)
    left_col = tk.Frame(main_area, bg=colors['bg'])
    left_col.pack(side='left', fill='both', expand=True)

    # Espaçador Central
    tk.Frame(main_area, bg=colors['bg'], width=20).pack(side='left')

    # Coluna Direita: Dashboard de Gráficos (Peso 3)
    right_col = tk.Frame(main_area, bg=colors['bg'])
    right_col.pack(side='right', fill='both', expand=True)
    # Dar mais peso à coluna direita no nivel do layout: não é grid, mas pack expand divide igualmente. 
    # Para proporções melhores, usaremos pack(expand=True) em ambos, mas o Frame pode ter width se forçado.
    # No pack left_col/right_col, expand=True preenche. Para dar peso, grid é melhor, mas vamos usar panedwindow ou grid? 
    # Melhor reconstruir com Grid local para o main_area
    main_area.pack_forget()
    main_area = tk.Frame(page, bg=colors['bg'])
    main_area.pack(fill='both', expand=True)
    main_area.columnconfigure(0, weight=5) # Coluna esquerda, weight é a proporção de espaço que ela ocupa
    main_area.columnconfigure(1, weight=1, minsize=20) # Espaçador central
    main_area.columnconfigure(2, weight=8) # Coluna direita
    main_area.rowconfigure(0, weight=1)

    left_col = tk.Frame(main_area, bg=colors['bg'])
    left_col.grid(row=0, column=0, sticky='nsew')
    
    right_col = tk.Frame(main_area, bg=colors['bg'])
    right_col.grid(row=0, column=2, sticky='nsew')


    # ── Coluna Esquerda: Lista de Registros ────────────────────
    container = tk.Frame(left_col, bg=colors['dim'], highlightthickness=1, highlightbackground=colors['topbar_border'])
    container.pack(fill='both', expand=True, padx=(30, 5)) # Margem à direita para não grudar no centro

    canvas = tk.Canvas(container, bg=colors['bg'], highlightthickness=0)
    scrollable_frame = tk.Frame(canvas, bg=colors['bg'])

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=canvas.winfo_width())
    def _on_canvas_configure(event):
        canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
    canvas.bind("<Configure>", _on_canvas_configure)

    canvas.pack(side="left", fill="both", expand=True)

    # Mapeamentos de meses e dias
    meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    dias_semana_curto = {0:'Seg', 1:'Ter', 2:'Qua', 3:'Qui', 4:'Sex', 5:'Sáb', 6:'Dom'}

    def fmt_time(secs):
        m, s = divmod(int(abs(secs)), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}h {m:02d}m" if h else f"{m:02d}m {s:02d}s"

    # Carrega todos os dias
    arquivos_json = []
    if os.path.exists(SESSION_DIR):
        arquivos_json = sorted([f for f in os.listdir(SESSION_DIR) if f.endswith(".json")], reverse=True)

    if not arquivos_json:
        tk.Label(scrollable_frame, text="Nenhum registro encontrado.", 
                 font=font_small, bg=colors['dim'], fg=colors['text_dim']).pack(pady=40)

    # ── Processamento de Dados (Lista e Gráficos) ──────────────
    today = datetime.datetime.now().date()
    # últimos 7 dias: do dia atual para 6 dias atrás
    last_7_dates = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
    
    chart_data = { d.strftime("%Y-%m-%d"): {'focus_time': 0, 'efficiency': 0, 'valid': False} for d in last_7_dates }

    for arquivo in arquivos_json:
        caminho = os.path.join(SESSION_DIR, arquivo)
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                sessoes = json.load(f)
                if not isinstance(sessoes, list):
                    sessoes = [sessoes]
        except Exception:
            continue
        
        if not sessoes:
            continue
        
        data_str = sessoes[0].get("date", arquivo.replace(".json", ""))
        try:
            dt = datetime.datetime.strptime(data_str, "%Y-%m-%d")
            data_formatada = f"{dt.day:02d}/{dt.month:02d}"
        except:
            data_formatada = data_str

        total_time = sum(s.get("session_duration", 0) for s in sessoes)
        total_focus = sum((s.get("session_duration", 0) * s.get("focus_pct", 0) / 100) for s in sessoes)
        
        # Popula dados para gráficos se estiver nos ultimos 7 dias
        if data_str in chart_data:
            chart_data[data_str]['focus_time'] = total_focus
            chart_data[data_str]['valid'] = True
            # Eficiência: media ponderada pelo tempo, ou media simples das eficiencias
            sum_eff = sum(s.get("focus_pct", 0) * s.get("session_duration", 0) for s in sessoes)
            if total_time > 0:
                chart_data[data_str]['efficiency'] = sum_eff / total_time

        # Renderizar na UI da Lista
        total_completed = 0
        total_abandoned = 0
        for s in sessoes:
            for t in s.get("tasks", []):
                if t.get("status") == "Concluída": total_completed += 1
                else: total_abandoned += 1

        day_card = tk.Frame(scrollable_frame, bg=colors['dim'], highlightthickness=1, highlightbackground=colors['topbar_border'])
        day_card.pack(fill='x', pady=8, padx=10) # Ajustado padx e pady do card

        day_header = tk.Frame(day_card, bg=colors['dim'], cursor="hand2")
        day_header.pack(fill='x', padx=15, pady=12)

        lbl_title = tk.Label(day_header, text=f"📅 {data_formatada}", 
                 font=("Cascadia Code", 14, "bold"), bg=colors['dim'], fg=colors['fg'], cursor="hand2")
        lbl_title.pack(side='left')
        
        resumo_cnt = tk.Frame(day_header, bg=colors['dim'], cursor="hand2")
        resumo_cnt.pack(side='right')

        resumo_str = f"Foco: {fmt_time(total_focus)} | Tarefas: {total_completed}/{total_abandoned}"
        lbl_resumo = tk.Label(resumo_cnt, text=resumo_str, 
                 font=("Cascadia Code", 10), bg=colors['dim'], fg=colors['text_dim'], cursor="hand2")
        lbl_resumo.pack(side='left', padx=(0, 12))

        def _delete_day(f_path=caminho, f_name=arquivo):
            if CustomDialog.ask_yes_no(root, "Excluir Registro", "Deseja realmente excluir todos os dados deste dia?"):
                try:
                    os.remove(f_path)
                    md_path = f_path.replace(".json", ".md")
                    if os.path.exists(md_path):
                        os.remove(md_path)
                    if app:
                        app._open_config_page("registros")
                except Exception as ex:
                    CustomDialog.show_error(root, "Erro ao excluir", str(ex))

        btn_del = tk.Button(resumo_cnt, text="🗑", font=("Cascadia Code", 11), bg=colors['dim'], fg=colors['accent'],
                            relief='flat', cursor='hand2', bd=0, activebackground=colors['dim'], activeforeground='#fff',
                            command=lambda p=caminho, a=arquivo: _delete_day(p, a))
        btn_del.pack(side='right')

        sessions_container = tk.Frame(day_card, bg=colors['bg'])

        def toggle_day(e=None, c=sessions_container, b=btn_del):
            if b.winfo_exists() and e and e.widget == b:
                return 
            if c.winfo_ismapped(): c.pack_forget()
            else: c.pack(fill='x', padx=2, pady=2)

        for w in (day_header, lbl_title, resumo_cnt, lbl_resumo):
            w.bind("<Button-1>", toggle_day)

        for i, s in enumerate(sessoes, 1):
            sess_frame = tk.Frame(sessions_container, bg=colors['bg'], highlightthickness=1, highlightbackground=colors['dim'])
            sess_frame.pack(fill='x', pady=4, padx=10)

            sess_header = tk.Frame(sess_frame, bg=colors['bg'], cursor="hand2")
            sess_header.pack(fill='x', padx=8, pady=6)

            start = s.get("start", "--:--")
            end = s.get("end", "--:--")
            f_pct = s.get("focus_pct", 0)

            tk.Label(sess_header, text=f"S{i} ({start}-{end})", 
                     font=("Cascadia Code", 11, "bold"), bg=colors['bg'], fg=colors['focus'], cursor="hand2").pack(side='left')

            tk.Label(sess_header, text=f"Foco: {f_pct}%", 
                     font=("Cascadia Code", 10), bg=colors['bg'], fg=colors['text_dim'], cursor="hand2").pack(side='right')

            tasks_container = tk.Frame(sess_frame, bg=colors['dim'])

            def toggle_sess(e=None, c=tasks_container):
                if c.winfo_ismapped(): c.pack_forget()
                else: c.pack(fill='x', padx=2, pady=2)

            for w in (sess_header,) + tuple(sess_header.winfo_children()):
                w.bind("<Button-1>", toggle_sess)

            for t in s.get("tasks", []):
                t_row = tk.Frame(tasks_container, bg=colors['dim'])
                t_row.pack(fill='x', padx=10, pady=2)

                name = t.get("name", "Desconhecida")
                if len(name) > 15: name = name[:12] + "..."
                st = t.get("status", "")
                color_st = colors['success'] if st == "Concluída" else colors['accent']

                tk.Label(t_row, text=name, font=("Cascadia Code", 10), bg=colors['dim'], fg=colors['fg'], anchor='w').pack(side='left')
                tk.Label(t_row, text=st, font=("Cascadia Code", 10, "bold"), bg=colors['dim'], fg=color_st).pack(side='right')

    # Mousewheel
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    def _on_mousewheel_up(event):
        canvas.yview_scroll(-1, "units")
    def _on_mousewheel_down(event):
        canvas.yview_scroll(1, "units")

    def bind_scroll(widget):
        widget.bind("<MouseWheel>", _on_mousewheel)
        widget.bind("<Button-4>", _on_mousewheel_up)
        widget.bind("<Button-5>", _on_mousewheel_down)
        for child in widget.winfo_children():
            bind_scroll(child)

    scrollable_frame.bind("<Configure>", lambda e: bind_scroll(scrollable_frame), add="+")
    canvas.bind("<MouseWheel>", _on_mousewheel)


    # ── Coluna Direita: Dashboard de Gráficos ──────────────────
    
    # 1. Gráfico de Eficiência (Linha)
    frame_eff = tk.Frame(right_col, bg=colors['bg'])
    frame_eff.pack(fill='both', expand=True, pady=(5, 30))
    tk.Label(frame_eff, text="📈 Eficiência Média Semanal (%)", font=("Cascadia Code", 12, "bold"), bg=colors['bg'], fg=colors['fg']).pack(anchor='w', pady=(0, 5)) 
    
    cv_eff = tk.Canvas(frame_eff, bg=colors['dim'], highlightthickness=1, highlightbackground=colors['topbar_border'])
    cv_eff.pack(fill='both', expand=True)

    # 2. Gráfico de Tempo de Foco (Barras)
    frame_foco = tk.Frame(right_col, bg=colors['bg'])
    frame_foco.pack(fill='both', expand=True, pady=(10, 0))
    tk.Label(frame_foco, text="⏳ Tempo de Foco Semanal (Máx 4h)", font=("Cascadia Code", 12, "bold"), bg=colors['bg'], fg=colors['fg']).pack(anchor='w', pady=(0, 5))
    
    cv_foco = tk.Canvas(frame_foco, bg=colors['dim'], highlightthickness=1, highlightbackground=colors['topbar_border'])
    cv_foco.pack(fill='both', expand=True)

    def draw_charts(e=None):
        cv_eff.delete("all")
        cv_foco.delete("all")
        
        w_eff = cv_eff.winfo_width()
        h_eff = cv_eff.winfo_height()
        w_fc = cv_foco.winfo_width()
        h_fc = cv_foco.winfo_height()

        if w_eff < 50 or h_eff < 50: return # não desenhar se for muito pequeno

        pad_x = 50
        pad_y = 30
        
        days_count = 7
        dx_eff = (w_eff - 2 * pad_x) / max(1, days_count - 1)
        dx_fc = (w_fc - 2 * pad_x) / days_count

        # Plot Eff
        pts_eff = []
        for i, dt in enumerate(last_7_dates):
            d_str = dt.strftime("%Y-%m-%d")
            eff = chart_data[d_str]['efficiency']
            
            x = pad_x + i * dx_eff
            y = h_eff - pad_y - (eff / 100) * (h_eff - 2 * pad_y)
            pts_eff.append((x, y))

            # Eixo X
            label = dias_semana_curto[dt.weekday()]
            cv_eff.create_text(x, h_eff - pad_y + 15, text=label, fill=colors['text_dim'], font=("Cascadia Code", 8))
            cv_foco.create_text(pad_x + i * dx_fc + dx_fc/2, h_fc - pad_y + 15, text=label, fill=colors['text_dim'], font=("Cascadia Code", 8))
            
            # Eixo Y Eff: Guias 0, 50, 100
            for v in (0, 50, 100):
                gy = h_eff - pad_y - (v / 100) * (h_eff - 2 * pad_y)
                cv_eff.create_line(pad_x, gy, w_eff - pad_x, gy, fill=colors['topbar_border'], dash=(2, 2))
                if i == 0:
                    cv_eff.create_text(pad_x - 15, gy, text=f"{v}%", fill=colors['text_dim'], font=("Cascadia Code", 8))

            # Desenha pontos Eff
            cv_eff.create_oval(x-4, y-4, x+4, y+4, fill=colors['focus'], outline=colors['bg'], width=2)
            if chart_data[d_str]['valid']:
                cv_eff.create_text(x, y-15, text=f"{int(eff)}%", fill=colors['fg'], font=("Cascadia Code", 8, "bold"))


            # Bars Foco (Max 4 horas = 14400 secs)
            MAX_SECS = 14400
            foco_s = chart_data[d_str]['focus_time']
            viz_s = min(foco_s, MAX_SECS)
            
            bx1 = pad_x + i * dx_fc + 10
            bx2 = bx1 + dx_fc - 20
            
            by_bottom = h_fc - pad_y
            by_top = by_bottom - (viz_s / MAX_SECS) * (h_fc - 2 * pad_y)
            
            # Guia 4h
            if i == 0:
                gy_top = h_fc - pad_y - (1) * (h_fc - 2 * pad_y)
                cv_foco.create_line(pad_x, gy_top, w_fc - pad_x, gy_top, fill=colors['topbar_border'], dash=(2, 2))
                cv_foco.create_text(pad_x - 15, gy_top, text="4h", fill=colors['text_dim'], font=("Cascadia Code", 8))
                
                gy_mid = h_fc - pad_y - (0.5) * (h_fc - 2 * pad_y)
                cv_foco.create_line(pad_x, gy_mid, w_fc - pad_x, gy_mid, fill=colors['topbar_border'], dash=(2, 2))
                cv_foco.create_text(pad_x - 15, gy_mid, text="2h", fill=colors['text_dim'], font=("Cascadia Code", 8))

            if viz_s > 0:
                cv_foco.create_rectangle(bx1, by_top, bx2, by_bottom, fill=colors['rest'], outline='')
                
                foco_m = int(foco_s // 60)
                if foco_s >= 14400:
                    top_text = "+4h"
                else:
                    h_decimal = foco_s / 3600
                    top_text = f"{h_decimal:.1f}h".replace('.', ',')
                
                in_text = f"{foco_m}m"
                
                # Texto em cima
                cv_foco.create_text((bx1+bx2)/2, by_top - 10, text=top_text, fill=colors['fg'], font=("Cascadia Code", 8, "bold"))
                
                # Texto dentro (apenas se >= 30 minutos)
                if foco_s >= 1800:
                    in_y = by_top + 10 if (by_bottom - by_top) >= 20 else (by_top + by_bottom) / 2
                    cv_foco.create_text((bx1+bx2)/2, in_y, text=in_text, fill=colors['bg'], font=("Cascadia Code", 8, "bold"))

        # Linha principal Eff
        if len(pts_eff) > 1:
            flat_pts = [p for pt in pts_eff for p in pt]
            # Desenha a linha atrás dos ovais (usando tags ou ordem natural)
            line_id = cv_eff.create_line(flat_pts, fill=colors['focus'], width=3, smooth=False)
            cv_eff.tag_lower(line_id)

    cv_eff.bind("<Configure>", draw_charts)
    cv_foco.bind("<Configure>", draw_charts)
