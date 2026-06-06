#!/bin/bash

# Detect available terminal emulator
if command -v gnome-terminal &> /dev/null; then
    TERM_CMD="gnome-terminal --"
elif command -v konsole &> /dev/null; then
    TERM_CMD="konsole -e"
elif command -v xterm &> /dev/null; then
    TERM_CMD="xterm -e"
else
    echo "Erro: nenhum emulador de terminal encontrado (gnome-terminal, konsole, xterm)."
    exit 1
fi

# Start server
echo "Iniciando o servidor..."
$TERM_CMD bash -c "source venv/bin/activate && python main.py; exec bash" &

# Wait before starting client
sleep 2

# Start client
echo "Iniciando o cliente..."
$TERM_CMD bash -c "cd cliente && python3 main.py; exec bash" &
