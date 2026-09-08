import threading
from queue import Empty, Queue

import customtkinter as ctk

from NOVA.commands.actions import criar_arquivo_texto, preparar_nome_arquivo, processar_comando
from NOVA.database.conversas import criar_conversa, listar_conversas_do_usuario
from NOVA.database.mensagens import criar_mensagem, listar_mensagens_da_conversa
from NOVA.models.intent import interpretar_local
from NOVA.utils.paths import ICON_PATH

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class NovaApp(ctk.CTk):
    def __init__(self, usuario_id, usuario_nome="Usuario"):
        self.aguardando_arquivo = False
        self.nome_arquivo = ""
        self.historico_comandos = []
        self.modo_atual = "dark"
        self.processando = False
        self.resultados = Queue()
        self.usuario_id = usuario_id
        self.usuario_nome = usuario_nome
        self.conversa_id_atual = None

        super().__init__()

        self.title("Nova")
        self.configurar_icone()
        self.geometry("1200x650")
        self.minsize(800, 650)
        self.criar_interface()
        self.after(100, self.verificar_resultados)

    def configurar_icone(self):
        if ICON_PATH.exists():
            try:
                self.iconbitmap(str(ICON_PATH))
            except ctk.tkinter.TclError:
                pass

    def criar_interface(self):
        self.configure(fg_color=("#f4f4f8", "#0b0b0f"))
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=("#e7e7ed", "#000000"), corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)

        self.logo = ctk.CTkLabel(
        self.sidebar,
        text="◉",
        font=("Segoe UI", 32),
        text_color="#ab19ff"
        )
        self.logo.pack(pady=(25, 20))
        self.btn_chat = ctk.CTkButton(
        self.sidebar,
        text="💬  Conversa",
        anchor="w",
        height=42,
        corner_radius=0,
        fg_color="transparent",
        hover_color=("#ddddE8", "#241528"),
        text_color=("#333333", "#dddddd"),
        command=self.mostrar_chat,
    )

        self.btn_historico = ctk.CTkButton(
            self.sidebar,
            text="◷  Histórico",
            anchor="w",
            height=42,
            corner_radius=0,
            fg_color="transparent",
            hover_color=("#ddddE8", "#1f1f2a"),
            text_color=("#333333", "#aaaaaa"),
            command=self.mostrar_historico,
        )

        self.btn_config = ctk.CTkButton(
            self.sidebar,
            text="⚙  Configurações",
            anchor="w",
            height=42,
            corner_radius=0,
            fg_color="transparent",
            hover_color=("#ddddE8", "#1f1f2a"),
            text_color=("#333333", "#aaaaaa"),
            command=self.mostrar_configuracoes,
        )

        for botao in (self.btn_chat, self.btn_historico, self.btn_config):
            botao.pack(fill="x", padx=0, pady=2)

        self.main = ctk.CTkFrame(
            self,
            fg_color=("#f4f4f8", "#0b0b0f"),
            corner_radius=0,
        )
        self.main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.mostrar_chat()

    def limpar_main(self):
        for widget in self.main.winfo_children():
            widget.destroy()

    def atualizar_menu(self, ativo):
        for nome, botao in (
            ("chat", self.btn_chat),
            ("historico", self.btn_historico),
            ("config", self.btn_config),
        ):
            if nome == ativo:
                botao.configure(
                    fg_color=("#eadfff", "#2a102f"),
                    text_color=("#58008b", "#ffffff"),
                )
            else:
                botao.configure(
                    fg_color="transparent",
                    text_color=("#555555", "#aaaaaa"),
                )

    def mostrar_chat(self, conversa_id=None):
        self.atualizar_menu("chat")
        self.limpar_main()

        if conversa_id is not None:
            self.conversa_id_atual = conversa_id

        ctk.CTkLabel(
            self.main,
            text=f"Olá, {self.usuario_nome}.\nO que vamos fazer hoje?",
            font=("Segoe UI", 24, "bold"),
            text_color=("#17171c", "#ffffff"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 15),
        )

        self.chat = ctk.CTkTextbox(
            self.main,
            fg_color=("#ffffff", "#15151c"),
            text_color=("#17171c", "#eeeeee"),
            corner_radius=15,
            font=("Segoe UI", 14),
        )

        self.chat.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        if conversa_id is None:
            self.chat.insert(
                "end",
                "Nova: Sistema iniciado com sucesso.\n\n"
            )

        else:
            mensagens = listar_mensagens_da_conversa(conversa_id)

            for mensagem in mensagens:
                remetente = mensagem["remetente"]
                conteudo = mensagem["conteudo"]

                self.chat.insert(
                    "end",
                    f"{remetente}: {conteudo}\n\n"
                )

        self.chat.configure(state="disabled")

        input_frame = ctk.CTkFrame(
            self.main,
            fg_color="transparent",
        )

        input_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(15, 0),
        )

        input_frame.grid_columnconfigure(0, weight=1)

        self.entrada = ctk.CTkEntry(
            input_frame,
            placeholder_text="Digite um comando... ex: pesquise Hollow Knight",
            height=45,
            font=("Segoe UI", 14),
        )

        self.entrada.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 10),
        )

        self.entrada.bind("<Return>", self.enviar_comando)

        self.botao = ctk.CTkButton(
            input_frame,
            text="Enviar",
            height=45,
            font=("Segoe UI", 14, "bold"),
            command=self.enviar_comando,
        )

        self.botao.grid(
            row=0,
            column=1,
        )

        if self.processando:
            self.entrada.configure(state="disabled")
            self.botao.configure(state="disabled")

    def mostrar_historico(self):
        self.atualizar_menu("historico")
        self.limpar_main()

        ctk.CTkLabel(
            self.main,
            text="Histórico de conversas",
            font=("Segoe UI", 24, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 15)
        )

        historico_frame = ctk.CTkScrollableFrame(
            self.main,
            fg_color="transparent",
        )

        historico_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        historico_frame.grid_columnconfigure(0, weight=1)

        conversas = listar_conversas_do_usuario(self.usuario_id)

        if not conversas:
            ctk.CTkLabel(
                historico_frame,
                text="Nenhuma conversa encontrada.",
                font=("Segoe UI", 14),
                text_color="gray",
            ).grid(
                row=0,
                column=0,
                sticky="w",
                padx=10,
                pady=10
            )

            return

        for i, conversa in enumerate(conversas):

            card = ctk.CTkFrame(
                historico_frame,
                fg_color=("#ffffff", "#15151c"),
                corner_radius=15,
            )

            card.grid(
                row=i,
                column=0,
                sticky="ew",
                padx=5,
                pady=(0, 10),
            )

            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                card,
                text=conversa["assunto"],
                font=("Segoe UI", 15, "bold"),
                anchor="w",
            ).grid(
                row=0,
                column=0,
                sticky="ew",
                padx=18,
                pady=(14, 2),
            )

            ctk.CTkLabel(
                card,
                text=f"Iniciada em: {conversa['data_inicio']}",
                font=("Segoe UI", 12),
                text_color="gray",
                anchor="w",
            ).grid(
                row=1,
                column=0,
                sticky="ew",
                padx=18,
                pady=(0, 14),
            )

    def mostrar_configuracoes(self):
        self.atualizar_menu("config")
        self.limpar_main()

        ctk.CTkLabel(
            self.main,
            text="Configurações",
            font=("Segoe UI", 24, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 20),
        )

        # =========================
        # APARÊNCIA
        # =========================

        aparencia_card = ctk.CTkFrame(
            self.main,
            fg_color=("#ffffff", "#15151c"),
            corner_radius=15,
        )

        aparencia_card.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(0, 15),
        )

        aparencia_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            aparencia_card,
            text="Aparência",
            font=("Segoe UI", 16, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=18,
            pady=(15, 3),
        )

        ctk.CTkLabel(
            aparencia_card,
            text="Escolha como a Nova aparece para você.",
            font=("Segoe UI", 12),
            text_color="gray",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=18,
            pady=(0, 12),
        )

        self.switch_modo = ctk.CTkSwitch(
            aparencia_card,
            text="Modo claro",
            command=self.alternar_modo,
        )

        self.switch_modo.grid(
            row=2,
            column=0,
            sticky="w",
            padx=18,
            pady=(0, 15),
        )

        if self.modo_atual == "light":
            self.switch_modo.select()

        # =========================
        # CONTA
        # =========================

        conta_card = ctk.CTkFrame(
            self.main,
            fg_color=("#ffffff", "#15151c"),
            corner_radius=15,
        )

        conta_card.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 15),
        )

        conta_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            conta_card,
            text="Conta",
            font=("Segoe UI", 16, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=18,
            pady=(15, 3),
        )

        ctk.CTkLabel(
            conta_card,
            text=f"Conectado como {self.usuario_nome}",
            font=("Segoe UI", 13),
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=18,
            pady=(0, 4),
        )

        ctk.CTkLabel(
            conta_card,
            text="Sua conta mantém suas conversas separadas dos outros usuários.",
            font=("Segoe UI", 12),
            text_color="gray",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=18,
            pady=(0, 15),
        )

        # =========================
        # NOVA
        # =========================

        nova_card = ctk.CTkFrame(
            self.main,
            fg_color=("#ffffff", "#15151c"),
            corner_radius=15,
        )

        nova_card.grid(
            row=3,
            column=0,
            sticky="ew",
        )

        ctk.CTkLabel(
            nova_card,
            text="Nova",
            font=("Segoe UI", 16, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=18,
            pady=(15, 3),
        )

        ctk.CTkLabel(
            nova_card,
            text="Mais opções da assistente serão adicionadas aqui.",
            font=("Segoe UI", 12),
            text_color="gray",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=18,
            pady=(0, 15),
        )

    def alternar_modo(self):
        self.modo_atual = "light" if self.switch_modo.get() else "dark"
        ctk.set_appearance_mode(self.modo_atual)

    def escrever_chat(self, texto):
        if not hasattr(self, "chat") or not self.chat.winfo_exists():
            return
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{texto}\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def concluir_processamento(self, resposta):
        self.processando = False

        criar_mensagem(
            conversa_id=self.conversa_id_atual,
            remetente="nova",
            conteudo=resposta,
        )

        if hasattr(self, "entrada") and self.entrada.winfo_exists():
            self.entrada.configure(state="normal")
            self.botao.configure(state="normal")
            self.entrada.focus()

        self.escrever_chat(f"Nova: {resposta}")

    def verificar_resultados(self):
        try:
            while True:
                self.concluir_processamento(self.resultados.get_nowait())
        except Empty:
            pass
        self.after(100, self.verificar_resultados)

    def executar_comando_em_segundo_plano(self, comando):
        def tarefa():
            try:
                resposta = processar_comando(comando)
            except Exception as erro:
                print(f"[ERRO] Comando: {comando}")
                print(f"[ERRO] {type(erro).__name__}: {erro}")
                resposta = "Ocorreu um erro ao executar esse comando."

            self.resultados.put(resposta)

        self.processando = True
        self.entrada.configure(state="disabled")
        self.botao.configure(state="disabled")
        threading.Thread(target=tarefa, daemon=True).start()

    def enviar_comando(self, event=None):
        if self.processando:
            return
        comando = self.entrada.get().strip()
        if not comando:
            return

        self.entrada.delete(0, "end")
        self.historico_comandos.append(comando)
        self.escrever_chat(f"Você: {comando}")
        
        if self.conversa_id_atual is None:
            self.conversa_id_atual = criar_conversa(
                usuario_id=self.usuario_id,
                assunto=comando,
            )

        criar_mensagem(
                conversa_id=self.conversa_id_atual,
                remetente="usuario",
                conteudo=comando,
            )

        # O conteúdo é sempre salvo antes de tentar interpretar um novo comando.
        if self.aguardando_arquivo:
            resposta = criar_arquivo_texto(self.nome_arquivo, comando)
            self.aguardando_arquivo = False
            self.nome_arquivo = ""
            self.escrever_chat(f"Nova: {resposta}")
            return

        intencao = interpretar_local(comando)
        if intencao and intencao["acao"] == "criar_arquivo":
            try:
                self.nome_arquivo = preparar_nome_arquivo(intencao["valor"]).name
            except ValueError as erro:
                self.escrever_chat(f"Nova: {erro}")
                return
            self.aguardando_arquivo = True
            self.escrever_chat(f"Nova: O que deseja escrever em '{self.nome_arquivo}'?")
            return

        self.executar_comando_em_segundo_plano(comando)


if __name__ == "__main__":
    app = NovaApp()
    app.mainloop()
