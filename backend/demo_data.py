"""Opt-in, deterministic sample library for trying the UI without a local model."""

from __future__ import annotations

import argparse
import json
import os
import xml.sax.saxutils
import zipfile
from io import BytesIO
from pathlib import Path

from .docx_extract import extract_docx, validate_docx
from .storage import Store


MARKER = "demo-seed-v1.json"
NOTICE = "Muestra ficticia para probar la interfaz. No es material estratégico ni una recomendación de juego."


def _docx(blocks: list[tuple[str, object]]) -> bytes:
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    body = []
    for kind, value in blocks:
        if kind == "paragraph":
            body.append(f'<w:p><w:r><w:t xml:space="preserve">{xml.sax.saxutils.escape(value)}</w:t></w:r></w:p>')
        else:
            rows = []
            for row in value:
                cells = "".join(f'<w:tc><w:p><w:r><w:t>{xml.sax.saxutils.escape(cell)}</w:t></w:r></w:p></w:tc>' for cell in row)
                rows.append(f"<w:tr>{cells}</w:tr>")
            body.append(f"<w:tbl>{''.join(rows)}</w:tbl>")
    document = f'<w:document xmlns:w="{w}"><w:body>{"".join(body)}<w:sectPr/></w:body></w:document>'
    content_types = ('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                     '<Default Extension="xml" ContentType="application/xml"/>'
                     '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                     '</Types>')
    relationships = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                     '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                     '</Relationships>')
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in (("[Content_Types].xml", content_types), ("_rels/.rels", relationships),
                              ("word/document.xml", document)):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content.encode("utf-8"))
    return output.getvalue()


DOCUMENTS = (
    ("Muestra - conceptos y posiciones.docx", [
        ("paragraph", "Muestra: conceptos y posiciones"),
        ("paragraph", NOTICE),
        ("paragraph", "BTN, SB y BB son etiquetas de posición. Las notas de una mano distinguen posición, acción previa y calle."),
        ("paragraph", "Antes de estudiar un bote se anota quién abrió, quién igualó y qué información falta."),
        ("table", [["Elemento", "Ejemplo de anotación"], ["Posición", "BTN frente a BB"], ["Calle", "Preflop o flop"]]),
    ]),
    ("Muestra - mano y calles.docx", [
        ("paragraph", "Muestra: registro de una mano"),
        ("paragraph", NOTICE),
        ("paragraph", "Ejemplo ficticio: BTN abre y BB iguala. En el flop aparecen A♠, 7♦ y 2♣."),
        ("paragraph", "Se registran por separado las posibles líneas de bet y check. La muestra no asigna frecuencias ni recomienda una línea."),
        ("paragraph", "En el turn aparece 4♥. Se anota el cambio de calle antes de revisar cualquier conclusión."),
        ("paragraph", "Dos notas parecidas se muestran como candidatas de revisión; no se fusionan automáticamente."),
    ]),
)


