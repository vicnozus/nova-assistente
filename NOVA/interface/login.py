import customtkinter as ctk

from NOVA.database.users import autenticar_usuario, criar_usuario, inicializar_banco
from NOVA.interface.app import NovaApp
from NOVA.utils.paths import ICON_PATH


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        inicializar_banco()

        self.modo = "login"
        self.usuario_id = None
        self.usuario_nome = None

        self.title("Nova - Entrar")
        self.geometry("820x520")
        self.minsize(720, 480)
        self.configure(fg_color=("#f4f4f8", "#0b0b0f"))
        self._configurar_icone()
        self.criar_interface()

    def _configurar_icone(self):
        if ICON_PATH.exists():
            try:
                self.iconbitmap(str(ICON_PATH))
            except ctk.tkinter.TclError:
                pass

    def criar_interface(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        painel_marca = ctk.CTkFrame(self, corner_radius=0, fg_color=("#e9e7f2", "#050507"))
        painel_marca.grid(row=0, column=0, sticky="nsew")
        painel_marca.grid_columnconfigure(0, weight=1)
        painel_marca.grid_rowconfigure(0, weight=1)

        bloco_marca = ctk.CTkFrame(painel_marca, fg_color="transparent")
        bloco_marca.grid(row=0, column=0, sticky="nsew", padx=48, pady=48)
        bloco_marca.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            bloco_marca,
            text="Nova",
            font=("Segoe UI", 48, "bold"),
            text_color=("#2d123f", "#ffffff"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            bloco_marca,
            text="Sua assistente desktop",
            font=("Segoe UI", 18),
            text_color=("#5f526d", "#c9bdd4"),
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))
        ctk.CTkLabel(
            bloco_marca,
            text="Entre na sua conta para continuar.",
            font=("Segoe UI", 14),
            text_color=("#6d6077", "#a99fb1"),
        ).grid(row=3, column=0, sticky="sw")

        self.formulario = ctk.CTkFrame(self, corner_radius=0, fg_color=("#f4f4f8", "#0b0b0f"))
        self.formulario.grid(row=0, column=1, sticky="nsew", padx=44, pady=44)
        self.formulario.grid_columnconfigure(0, weight=1)

        self.seletor = ctk.CTkSegmentedButton(
            self.formulario,
            values=["Entrar", "Cadastro"],
            command=self.alterar_modo,
        )
        self.seletor.grid(row=0, column=0, sticky="ew", pady=(0, 28))
        self.seletor.set("Entrar")

        self.titulo = ctk.CTkLabel(
            self.formulario,
            text="Entrar",
            font=("Segoe UI", 28, "bold"),
            text_color=("#17171c", "#ffffff"),
        )
        self.titulo.grid(row=1, column=0, sticky="w", pady=(0, 18))

        self.nome = ctk.CTkEntry(self.formulario, placeholder_text="Nome", height=44)
        self.email = ctk.CTkEntry(self.formulario, placeholder_text="E-mail", height=44)
        self.senha = ctk.CTkEntry(self.formulario, placeholder_text="Senha", height=44, show="*")
        self.confirmar_senha = ctk.CTkEntry(
            self.formulario,
            placeholder_text="Confirmar senha",
            height=44,
            show="*",
        )

        for campo in (self.nome, self.email, self.senha, self.confirmar_senha):
            campo.bind("<Return>", self.enviar)

        self.mensagem = ctk.CTkLabel(
            self.formulario,
            text="",
            anchor="w",
            font=("Segoe UI", 13),
            text_color=("#7a1846", "#ffb4c8"),
        )

        self.botao = ctk.CTkButton(
            self.formulario,
            text="Entrar",
            height=44,
            font=("Segoe UI", 14, "bold"),
            command=self.enviar,
        )

        self.alterar_modo("Entrar")

    def alterar_modo(self, valor):
        self.modo = "cadastro" if valor == "Cadastro" else "login"
        self.mensagem.configure(text="")

        for campo in (self.nome, self.email, self.senha, self.confirmar_senha, self.mensagem, self.botao):
            campo.grid_forget()

        self.titulo.configure(text="Criar conta" if self.modo == "cadastro" else "Entrar")
        linha = 2

        if self.modo == "cadastro":
            self.nome.grid(row=linha, column=0, sticky="ew", pady=(0, 12))
            linha += 1

        self.email.grid(row=linha, column=0, sticky="ew", pady=(0, 12))
        linha += 1
        self.senha.grid(row=linha, column=0, sticky="ew", pady=(0, 12))
        linha += 1

        if self.modo == "cadastro":
            self.confirmar_senha.grid(row=linha, column=0, sticky="ew", pady=(0, 12))
            linha += 1

        self.mensagem.grid(row=linha, column=0, sticky="ew", pady=(2, 14))
        self.botao.configure(text="Criar conta" if self.modo == "cadastro" else "Entrar")
        self.botao.grid(row=linha + 1, column=0, sticky="ew")

    def enviar(self, event=None):
        email = self.email.get()
        senha = self.senha.get()

        if self.modo == "cadastro":
            if senha != self.confirmar_senha.get():
                self.exibir_mensagem("As senhas nao conferem.", erro=True)
                return

            sucesso, mensagem = criar_usuario(self.nome.get(), email, senha)
            self.exibir_mensagem(mensagem, erro=not sucesso)
            if sucesso:
                self.seletor.set("Entrar")
                self.alterar_modo("Entrar")
                self.email.delete(0, "end")
                self.email.insert(0, email)
                self.senha.delete(0, "end")
            return

        sucesso, mensagem, usuario_id, nome = autenticar_usuario(email, senha)
        self.exibir_mensagem(mensagem, erro=not sucesso)
        if sucesso:
            self.usuario_id = usuario_id
            self.usuario_nome = nome
            self.after(250, self.abrir_nova)

    def exibir_mensagem(self, texto, erro=True):
        cor = ("#7a1846", "#ffb4c8") if erro else ("#236b38", "#94e4a8")
        self.mensagem.configure(text=texto, text_color=cor)

    def abrir_nova(self):
        nome = self.usuario_nome or "Usuario"

        self.destroy()

        app = NovaApp(
            usuario_id=self.usuario_id,
            usuario_nome=nome,
        )

        app.mainloop()


if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()
