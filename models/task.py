# models/task.py
import datetime

class Task:
    """
    Representa os dados e estado de uma tarefa.
    Isolamos isso aqui para que a interface apenas leia e altere estes dados.
    """
    def __init__(self, name: str, weight: int):
        self.name   = name
        self.weight = max(1, min(3, int(weight))) # Garante peso entre 1 e 3

        self.duration_seconds      = 0
        self.start_time_real       = None
        self.end_time_real         = None
        self.duration_seconds_real = 0
        self.status                = "Pendente"
        self.start_time            = None

    def calculate_real_duration(self):
        """Calcula o tempo real gasto na tarefa com base no início e fim."""
        if self.start_time_real and self.end_time_real:
            self.duration_seconds_real = int(
                (self.end_time_real - self.start_time_real).total_seconds()
            )
        return self.duration_seconds_real