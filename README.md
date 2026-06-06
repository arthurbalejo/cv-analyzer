# CV Analyzer — Trabalho Final Sistema de Tempo Real

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

## Dependências

| Componente | Dependência | Como instalar |
|---|---|---|
| Ambos | Python 3.14+ | — |
| Servidor | `python-dotenv` | `pip install python-dotenv` (dentro do venv) |
| Cliente | `python3-tk` | `sudo apt install python3-tk` |
| Ambos | `socket`, `threading`, `tkinter`, `json`, `uuid`, `time` | stdlib — sem instalação |

## Como rodar

### 1. Instalar dependências

**Servidor** (usar venv):
```bash
cd servidor
python3 -m venv venv
source venv/bin/activate
pip install python-dotenv
```

**Cliente** (sem venv):
```bash
sudo apt install python3-tk
```

### 2. Configurar API Key

Crie o arquivo `servidor/.env` com o conteúdo:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Iniciar servidor
```bash
cd servidor
source venv/bin/activate
python main.py
```

### 4. Iniciar cliente (outro terminal)
```bash
cd cliente
python3 main.py
```

### 5. Na GUI
1. Clique em **Conectar** (padrão: 127.0.0.1:9001)
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

## Apresentação — Conceitos Aplicados

| Requisito | Implementação |
|---|---|
| 4 threads | `network_thread`, `monitor_thread`, `gc_thread`, `worker_thread` |
| 2 threads periódicas | `monitor_thread` (2s), `gc_thread` (30s) |
| 1 thread de rede | `network_thread` |
| 1 thread com mutex/condição | `worker_thread` com `cv.wait_for()` |
| mutex | `threading.Lock()` protegendo `fila`, `resultados`, `metricas` |
| variável de condição | `threading.Condition(lock)`, padrão produtor/consumidor |
| comunicação em rede | sockets TCP porta 9001 |
| interface gráfica | tkinter 5 abas + polling automático 5s |
| 6+ comandos | 7 comandos implementados |
