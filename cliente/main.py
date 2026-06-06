"""
Cliente GUI — Analisador de Currículos
Trabalho Final — Sistemas Operacionais

Interface tkinter com:
  - Conexão ao servidor
  - Envio dos 7 comandos
  - Visualização de respostas e status
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import threading
import json
import time

# ─── Comunicação com o servidor ──────────────────────────────────────────────

def enviar_comando(host, port, mensagem: str) -> str:
    """Abre conexão TCP, envia mensagem, retorna resposta."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(90)
        s.connect((host, int(port)))
        s.sendall((mensagem + "\n").encode("utf-8"))
        partes = []
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            partes.append(chunk)
            if chunk.endswith(b"\n"):
                break
        return b"".join(partes).decode("utf-8").strip()


# ─── Paleta e estilos ─────────────────────────────────────────────────────────

BG       = "#0f1117"
BG2      = "#1a1d27"
BG3      = "#242736"
ACCENT   = "#6c63ff"
ACCENT2  = "#a78bfa"
SUCCESS  = "#34d399"
ERROR    = "#f87171"
WARNING  = "#fbbf24"
FG       = "#e2e8f0"
FG2      = "#94a3b8"
FONT_UI  = ("Consolas", 10)
FONT_H   = ("Consolas", 13, "bold")
FONT_SM  = ("Consolas", 9)


