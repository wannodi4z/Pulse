"""Build two complete, isolated UI alternatives without changing the stable application."""
import argparse,subprocess,zipfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build(output):
    output.mkdir(parents=True,exist_ok=True)
    # Only tracked files enter a release: no local database, keys, environment or caches.
    files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    for key,label in [('orbit','Orbit'),('prisma','Prisma')]:
        dest=output/('Operational_Pulse_'+label)
        if dest.exists():shutil.rmtree(dest)
        dest.mkdir()
        for name in files:
            src=ROOT/name
            if name and src.is_file() and not name.startswith('.git/'):
                target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
        theme=dest/'frontend/static/alternative.css';shutil.copy2(ROOT/'alternatives'/key/'theme.css',theme)
        shutil.copy2(ROOT/'alternatives/presentation-base.css',dest/'frontend/static/presentation-base.css')
        shutil.copy2(ROOT/'alternatives/presentation.js',dest/'frontend/static/presentation.js')
        index=dest/'frontend/index.html';html=index.read_text();html=html.replace('<html lang="es-MX">','<html lang="es-MX" data-experience="'+key+'">');html=html.replace('</head>','  <link rel="stylesheet" href="/static/presentation-base.css?v=1.0.10-'+key+'">\n  <link rel="stylesheet" href="/static/alternative.css?v=1.0.10-'+key+'">\n  <script src="/static/presentation.js?v=1.0.10-'+key+'" defer></script>\n</head>').replace('<title>Operational Pulse</title>','<title>Operational Pulse · '+label+'</title>');index.write_text(html)
        (dest/'LEEME_ALTERNATIVA.md').write_text(f'''# Pulse {label} · alternativa de interfaz

Basada en v1.0.10. Proyecto completo, mismos permisos, API, cálculos y flujos.

1. Extrae esta carpeta en una ubicación distinta de la versión estable.
2. Instala el entorno como indica README.md y ejecuta start.command.
3. Detén cualquier otra instancia en el puerto 5510 antes de abrir ésta.
4. Al estrenarse, utiliza los datos de demostración incluidos; no incluye tu base personal.

No mezcles archivos entre alternativas ni reemplaces la carpeta estable para probar.
Para usar una copia de tus datos, detén Pulse y copia juntos la base .db y su .key a esta carpeta, conservando el original. El respaldo personal .pulse conserva su función habitual.

La composición visual está en frontend/static/presentation.js, presentation-base.css y alternative.css. Es una nueva distribución de menús, pantallas y componentes; usa las mismas acciones, formularios y API. app.js, layout.js y el backend originales se conservan sin cambios. El manual general corresponde a la interfaz estable; consulta la comparación visual de estas alternativas.
''')
        archive=output/('Operational_Pulse_'+label+'_Alternativa_Completa.zip')
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for path in sorted(dest.rglob('*')):
                if path.is_file():z.write(path,Path(dest.name)/path.relative_to(dest))
        print(dest);print(archive)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT.parent/'deliverables'/'alternativas');build(ap.parse_args().output)
