"""Read the registered ROM and produce a static header/CHR survey; never patch it."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'manifests/source_rom.json').read_text(encoding='utf-8'))
    source = args.rom or root / manifest['path']
    data = source.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != manifest['sha256'] or len(data) != manifest['size_bytes']:
        raise SystemExit('Source identity mismatch')
    h = data[:16]
    if h[:4] != b'NES\x1a' or (h[7] & 12) != 0:
        raise SystemExit('This survey supports the registered iNES 1.0 input only')
    trainer = 512 if h[6] & 4 else 0
    prg_start = 16 + trainer
    prg_size = h[4] * 16384
    chr_start = prg_start + prg_size
    chr_size = h[5] * 8192
    if chr_start + chr_size != len(data):
        raise SystemExit('Unexpected file length')
    chr_data = data[chr_start:chr_start + chr_size]
    report = {
        'scope': 'Static header and raw CHR decode; no runtime or text-engine proof',
        'source_sha256': digest,
        'file_size_bytes': len(data),
        'header_hex': h.hex(' ').upper(),
        'header_format': 'iNES 1.0',
        'mapper': (h[6] >> 4) | (h[7] & 0xf0),
        'submapper': None,
        'trainer_bytes': trainer,
        'battery_flag': bool(h[6] & 2),
        'four_screen_flag': bool(h[6] & 8),
        'mirroring_header_bit': h[6] & 1,
        'prg': {'start': prg_start, 'end_exclusive': chr_start, 'size': prg_size,
                'sha256': hashlib.sha256(data[prg_start:chr_start]).hexdigest()},
        'chr': {'start': chr_start, 'end_exclusive': len(data), 'size': chr_size,
                'sha256': hashlib.sha256(chr_data).hexdigest(), 'tile_count': chr_size // 16},
        'chr_pages': [],
    }
    from PIL import Image, ImageDraw, __version__ as pillow_version
    report['pillow_version'] = pillow_version
    output = args.output.resolve()
    if output == source.resolve() or root / 'original' == output or root / 'original' in output.parents:
        raise SystemExit('Output must not be in original/')
    output.mkdir(parents=True, exist_ok=True)
    palette = [0, 85, 170, 255]
    overview = Image.new('RGB', (8 * 264, 4 * 284), '#303030')
    draw = ImageDraw.Draw(overview)
    for page in range(chr_size // 4096):
        page_data = chr_data[page * 4096:(page + 1) * 4096]
        sheet = Image.new('L', (128, 128))
        pixels = sheet.load()
        rebuilt = bytearray()
        for tile in range(256):
            raw = page_data[tile * 16:(tile + 1) * 16]
            encoded = bytearray(16)
            for y in range(8):
                for x in range(8):
                    value = ((raw[y] >> (7-x)) & 1) | (((raw[y+8] >> (7-x)) & 1) << 1)
                    pixels[(tile % 16) * 8 + x, (tile // 16) * 8 + y] = palette[value]
                    encoded[y] |= (value & 1) << (7-x)
                    encoded[y+8] |= ((value >> 1) & 1) << (7-x)
            rebuilt.extend(encoded)
        if bytes(rebuilt) != page_data:
            raise SystemExit('CHR roundtrip mismatch')
        name = f'chr_page_{page:02X}.png'
        sheet.save(output / name)
        x, y = (page % 8) * 264, (page // 8) * 284
        draw.text((x+4, y+2), f'PAGE {page:02X} FILE {chr_start+page*4096:05X}', fill='white')
        overview.paste(sheet.resize((256, 256), Image.Resampling.NEAREST), (x+4, y+20))
        report['chr_pages'].append({'page_4k': page, 'file_offset': chr_start+page*4096,
                                    'chr_1k_banks': list(range(page*4, page*4+4)),
                                    'png': name, 'decode_encode_equal': True})
    overview.save(output / 'chr_overview.png')
    focus = Image.new('RGB', (1040, 1080), '#303030')
    focus_draw = ImageDraw.Draw(focus)
    for index, page in enumerate([0x0e, 0x1e, 0x12, 0x1a]):
        sheet = Image.open(output / f'chr_page_{page:02X}.png')
        x, y = (index % 2) * 520, (index // 2) * 540
        focus_draw.text((x+4, y+2), f'PAGE {page:02X} FILE {chr_start+page*4096:05X}', fill='white')
        focus.paste(sheet.resize((512, 512), Image.Resampling.NEAREST), (x+4, y+20))
    focus.save(output / 'chr_candidates.png')
    report['chr_decode_encode_all_equal'] = True
    (output / 'rom_survey.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({key: val for key, val in report.items() if key != 'chr_pages'}, indent=2))


if __name__ == '__main__':
    main()
