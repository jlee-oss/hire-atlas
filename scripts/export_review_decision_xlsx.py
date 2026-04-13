#!/usr/bin/env python3

import argparse
import csv
import datetime as dt
import pathlib
import zipfile
from xml.sax.saxutils import escape


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CSV_PATH = ROOT / "data" / "review_decision_sheet_001.csv"
DEFAULT_XLSX_PATH = ROOT / "data" / "review_decision_sheet_001.xlsx"

DECISION_OPTIONS = [
    "approve_draft",
    "approve_low",
    "approve_current",
    "needs_edit",
    "skip",
]


def column_letter(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def xml_decl(body: str) -> str:
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + body


def inline_str_cell(ref: str, value: str, style: int | None = None) -> str:
    style_attr = f' s="{style}"' if style is not None else ""
    safe = escape(value or "")
    return f'<c r="{ref}" t="inlineStr"{style_attr}><is><t xml:space="preserve">{safe}</t></is></c>'


def build_sheet_xml(rows: list[dict], fieldnames: list[str]) -> str:
    total_rows = len(rows) + 1
    last_col = column_letter(len(fieldnames))
    decision_col = column_letter(fieldnames.index("decision") + 1)

    width_overrides = {
        "A": 18,
        "B": 20,
        "C": 18,
        "D": 42,
        "E": 14,
        "F": 14,
        "G": 18,
        "H": 18,
        "I": 34,
        "J": 34,
        "K": 34,
        "L": 18,
        "M": 18,
        "N": 28,
        "O": 22,
        "P": 30,
        "Q": 14,
        "R": 34,
    }
    cols_xml = []
    for index in range(1, len(fieldnames) + 1):
        letter = column_letter(index)
        width = width_overrides.get(letter, 18)
        cols_xml.append(f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>')

    sheet_rows = []
    header_cells = []
    for col_index, field in enumerate(fieldnames, start=1):
        ref = f"{column_letter(col_index)}1"
        header_cells.append(inline_str_cell(ref, field, style=1))
    sheet_rows.append(f'<row r="1" spans="1:{len(fieldnames)}" ht="26" customHeight="1">{"".join(header_cells)}</row>')

    wrap_fields = {
        "title",
        "currentSummary",
        "draftSummary",
        "draftKeywords",
        "manualSummary",
        "manualKeywords",
        "confirmNotes",
    }

    for row_index, row in enumerate(rows, start=2):
        cells = []
        for col_index, field in enumerate(fieldnames, start=1):
            ref = f"{column_letter(col_index)}{row_index}"
            value = str(row.get(field, "") or "")
            style = 2 if field in wrap_fields else None
            cells.append(inline_str_cell(ref, value, style=style))
        sheet_rows.append(f'<row r="{row_index}" spans="1:{len(fieldnames)}">{"".join(cells)}</row>')

    formula = ",".join(DECISION_OPTIONS)

    body = f"""
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dimension ref="A1:{last_col}{total_rows}"/>
  <sheetViews>
    <sheetView workbookViewId="0">
      <pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>
      <selection pane="bottomLeft" activeCell="A2" sqref="A2"/>
    </sheetView>
  </sheetViews>
  <sheetFormatPr defaultRowHeight="18"/>
  <cols>{''.join(cols_xml)}</cols>
  <sheetData>{''.join(sheet_rows)}</sheetData>
  <autoFilter ref="A1:{last_col}{total_rows}"/>
  <dataValidations count="1">
    <dataValidation type="list" allowBlank="1" showInputMessage="1" showErrorMessage="1" sqref="{decision_col}2:{decision_col}{total_rows}">
      <formula1>"{formula}"</formula1>
    </dataValidation>
  </dataValidations>
  <pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>
</worksheet>
"""
    return xml_decl(body)


def build_styles_xml() -> str:
    body = """
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font>
      <sz val="11"/>
      <name val="Aptos"/>
      <family val="2"/>
    </font>
    <font>
      <b/>
      <sz val="11"/>
      <color rgb="FF1F2937"/>
      <name val="Aptos"/>
      <family val="2"/>
    </font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill>
      <patternFill patternType="solid">
        <fgColor rgb="FFEFF6FF"/>
        <bgColor indexed="64"/>
      </patternFill>
    </fill>
  </fills>
  <borders count="2">
    <border>
      <left/><right/><top/><bottom/><diagonal/>
    </border>
    <border>
      <left style="thin"><color rgb="FFD6DFEB"/></left>
      <right style="thin"><color rgb="FFD6DFEB"/></right>
      <top style="thin"><color rgb="FFD6DFEB"/></top>
      <bottom style="thin"><color rgb="FFD6DFEB"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="3">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">
      <alignment vertical="center"/>
    </xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1">
      <alignment vertical="top" wrapText="1"/>
    </xf>
  </cellXfs>
  <cellStyles count="1">
    <cellStyle name="Normal" xfId="0" builtinId="0"/>
  </cellStyles>
</styleSheet>
"""
    return xml_decl(body)


def build_content_types_xml() -> str:
    body = """
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""
    return xml_decl(body)


def build_root_rels_xml() -> str:
    body = """
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""
    return xml_decl(body)


def build_workbook_xml() -> str:
    body = """
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="review_decision" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""
    return xml_decl(body)


def build_workbook_rels_xml() -> str:
    body = """
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""
    return xml_decl(body)


def build_app_xml() -> str:
    body = """
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
  <DocSecurity>0</DocSecurity>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs>
    <vt:vector size="2" baseType="variant">
      <vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant>
      <vt:variant><vt:i4>1</vt:i4></vt:variant>
    </vt:vector>
  </HeadingPairs>
  <TitlesOfParts>
    <vt:vector size="1" baseType="lpstr">
      <vt:lpstr>review_decision</vt:lpstr>
    </vt:vector>
  </TitlesOfParts>
</Properties>
"""
    return xml_decl(body)


def build_core_xml() -> str:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    body = f"""
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
  <dc:title>review_decision_sheet_001</dc:title>
</cp:coreProperties>
"""
    return xml_decl(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH))
    parser.add_argument("--output", default=str(DEFAULT_XLSX_PATH))
    args = parser.parse_args()

    csv_path = pathlib.Path(args.csv)
    output_path = pathlib.Path(args.output)

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", build_content_types_xml())
        zf.writestr("_rels/.rels", build_root_rels_xml())
        zf.writestr("docProps/app.xml", build_app_xml())
        zf.writestr("docProps/core.xml", build_core_xml())
        zf.writestr("xl/workbook.xml", build_workbook_xml())
        zf.writestr("xl/_rels/workbook.xml.rels", build_workbook_rels_xml())
        zf.writestr("xl/styles.xml", build_styles_xml())
        zf.writestr("xl/worksheets/sheet1.xml", build_sheet_xml(rows, fieldnames))

    print(f"Wrote Excel workbook to {output_path}")


if __name__ == "__main__":
    main()
