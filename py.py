import hashlib

hash_original = "acec81120f96f4df43da90b43d00d4675a73bf539326563db94d1b79c305fe97"

senha = input("Digite uma possível senha: ")

hash_teste = hashlib.sha256(senha.encode()).hexdigest()

if hash_teste == hash_original:
    print("Senha encontrada!")
else:
    print("Senha incorreta!")