def subtrair_e_multiplicar_por_dois(a, b):
    return (a - b) * 2

def calcular_media(numeros):
    if not numeros:
        return 0.0
    return sum(numeros) / len(numeros)

if __name__ == "__main__":
    print("Olá Mundo")
    resultado = subtrair_e_multiplicar_por_dois(10, 4)
    print(f"Resultado: {resultado}")
    
    valores_teste = [10, 20, 30, 40, 50]
    media = calcular_media(valores_teste)
    print(f"Média de {valores_teste}: {media}")
