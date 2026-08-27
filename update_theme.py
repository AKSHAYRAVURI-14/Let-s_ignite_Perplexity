import re

css_path = 'c:/Users/nagav/perplexity/static/style.css'
js_path = 'c:/Users/nagav/perplexity/static/script.js'

with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

# Replace variables in root
root_replacements = {
    "--bg-primary: #150a0d;": "--bg-primary: #ffffff;",
    "--bg-secondary: rgba(43, 17, 24, 0.6);": "--bg-secondary: rgba(250, 250, 250, 0.85);",
    "--text-primary: #fdfcfaf0;": "--text-primary: #2c2c2c;",
    "--text-secondary: #dca889;": "--text-secondary: #7f8c8d;",
    "--accent: #dcb36d;": "--accent: #d4af37;",
    "--accent-glow: rgba(220, 179, 109, 0.4);": "--accent-glow: rgba(212, 175, 55, 0.4);",
    "--accent-dark: #8c1c27;": "--accent-dark: #a88825;",
    "--border-color: rgba(220, 179, 109, 0.3);": "--border-color: rgba(189, 195, 199, 0.6);",
    "--card-shadow: 0 15px 40px -10px rgba(0,0,0,0.7);": "--card-shadow: 0 15px 40px -10px rgba(0,0,0,0.08);"
}
for old, new in root_replacements.items():
    css = css.replace(old, new)

# Update gradients and rgba shadows
css = css.replace("rgba(140, 28, 39, 0.15)", "rgba(212, 175, 55, 0.05)")
css = css.replace("rgba(220, 179, 109, 0.1)", "rgba(189, 195, 199, 0.15)")
css = css.replace("rgba(0,0,0,0.6)", "rgba(0,0,0,0.03)")
css = css.replace("rgba(0,0,0,0.5)", "rgba(0,0,0,0.05)")
css = css.replace("color: #ff3366;", "color: var(--accent);")
css = css.replace("rgba(220, 179, 109, 0.05)", "rgba(212, 175, 55, 0.05)")
css = css.replace("linear-gradient(90deg, var(--accent-dark), transparent)", "linear-gradient(90deg, rgba(212, 175, 55, 0.15), transparent)")
css = css.replace("rgba(21, 10, 13, 0.7)", "rgba(255, 255, 255, 0.7)")
css = css.replace("linear-gradient(135deg, var(--accent), #f9e2b0)", "linear-gradient(135deg, #ffffff, #f1f2f6)")
css = css.replace("color: #3b2203;", "color: var(--accent-dark); border: 1px solid var(--accent);")
css = css.replace("linear-gradient(135deg, var(--accent-dark), #4a0d13)", "linear-gradient(135deg, #ecf0f1, #bdc3c7)")
css = css.replace("rgba(140, 28, 39, 0.6)", "rgba(212, 175, 55, 0.3)")
css = css.replace("rgba(0,0,0,0.8)", "rgba(0,0,0,0.05)")
css = css.replace("rgba(26, 11, 15, 0.8)", "rgba(255, 255, 255, 0.9)")
css = css.replace("rgba(0, 0, 0, 0.6)", "rgba(0,0,0,0.05)")
css = css.replace("rgba(220, 179, 109, 0.25)", "rgba(212, 175, 55, 0.15)")
css = css.replace("rgba(220, 179, 109, 0.5)", "var(--text-secondary)")
css = css.replace("rgba(140, 28, 39, 0.8)", "var(--accent-glow)")
css = css.replace("linear-gradient(135deg, var(--accent-dark), #4a0d13) !important", "linear-gradient(135deg, var(--accent), var(--accent-dark)) !important")
css = css.replace("color: var(--accent) !important", "color: #fff !important")
css = css.replace("background: var(--accent) !important", "background: #fff !important")
css = css.replace("color: #1a0b0e !important", "color: var(--accent-dark) !important")
css = css.replace("rgba(26, 11, 15, 0.5)", "rgba(255, 255, 255, 0.8)")
css = css.replace("rgba(0,0,0,0.3)", "rgba(0,0,0,0.05)")
css = css.replace("rgba(140, 28, 39, 0.4)", "rgba(212, 175, 55, 0.15)")
css = css.replace("rgba(0,0,0,0.4)", "rgba(0,0,0,0.05)")
css = css.replace("background: var(--bg-primary);", "background: #ffffff;")
css = css.replace("background: var(--accent-dark);", "background: var(--bg-secondary);")
# For Ai-avatar and user-avatar overrides in messages
css = css.replace(".ai-avatar {\n    background: var(--bg-primary);\n    color: var(--accent);\n}", ".ai-avatar {\n    background: #ffffff;\n    color: var(--accent-dark);\n}")
css = css.replace(".user .message-content {\n    background: rgba(212, 175, 55, 0.05);\n    padding: 18px 26px;\n    border-radius: 12px 12px 0 12px;\n    border: 1px solid var(--border-color);\n    box-shadow: 0 8px 25px rgba(0,0,0,0.05);\n    color: var(--accent);\n    font-style: italic;\n}", ".user .message-content {\n    background: rgba(212, 175, 55, 0.08);\n    padding: 18px 26px;\n    border-radius: 12px 12px 0 12px;\n    border: 1px solid rgba(212, 175, 55, 0.3);\n    box-shadow: 0 8px 25px rgba(0,0,0,0.05);\n    color: var(--text-primary);\n}")
css = css.replace("background: rgba(220, 179, 109, 0.08);", "background: rgba(189, 195, 199, 0.15);")
css = css.replace("border: 1px solid rgba(220, 179, 109, 0.3);", "border: 1px solid rgba(189, 195, 199, 0.6);")

with open(css_path, 'w', encoding='utf-8') as f:
    f.write(css)

with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

js = js.replace("webBtn.style.background = 'var(--accent-dark)';", "webBtn.style.background = 'rgba(212, 175, 55, 0.15)';")
js = js.replace("webBtn.style.color = 'var(--accent)';", "webBtn.style.color = 'var(--accent-dark)';")
js = js.replace("webBtn.style.boxShadow = '0 0 15px rgba(140, 28, 39, 0.8)';", "webBtn.style.boxShadow = '0 0 15px var(--accent-glow)';")
js = js.replace("rgba(255,255,255,0.1)", "var(--border-color)")
js = js.replace("micBtn.style.color = '#ff4757';", "micBtn.style.color = 'var(--accent-dark)';")

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated style.css and script.js")
