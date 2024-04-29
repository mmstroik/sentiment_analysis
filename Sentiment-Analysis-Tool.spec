# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/mmstr/projects/sentiment_analysis/pie_icon.ico', '.'), ('C:/Users/mmstr/miniconda3/envs/sentiment//Lib/site-packages/sv_ttk', 'sv_ttk'), ('C:/Users/mmstr/miniconda3/envs/sentiment/Lib/site-packages/aiohttp', 'aiohttp'), ('C:/Users/mmstr/miniconda3/envs/sentiment/Lib/site-packages/pandas', 'pandas'), ('C:/Users/mmstr/miniconda3/envs/sentiment/Lib/site-packages/openpyxl', 'openpyxl'), ('C:/Users/mmstr/miniconda3/envs/sentiment/Lib/site-packages/tiktoken', 'tiktoken')],
    hiddenimports=['requests', 'charset_normalizer', 'tiktoken'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Sentiment-Analysis-Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['pie_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Sentiment-Analysis-Tool',
)
