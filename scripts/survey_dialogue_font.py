"""Measure source tile geometry and verify renderer limits against ROM and capture."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    capture = args.capture.resolve()
    out = args.output.resolve()
    capture.relative_to((ROOT / 'qa').resolve())
    out.relative_to((ROOT / 'qa').resolve())
    assert not out.exists()
    manifest = json.loads((ROOT / 'manifests/source_rom.json').read_text(encoding='utf-8'))
    rom = (ROOT / manifest['path']).read_bytes()
    assert hashlib.sha256(rom).hexdigest() == manifest['sha256']
    # The original renderer increments the column by one tile, wraps at $14,
    # resets to $04, increments row by one, then wraps at $0B back to $04.
    advance = bytes.fromhex('EE AA 07 AD AA 07 C9 14 90 14 A9 04 8D AA 07 EE AB 07 AD AB 07 C9 0B 90 05 A9 04 8D AB 07 60')
    assert rom[0x17290:0x17290 + len(advance)] == advance
    # PPU upload buffer count is 1: one nametable entry per glyph.
    emitter = bytes.fromhex('A6 1E A9 01 20 EA B2 A5 01 20 EA B2 A5 00 20 EA B2 68 20 EA B2 A9 FF 20 EA B2 60')
    assert rom[0x172DF:0x172DF + len(emitter)] == emitter
    ppu = (capture / 'frame_0840_ppu.bin').read_bytes()
    ram = (capture / 'frame_0840_ram.bin').read_bytes()
    assert ram[0x7DE:0x7E0] == b'\0\0'
    state = (capture / 'frame_0840_state.txt').read_text()
    assert 'ppu.control.backgroundPatternAddr=0' in state
    maps = {}
    for line in (capture / 'frame_0840_chr_mapping.txt').read_text().splitlines():
        address, offset, kind = line.split()
        maps[int(address, 16)] = int(offset)
    # Source CHR offsets exclude header and PRG, hence +$20010 here.
    assert ppu[:0x400] == rom[0x20010 + maps[0]:0x20410 + maps[0]]
    assert ppu[0x400:0x800] == rom[0x20010 + maps[0x400]:0x20410 + maps[0x400]]
    glyphs = json.loads((ROOT / 'extracted/text/dialogue_20261001/dialogue_tokens.json').read_text(encoding='utf-8'))['glyphs']
    measurements = []
    for code, char in glyphs.items():
        tile = int(code, 16)
        data = ppu[tile * 16:tile * 16 + 16]
        points = [(x, y) for y in range(8) for x in range(8)
                  if ((data[y] | data[y + 8]) >> (7 - x)) & 1]
        box = None if not points else [min(x for x, y in points), min(y for x, y in points),
                                       max(x for x, y in points) + 1, max(y for x, y in points) + 1]
        measurements.append({'code': code, 'char': char, 'bbox_exclusive': box,
                             'ink_width': 0 if box is None else box[2] - box[0],
                             'ink_height': 0 if box is None else box[3] - box[1]})
    # Preserve the raw 256x240 screenshot; derived annotated view uses nearest scaling.
    annotated = Image.open(capture / 'frame_0840.png').convert('RGB').resize((768, 720), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(annotated)
    for x in range(32, 161, 8):
        draw.line((x * 3, 32 * 3, x * 3, 88 * 3), fill=(75, 90, 105))
    for y in range(32, 89, 8):
        draw.line((32 * 3, y * 3, 160 * 3, y * 3), fill=(75, 90, 105))
    draw.rectangle((96, 96, 480, 264), outline=(0, 255, 180), width=2)
    draw.text((30, 25), '128 x 56 px / 16 columns x 7 rows / cell 8 x 8 px', fill=(0, 255, 180))
    annotated.save(capture / 'text_grid_annotated.png')
    report = {
        'source_sha256': manifest['sha256'], 'capture': str(capture.relative_to(ROOT)),
        'static': {'advance_cpu_address': '$B280', 'advance_file_offset': '0x17290',
                   'advance_expected_hex': advance.hex(' ').upper(),
                   'single_tile_emit_cpu_address': '$B2CF', 'single_tile_emit_file_offset': '0x172DF',
                   'single_tile_emit_expected_hex': emitter.hex(' ').upper(),
                   'cell_px': [8, 8], 'tile_bytes_2bpp': 16, 'column_range': [4, 19],
                   'row_range': [4, 10], 'window_tiles': [16, 7], 'window_px': [128, 56],
                   'overflow_behavior': 'wrap to column 4; row >=11 wraps to row 4 (no automatic new page)'},
        'runtime': {'exit_code': json.loads((capture / 'environment.json').read_text())['exit_code'],
                    'cold_boot_controller_only': True, 'ram_origin_tiles': [ram[0x7DE], ram[0x7DF]],
                    'sample_screen_rect_exclusive': [32, 32, 160, 88],
                    'ppu_chr_source_bytes_match': True, 'bg_pattern_address': 0,
                    'font_chr_mapping': {'0000': f'CHR 0x{maps[0]:05X}; ROM 0x{maps[0]+0x20010:05X}',
                                         '0400': f'CHR 0x{maps[0x400]:05X}; ROM 0x{maps[0x400]+0x20010:05X}'}},
        'font_ink': {'glyph_count_measured': len(measurements),
                     'max_width': max(m['ink_width'] for m in measurements),
                     'max_height': max(m['ink_height'] for m in measurements), 'glyphs': measurements},
        'layout_arithmetic_only': [
            {'cell_px': [8, 8], 'columns': 16, 'rows': 7, 'tiles_per_glyph': 1, 'renderer_change': False},
            {'cell_px': [8, 16], 'columns': 16, 'rows': 3, 'tiles_per_glyph': 2, 'renderer_change': True},
            {'cell_px': [16, 16], 'columns': 8, 'rows': 3, 'tiles_per_glyph': 4, 'renderer_change': True}],
        'validation_scope': {'static': 'PASS', 'source_runtime': 'PASS',
                             'source_scene_visual': 'inspect source screenshots separately',
                             'korean_build_apply': 'NOT PERFORMED', 'korean_runtime_visual': 'NOT PERFORMED'},
        'files': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(capture.iterdir()) if p.is_file()}}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'cell_px': [8, 8], 'window_px': [128, 56],
                      'ink_max': [report['font_ink']['max_width'], report['font_ink']['max_height']],
                      'measured_glyphs': len(measurements)}))


if __name__ == '__main__':
    main()
