"""Gera o orçamento em PDF (com amostra de cores do papel) e a mensagem pronta para WhatsApp.

Uso:
    python -m orcamento.gerar exemplos/pedido.json
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from .calculo import Orcamento, Papel, Parede, brl, calcular

RAIZ = Path(__file__).resolve().parents[1]
LOJA = "Sua Loja de Papel de Parede"  # troque pelo nome da loja


def carregar_catalogo(caminho: Path = RAIZ / "exemplos" / "catalogo.csv") -> dict[str, Papel]:
    with open(caminho, encoding="utf-8") as f:
        return {
            r["codigo"]: Papel(r["codigo"], r["nome"], r["colecao"], r["cor_principal"], r["cor_secundaria"],
                               float(r["largura_m"]), float(r["comprimento_m"]), float(r["rapport_cm"]), float(r["preco_rolo"]))
            for r in csv.DictReader(f)
        }


def cor_texto(hex_fundo: str):
    """Texto branco em fundo escuro e grafite em fundo claro (legibilidade)."""
    r, g, b = (int(hex_fundo.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    return colors.white if (0.299 * r + 0.587 * g + 0.114 * b) < 150 else colors.HexColor("#333333")


def mensagem_whatsapp(cliente: str, papel: Papel, orc: Orcamento, prazo: int) -> str:
    return (
        f"Olá, {cliente.split()[0]}! Segue seu orçamento 😊\n\n"
        f"🧻 *{papel.nome}* ({papel.codigo}), coleção {papel.colecao}\n"
        f"📐 Área: {orc.area_m2:.2f} m² · *{orc.rolos} rolo(s)*\n"
        f"💰 Papel: {brl(orc.valor_papel)}\n"
        + (f"🛠️ Instalação: {brl(orc.valor_mao_de_obra)}\n" if orc.valor_mao_de_obra else "")
        + (f"🚚 Frete: {brl(orc.frete)}\n" if orc.frete else "")
        + f"\n*Total: {brl(orc.total)}*\n"
        f"📦 Produto sob encomenda, prazo de {prazo} dias úteis.\n"
        f"Orçamento válido por 7 dias. Posso confirmar o pedido?"
    )


def gerar_pdf(destino: Path, pedido: dict, papel: Papel, paredes: list[Parede], orc: Orcamento) -> Path:
    c = canvas.Canvas(str(destino), pagesize=A4)
    w, h = A4
    c.setFillColor(colors.HexColor(papel.cor_principal)); c.rect(0, h - 3 * cm, w, 3 * cm, fill=1, stroke=0)
    c.setFillColor(cor_texto(papel.cor_principal)); c.setFont("Helvetica-Bold", 20); c.drawString(2 * cm, h - 1.9 * cm, LOJA)
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, h - 4.2 * cm, "Orçamento")
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, h - 4.9 * cm, f"Cliente: {pedido['cliente']}   ·   Data: {date.today():%d/%m/%Y}   ·   Validade: {(date.today() + timedelta(days=7)):%d/%m/%Y}")

    # Amostra de cores
    y = h - 7.5 * cm
    c.setFont("Helvetica-Bold", 11); c.drawString(2 * cm, y + 1.6 * cm, f"{papel.nome} ({papel.codigo}), coleção {papel.colecao}")
    for i, cor in enumerate([papel.cor_principal, papel.cor_secundaria]):
        c.setFillColor(colors.HexColor(cor)); c.setStrokeColor(colors.grey)
        c.rect(2 * cm + i * 3.2 * cm, y - 0.6 * cm, 2.8 * cm, 1.8 * cm, fill=1, stroke=1)
        c.setFillColor(colors.black); c.setFont("Helvetica", 8)
        c.drawString(2 * cm + i * 3.2 * cm, y - 1.0 * cm, ("Principal " if i == 0 else "Secundária ") + cor)

    # Tabela de paredes
    y -= 2.4 * cm
    c.setFont("Helvetica-Bold", 10)
    for x, t in [(2, "Parede"), (9, "Largura"), (11.5, "Altura"), (14, "Área (m2)")]:
        c.drawString(x * cm, y, t)
    c.setFont("Helvetica", 10)
    for p in paredes:
        y -= 0.6 * cm
        for x, t in [(2, p.descricao), (9, f"{p.largura_m:.2f} m"), (11.5, f"{p.altura_m:.2f} m"), (14, f"{p.area_m2:.2f}")]:
            c.drawString(x * cm, y, t)

    # Totais
    y -= 1.2 * cm
    linhas = [(f"Papel: {orc.rolos} rolo(s) x {brl(papel.preco_rolo)}", orc.valor_papel)]
    if orc.valor_mao_de_obra:
        linhas.append((f"Instalação: {orc.area_m2:.2f} m2", orc.valor_mao_de_obra))
    if orc.frete:
        linhas.append(("Frete", orc.frete))
    for txt, val in linhas:
        c.drawString(2 * cm, y, txt); c.drawRightString(w - 2 * cm, y, brl(val)); y -= 0.6 * cm
    c.line(2 * cm, y + 0.3 * cm, w - 2 * cm, y + 0.3 * cm)
    c.setFont("Helvetica-Bold", 13); c.drawString(2 * cm, y - 0.3 * cm, "Total"); c.drawRightString(w - 2 * cm, y - 0.3 * cm, brl(orc.total))
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(2 * cm, 2 * cm, f"Produto sob encomenda · prazo de {pedido.get('prazo_dias_uteis', 15)} dias úteis após confirmação.")
    c.save()
    return destino


def main(caminho_pedido: str) -> None:
    pedido = json.loads(Path(caminho_pedido).read_text(encoding="utf-8"))
    papel = carregar_catalogo()[pedido["papel"]]
    paredes = [Parede(**p) for p in pedido["paredes"]]
    orc = calcular(papel, paredes, pedido.get("mao_de_obra_m2", 0), pedido.get("frete", 0))
    saida = RAIZ / "saida"; saida.mkdir(exist_ok=True)
    pdf = gerar_pdf(saida / f"orcamento_{pedido['cliente'].split()[0].lower()}.pdf", pedido, papel, paredes, orc)
    msg = mensagem_whatsapp(pedido["cliente"], papel, orc, pedido.get("prazo_dias_uteis", 15))
    (saida / "mensagem_whatsapp.txt").write_text(msg, encoding="utf-8")
    print(msg, f"\n\nPDF: {pdf}", sep="")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(RAIZ / "exemplos" / "pedido.json"))
