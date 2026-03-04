# services/session.py
import os
import json
import datetime
from config import STATE_FILE, SESSION_DIR, LOG_STATISTICS
from models.task import Task

class SessionManager:
    """Responsável por:
    - Salvar/restaurar estado de sessão (state.json) para recuperação
    - Persistir cada sessão em JSON e Markdown (data/sessions/)
    - Alimentar o arquivo de estatísticas semanais
    """

    def __init__(self):
        os.makedirs(SESSION_DIR, exist_ok=True)

    # ── State (recuperação após desligamento abrupto) ─────────────

    def save_state(self, app):
        """Snapshot do estado atual da sessão. Chamado a cada mudança."""
        if not app.session_start_time:
            return
        state = {
            "status":              "running",
            "session_id":          app.session_start_time.isoformat(),
            "session_start":       app.session_start_time.isoformat(),
            "planned_end":         app.planned_end_time.isoformat() if app.planned_end_time else None,
            "current_task_index":  app.current_task_index,
            "is_break":            app.is_break,
            "time_left":           app.time_left,
            "total_paused_time":   app.total_paused_time,
            "break_per_slot":      app.break_per_slot,
            "tasks": [
                {
                    "name":                 t.name,
                    "weight":               t.weight,
                    "status":               t.status,
                    "duration_seconds":     t.duration_seconds,
                    "duration_seconds_real":t.duration_seconds_real,
                    "start_time":           t.start_time.isoformat() if t.start_time else None,
                    "start_time_real":      t.start_time_real.isoformat() if t.start_time_real else None,
                    "end_time_real":        t.end_time_real.isoformat() if t.end_time_real else None,
                }
                for t in app.tasks
            ],
            "breaks_real": [
                {
                    "index":    b["index"],
                    "start":    b["start"].isoformat() if isinstance(b["start"], datetime.datetime) else b["start"],
                    "end":      b["end"].isoformat() if isinstance(b["end"], datetime.datetime) else b["end"],
                    "duration": b["duration"],
                }
                for b in app.breaks_real
            ],
        }
        self._atomic_write(STATE_FILE, state)

    def clear_state(self):
        """Marca sessão como concluída no state.json."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                state["status"] = "completed"
                self._atomic_write(STATE_FILE, state)
            except Exception:
                pass

    def load_state(self):
        """Retorna state.json se houver sessão interrompida, ou None."""
        if not os.path.exists(STATE_FILE):
            return None
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
            if state.get("status") == "running":
                return state
        except Exception:
            pass
        return None

    def restore_tasks(self, state: dict) -> list:
        """Reconstrói lista de Task a partir do state salvo."""
        tasks = []
        for td in state.get("tasks", []):
            t = Task(td["name"], td["weight"])
            t.status               = td["status"]
            t.duration_seconds     = td["duration_seconds"]
            t.duration_seconds_real= td["duration_seconds_real"]
            t.start_time           = datetime.datetime.fromisoformat(td["start_time"]) if td["start_time"] else None
            t.start_time_real      = datetime.datetime.fromisoformat(td["start_time_real"]) if td["start_time_real"] else None
            t.end_time_real        = datetime.datetime.fromisoformat(td["end_time_real"]) if td["end_time_real"] else None
            tasks.append(t)
        return tasks

    # ── Persistência de sessão concluída ─────────────────────────

    def save_session(self, app, stats: dict):
        """Salva sessão concluída em JSON e Markdown."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        base  = os.path.join(SESSION_DIR, today)

        session_data = self._build_session_data(app, stats)

        # JSON (para leitura programática / e-mail)
        self._save_session_json(f"{base}.json", session_data)

        # Markdown (legível por humanos)
        self._save_session_md(f"{base}.md", session_data)

        # Estatísticas semanais
        self._update_statistics(today, stats)

        return session_data

    def _build_session_data(self, app, stats: dict) -> dict:
        total_tasks = len(app.tasks)
        completed = sum(1 for t in app.tasks if t.status == "Concluída")
        abandoned = sum(1 for t in app.tasks if t.status == "Abandonada")
        
        return {
            "date":            datetime.datetime.now().strftime("%Y-%m-%d"),
            "start":           app.session_start_time.strftime("%H:%M:%S"),
            "end":             app.session_end_time.strftime("%H:%M:%S"),
            "planned_end":     app.planned_end_time.strftime("%H:%M:%S") if app.planned_end_time else "-",
            "session_duration":stats["session_duration"],
            "efficiency":      stats.get("efficiency", 0),
            "focus_pct":       int(stats["total_focus_real"] / stats["session_duration"] * 100) if stats["session_duration"] > 0 else 0,
            "break_pct":       int(stats["total_breaks_real"] / stats["session_duration"] * 100) if stats["session_duration"] > 0 else 0,
            "pause_pct":       int(stats["total_paused_time"] / stats["session_duration"] * 100) if stats["session_duration"] > 0 else 0,
            "tasks_completed_pct": int(completed / total_tasks * 100) if total_tasks > 0 else 0,
            "tasks_abandoned_pct": int(abandoned / total_tasks * 100) if total_tasks > 0 else 0,
            "time_diff_secs":  stats["total_planned"] - stats["session_duration"],
            "tasks": [
                {
                    "name":       t.name,
                    "weight":     t.weight,
                    "status":     t.status,
                    "planned_s":  t.duration_seconds,
                    "real_s":     t.duration_seconds_real,
                    "diff_s":     t.duration_seconds_real - t.duration_seconds,
                }
                for t in app.tasks
            ],
        }

    def _save_session_json(self, filepath: str, data: dict):
        existing = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                if not isinstance(existing, list):
                    existing = [existing]
            except Exception:
                existing = []
        existing.append(data)
        self._atomic_write(filepath, existing)

    def _save_session_md(self, filepath: str, data: dict):
        lines = []

        # Se arquivo já existe, lê o conteúdo anterior
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            lines.append("\n---\n\n")

        def fmt(secs):
            m, s = divmod(int(abs(secs)), 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

        diff = data["time_diff_secs"]
        diff_str = f"{'+'if diff>=0 else ''}{fmt(diff)}"
        diff_emoji = "✅" if diff >= 0 else "⚠️"

        block = [
            f"# Sessão — {data['date']}\n\n",
            f"**Início:** {data['start']} | **Fim:** {data['end']} | **Planejado até:** {data['planned_end']}\n\n",
            f"## Resumo\n\n",
            f"| Métrica | Valor |\n",
            f"|---------|-------|\n",
            f"| Duração total | {fmt(data['session_duration'])} |\n",
            f"| Eficiência de foco | {data['efficiency']}% |\n",
            f"| Foco | {data['focus_pct']}% |\n",
            f"| Descanso | {data['break_pct']}% |\n",
            f"| Pausa (extra) | {data['pause_pct']}% |\n",
            f"| Saldo de tempo | {diff_emoji} {diff_str} |\n\n",
            f"## Tarefas\n\n",
            f"| # | Tarefa | Peso | Planejado | Real | Variação | Status |\n",
            f"|---|--------|------|-----------|------|----------|--------|\n",
        ]
        for i, t in enumerate(data["tasks"], 1):
            v = t["diff_s"]
            v_str = f"{'+'if v>=0 else ''}{fmt(v)}"
            block.append(
                f"| {i} | {t['name']} | {t['weight']}x | {fmt(t['planned_s'])} | "
                f"{fmt(t['real_s'])} | {v_str} | {t['status']} |\n"
            )
        block.append("\n")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines + block)

    # ── Estatísticas semanais ────────────────────────────────────

    def _update_statistics(self, today: str, stats: dict):
        try:
            efficiency = int((stats["total_focus_real"] / stats["session_duration"]) * 100) \
                if stats["session_duration"] > 0 else 0
            data = {}
            if os.path.exists(LOG_STATISTICS):
                with open(LOG_STATISTICS, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            if today not in data:
                data[today] = []
            data[today].append(efficiency)
            self._atomic_write(LOG_STATISTICS, data)
        except Exception:
            pass

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _atomic_write(filepath: str, obj):
        """Escreve em arquivo temporário e renomeia atomicamente."""
        tmp = filepath + ".tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, default=str)
        os.replace(tmp, filepath)

    # ── Leitura para e-mail ──────────────────────────────────────

    def load_today_sessions(self) -> list:
        """Retorna lista de sessões do dia atual."""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        path  = os.path.join(SESSION_DIR, f"{today}.json")
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, list) else [data]
        except Exception:
            return []

    def load_week_sessions(self) -> list:
        """Retorna sessões dos últimos 7 dias."""
        sessions = []
        for i in range(7):
            d = (datetime.datetime.now() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            path = os.path.join(SESSION_DIR, f"{d}.json")
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        sessions.extend(data)
                    else:
                        sessions.append(data)
                except Exception:
                    pass
        return sessions

class StatisticsManager:
    """Gerenciador de estatísticas de foco semanal."""

    def __init__(self):
        self.days_map  = {0:'D',1:'2',2:'3',3:'4',4:'5',5:'6',6:'S'}
        self.days_full = {0:'Domingo',1:'Segunda',2:'Terça',3:'Quarta',
                          4:'Quinta',5:'Sexta',6:'Sábado'}

    def get_weekly_focus_efficiency(self):
        weekly_data = {i: [] for i in range(7)}
        try:
            if not os.path.exists(LOG_STATISTICS):
                return {i: 0 for i in range(7)}
            with open(LOG_STATISTICS, 'r', encoding='utf-8') as f:
                stats_file = json.load(f)
            for date_str, efficiencies in stats_file.items():
                try:
                    session_date  = datetime.datetime.fromisoformat(date_str).date()
                    weekday       = session_date.weekday()
                    adjusted_day  = (weekday + 1) % 7
                    if isinstance(efficiencies, list):
                        for e in efficiencies: weekly_data[adjusted_day].append(int(e))
                    elif isinstance(efficiencies, (int, float)):
                        weekly_data[adjusted_day].append(int(efficiencies))
                except Exception: pass
            return {d: (int(sum(v)/len(v)) if v else 0) for d, v in weekly_data.items()}
        except Exception:
            return {i: 0 for i in range(7)}

    def calculate_session_focus_efficiency(self, stats):
        sd = stats['session_duration']
        if sd <= 0: return 0
        return min(int((stats['total_focus_real'] / sd) * 100), 100)

