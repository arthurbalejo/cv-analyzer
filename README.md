# CV Analyzer — Trabalho Final SO

Sistema cliente-servidor de análise de currículos com threads, sincronização e interface gráfica.

## Estrutura

```
.
├── servidor/
│   ├── main.py        # servidor TCP + 4 threads
│   └── api_claude.py  # integração com a API Anthropic
└── cliente/
    └── main.py        # GUI tkinter
```

## Arquitetura de Threads

| Thread | Tipo | Detalhes |
|---|---|---|
| `network_thread` | Rede | Aceita conexões TCP; lança thread por cliente |
| `monitor_thread` | **Periódica** (2s) | Atualiza métricas (uptime, fila, clientes) |
| `gc_thread` | **Periódica** (30s) | Remove resultados expirados (>10min) |
| `worker_thread` | **Condição** | Dorme em `cv.wait_for()`; acorda quando há job na fila |

## Sincronização

- **`threading.Lock` (mutex)**: protege `fila`, `resultados` e `metricas`
- **`threading.Condition` (variável de condição)**: `worker_thread` dorme até `cv.notify()` ser chamado pela `network_thread` ao receber `SUBMIT_JOB`

## Comandos (7)

| Comando | Uso |
|---|---|
| `SUBMIT_JOB` | Envia vaga + currículo para análise |
| `GET_RESULT` | Busca resultado por job_id |
| `GET_STATUS` | Retorna métricas do servidor |
| `LIST_JOBS` | Lista todos os jobs e status |
| `CANCEL_JOB` | Cancela job pendente na fila |
| `CLEAR_QUEUE` | Limpa todos os jobs pendentes |
| `SET_CRITERIA` | Define critério extra de análise |

## Como rodar

### 1. Instalar dependências
```bash
pip install requests   # ou nenhuma — usa urllib da stdlib
```

### 2. Configurar API Key
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```
Ou edite diretamente `servidor/api_claude.py`, linha `API_KEY = ...`

### 3. Iniciar servidor
```bash
cd servidor
python main.py
```

### 4. Iniciar cliente (outro terminal)
```bash
cd cliente
python main.py
```

### 5. Na GUI
1. Clique em **Conectar** (padrão: 127.0.0.1:9000)
2. Aba **Submeter Job**: cole a descrição da vaga e o currículo → **Enviar para Análise**
3. Aba **Resultado**: cole o Job ID retornado → **Buscar** (aguarde ~10s para a API responder)
4. Aba **Jobs**: liste, cancele ou limpe a fila
5. Aba **Status Servidor**: veja métricas em tempo real

## Protocolo TCP

Mensagens em texto puro terminadas com `\n`.

```
# Cliente → Servidor
SUBMIT_JOB
<descrição da vaga>
---
<currículo>

# Servidor → Cliente
OK job_id=<uuid>

# Cliente → Servidor
GET_RESULT
<job_id>

# Servidor → Cliente
OK {"status": "concluido", "resultado": "...análise..."}
```
