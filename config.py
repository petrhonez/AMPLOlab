# config.py
import os

# Caminhos de arquivo
STATE_FILE      = "state.json"
CONFIG_FILE     = "config.json"
LOG_STATISTICS  = "focus_statistics.json"
SESSION_DIR     = os.path.join("data", "sessions")
SOUNDS_DIR      = "sounds"

# Cores padrão
COLORS = {
    'bg': '#0a0a0a',
    'fg': '#ffffff',
    'dim': '#222222',
    'topbar_border': '#333333',
    'focus': '#ffd700',
    'rest': '#00bfff',
    'text_dim': '#888888',
    'accent': '#ff3333',
    'success': '#32cd32',
    'current_highlight': '#ffa600'
}

# Fontes
BASE_FONT = "Cascadia Code"


# Inicialização
FONT_CLOCK  = (BASE_FONT, 58, "bold")
FONT_DATE   = (BASE_FONT, 18)
FONT_MAIN   = (BASE_FONT, 20, "bold")
FONT_SMALL  = (BASE_FONT, 11)
FONT_TOPBAR = (BASE_FONT, 8)
FONT_STATS  = (BASE_FONT, 14)
FONT_BUTTON_SMALL = (BASE_FONT, 8)