def seed(store: Store, empty_only: bool = False) -> dict[str, object]:
    marker = store.data_dir / MARKER
    if marker.exists():
        return {"status": "already_seeded", **json.loads(marker.read_text(encoding="utf-8"))}
    if empty_only and (store.list_documents() or store.list_topics()):
        return {"status": "skipped_nonempty"}

    documents = []
    for filename, blocks in DOCUMENTS:
        content = _docx(blocks)
        validate_docx(content, filename)
        document, created = store.save_document(filename, content, state="extracted")
        if created or not store.list_fragments(document["id"]):
            extracted = extract_docx(content, filename)
            store.replace_fragments(document["id"], extracted.fragments)
            store.set_document_state(document["id"], "extracted", extracted.warnings)
        documents.append(store.list_fragments(document["id"]))

    existing_branches = {(item["name"], item["parent_id"]): item for item in store.list_branches()}
    def branch(name: str, parent: str | None = None) -> str:
        key = (name, parent)
        if key not in existing_branches:
            existing_branches[key] = store.create_branch(name, parent)
        return existing_branches[key]["id"]

    fundamentals = branch("Muestra · Fundamentos")
    preflop = branch("Muestra · Preflop", fundamentals)
    postflop = branch("Muestra · Postflop", fundamentals)
    flop = branch("Muestra · Flop", postflop)
    turn = branch("Muestra · Turn", postflop)
    blinds = branch("Muestra · Guerra de ciegas", preflop)

    topics = {item["title"]: item for item in store.list_topics()}
    specifications = [
        ("Muestra · Posiciones en la mesa", "BTN, SB y BB identifican posiciones en una mano.",
         "Esta ficha demuestra un tema básico enlazado a una fuente y a una rama.", "", "basic", fundamentals, documents[0][2], None),
        ("Muestra · Acciones preflop", "Las notas distinguen quién abrió y quién igualó.",
         "Usa este ejemplo para recorrer prerrequisitos y fuentes; no contiene una recomendación de juego.",
         "Si falta una acción, se deja pendiente de revisión.", "basic", preflop, documents[0][3], "Muestra · Posiciones en la mesa"),
        ("Muestra · BTN frente a BB", "Ejemplo de anotación de posiciones y calle.",
         "La tabla del documento muestra cómo se presenta una fuente tabular en la interfaz.",
         "El ejemplo es ficticio.", "intermediate", blinds, documents[0][4], "Muestra · Acciones preflop"),
        ("Muestra · Lectura del flop", "Un registro ficticio recoge el flop A♠ 7♦ 2♣.",
         "Esta ficha permite navegar desde una fuente hasta un tema del flop.",
         "No se deduce ninguna frecuencia de apuesta.", "intermediate", flop, documents[1][2], "Muestra · Acciones preflop"),
        ("Muestra · Bet y check en el flop", "Las líneas bet y check se anotan por separado.",
         "Esta ficha demuestra dos temas cercanos sin convertir el ejemplo en consejo estratégico.",
         "La muestra no recomienda ninguna línea.", "intermediate", flop, documents[1][3], "Muestra · Lectura del flop"),
        ("Muestra · Cambio al turn", "El turn se registra como una nueva calle.",
         "La carta 4♥ del ejemplo permite probar un tema más profundo y su prerrequisito.",
         "El ejemplo es ficticio.", "advanced", turn, documents[1][4], "Muestra · Lectura del flop"),
    ]
    for title, summary, explanation, conditions, difficulty, branch_id, fragment, prerequisite in specifications:
        if title not in topics:
            topics[title] = store.create_topic({
                "title": title, "summary": summary, "explanation": explanation,
                "conditions": conditions, "difficulty": difficulty, "review_status": "proposed",
                "tags": ["muestra"], "branch_id": branch_id, "source_fragment_id": fragment["id"],
            })
        if prerequisite and topics[prerequisite]["id"] not in topics[title]["prerequisites"]:
            store.add_prerequisite(topics[title]["id"], topics[prerequisite]["id"])

    # Demo-only candidate so the similarity screen has a reviewable example.
    with store.transaction() as db:
        db.execute("INSERT OR IGNORE INTO topic_similarities(topic_id,candidate_id,score) VALUES (?,?,?)",
                   (topics["Muestra · Bet y check en el flop"]["id"], topics["Muestra · Lectura del flop"]["id"], 0.68))

    summary = {"documents": len(DOCUMENTS), "topics": len(specifications), "branches": 6}
    temporary = marker.with_suffix(".tmp")
    temporary.write_text(json.dumps(summary), encoding="utf-8")
    os.replace(temporary, marker)
    return {"status": "seeded", **summary}


def main() -> None:
    parser = argparse.ArgumentParser(description="Add clearly labelled sample data to a Poker Roots library")
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--empty-only", action="store_true", help="Skip if the library already contains data")
    args = parser.parse_args()
    print(json.dumps(seed(Store(args.data_dir), empty_only=args.empty_only), ensure_ascii=False))


if __name__ == "__main__":
    main()
