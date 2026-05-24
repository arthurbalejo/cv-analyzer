"""
Servidor de Análise de Currículos
Trabalho Final — Sistemas Operacionais

Threads:
  1. network_thread     — aceita conexões TCP e despacha clientes
  2. monitor_thread     — periódica (2s): coleta métricas do servidor
  3. gc_thread          — periódica (30s): limpa resultados antigos
  4. worker_thread      — condição: processa jobs da fila (dorme até cv.notify)
"""

import socket
import threading
import time
import uuid
import json
from dotenv import load_dotenv
load_dotenv()
from api_claude import analisar_curriculo

# ─── Estado compartilhado ────────────────────────────────────────────────────

lock = threading.Lock()
cv   = threading.Condition(lock)   # variável de condição (protege fila + resultados)

fila      = []          # jobs pendentes: [{"id", "vaga", "curriculo", "ts"}]
resultados = {}         # job_id → {"status", "resultado", "ts"}
metricas  = {           # atualizadas pela monitor_thread
    "uptime_s": 0,
    "jobs_processados": 0,
    "jobs_na_fila": 0,
    "clientes_ativos": 0,
    "inicio": time.time(),
}

clientes_ativos = 0     # protegido pelo lock

HOST = "0.0.0.0"
PORT = 9001

# ─── Thread 4: Worker (variável de condição) ─────────────────────────────────

def worker_thread():
    """Dorme em cv.wait() até haver job na fila. Processa um por vez."""
    print("[worker] iniciado")
    while True:
        with cv:
            # bloqueia enquanto fila estiver vazia
            cv.wait_for(lambda: len(fila) > 0)
            job = fila.pop(0)

        print(f"[worker] processando job {job['id'][:8]}...")

        # atualiza status para PROCESSANDO (fora do cv, usando lock direto)
        with lock:
            resultados[job["id"]]["status"] = "processando"

        try:
            resultado = analisar_curriculo(job["vaga"], job["curriculo"])
            status = "concluido"
        except Exception as e:
            resultado = f"Erro ao chamar API: {e}"
            status = "erro"

        with lock:
            resultados[job["id"]]["status"]    = status
            resultados[job["id"]]["resultado"] = resultado
            resultados[job["id"]]["ts_fim"]    = time.time()
            metricas["jobs_processados"] += 1

        print(f"[worker] job {job['id'][:8]} → {status}")


# ─── Thread 2: Monitor periódica (2s) ────────────────────────────────────────

def monitor_thread():
    """Atualiza métricas do servidor a cada 2 segundos."""
    print("[monitor] iniciado")
    while True:
        time.sleep(2)
        with lock:
            metricas["uptime_s"]      = int(time.time() - metricas["inicio"])
            metricas["jobs_na_fila"]  = len(fila)
            metricas["clientes_ativos"] = clientes_ativos


# ─── Thread 3: GC periódica (30s) ────────────────────────────────────────────

def gc_thread():
    """Remove resultados com mais de 10 minutos a cada 30 segundos."""
    print("[gc] iniciado")
    while True:
        time.sleep(30)
        agora = time.time()
        with lock:
            expirados = [
                jid for jid, r in resultados.items()
                if r.get("ts_fim") and (agora - r["ts_fim"]) > 600
            ]
            for jid in expirados:
                del resultados[jid]
        if expirados:
            print(f"[gc] removidos {len(expirados)} resultado(s) expirado(s)")


# ─── Tratamento de comandos ───────────────────────────────────────────────────

def cmd_submit(args):
    """SUBMIT_JOB\n<vaga>\n---\n<curriculo>"""
    try:
        partes = args.split("\n---\n", 1)
        if len(partes) != 2:
            return "ERR formato: SUBMIT_JOB\\n<vaga>\\n---\\n<curriculo>"
        vaga, curriculo = partes
        job_id = str(uuid.uuid4())

        with cv:
            fila.append({
                "id": job_id,
                "vaga": vaga.strip(),
                "curriculo": curriculo.strip(),
                "ts": time.time(),
            })
            resultados[job_id] = {
                "status": "pendente",
                "resultado": None,
                "ts_inicio": time.time(),
                "ts_fim": None,
            }
            cv.notify()   # acorda worker_thread

        return f"OK job_id={job_id}"
    except Exception as e:
        return f"ERR {e}"


