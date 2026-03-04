# services/email_svc.py
import os
import json
import smtplib
import threading
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import CONFIG_FILE
from services.sessions import SessionManager

class EmailManager:
    """Envia relatório diário às 20:30 e bônus semanal às segundas.
    Credenciais lidas de config.json (criado automaticamente na 1ª vez)."""

    def __init__(self, session_manager: SessionManager):
        self.sm = session_manager
        self._ensure_config()

    def _ensure_config(self):
        """Cria config.json de exemplo se não existir."""
        if not os.path.exists(CONFIG_FILE):
            template = {
                "email": {
                    "enabled":   False,
                    "sender":    "seu_email@gmail.com",
                    "password":  "sua_app_password_aqui",
                    "recipient": "destino@email.com",
                    "smtp_host": "smtp.gmail.com",
                    "smtp_port": 587
                }
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)

    def _load_config(self) -> dict:
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get("email", {})
        except Exception:
            return {}

    # ── Envio ─────────────────────────────────────────────────────

    def send_daily_report(self):
        """Envia relatório do dia. Chamado pelo scheduler."""
        cfg = self._load_config()
        if not cfg.get("enabled", False):
            return
        sessions = self.sm.load_today_sessions()
        subject, body = self._build_daily_report(sessions)
        self._send(cfg, subject, body)

    def send_weekly_report(self):
        """Relatório bônus semanal (segunda-feira)."""
        cfg = self._load_config()
        if not cfg.get("enabled", False):
            return
        sessions = self.sm.load_week_sessions()
        subject, body = self._build_weekly_report(sessions)
        self._send(cfg, subject, body)

    def send_test_email(self):
        """Envia um e-mail de teste para validar as configurações."""
        cfg = self._load_config()
        if not cfg:
            return False, "Configuração de e-mail não encontrada."
            
        subject = "🌐 Amplo — Teste de Configuração"
        today_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        body = self._html_wrapper(f"""
            <h2 style='color:#ffd700'>🧪 Teste de E-mail de Configuração</h2>
            <p>Este é um e-mail de teste enviado para validar suas configurações no <b>Amplo</b>.</p>
            <p style='color:#888; font-size:12px;'>Enviado em: {today_str}</p>
        """)
        
        try:
            self._send(cfg, subject, body)
            return True, "E-mail de teste enviado com sucesso!"
        except Exception as e:
            return False, f"Erro ao enviar e-mail de teste: {e}"

    def _send(self, cfg: dict, subject: str, body: str):
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = cfg["sender"]
            msg["To"]      = cfg["recipient"]
            msg.attach(MIMEText(body, "html", "utf-8"))

            with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
                server.starttls()
                server.login(cfg["sender"], cfg["password"])
                server.sendmail(cfg["sender"], cfg["recipient"], msg.as_string())
        except Exception as e:
            print(f"[EmailManager] Erro ao enviar: {e}")

    # ── Builders de HTML ─────────────────────────────────────────

    @staticmethod
    def _fmt(secs):
        secs = int(abs(secs))
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def _build_daily_report(self, sessions: list):
        today_str = datetime.datetime.now().strftime("%d/%m/%Y")
        subject   = f"📊 Amplo — Relatório {today_str}"

        if not sessions:
            body = self._html_wrapper(
                f"<h2>Relatório do dia {today_str}</h2>"
                "<p style='color:#888'>Nenhuma sessão registrada hoje.</p>"
            )
            return subject, body

        session_html = ""
        for i, s in enumerate(sessions, 1):
            diff = s.get("time_diff_secs", 0)
            diff_str   = f"{'+'if diff>=0 else ''}{self._fmt(diff)}"
            diff_color = "#32cd32" if diff >= 0 else "#ff3333"
            
            fp = s.get("focus_pct", 0)
            pp = s.get("pause_pct", 0)
            bp = s.get("break_pct", 0)
            
            cp = s.get("tasks_completed_pct", 0)
            ap = s.get("tasks_abandoned_pct", 0)

            session_html += f"""
            <div style='background:#1a1a1a; padding:20px; border-radius:8px; margin-bottom:30px; border: 1px solid #333;'>
                <h3 style='margin-top:0; color:#ffd700'>Sessão #{i} ({s.get('start','?')} – {s.get('end','?')})</h3>
                <table style='width:100%; border-collapse:collapse; margin-bottom:20px;'>
                    <tr>
                        <td style='color:#888; font-size:12px;'>DURAÇÃO</td>
                        <td style='color:#888; font-size:12px;'>GANHO/PERDA</td>
                        <td style='color:#888; font-size:12px;'>EFICIÊNCIA</td>
                    </tr>
                    <tr>
                        <td style='font-size:18px; font-weight:bold;'>{self._fmt(s.get('session_duration',0))}</td>
                        <td style='font-size:18px; font-weight:bold; color:{diff_color};'>{diff_str}</td>
                        <td style='font-size:18px; font-weight:bold; color:#32cd32;'>{s.get('efficiency',0)}%</td>
                    </tr>
                </table>

                <!-- Barra de Sessão -->
                <div style='margin-bottom:15px;'>
                    <div style='color:#888; font-size:11px; margin-bottom:5px; font-weight:bold;'>PROGRESSO DA SESSÃO</div>
                    <div style='height:20px; width:100%; background:#333; border-radius:4px; overflow:hidden; display:flex;'>
                        <div style='width:{fp}%; background:#ffd700;' title='Foco'></div>
                        <div style='width:{pp}%; background:#ffa600;' title='Pausa'></div>
                        <div style='width:{bp}%; background:#00bfff;' title='Descanso'></div>
                    </div>
                    <div style='font-size:10px; margin-top:5px; color:#888;'>
                        <span style='color:#ffd700'>■</span> FOCO {fp}% &nbsp;&nbsp;
                        <span style='color:#ffa600'>■</span> PAUSA {pp}% &nbsp;&nbsp;
                        <span style='color:#00bfff'>■</span> DESCABSO {bp}%
                    </div>
                </div>

                <!-- Barra de Tasks -->
                <div>
                    <div style='color:#888; font-size:11px; margin-bottom:5px; font-weight:bold;'>CHECK DE TAREFAS</div>
                    <div style='height:20px; width:100%; background:#333; border-radius:4px; overflow:hidden; display:flex;'>
                        <div style='width:{cp}%; background:#32cd32;' title='Concluídas'></div>
                        <div style='width:{ap}%; background:#ff3333;' title='Abandonadas'></div>
                    </div>
                    <div style='font-size:10px; margin-top:5px; color:#888;'>
                        <span style='color:#32cd32'>■</span> CONCLUÍDAS {cp}% &nbsp;&nbsp;
                        <span style='color:#ff3333'>■</span> ABANDONADAS {ap}%
                    </div>
                </div>
            </div>
            """

        body = self._html_wrapper(f"""
          <h2 style='color:#32cd32; margin-bottom:30px;'>🎯 Relatório de Foco — {today_str}</h2>
          {session_html}
          <p style='color:#888; font-size:12px; margin-top:40px;'>Resumo simplificado do seu desempenho hoje.</p>
        """)
        return subject, body

    def _build_weekly_report(self, sessions: list):
        subject = f"🏆 Amplo — Relatório Semanal"
        if not sessions:
            body = self._html_wrapper("<h2>Nenhuma sessão na semana.</h2>")
            return subject, body

        total_secs  = sum(s.get("session_duration", 0) for s in sessions)
        avg_eff     = int(sum(s.get("efficiency", 0) for s in sessions) / len(sessions))
        total_focus = sum(s.get("focus_pct", 0) * s.get("session_duration", 0) / 100
                          for s in sessions)

        body = self._html_wrapper(f"""
          <h2 style='color:#ffd700'>🏆 Relatório Semanal</h2>
          <div style='background:#1a1a1a;padding:20px;border-radius:8px;
                      display:flex;gap:40px;flex-wrap:wrap'>
            <div><div style='color:#888;font-size:12px'>TEMPO TOTAL</div>
                 <div style='font-size:28px;font-weight:bold;color:#ffd700'>{self._fmt(total_secs)}</div></div>
            <div><div style='color:#888;font-size:12px'>TEMPO EM FOCO</div>
                 <div style='font-size:28px;font-weight:bold;color:#ffd700'>{self._fmt(total_focus)}</div></div>
            <div><div style='color:#888;font-size:12px'>EFICIÊNCIA MÉDIA</div>
                 <div style='font-size:28px;font-weight:bold;color:#32cd32'>{avg_eff}%</div></div>
          </div>
          <p style='color:#888;margin-top:24px'>Continue assim! 🚀</p>
        """)
        return subject, body

    @staticmethod
    def _html_wrapper(content: str) -> str:
        return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'></head>
<body style='background:#0a0a0a;color:#ffffff;font-family:monospace;
             max-width:700px;margin:0 auto;padding:24px'>
  {content}
  <hr style='border-color:#333;margin-top:40px'>
  <p style='color:#444;font-size:11px'>Amplo — gerado automaticamente</p>
</body></html>"""

class EmailScheduler:
    """Verifica o horário a cada 30s e dispara o envio quando apropriado.
    Não usa APScheduler para manter dependências mínimas."""

    def __init__(self, email_manager: EmailManager):
        self.em      = email_manager
        self._stop   = threading.Event()
        self._sent_today: str = ""          # evita duplo disparo

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        while not self._stop.wait(30):
            now = datetime.datetime.now()
            key = now.strftime("%Y-%m-%d")

            # Relatório diário às 20:30
            if now.hour == 20 and now.minute == 30 and self._sent_today != key:
                self._sent_today = key
                threading.Thread(target=self.em.send_daily_report, daemon=True).start()

                # Relatório semanal toda segunda-feira (weekday=0)
                if now.weekday() == 0:
                    threading.Thread(target=self.em.send_weekly_report, daemon=True).start()
