import pytest

from orcamento.calculo import (
    Papel,
    Parede,
    brl,
    calcular,
    faixas_por_rolo,
    rolos_necessarios,
)
from orcamento.gerar import carregar_catalogo, mensagem_whatsapp

LISO = Papel("X", "Liso", "T", "#fff", "#000", 0.53, 10, 0, 100.0)
ESTAMPADO = Papel("Y", "Estampa grande", "T", "#fff", "#000", 0.53, 10, 90, 100.0)


def test_faixas_por_rolo_liso():
    assert faixas_por_rolo(LISO, 2.7) == 3      # 10 // 2.8


def test_faixas_por_rolo_com_rapport():
    assert faixas_por_rolo(ESTAMPADO, 2.7) == 2  # 2.8 m vira 3.6 m (4 x 90 cm)


def test_rolos_parede_tv():
    # 3.2 m / 0.53 = 7 faixas -> liso: ceil(7/3)=3 rolos ; estampado: ceil(7/2)=4 rolos
    paredes = [Parede("TV", 3.2, 2.7)]
    assert rolos_necessarios(LISO, paredes) == 3
    assert rolos_necessarios(ESTAMPADO, paredes) == 4


def test_altura_maior_que_rolo():
    with pytest.raises(ValueError):
        rolos_necessarios(LISO, [Parede("pé-direito duplo", 2, 11)])


def test_orcamento_total():
    o = calcular(LISO, [Parede("A", 3.2, 2.7, descontos_m2=1.64)], mao_de_obra_m2=25, frete=40)
    assert o.area_m2 == pytest.approx(7.0)
    assert o.total == pytest.approx(3 * 100 + 7 * 25 + 40)


def test_brl():
    assert brl(1234.5) == "R$ 1.234,50"


def test_catalogo_e_mensagem():
    papel = carregar_catalogo()["PP-203"]
    o = calcular(papel, [Parede("A", 3.2, 2.7)])
    msg = mensagem_whatsapp("Maria Exemplo", papel, o, 15)
    assert "Maria" in msg and "Folhagem Tropical" in msg and brl(o.total) in msg
