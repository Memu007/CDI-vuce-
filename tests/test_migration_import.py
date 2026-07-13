"""Contrato de integración del migrador de clientes.

Estos tests describen el MVP de ``Clientes > Traer mis clientes``. La etapa de
análisis siempre es una vista previa: no puede escribir clientes. La única
operación que persiste datos es ``confirm`` y debe poder deshacerse.

Importante: por ahora el migrador solo incorpora datos estables de la ficha del
cliente. Las columnas de peso quedan fuera deliberadamente porque el producto
aún no puede distinguir con seguridad peso unitario de peso total por renglón.
"""

from __future__ import annotations

import io
import json

import pytest


ANALYZE_URL = "/api/migrations/analyze"


def _valid_cuit(serial: int) -> str:
    """Genera un CUIT sintácticamente válido y determinístico para cada test."""
    # Separar los stems para que, si uno cae en verificador 10 y avanza al
    # siguiente, no colisione con el CUIT pedido por otro test.
    candidate = serial * 10
    weights = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    while True:
        stem = f"30{candidate:08d}"[-10:]
        remainder = sum(int(digit) * weight for digit, weight in zip(stem, weights)) % 11
        verifier = 11 - remainder
        if verifier == 11:
            verifier = 0
        if verifier != 10:
            return f"{stem}{verifier}"
        candidate += 1


def _csv_bytes(headers: list[str], rows: list[list[object]], separator: str = ",") -> bytes:
    lines = [separator.join(headers)]
    lines.extend(separator.join(str(value) for value in row) for row in rows)
    return ("\n".join(lines) + "\n").encode("utf-8")