# ─── Janela principal ─────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CV Analyzer — Cliente")
        self.geometry("1100x760")
        self.configure(bg=BG)
        self.resizable(True, True)

        self._build_ui()
        self._poll_status()   # inicia polling de status quando conectado

    # ── Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header
        hdr = tk.Frame(self, bg=BG, pady=10)
        hdr.pack(fill="x", padx=20)

        tk.Label(hdr, text="⬡ CV ANALYZER", font=("Consolas", 16, "bold"),
                 bg=BG, fg=ACCENT2).pack(side="left")
        self.lbl_conn = tk.Label(hdr, text="● desconectado",
                                  font=FONT_SM, bg=BG, fg=ERROR)
        self.lbl_conn.pack(side="right")

        # ── Conexão
        conn_frame = tk.LabelFrame(self, text=" Servidor ", font=FONT_SM,
                                   bg=BG2, fg=FG2, bd=1, relief="flat",
                                   labelanchor="nw")
        conn_frame.pack(fill="x", padx=20, pady=(0, 8))

        inner = tk.Frame(conn_frame, bg=BG2)
        inner.pack(padx=10, pady=8, fill="x")

        tk.Label(inner, text="Host:", bg=BG2, fg=FG2, font=FONT_SM).pack(side="left")
        self.ent_host = tk.Entry(inner, width=18, bg=BG3, fg=FG,
                                  insertbackground=FG, font=FONT_UI, bd=0)
        self.ent_host.insert(0, "127.0.0.1")
        self.ent_host.pack(side="left", padx=(4, 12))

        tk.Label(inner, text="Porta:", bg=BG2, fg=FG2, font=FONT_SM).pack(side="left")
        self.ent_port = tk.Entry(inner, width=7, bg=BG3, fg=FG,
                                  insertbackground=FG, font=FONT_UI, bd=0)
        self.ent_port.insert(0, "9001")
        self.ent_port.pack(side="left", padx=(4, 12))

        self.btn_conn = self._btn(inner, "Conectar", self._testar_conexao,
                                   color=ACCENT)
        self.btn_conn.pack(side="left")

        # ── Notebook de comandos
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG3, foreground=FG2,
                         font=FONT_SM, padding=[12, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", BG2)],
                  foreground=[("selected", ACCENT2)])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        self._tab_submit(nb)
        self._tab_result(nb)
        self._tab_jobs(nb)
        self._tab_status(nb)
        self._tab_adv(nb)

        # ── Log
        log_frame = tk.LabelFrame(self, text=" Log de Respostas ", font=FONT_SM,
                                   bg=BG2, fg=FG2, bd=1, relief="flat")
        log_frame.pack(fill="x", padx=20, pady=(0, 12))

        self.log = scrolledtext.ScrolledText(
            log_frame, height=7, bg=BG3, fg=FG2,
            font=FONT_SM, bd=0, wrap="word",
            insertbackground=FG,
        )
        self.log.pack(fill="x", padx=8, pady=8)
        self.log.configure(state="disabled")

        self._log("Sistema iniciado. Configure o servidor e clique em Conectar.")

    # ── Abas ───────────────────────────────────────────────────────────────

    def _tab_submit(self, nb):
        f = self._frame(nb)
        nb.add(f, text="📄 Submeter Job")

        tk.Label(f, text="Descrição da Vaga", bg=BG2, fg=FG2,
                 font=FONT_SM).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 2))
        self.txt_vaga = scrolledtext.ScrolledText(
            f, height=7, bg=BG3, fg=FG, font=FONT_SM, bd=0,
            insertbackground=FG, wrap="word")
        self.txt_vaga.grid(row=1, column=0, padx=12, sticky="ew")

        tk.Label(f, text="Currículo do Candidato", bg=BG2, fg=FG2,
                 font=FONT_SM).grid(row=2, column=0, sticky="w", padx=12, pady=(8, 2))
        self.txt_cv = scrolledtext.ScrolledText(
            f, height=8, bg=BG3, fg=FG, font=FONT_SM, bd=0,
            insertbackground=FG, wrap="word")
        self.txt_cv.grid(row=3, column=0, padx=12, pady=(0, 8), sticky="ew")

        self._btn(f, "▶  Enviar para Análise", self._submit_job,
                  color=ACCENT).grid(row=4, column=0, padx=12, pady=(0, 8), sticky="w")

        id_row = tk.Frame(f, bg=BG2)
        id_row.grid(row=5, column=0, padx=12, pady=(0, 12), sticky="ew")
        tk.Label(id_row, text="Job ID:", bg=BG2, fg=FG2, font=FONT_SM).pack(side="left")
        self.ent_submitted_id = tk.Entry(
            id_row, width=44, bg=BG3, fg=SUCCESS, font=FONT_UI, bd=0,
            state="readonly", readonlybackground=BG3)
        self.ent_submitted_id.pack(side="left", padx=(6, 8))
        self._btn(id_row, "Copiar ID", self._copy_submitted_id,
                  color=ACCENT2).pack(side="left")

        f.columnconfigure(0, weight=1)

    def _tab_result(self, nb):
        f = self._frame(nb)
        nb.add(f, text="🔍 Resultado")

        row = tk.Frame(f, bg=BG2)
        row.pack(fill="x", padx=12, pady=12)

        tk.Label(row, text="Job ID:", bg=BG2, fg=FG2, font=FONT_SM).pack(side="left")
        self.ent_jobid = tk.Entry(row, width=40, bg=BG3, fg=FG,
                                   insertbackground=FG, font=FONT_UI, bd=0)
        self.ent_jobid.pack(side="left", padx=(6, 10))
        self._btn(row, "Buscar", self._get_result, color=ACCENT2).pack(side="left")

        self.lbl_status_job = tk.Label(f, text="", bg=BG2, fg=FG2, font=FONT_SM)
        self.lbl_status_job.pack(anchor="w", padx=12)

        self.txt_result = scrolledtext.ScrolledText(
            f, bg=BG3, fg=FG, font=FONT_SM, bd=0,
            insertbackground=FG, wrap="word")
        self.txt_result.pack(fill="both", expand=True, padx=12, pady=8)

    def _tab_jobs(self, nb):
        f = self._frame(nb)
        nb.add(f, text="📋 Jobs")

        btns = tk.Frame(f, bg=BG2)
        btns.pack(fill="x", padx=12, pady=10)
        self._btn(btns, "↻  Listar Jobs", self._list_jobs, color=ACCENT2).pack(side="left", padx=(0, 8))
        self._btn(btns, "✕  Cancelar Selecionado", self._cancel_job, color=WARNING).pack(side="left", padx=(0, 8))
        self._btn(btns, "🗑  Limpar Fila", self._clear_queue, color=ERROR).pack(side="left", padx=(0, 8))
        self._btn(btns, "Copiar ID Selecionado", self._on_job_select,
                  color=ACCENT).pack(side="left")

        cols = ("id", "status")
        self.tree = ttk.Treeview(f, columns=cols, show="headings", height=14)
        style = ttk.Style()
        style.configure("Treeview", background=BG3, foreground=FG,
                         fieldbackground=BG3, font=FONT_SM, rowheight=24)
        style.configure("Treeview.Heading", background=BG2, foreground=FG2,
                         font=FONT_SM)
        self.tree.heading("id",     text="Job ID")
        self.tree.heading("status", text="Status")
        self.tree.column("id",     width=320)
        self.tree.column("status", width=140)
        self.tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.tree.bind("<<TreeviewSelect>>", self._on_job_select)

    def _tab_status(self, nb):
        f = self._frame(nb)
        nb.add(f, text="📊 Status Servidor")

        self._btn(f, "↻  Atualizar Status", self._get_status,
                  color=ACCENT2).pack(anchor="w", padx=12, pady=12)

        self.lbl_metrics = tk.Label(
            f, text="—", bg=BG2, fg=FG,
            font=("Consolas", 11), justify="left", anchor="w")
        self.lbl_metrics.pack(fill="x", padx=20, pady=4)

    def _tab_adv(self, nb):
        f = self._frame(nb)
        nb.add(f, text="⚙ Avançado")

        tk.Label(f, text="Critério Extra de Análise (SET_CRITERIA):",
                 bg=BG2, fg=FG2, font=FONT_SM).pack(anchor="w", padx=12, pady=(12, 4))
        self.ent_criteria = tk.Entry(f, bg=BG3, fg=FG, insertbackground=FG,
                                      font=FONT_UI, bd=0)
        self.ent_criteria.pack(fill="x", padx=12)
        self.ent_criteria.insert(0, "Priorize experiência com Python e sistemas distribuídos.")
        self._btn(f, "Definir Critério", self._set_criteria,
                  color=ACCENT).pack(anchor="w", padx=12, pady=8)

    # ── Helpers de widget ──────────────────────────────────────────────────

    def _frame(self, parent):
        return tk.Frame(parent, bg=BG2)

    def _btn(self, parent, text, cmd, color=ACCENT):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=color, fg="#ffffff", activebackground=BG3,
            font=FONT_SM, bd=0, padx=12, pady=5, cursor="hand2",
            relief="flat",
        )

    def _log(self, msg: str, color=FG2):
        ts = time.strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert("end", f"[{ts}] {msg}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _host_port(self):
        return self.ent_host.get().strip(), self.ent_port.get().strip()

    def _run_async(self, fn):
        """Executa fn em thread separada para não travar a GUI."""
        threading.Thread(target=fn, daemon=True).start()

    def _send(self, mensagem: str) -> str | None:
        h, p = self._host_port()
        try:
            resp = enviar_comando(h, p, mensagem)
            return resp
        except Exception as e:
            self._log(f"ERRO de conexão: {e}", ERROR)
            self.lbl_conn.config(text="● desconectado", fg=ERROR)
            return None

    # ── Comandos ───────────────────────────────────────────────────────────

    def _testar_conexao(self):
        def _():
            resp = self._send("GET_STATUS")
            if resp and resp.startswith("OK"):
                self.lbl_conn.config(text="● conectado", fg=SUCCESS)
                self._log(f"Conexão OK → {resp[:80]}", SUCCESS)
            else:
                self.lbl_conn.config(text="● falhou", fg=ERROR)
                self._log(f"Falha na conexão: {resp}", ERROR)
        self._run_async(_)

    def _submit_job(self):
        vaga = self.txt_vaga.get("1.0", "end").strip()
        cv   = self.txt_cv.get("1.0", "end").strip()
        if not vaga or not cv:
            messagebox.showwarning("Atenção", "Preencha a vaga e o currículo.")
            return

        def _():
            msg  = f"SUBMIT_JOB\n{vaga}\n---\n{cv}"
            resp = self._send(msg)
            if resp and resp.startswith("OK"):
                job_id = resp.split("job_id=")[-1].strip()
                self.ent_submitted_id.configure(state="normal")
                self.ent_submitted_id.delete(0, "end")
                self.ent_submitted_id.insert(0, job_id)
                self.ent_submitted_id.configure(state="readonly")
                self.ent_jobid.delete(0, "end")
                self.ent_jobid.insert(0, job_id)
                self._log(f"Job submetido: {job_id[:18]}...", SUCCESS)
            else:
                self._log(f"Erro ao submeter: {resp}", ERROR)
        self._run_async(_)

    def _get_result(self):
        job_id = self.ent_jobid.get().strip()
        if not job_id:
            messagebox.showwarning("Atenção", "Informe o Job ID.")
            return

        def _():
            resp = self._send(f"GET_RESULT\n{job_id}")
            if resp and resp.startswith("OK "):
                try:
                    data = json.loads(resp[3:])
                    status = data.get("status", "?")
                    resultado = data.get("resultado", "")
                    color = SUCCESS if status == "concluido" else WARNING
                    self.lbl_status_job.config(
                        text=f"Status: {status}", fg=color)
                    self.txt_result.configure(state="normal")
                    self.txt_result.delete("1.0", "end")
                    self.txt_result.insert("end", resultado or "(ainda processando...)")
                    self.txt_result.configure(state="disabled")
                    self._log(f"Resultado de {job_id[:18]}… → {status}")
                except Exception as e:
                    self._log(f"Erro ao parsear resultado: {e}", ERROR)
            else:
                self._log(f"Erro GET_RESULT: {resp}", ERROR)
        self._run_async(_)

    def _get_status(self):
        def _():
            resp = self._send("GET_STATUS")
            if resp and resp.startswith("OK "):
                try:
                    m = json.loads(resp[3:])
                    txt = (
                        f"  Uptime          : {m.get('uptime_s', 0)}s\n"
                        f"  Jobs processados: {m.get('jobs_processados', 0)}\n"
                        f"  Jobs na fila    : {m.get('jobs_na_fila', 0)}\n"
                        f"  Clientes ativos : {m.get('clientes_ativos', 0)}\n"
                    )
                    if "criterio_extra" in m:
                        txt += f"  Critério extra  : {m['criterio_extra'][:60]}\n"
                    self.lbl_metrics.config(text=txt)
                    self._log("Status atualizado.")
                except Exception as e:
                    self._log(f"Erro ao parsear status: {e}", ERROR)
            else:
                self._log(f"Erro GET_STATUS: {resp}", ERROR)
        self._run_async(_)

    def _list_jobs(self):
        def _():
            resp = self._send("LIST_JOBS")
            if resp and resp.startswith("OK "):
                try:
                    jobs = json.loads(resp[3:])
                    self.tree.delete(*self.tree.get_children())
                    for j in jobs:
                        tag = "ok" if j["status"] == "concluido" else "pend"
                        self.tree.insert("", "end",
                                         values=(j["id"], j["status"]),
                                         tags=(tag,))
                    self.tree.tag_configure("ok",   foreground=SUCCESS)
                    self.tree.tag_configure("pend", foreground=WARNING)
                    self._log(f"Listados {len(jobs)} job(s).")
                except Exception as e:
                    self._log(f"Erro ao listar: {e}", ERROR)
            else:
                self._log(f"Erro LIST_JOBS: {resp}", ERROR)
        self._run_async(_)

    def _cancel_job(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um job na tabela.")
            return
        job_id = self.tree.item(sel[0])["values"][0]

        def _():
            resp = self._send(f"CANCEL_JOB\n{job_id}")
            self._log(f"CANCEL_JOB {job_id[:18]}… → {resp}")
            self._list_jobs()
        self._run_async(_)

    def _clear_queue(self):
        if not messagebox.askyesno("Confirmar", "Limpar toda a fila?"):
            return

        def _():
            resp = self._send("CLEAR_QUEUE")
            self._log(f"CLEAR_QUEUE → {resp}")
            self._list_jobs()
        self._run_async(_)

    def _set_criteria(self):
        criteria = self.ent_criteria.get().strip()
        if not criteria:
            return

        def _():
            resp = self._send(f"SET_CRITERIA\n{criteria}")
            self._log(f"SET_CRITERIA → {resp}")
        self._run_async(_)

    def _copy_submitted_id(self):
        # Copy job_id from submit tab entry to clipboard.
        job_id = self.ent_submitted_id.get()
        if not job_id:
            return
        self.clipboard_clear()
        self.clipboard_append(job_id)
        self._log(f"Job ID {job_id[:18]}... copiado para area de transferencia")

    def _on_job_select(self, event=None):
        # Fill result tab entry and clipboard with job_id from selected row.
        sel = self.tree.selection()
        if not sel:
            return
        job_id = str(self.tree.item(sel[0])["values"][0])
        self.ent_jobid.delete(0, "end")
        self.ent_jobid.insert(0, job_id)
        self.clipboard_clear()
        self.clipboard_append(job_id)
        self._log(f"Job {job_id[:18]}... copiado para area de transferencia")

    # ── Polling automático de status ───────────────────────────────────────

    def _poll_status(self):
        """Atualiza status a cada 5s se conectado."""
        if self.lbl_conn.cget("text") == "● conectado":
            self._get_status()
        self.after(5000, self._poll_status)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
