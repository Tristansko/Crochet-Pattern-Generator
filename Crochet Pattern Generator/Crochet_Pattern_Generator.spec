\
    # PyInstaller spec for Crochet Pattern Generator
    # Build with: pyinstaller crochet_pattern_gui_fully_commented.spec
    # Produces a single-file executable in the `dist/` folder.

    block_cipher = None

    import sys
    import os
    import matplotlib

    from PyInstaller.utils.hooks import collect_submodules, collect_data_files
    hiddenimports = collect_submodules('matplotlib')
    datas = collect_data_files('matplotlib', subdir=None, include_py_files=False)

    a = Analysis(
        ['Crochet_Pattern_Generator.py'],
        pathex=[],
        binaries=[],
        datas=datas,
        hiddenimports=hiddenimports,
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
        noarchive=False,
    )
    pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='CrochetPatternGenerator',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,   # set True if you want a console window for logs
        icon=None,       # set to a .ico (Windows) or .icns (macOS) path if you have one
    )