def _xlsx_bytes(sheets: dict[str, tuple[list[str], list[list[object]]]]) -> bytes:
    try:
        from openpyxl import Workbook
    except ImportError:
        pytest.skip("openpyxl no está instalado")

    workbook = Workbook()
    default_sheet = workbook.active
    workbook.remove(default_sheet)
    for title, (headers, rows) in sheets.items():
        sheet = workbook.create_sheet(title=title)
        sheet.append(headers)
        for row in rows:
            sheet.append(row)

    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def _analyze(client, content: bytes, filename: str = "clientes.csv", content_type: str = "text/csv"):
    response = client.post(
        ANALYZE_URL,
        files={"file": (filename, io.BytesIO(content), content_type)},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload.get("batch_id")
    assert isinstance(payload.get("preview"), dict)
    return payload


def _confirm(client, batch_id: str):
    response = client.post(f"/api/migrations/{batch_id}/confirm")
    assert response.status_code == 200, response.text
    return response.json()


def _client_by_cuit(client, cuit: str):
    response = client.get(f"/api/clientes/by-cuit/{cuit}")
    assert response.status_code == 200, response.text
    return response.json()


def _preview_records(preview: dict) -> list[dict]:
    return [
        *preview.get("new_clients", []),
        *preview.get("existing_clients", []),
        *preview.get("conflicts", []),
        *preview.get("omitted", []),
    ]


def test_analyze_is_preview_only_and_does_not_create_clients(auth_override, client):
    cuit = _valid_cuit(91001)
    content = _csv_bytes(
        ["CUIT", "RAZON SOCIAL", "DIRECCION"],
        [[cuit, "Cliente solo preview", "Av. Prueba 123"]],
    )

    assert _client_by_cuit(client, cuit)["match"] == "none"
    payload = _analyze(client, content)

    assert payload["preview"]["summary"]["new_clients"] == 1
    assert _client_by_cuit(client, cuit)["match"] == "none"


def test_repeated_cuit_in_file_is_grouped_as_one_client(auth_override, client):
    cuit = _valid_cuit(91002)
    content = _csv_bytes(
        ["CUIT", "CLIENTE", "DIRECCION", "EMAIL", "FECHA INICIO ACTIVIDADES"],
        [
            [cuit, "Importadora Agrupada SA", "", "compras@agrupada.test", "01/06/2018"],
            [cuit, "Importadora Agrupada SA", "Paraná 456", "", "01/06/2018"],
            [cuit, "Importadora Agrupada SA", "Paraná 456", "compras@agrupada.test", "01/06/2018"],
        ],
    )

    payload = _analyze(client, content)
    preview = payload["preview"]
    assert preview["summary"]["total_rows"] == 3
    assert preview["summary"]["new_clients"] == 1
    assert len(preview["new_clients"]) == 1
    assert len(preview["new_clients"][0]["source_rows"]) == 3

    confirmed = _confirm(client, payload["batch_id"])
    assert confirmed["status"] == "confirmed"
    assert confirmed["created"] == 1
    stored = _client_by_cuit(client, cuit)
    assert stored["match"] == "exact"
    assert stored["cliente"]["fecha_inic_activ"] == "2018-06-01"


def test_existing_cuit_fills_only_empty_fields_and_preserves_conflicts(auth_override, client):
    cuit = _valid_cuit(91003)
    created = client.post(
        "/api/clientes",
        json={
            "nombre": "Razón social confirmada",
            "cuit": cuit,
            "telefono": "11 4444-1111",
            "direccion": "",
        },
    )
    assert created.status_code == 200, created.text

    content = _csv_bytes(
        ["CUIT", "CLIENTE", "TELEFONO", "DIRECCION", "FECHA INICIO ACTIVIDADES"],
        [[cuit, "Nombre distinto del Excel", "11 9999-9999", "Av. Nueva 987", "15/03/2010"]],
    )
    payload = _analyze(client, content)
    preview = payload["preview"]

    assert preview["summary"]["existing_clients"] + preview["summary"]["conflicts"] == 1
    record = next(record for record in _preview_records(preview) if record.get("cuit") == cuit)
    assert "direccion" in record.get("fillable_fields", {})
    assert "fecha_inic_activ" in record.get("fillable_fields", {})
    assert {"nombre", "telefono"}.issubset(set(record.get("conflicting_fields", {})))

    confirmed = _confirm(client, payload["batch_id"])
    assert confirmed["status"] == "confirmed"
    assert confirmed["updated"] == 1

    stored = _client_by_cuit(client, cuit)["cliente"]
    assert stored["direccion"] == "Av. Nueva 987"
    assert stored["nombre"] == "Razón social confirmada"
    assert stored["telefono"] == "11 4444-1111"
    assert stored["fecha_inic_activ"] == "2010-03-15"


def test_rows_without_cuit_are_never_auto_merged_or_created(auth_override, client):
    content = _csv_bytes(
        ["CLIENTE", "DIRECCION", "EMAIL"],
        [
            ["Mismo Nombre SA", "Calle Uno 1", "uno@sin-cuit.test"],
            ["Mismo Nombre SA", "Calle Dos 2", "dos@sin-cuit.test"],
        ],
    )

    before = client.get("/api/clientes").json()["clientes"]
    payload = _analyze(client, content)
    preview = payload["preview"]

    assert preview["summary"]["omitted"] == 2
    assert preview["summary"]["new_clients"] == 0
    assert all(not record.get("ready") for record in preview["omitted"])

    confirmed = _confirm(client, payload["batch_id"])
    assert confirmed["created"] == 0
    after = client.get("/api/clientes").json()["clientes"]
    assert len(after) == len(before)


def test_confirm_is_idempotent(auth_override, client):
    cuit = _valid_cuit(91004)
    payload = _analyze(
        client,
        _csv_bytes(["CUIT", "CLIENTE"], [[cuit, "Cliente idempotente"]]),
    )

    first = _confirm(client, payload["batch_id"])
    second = _confirm(client, payload["batch_id"])

    assert first["status"] == "confirmed"
    assert first["created"] == 1
    assert first["idempotent"] is False
    assert second["status"] == "confirmed"
    assert second["idempotent"] is True
    matching = [
        item for item in client.get("/api/clientes").json()["clientes"]
        if "".join(character for character in (item.get("cuit") or "") if character.isdigit()) == cuit
    ]
    assert len(matching) == 1


def test_undo_deletes_created_clients_and_restores_filled_fields(auth_override, client):
    existing_cuit = _valid_cuit(91005)
    new_cuit = _valid_cuit(91006)
    created = client.post(
        "/api/clientes",
        json={"nombre": "Cliente existente", "cuit": existing_cuit, "direccion": ""},
    )
    assert created.status_code == 200, created.text

    payload = _analyze(
        client,
        _csv_bytes(
            ["CUIT", "CLIENTE", "DIRECCION"],
            [
                [existing_cuit, "Cliente existente", "Dirección temporal 123"],
                [new_cuit, "Cliente creado por lote", "Dirección nueva 456"],
            ],
        ),
    )
    confirmed = _confirm(client, payload["batch_id"])
    assert confirmed["created"] == 1
    assert confirmed["updated"] == 1
    assert _client_by_cuit(client, existing_cuit)["cliente"]["direccion"] == "Dirección temporal 123"
    assert _client_by_cuit(client, new_cuit)["match"] == "exact"

    response = client.post(f"/api/migrations/{payload['batch_id']}/undo")
    assert response.status_code == 200, response.text
    undone = response.json()
    assert undone["success"] is True
    assert undone["status"] == "undone"
    assert undone["deleted"] == 1
    assert undone["restored"] == 1
    assert _client_by_cuit(client, new_cuit)["match"] == "none"
    assert not _client_by_cuit(client, existing_cuit)["cliente"].get("direccion")


def test_batch_is_private_to_its_owner(auth_override, client):
    from proyecto_maria.main import app, get_current_user

    cuit = _valid_cuit(91007)
    payload = _analyze(
        client,
        _csv_bytes(["CUIT", "CLIENTE"], [[cuit, "Cliente privado"]]),
    )

    other_user = dict(auth_override)
    other_user.update(username="otro_owner", effective_owner="otro_owner")
    app.dependency_overrides[get_current_user] = lambda: other_user
    try:
        forbidden_confirm = client.post(f"/api/migrations/{payload['batch_id']}/confirm")
        forbidden_undo = client.post(f"/api/migrations/{payload['batch_id']}/undo")
    finally:
        app.dependency_overrides[get_current_user] = lambda: auth_override

    # 404 evita revelar a otro tenant que el batch existe; 403 también aísla.
    assert forbidden_confirm.status_code in {403, 404}, forbidden_confirm.text
    assert forbidden_undo.status_code in {403, 404}, forbidden_undo.text
    assert _client_by_cuit(client, cuit)["match"] == "none"


def test_semicolon_csv_is_detected_without_user_configuration(auth_override, client):
    cuit_a = _valid_cuit(91008)
    cuit_b = _valid_cuit(91009)
    content = _csv_bytes(
        ["CUIT", "RAZON SOCIAL", "DOMICILIO"],
        [
            [cuit_a, "Cliente punto y coma A", "Calle A 1"],
            [cuit_b, "Cliente punto y coma B", "Calle B 2"],
        ],
        separator=";",
    )

    payload = _analyze(client, content, filename="clientes-punto-y-coma.csv")
    preview = payload["preview"]
    assert preview["summary"]["total_rows"] == 2
    assert preview["summary"]["new_clients"] == 2
    assert {record["cuit"] for record in preview["new_clients"]} == {cuit_a, cuit_b}


def test_xlsx_reads_clients_from_multiple_sheets(auth_override, client):
    cuit_a = _valid_cuit(91010)
    cuit_b = _valid_cuit(91011)
    content = _xlsx_bytes(
        {
            "Operaciones 2025": (
                ["CUIT IMPORTADOR", "CLIENTE", "DIRECCION"],
                [[cuit_a, "Cliente hoja histórica", "Calle Histórica 10"]],
            ),
            "Operaciones 2026": (
                ["CUIT IMPORTADOR", "CLIENTE", "DIRECCION"],
                [[cuit_b, "Cliente hoja actual", "Calle Actual 20"]],
            ),
        }
    )

    payload = _analyze(
        client,
        content,
        filename="operaciones-multihoja.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    preview = payload["preview"]
    assert preview["summary"]["total_rows"] == 2
    assert preview["summary"]["new_clients"] == 2
    assert {record["cuit"] for record in preview["new_clients"]} == {cuit_a, cuit_b}
    assert {source["sheet"] for record in preview["new_clients"] for source in record["source_rows"]} == {
        "Operaciones 2025",
        "Operaciones 2026",
    }


def test_weight_columns_are_not_staged_or_imported(auth_override, client):
    cuit = _valid_cuit(91012)
    sentinel_weight = "98765.4321"
    content = _csv_bytes(
        ["CUIT", "CLIENTE", "PESO", "PESO UNITARIO", "PESO NETO TOTAL"],
        [[cuit, "Cliente con pesos ambiguos", sentinel_weight, "12.34", "5678"]],
    )

    payload = _analyze(client, content)
    preview = payload["preview"]
    assert preview["summary"]["new_clients"] == 1
    record = preview["new_clients"][0]
    assert not ({"peso", "peso_unitario", "peso_total", "peso_neto_total"} & set(record))
    assert sentinel_weight not in json.dumps(record, ensure_ascii=False)

    confirmed = _confirm(client, payload["batch_id"])
    assert confirmed["created"] == 1
    stored = _client_by_cuit(client, cuit)["cliente"]
    assert not ({"peso", "peso_unitario", "peso_total", "peso_neto_total"} & set(stored))
    assert sentinel_weight not in json.dumps(stored, ensure_ascii=False)


def test_gemini_samples_never_include_client_pii():
    from proyecto_maria.services.migration_ai_mapper import _mask_sample

    assert _mask_sample("compras@cliente-real.com") == "EMAIL_***"
    assert _mask_sample("30-12345678-1") == "CUIT_***********"
    assert _mask_sample("Importadora Confidencial SA").startswith("TEXTO_")
    assert "Confidencial" not in _mask_sample("Importadora Confidencial SA")


@pytest.mark.asyncio
async def test_ambiguous_headers_can_use_safe_ai_mapping_without_accepting_weight():
    from proyecto_maria.services.migration_service import analyze_migration_file_async

    cuit = _valid_cuit(91013)
    content = _csv_bytes(
        ["IDENTIFICADOR INTERNO", "DENOMINACION PROPIA", "PESO TOTAL"],
        [[cuit, "Cliente encabezados raros", "99999"]],
    )
    calls = []

    async def fake_mapper(headers, samples):
        calls.append((headers, samples))
        return {
            "IDENTIFICADOR INTERNO": "cuit",
            "DENOMINACION PROPIA": "nombre",
            # Aunque una IA se equivoque, peso nunca puede alimentar la ficha.
            "PESO TOTAL": "direccion",
        }

    preview = await analyze_migration_file_async(
        content,
        "ambiguo.csv",
        existing_clients=[],
        header_mapper=fake_mapper,
    )
    assert len(calls) == 1
    assert preview["summary"]["new_clients"] == 1
    record = preview["new_clients"][0]
    assert record["nombre"] == "Cliente encabezados raros"
    assert record["direccion"] == ""
    assert "99999" not in json.dumps(record, ensure_ascii=False)


@pytest.mark.asyncio
async def test_known_headers_do_not_spend_ai_fallback():
    from proyecto_maria.services.migration_service import analyze_migration_file_async

    cuit = _valid_cuit(91014)
    content = _csv_bytes(["CUIT", "CLIENTE"], [[cuit, "Cliente local"]])

    async def should_not_run(_headers, _samples):
        raise AssertionError("El mapeo local ya era suficiente")

    preview = await analyze_migration_file_async(
        content,
        "local.csv",
        existing_clients=[],
        header_mapper=should_not_run,
    )
    assert preview["summary"]["new_clients"] == 1


def test_multiple_existing_clients_with_same_cuit_are_never_chosen_silently(auth_override, client):
    cuit = _valid_cuit(91015)
    first = client.post("/api/clientes", json={"nombre": "Duplicado uno", "cuit": cuit})
    second = client.post("/api/clientes", json={"nombre": "Duplicado dos", "cuit": cuit})
    assert first.status_code == 200
    assert second.status_code == 200

    payload = _analyze(
        client,
        _csv_bytes(["CUIT", "CLIENTE", "DIRECCION"], [[cuit, "Duplicado", "No aplicar 123"]]),
    )
    preview = payload["preview"]
    assert preview["summary"]["conflicts"] == 1
    assert preview["conflicts"][0]["reason"] == "multiple_existing_clients"

    confirmed = _confirm(client, payload["batch_id"])
    assert confirmed["created"] == 0
    assert confirmed["updated"] == 0
    assert confirmed["skipped"] == 1
    matching = [
        item for item in client.get("/api/clientes").json()["clientes"]
        if "".join(character for character in (item.get("cuit") or "") if character.isdigit()) == cuit
    ]
    assert len(matching) == 2
    assert all(not item.get("direccion") for item in matching)
