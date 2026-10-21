import threading
from queue import Empty, Queue

import customtkinter as ctk

from PIL import Image
from NOVA.interface.theme import *
from NOVA.commands.actions import criar_arquivo_texto, preparar_nome_arquivo, processar_comando
from NOVA.database.conversas import criar_conversa, listar_conversas_do_usuario
from NOVA.database.mensagens import criar_mensagem, listar_mensagens_da_conversa
from NOVA.models.intent import interpretar_local
from NOVA.utils.paths import DARK_PURPLE_THEME_PATH, ICON_PATH

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme(str(DARK_PURPLE_THEME_PATH))


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

        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=("#e7e7ed", "#111118"), corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)
        
                # Logo / identidade da Nova
        self.logo_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        self.logo_frame.pack(
            fill="x",
            padx=18,
            pady=(24, 20)
        )

        self.logo_img = ctk.CTkImage(
            light_image=Image.open("Nova/assets/nova.png"),
            dark_image=Image.open("Nova/assets/nova.png"),
            size=(40, 40)
        )

        self.logo = ctk.CTkLabel(
            self.logo_frame,
            text="",
            image=self.logo_img
        )

        self.logo.pack(
            side="left"
        )

        self.logo_texto = ctk.CTkLabel(
            self.logo_frame,
            text="NOVA",
            font=("Segoe UI", 18, "bold"),
            text_color=TEXT_PRIMARY
        )

        self.logo_texto.pack(
            side="left",
            padx=(10, 0)
        )

                # Ícones da navegação
        self.icon_chat = ctk.CTkImage(
            light_image=Image.open("Nova/assets/icons/chat.png"),
            dark_image=Image.open("Nova/assets/icons/chat.png"),
            size=(22, 22)
        )

        self.icon_history = ctk.CTkImage(
            light_image=Image.open("Nova/assets/icons/history.png"),
            dark_image=Image.open("Nova/assets/icons/history.png"),
            size=(22, 22)
        )

        self.icon_settings = ctk.CTkImage(
            light_image=Image.open("Nova/assets/icons/settings.png"),
            dark_image=Image.open("Nova/assets/icons/settings.png"),
            size=(22, 22)
        )

        self.btn_chat = ctk.CTkButton(
            self.sidebar,
            text="Conversa",
            image=self.icon_chat,
            compound="left",
            anchor="w",
            height=42,
            corner_radius=8,
            fg_color="transparent",
            hover_color=NAV_HOVER,
            text_color=TEXT_SECONDARY,
            command=self.mostrar_chat,
        )

        self.btn_historico = ctk.CTkButton(
            self.sidebar,
            text="Histórico",
            image=self.icon_history,
            compound="left",
            anchor="w",
            height=42,
            corner_radius=8,
            fg_color="transparent",
            hover_color=NAV_HOVER,
            text_color=TEXT_SECONDARY,
            command=self.mostrar_historico,
        )

        self.btn_config = ctk.CTkButton(
            self.sidebar,
            text="Configurações",
            image=self.icon_settings,
            compound="left",
            anchor="w",
            height=42,
            corner_radius=8,
            fg_color="transparent",
            hover_color=NAV_HOVER,
            text_color=TEXT_SECONDARY,
            command=self.mostrar_configuracoes,
        )


        self.btn_nova_conversa = ctk.CTkButton(
            self.sidebar,
            text="+  Nova conversa",
            anchor="w",
            height=42,
            corner_radius=10,

            fg_color=PURPLE,
            hover_color=PURPLE_HOVER,

            text_color="white",

            command=self.nova_conversa
        )

        self.btn_nova_conversa.pack(
            fill="x",
            padx=12,
            pady=(0, 18)
        )


        for botao in (self.btn_chat, self.btn_historico, self.btn_config):
            botao.pack(
                fill="x",
                padx=10,
                pady=2
            )

        # =========================
        # RODAPÉ DA SIDEBAR
        # =========================

        self.sidebar_footer = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )

        self.sidebar_footer.pack(
            side="bottom",
            fill="x",
            padx=14,
            pady=16
        )

        # Linha divisória
        self.footer_divider = ctk.CTkFrame(
            self.sidebar_footer,
            height=1,
            fg_color=("#cccccc", "#292933")
        )

        self.footer_divider.pack(
            fill="x",
            pady=(0, 14)
        )

        # Status
        self.footer_status = ctk.CTkLabel(
            self.sidebar_footer,
            text="●  Nova online",
            font=("Segoe UI", 12),
            text_color=("#6d28d9", "#a970ff"),
            anchor="w"
        )

        self.footer_status.pack(
            fill="x"
        )

        # Usuário
        self.footer_usuario = ctk.CTkLabel(
            self.sidebar_footer,
            text=self.usuario_nome,
            font=("Segoe UI", 13, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w"
        )

        self.footer_usuario.pack(
            fill="x",
            pady=(4, 0)
        )

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
                    fg_color=("#e9ddff", "#24162e"),
                    text_color=("#6d28d9", "#ffffff"),
                )
            else:
                botao.configure(
                    fg_color="transparent",
                    text_color=TEXT_SECONDARY,
                )

    def mostrar_chat(self, conversa_id=None):
        self.atualizar_menu("chat")
        self.limpar_main()

        if conversa_id is not None:
            if conversa_id != self.conversa_id_atual:
                self.aguardando_arquivo = False
                self.nome_arquivo = ""
            self.conversa_id_atual = conversa_id
        conversa_id = self.conversa_id_atual

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

        self.chat = ctk.CTkScrollableFrame(
            self.main,
            fg_color="transparent",
            corner_radius=0,
        )

        self.chat.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        self.chat.grid_columnconfigure(0, weight=1)

        if conversa_id is None:
            self.adicionar_mensagem(
                "nova",
                "Sistema iniciado com sucesso."
            )

        else:
            mensagens = listar_mensagens_da_conversa(conversa_id)

            for mensagem in mensagens:
                remetente = mensagem["remetente"]
                conteudo = mensagem["conteudo"]

                self.adicionar_mensagem(
                    remetente,
                    conteudo
                )


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
            placeholder_text="Digite uma mensagem para a Nova...",
            height=46,
            corner_radius=12,
            fg_color=INPUT_BG,
            border_color=INPUT_BORDER,
            border_width=1,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_SECONDARY,
        )

        self.entrada.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 10)
        )

        self.entrada.bind("<Return>", self.enviar_comando)

        self.btn_enviar = ctk.CTkButton(
            input_frame,
            text="➤",
            width=60,
            height=46,
            corner_radius=12,
            fg_color=PURPLE,
            hover_color=PURPLE_HOVER,
            command=self.enviar_comando,
        )

        self.btn_enviar.grid(
            row=0,
            column=1,
        )

        if self.processando:
            self.entrada.configure(state="disabled")
            self.btn_enviar.configure(state="disabled")

    def adicionar_mensagem(self, remetente, conteudo):

        # Uma linha ocupa toda a largura do chat
        linha = ctk.CTkFrame(
            self.chat,
            fg_color="transparent"
        )

        linha.pack(
            fill="x",
            padx=8,
            pady=6
        )

        # =========================
        # USUÁRIO
        # =========================
        if remetente == "usuario":

            mensagem = ctk.CTkLabel(
                linha,
                text=conteudo,
                font=("Segoe UI", 14),
                text_color="#ffffff",
                fg_color=("#7c3aed", "#5b21b6"),
                corner_radius=14,
                anchor="w",
                justify="left",
                wraplength=550,
            )

            mensagem.pack(
                side="right",
                padx=(120, 5),
                ipadx=12,
                ipady=8
            )

        # =========================
        # NOVA
        # =========================
        else:

            bloco_nova = ctk.CTkFrame(
                linha,
                fg_color="transparent"
            )

            bloco_nova.pack(
                side="left",
                padx=(5, 120)
            )

            nome = ctk.CTkLabel(
                bloco_nova,
                text="Nova",
                font=("Segoe UI", 12, "bold"),
                text_color=("#6d28d9", "#a970ff"),
                anchor="w"
            )

            nome.pack(
                anchor="w",
                pady=(0, 3)
            )

            mensagem = ctk.CTkLabel(
                bloco_nova,
                text=conteudo,
                font=("Segoe UI", 14),
                text_color=TEXT_PRIMARY,
                anchor="w",
                justify="left",
                wraplength=650
            )

            mensagem.pack(
                anchor="w"
            )
            
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
            conversa_id = conversa["id"]


            card = ctk.CTkFrame(
                historico_frame,
                fg_color=("#ffffff", "#15151c"),
                corner_radius=15,
                cursor="hand2",
            )

            card.grid(
                row=i,
                column=0,
                sticky="ew",
                padx=5,
                pady=(0, 10),
            )

            card.grid_columnconfigure(0, weight=1)

            card.bind(
                "<Button-1>",
                lambda event, cid=conversa_id: self.abrir_conversa(cid)
            )

                    # Título
            titulo = ctk.CTkLabel(
                card,
                text=conversa["assunto"],
                font=("Segoe UI", 15, "bold"),
                anchor="w",
            )

            titulo.grid(
                row=0,
                column=0,
                sticky="ew",
                padx=18,
                pady=(14, 2),
            )

            # Data
            data = ctk.CTkLabel(
                card,
                text=f"Iniciada em: {conversa['data_inicio']}",
                font=("Segoe UI", 12),
                text_color="gray",
                anchor="w",
            )

            data.grid(
                row=1,
                column=0,
                sticky="ew",
                padx=18,
                pady=(0, 14),
            )

            # Clique
            abrir = lambda event, cid=conversa_id: self.abrir_conversa(cid)

            card.bind("<Button-1>", abrir)
            titulo.bind("<Button-1>", abrir)
            data.bind("<Button-1>", abrir)

    def abrir_conversa(self, conversa_id):
        self.mostrar_chat(conversa_id)

    def nova_conversa(self):
        self.conversa_id_atual = None
        self.mostrar_chat()

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

    def escrever_chat(self, remetente, conteudo):
        if not hasattr(self, "chat") or not self.chat.winfo_exists():
            return

        self.adicionar_mensagem(remetente, conteudo)

        self.chat.update_idletasks()
        self.chat._parent_canvas.yview_moveto(1.0)

    def concluir_processamento(self, resposta, conversa_id=None):
        self.processando = False
        if conversa_id is None:
            conversa_id = self.conversa_id_atual

        criar_mensagem(
            conversa_id=conversa_id,
            remetente="nova",
            conteudo=resposta,
        )

        if hasattr(self, "entrada") and self.entrada.winfo_exists():
            self.entrada.configure(state="normal")
            self.btn_enviar.configure(state="normal")
            self.entrada.focus()

        if conversa_id == self.conversa_id_atual:
            self.escrever_chat("nova", resposta)

    def verificar_resultados(self):
        try:
            while True:
                conversa_id, resposta = self.resultados.get_nowait()
                self.concluir_processamento(resposta, conversa_id)
        except Empty:
            pass
        self.after(100, self.verificar_resultados)

    def executar_comando_em_segundo_plano(self, comando):
        conversa_id = self.conversa_id_atual

        def tarefa():
            try:
                resposta = processar_comando(comando)
            except Exception as erro:
                print(f"[ERRO] Comando: {comando}")
                print(f"[ERRO] {type(erro).__name__}: {erro}")
                resposta = "Ocorreu um erro ao executar esse comando."

            self.resultados.put((conversa_id, resposta))

        self.processando = True
        self.entrada.configure(state="disabled")
        self.btn_enviar.configure(state="disabled")
        threading.Thread(target=tarefa, daemon=True).start()

    def enviar_comando(self, event=None):
        if self.processando:
            return
        comando = self.entrada.get().strip()
        if not comando:
            return

        self.entrada.delete(0, "end")
        self.historico_comandos.append(comando)
        self.escrever_chat("usuario", comando)

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
            self.concluir_processamento(resposta)
            return

        intencao = interpretar_local(comando)
        if intencao and intencao["acao"] == "criar_arquivo":
            try:
                self.nome_arquivo = preparar_nome_arquivo(intencao["valor"]).name
            except ValueError as erro:
                self.concluir_processamento(str(erro))
                return
            self.aguardando_arquivo = True
            self.concluir_processamento(f"O que deseja escrever em '{self.nome_arquivo}'?")
            return

        self.executar_comando_em_segundo_plano(comando)


if __name__ == "__main__":
    app = NovaApp()
    app.mainloop()
