"""Cálculo de quantidade de rolos e valores do orçamento."""
from __future__ import annotations

import math
from dataclasses import dataclass

SOBRA_CORTE_M = 0.10  # margem de corte por faixa (5 cm em cima + 5 cm embaixo)


@dataclass
class Parede:
    descricao: str
    largura_m: float
    altura_m: float
    descontos_m2: float = 0.0  # portas/janelas que NÃO serão revestidas

    @property
    def area_m2(self) -> float:
        return max(self.largura_m * self.altura_m - self.descontos_m2, 0)


@dataclass
class Papel:
    codigo: str
    nome: str
    colecao: str
    cor_principal: str
    cor_secundaria: str
    largura_m: float
    comprimento_m: float
    rapport_cm: float
    preco_rolo: float


def faixas_por_rolo(papel: Papel, altura_m: float) -> int:
    """Quantas faixas inteiras saem de um rolo, considerando o rapport (repetição da estampa)."""
    rapport = papel.rapport_cm / 100
    altura_faixa = altura_m + SOBRA_CORTE_M
    if rapport > 0:  # cada faixa precisa começar no mesmo ponto da estampa
        altura_faixa = math.ceil(altura_faixa / rapport) * rapport
    return int(papel.comprimento_m // altura_faixa)


def rolos_necessarios(papel: Papel, paredes: list[Parede]) -> int:
    """Calcula por parede (faixas não se aproveitam entre alturas diferentes de forma confiável)."""
    total_faixas_por_altura: dict[float, int] = {}
    for p in paredes:
        faixas = math.ceil(p.largura_m / papel.largura_m)
        total_faixas_por_altura[p.altura_m] = total_faixas_por_altura.get(p.altura_m, 0) + faixas
    rolos = 0
    for altura, faixas in total_faixas_por_altura.items():
        por_rolo = faixas_por_rolo(papel, altura)
        if por_rolo == 0:
            raise ValueError(f"Altura {altura} m maior que o rolo de {papel.comprimento_m} m")
        rolos += math.ceil(faixas / por_rolo)
    return rolos


@dataclass
class Orcamento:
    rolos: int
    area_m2: float
    valor_papel: float
    valor_mao_de_obra: float
    frete: float

    @property
    def total(self) -> float:
        return round(self.valor_papel + self.valor_mao_de_obra + self.frete, 2)


def calcular(papel: Papel, paredes: list[Parede], mao_de_obra_m2: float = 0.0, frete: float = 0.0) -> Orcamento:
    rolos = rolos_necessarios(papel, paredes)
    area = round(sum(p.area_m2 for p in paredes), 2)
    return Orcamento(rolos, area, round(rolos * papel.preco_rolo, 2), round(area * mao_de_obra_m2, 2), frete)


def brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
