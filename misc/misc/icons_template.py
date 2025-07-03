from enum import Enum

def lighten_color(hex_color, amount=0.2):
    hex_color = hex_color.lstrip('#')
    r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

    r = int(r + (255 - r) * amount)
    g = int(g + (255 - g) * amount)
    b = int(b + (255 - b) * amount)

    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))

def relative_luminance(rgb):
    def channel(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = map(channel, rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(lum1, lum2):
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)

def best_contrast_color(background_hex):
    bg_rgb = hex_to_rgb(background_hex)
    bg_lum = relative_luminance(bg_rgb)
    
    black_lum = relative_luminance((0, 0, 0))
    white_lum = relative_luminance((1, 1, 1))
    
    contrast_with_black = contrast_ratio(bg_lum, black_lum)
    contrast_with_white = contrast_ratio(bg_lum, white_lum)

    return "black" if contrast_with_black > contrast_with_white else "white"

class TestedType(str,Enum):
    not_tested="empty"
    tested_correct="correct"
    tested_wrong="wrong"

class CorrectionType(int,Enum):
    improvement_possible=1
    correction_necessary=2
    correction_positiv=3

def icon_assignment_template(color: str, border: str, cross: str, check: str, tested: TestedType = None, corrected: CorrectionType = None):

    lines = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">\n'
    lines += f'   <rect x="10" y="10" width="80" height="80" fill="none" stroke="{border}" stroke-width="5"/>\n'
    lines += f'   <rect x="15" y="15" width="70" height="70" fill="{color}"/>\n'

    if tested == None or tested == TestedType.not_tested:
        pass

    elif tested == TestedType.tested_correct:
        lines += f'   <path d="M30,50 L42,68 L75,32" fill="none" stroke="{check}" stroke-width="14"/>\n'

    elif tested == TestedType.tested_wrong:
        lines += f'   <path d="M25,25 L75,75" fill="none" stroke="{cross}" stroke-width="14"/>\n'
        lines += f'   <path d="M75,25 L25,75" fill="none" stroke="{cross}" stroke-width="14"/>\n'

    lines += '</svg>'

    return lines

def icon_unit_template(color: str, theme: str):

    default_header_color ="#ffe760"

    theme_color = best_contrast_color(color)
    print(f"{color} -> {theme_color}")

    return f'''
<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <!-- Hintergrundkarte (Unit) -->
  <rect x="10" y="10" width="80" height="80" rx="8" ry="8" fill="{color}" stroke="black" stroke-width="4"/>

  <!-- Kalender-Header -->
  <rect x="10" y="10" width="80" height="20" fill="{lighten_color(color, 0.7)}" stroke="black" stroke-width="4"/>

</svg>
'''


#     <!-- Linien für Text -->
#   <line x1="40" y1="40" x2="80" y2="40" stroke="{theme_color}" stroke-width="8"/>
#   <line x1="40" y1="60" x2="80" y2="60" stroke="{theme_color}" stroke-width="8"/>
#   <line x1="40" y1="80" x2="80" y2="80" stroke="{theme_color}" stroke-width="8"/>

#   <!-- Kleine Aufgaben-Kästchen -->
#   <rect x="20" y="35" width="15" height="11" fill="{theme_color}" stroke="black" stroke-width="1.5"/>
#   <rect x="20" y="55" width="15" height="11" fill="{theme_color}" stroke="black" stroke-width="1.5"/>
#   <rect x="20" y="75" width="15" height="11" fill="{theme_color}" stroke="black" stroke-width="1.5"/>

