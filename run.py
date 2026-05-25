"""Ponto de entrada do PMAS — configurável por variáveis de ambiente.

Uso rápido:
    python run.py

Opções via env:
    PMAS_PORT=9000          porta customizada (padrão: 8765)
    PMAS_HOST=0.0.0.0       expõe na rede local (padrão: 127.0.0.1)
    PMAS_ENV=production     desativa reload automático
    PMAS_SECRET_KEY=...     chave JWT persistente (obrigatório em produção)
    PMAS_LOG_LEVEL=DEBUG    nível de log
"""
from __future__ import annotations

import os
import sys

import uvicorn

if __name__ == "__main__":
    host   = os.getenv("PMAS_HOST", "127.0.0.1")
    port   = int(os.getenv("PMAS_PORT", "8765"))
    frozen = getattr(sys, "frozen", False)

    if frozen:
        # Em executável PyInstaller: importação direta + reload desativado
        # (módulos Python não existem como ficheiros no binário)
        from backend.app.main import app as _app
        uvicorn.run(_app, host=host, port=port, reload=False)
    else:
        dev = os.getenv("PMAS_ENV", "development") != "production"
        uvicorn.run("backend.app.main:app", host=host, port=port, reload=dev)
