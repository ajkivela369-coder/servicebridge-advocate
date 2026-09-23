import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject, TextStringObject, ArrayObject, FloatObject

from servicebridge.cli import main
from servicebridge.packet import assemble, inspect_packet


def test_packet_retains_selected_pages_and_clickable_url(tmp_path: Path, capsys):
    source = tmp_path / 'source.pdf'
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)
    writer.add_uri(1, 'https://www.ecfr.gov/', [40, 40, 160, 55])
    with source.open('wb') as stream:
        writer.write(stream)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'jurisdiction': 'VA', 'items': [
        {'path': source.name, 'pages': [2], 'kind': 'law', 'citation': '38 CFR, verify section', 'label': 'Law source'}]}))
    output = tmp_path / 'packet.pdf'
    report = assemble(manifest, output)
    assert report['ready'] and report['page_count'] == 1
    assert report['pages'][0]['links'][0]['url'] == 'https://www.ecfr.gov/'
    assert report['index'][0]['source_pages'] == [2]
    assert len(PdfReader(output).pages) == 1
    assert main(['packet', 'check', str(output)]) == 0
    assert 'https://www.ecfr.gov/' in capsys.readouterr().out


def test_packet_rejects_invalid_selection_and_reports_limit(tmp_path: Path):
    source = tmp_path / 's.pdf'
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with source.open('wb') as stream:
        writer.write(stream)
    manifest = tmp_path / 'm.json'
    manifest.write_text(json.dumps({'items': [{'path': 's.pdf', 'pages': [2]}]}))
    try:
        assemble(manifest, tmp_path / 'out.pdf')
        assert False, 'out-of-range page accepted'
    except ValueError as error:
        assert 'page outside' in str(error)
    manifest.write_text(json.dumps({'items': [{'path': 's.pdf', 'pages': [1]}]}))
    assert not assemble(manifest, tmp_path / 'out.pdf', max_mb=0.00001)['ready']
