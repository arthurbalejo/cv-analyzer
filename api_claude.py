"""
Módulo de integração com a API da Anthropic.
Chamado pela worker_thread do servidor.
"""

import os
import json
import urllib.request
import urllib.error

# Coloque sua chave aqui ou defina a variável de ambiente ANTHROPIC_API_KEY
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_URL = "https://api.anthropic.com/v1/messages"


def analisar_curriculo(vaga: str, curriculo: str) -> str:
    """
    Envia vaga + currículo para a API Claude e retorna a análise como string.
    Levanta exceção em caso de erro HTTP.
    """

    prompt = f"""Você é um recrutador técnico experiente. Analise o currículo abaixo em relação à descrição da vaga.

=== DESCRIÇÃO DA VAGA ===
{vaga}

=== CURRÍCULO DO CANDIDATO ===
{curriculo}

=== INSTRUÇÕES ===
Responda em português com:

1. **Pontuação de compatibilidade**: X/10
2. **Pontos fortes**: liste as habilidades/experiências do candidato que atendem à vaga
3. **Lacunas**: habilidades exigidas pela vaga que o candidato não demonstra
4. **Recomendação**: APROVADO PARA ENTREVISTA / REQUER AVALIAÇÃO / NÃO RECOMENDADO
5. **Justificativa**: 2-3 frases explicando a recomendação

Seja objetivo e direto."""

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"]
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {corpo}")
