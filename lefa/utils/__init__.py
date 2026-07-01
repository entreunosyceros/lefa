"""
Utilidades compartidas de formato y presentación.
"""

def formato_moneda(valor: float) -> str:
    """Formatea un importe en euros con dos decimales."""
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
