from typing import List


def read_int(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Valor inválido! Digite um número inteiro.")

def read_positive_int(prompt: str) -> int:
    while True:
        try:
            value = int(input(prompt))
        except ValueError:
            print("Valor inválido! Digite um número inteiro.")
            continue

        if value < 0:
            print("Valor inválido! Digite um número inteiro não negativo.")
            continue

        return value

def read_option(prompt: str, options: List[int]) -> int:
    while True:
        try:
            value = int(input(prompt))
        except ValueError:
            print("Valor inválido! Digite um número inteiro.")
            continue

        if value in options:
            return value

        print(f"Valor inválido! Escolha uma das opções: {options}")
        continue