def cmd_get_result(args):
    """GET_RESULT <job_id>"""
    job_id = args.strip()
    with lock:
        r = resultados.get(job_id)
    if r is None:
        return "ERR job não encontrado"
    payload = {
        "status":    r["status"],
        "resultado": r["resultado"] or "",
    }
    return "OK " + json.dumps(payload, ensure_ascii=False)


def cmd_get_status(_args):
    """GET_STATUS"""
    with lock:
        m = dict(metricas)
        m["jobs_na_fila"] = len(fila)
    return "OK " + json.dumps(m, ensure_ascii=False)


def cmd_list_jobs(_args):
    """LIST_JOBS"""
    with lock:
        jobs = [
            {"id": jid, "status": r["status"]}
            for jid, r in resultados.items()
        ]
    return "OK " + json.dumps(jobs, ensure_ascii=False)


def cmd_cancel_job(args):
    """CANCEL_JOB <job_id>"""
    job_id = args.strip()
    with cv:
        idx = next((i for i, j in enumerate(fila) if j["id"] == job_id), None)
        if idx is None:
            return "ERR job não encontrado na fila (pode já estar em processamento)"
        fila.pop(idx)
        resultados[job_id]["status"] = "cancelado"
    return f"OK job {job_id[:8]} cancelado"


def cmd_clear_queue(_args):
    """CLEAR_QUEUE"""
    with cv:
        cancelados = len(fila)
        for job in fila:
            resultados[job["id"]]["status"] = "cancelado"
        fila.clear()
    return f"OK {cancelados} job(s) removido(s) da fila"


def cmd_set_criteria(args):
    """SET_CRITERIA <texto> — ajusta critério extra de análise"""
    # Salva no estado global para a api_claude usar
    with lock:
        metricas["criterio_extra"] = args.strip()
    return f"OK critério definido: {args.strip()[:60]}"


COMANDOS = {
    "SUBMIT_JOB":   cmd_submit,
    "GET_RESULT":   cmd_get_result,
    "GET_STATUS":   cmd_get_status,
    "LIST_JOBS":    cmd_list_jobs,
    "CANCEL_JOB":  cmd_cancel_job,
    "CLEAR_QUEUE":  cmd_clear_queue,
    "SET_CRITERIA": cmd_set_criteria,
}


# ─── Thread 1: Rede — handler por cliente ────────────────────────────────────

def handle_client(conn, addr):
    global clientes_ativos
    print(f"[net] cliente conectado: {addr}")

    with lock:
        clientes_ativos += 1

    try:
        # Recebe mensagem (até 64KB)
        partes = []
        conn.settimeout(60)
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            partes.append(chunk)
            if chunk.endswith(b"\n"):
                break
        data = b"".join(partes).decode("utf-8").strip()

        if not data:
            conn.send(b"ERR mensagem vazia\n")
            return

        # Separa comando dos argumentos (primeira linha é o comando)
        linhas = data.split("\n", 1)
        comando = linhas[0].strip()
        args    = linhas[1] if len(linhas) > 1 else ""

        handler = COMANDOS.get(comando)
        if handler is None:
            resposta = f"ERR comando desconhecido: {comando}"
        else:
            resposta = handler(args)

        conn.send((resposta + "\n").encode("utf-8"))

    except Exception as e:
        try:
            conn.send(f"ERR interno: {e}\n".encode())
        except:
            pass
    finally:
        conn.close()
        with lock:
            clientes_ativos -= 1
        print(f"[net] cliente desconectado: {addr}")


def network_thread():
    """Aceita conexões e lança uma thread por cliente."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(10)
    print(f"[net] escutando em {HOST}:{PORT}")

    while True:
        conn, addr = srv.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    threads = [
        threading.Thread(target=network_thread, daemon=True,  name="network"),
        threading.Thread(target=monitor_thread,  daemon=True,  name="monitor"),
        threading.Thread(target=gc_thread,        daemon=True,  name="gc"),
        threading.Thread(target=worker_thread,    daemon=True,  name="worker"),
    ]

    print("=== Servidor de Análise de Currículos ===")
    for t in threads:
        t.start()
        print(f"  ✓ {t.name}_thread iniciada")

    print(f"\nServidor rodando na porta {PORT}. Ctrl+C para encerrar.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[main] encerrando servidor.")
