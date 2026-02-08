import datetime as dt
from decimal import Decimal, ROUND_HALF_UP


def _safe_text(value):
    if value is None:
        return "-"
    text = str(value)
    return text


def _format_dt(value):
    if not value:
        return "-"
    if isinstance(value, (dt.date, dt.datetime)):
        if isinstance(value, dt.datetime):
            return value.strftime("%d/%m/%Y %H:%M")
        return value.strftime("%d/%m/%Y")
    return str(value)


def _pdf_escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_text(text, max_chars=88):
    if not text:
        return [""]
    words = text.split()
    lines = []
    current = []
    current_len = 0
    for word in words:
        if current_len + len(word) + (1 if current else 0) > max_chars:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += len(word) + (1 if current_len else 0)
    if current:
        lines.append(" ".join(current))
    return lines


def _format_money(value):
    try:
        val = Decimal(str(value))
    except Exception:
        val = Decimal("0")
    return f"{val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"


def build_invoice_pdf(invoice, items=None):
    order = invoice.order
    items = items or []
    currency = "EUR"

    lines = [
        "Arrebita - Fatura",
        "",
        f"Numero da fatura: {_safe_text(invoice.invoice_number)}",
        f"Data de emissao: {_format_dt(invoice.issued_at)}",
        "",
        f"Encomenda: {_safe_text(order.order_number)} (ID {order.order_id})",
        f"Estado: {_safe_text(order.status)}",
        f"Tipo: {_safe_text(order.kind)}",
        "",
        "Dados de faturacao:",
        f"Nome: {_safe_text(order.billing_name)}",
        f"NIF: {_safe_text(order.billing_nif)}",
        f"Morada: {_safe_text(order.billing_address)}",
    ]

    text_commands = ["BT", "/F1 12 Tf"]
    y = 760
    for line in lines:
        text_commands.append(f"1 0 0 1 50 {y} Tm")
        text_commands.append(f"({_pdf_escape(line)}) Tj")
        y -= 16

    y -= 10

    # table setup
    x0, x1, x2, x3, x4, x5 = 50, 300, 360, 430, 500, 562
    header_h = 18
    row_h = 16

    max_rows = int((y - 120) / row_h) if y > 120 else 0
    truncated = False
    if max_rows and len(items) > max_rows:
        items = items[: max_rows - 1]
        truncated = True

    table_top = y
    total_lines = len(items) + (1 if truncated else 0)
    table_bottom = table_top - header_h - row_h * total_lines

    draw_commands = ["0.8 w"]
    # outer border
    draw_commands.append(f"{x0} {table_bottom} {x5 - x0} {header_h + row_h * total_lines} re S")
    # header line
    draw_commands.append(f"{x0} {table_top - header_h} m {x5} {table_top - header_h} l S")
    # vertical lines
    for x in (x1, x2, x3, x4):
        draw_commands.append(f"{x} {table_bottom} m {x} {table_top} l S")

    # header labels
    text_commands.append(f"1 0 0 1 {x0 + 6} {table_top - 13} Tm")
    text_commands.append(f"({_pdf_escape('Item')}) Tj")
    text_commands.append(f"1 0 0 1 {x2 + 6} {table_top - 13} Tm")
    text_commands.append(f"({_pdf_escape('Qtd')}) Tj")
    text_commands.append(f"1 0 0 1 {x3 + 6} {table_top - 13} Tm")
    text_commands.append(f"({_pdf_escape('Unit')} ) Tj")
    text_commands.append(f"1 0 0 1 {x4 + 6} {table_top - 13} Tm")
    text_commands.append(f"({_pdf_escape('Total')}) Tj")

    current_y = table_top - header_h - 12
    subtotal = Decimal("0")

    for item in items:
        name = _safe_text(item.get("wine_name") or item.get("wine_id"))
        qty = int(item.get("quantity") or 0)
        unit_price = Decimal(str(item.get("unit_price") or 0))
        line_total = unit_price * Decimal(qty)
        subtotal += line_total

        name_lines = _wrap_text(name, max_chars=38)
        text_commands.append(f"1 0 0 1 {x0 + 6} {current_y} Tm")
        text_commands.append(f"({_pdf_escape(name_lines[0])}) Tj")
        text_commands.append(f"1 0 0 1 {x2 + 6} {current_y} Tm")
        text_commands.append(f"({_pdf_escape(str(qty))}) Tj")
        text_commands.append(f"1 0 0 1 {x3 + 6} {current_y} Tm")
        text_commands.append(f"({_pdf_escape(_format_money(unit_price))} {currency}) Tj")
        text_commands.append(f"1 0 0 1 {x4 + 6} {current_y} Tm")
        text_commands.append(f"({_pdf_escape(_format_money(line_total))} {currency}) Tj")

        current_y -= row_h

    if truncated:
        text_commands.append(f"1 0 0 1 {x0 + 6} {current_y} Tm")
        text_commands.append(f"({_pdf_escape('Mais itens na encomenda...')}) Tj")

    total_y = table_bottom - 24
    text_commands.append(f"1 0 0 1 {x3 + 6} {total_y} Tm")
    text_commands.append(f"({_pdf_escape('Total')}) Tj")
    text_commands.append(f"1 0 0 1 {x4 + 6} {total_y} Tm")
    text_commands.append(f"({_pdf_escape(_format_money(subtotal))} {currency}) Tj")

    text_commands.append("ET")

    content = "\n".join(draw_commands + text_commands)
    content_bytes = content.encode("latin-1", "replace")

    objects = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    objects.append(
        b"<< /Length %d >>\nstream\n" % len(content_bytes)
        + content_bytes
        + b"\nendstream"
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    result = bytearray()
    result.extend(b"%PDF-1.4\n")

    offsets = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(result))
        result.extend(f"{index} 0 obj\n".encode("ascii"))
        result.extend(obj)
        result.extend(b"\nendobj\n")

    xref_start = len(result)
    result.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    result.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        result.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    result.extend(b"trailer\n")
    result.extend(f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("ascii"))
    result.extend(b"startxref\n")
    result.extend(f"{xref_start}\n".encode("ascii"))
    result.extend(b"%%EOF\n")

    return bytes(result)
