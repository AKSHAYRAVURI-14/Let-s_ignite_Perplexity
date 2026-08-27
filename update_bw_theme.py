import re

css_path = 'c:/Users/nagav/perplexity/static/style.css'
js_path = 'c:/Users/nagav/perplexity/static/script.js'

with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

# Replace root variables
css = css.replace("--bg-primary: #fcfcfd;", "--bg-primary: #ffffff;")
css = css.replace("--bg-secondary: rgba(255, 255, 255, 0.75);", "--bg-secondary: rgba(255, 255, 255, 0.9);")
css = css.replace("--text-primary: #0a0a0a;", "--text-primary: #000000;")
css = css.replace("--text-secondary: #4a4a4f;", "--text-secondary: #333333;")
css = css.replace("--accent: #d4af37;", "--accent: #000000;")
css = css.replace("--accent-light: #fcf6e3;", "--accent-light: #f0f0f0;")
css = css.replace("--accent-glow: rgba(212, 175, 55, 0.4);", "--accent-glow: rgba(0, 0, 0, 0.2);")
css = css.replace("--accent-dark: #8c6e15;", "--accent-dark: #000000;")
css = css.replace("--border-color: rgba(212, 175, 55, 0.15);", "--border-color: rgba(0, 0, 0, 0.15);")
css = css.replace("--silver-glow: rgba(189, 195, 199, 0.4);", "--silver-glow: rgba(0, 0, 0, 0.1);")

# Replace rbga and hex values
css = re.sub(r'rgba\(212,\s*175,\s*55,\s*([^)]+)\)', r'rgba(0, 0, 0, \1)', css)
css = re.sub(r'rgba\(189,\s*195,\s*199,\s*([^)]+)\)', r'rgba(0, 0, 0, \1)', css)
css = css.replace("#dfba52", "#666666")
css = css.replace("#c29f31", "#444444")
css = css.replace("linear-gradient(135deg, var(--accent), var(--accent-dark)) !important;", "linear-gradient(135deg, #222222, #000000) !important;")
css = css.replace("color: #0a0a0a !important;", "color: #ffffff !important;")

# For user messages where the background becomes dark
css = css.replace("color: #0a0a0a;", "color: #ffffff;")

with open(css_path, 'w', encoding='utf-8') as f:
    f.write(css)

with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

js = re.sub(r'rgba\(212,\s*175,\s*55,\s*([^)]+)\)', r'rgba(0, 0, 0, \1)', js)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated style.css and script.js to black and white theme")
