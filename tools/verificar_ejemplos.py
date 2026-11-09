#!/usr/bin/env python3
"""Compila y ejecuta cada bloque ```csharp del atlas con el framework de pruebas que declara.

Cada framework recibe un proyecto de verificación propio en `.verificacion/<fw>/`, con los mismos
paquetes (Directory.Packages.props) y la misma biblioteca de dominio (src/Tienda.Dominio) que el
laboratorio. Los bloques se envuelven en un espacio de nombres único, se compilan con
TreatWarningsAsErrors y luego se ejecutan con `dotnet test`: todas las pruebas deben pasar.

Marcas en Markdown
  <!-- fw=xunit -->        framework por defecto para los bloques siguientes del archivo
  ```csharp xunit          bloque para xUnit.net v3     (también: nunit, mstest)
  ```csharp dominio        C# sin framework de pruebas: se compila en los tres proyectos, visible para todos
  ```csharp metodos        el bloque son miembros sueltos: se envuelven en una clase de pruebas
  ```csharp aislado        se compila en un proyecto propio (p. ej., atributos [assembly: ...])
  ```csharp omitir         no se compila: sintaxis histórica, pseudocódigo o API de terceros

Uso:
  python3 tools/verificar_ejemplos.py [--solo xunit] [--lista] [--sin-ejecutar]
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / ".verificacion"
FRAMEWORKS = ("xunit", "nunit", "mstest")
MARCAS = set(FRAMEWORKS) | {"dominio", "metodos", "aislado", "omitir"}

# Proyecto de verificación por framework: el mismo que usa el laboratorio.
PROYECTOS = {
    "xunit": """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><OutputType>Exe</OutputType><RootNamespace>Tienda.Pruebas</RootNamespace>
  <NoWarn>$(NoWarn);CS1998;xUnit1051</NoWarn></PropertyGroup>
  <ItemGroup>
    <PackageReference Include="xunit.v3" />
    <PackageReference Include="Microsoft.Extensions.TimeProvider.Testing" />
    <Using Include="Xunit" />
  </ItemGroup>
{comun}
</Project>""",
    "nunit": """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><OutputType>Exe</OutputType><EnableNUnitRunner>true</EnableNUnitRunner>
  <RootNamespace>Tienda.Pruebas</RootNamespace><NoWarn>$(NoWarn);CS1998</NoWarn></PropertyGroup>
  <ItemGroup>
    <PackageReference Include="NUnit" />
    <PackageReference Include="NUnit3TestAdapter" />
    <PackageReference Include="NUnit.Analyzers" PrivateAssets="all" />
    <PackageReference Include="Microsoft.Extensions.TimeProvider.Testing" />
    <Using Include="NUnit.Framework" />
  </ItemGroup>
{comun}
</Project>""",
    "mstest": """<Project Sdk="MSTest.Sdk">
  <PropertyGroup><RootNamespace>Tienda.Pruebas</RootNamespace><NoWarn>$(NoWarn);CS1998</NoWarn></PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.Extensions.TimeProvider.Testing" />
  </ItemGroup>
{comun}
</Project>""",
}
COMUN = """  <ItemGroup>
    <ProjectReference Include="{raiz}/src/Tienda.Dominio/Tienda.Dominio.csproj" />
    <Compile Include="{raiz}/tests/Comun/*.cs" Link="Comun/%(Filename)%(Extension)" />
  </ItemGroup>"""
CLASE = {
    "xunit": "public class Metodos_{n}\n{{\n{codigo}\n}}",
    "nunit": "public class Metodos_{n}\n{{\n{codigo}\n}}",
    "mstest": "[TestClass]\npublic class Metodos_{n}\n{{\n{codigo}\n}}",
}


@dataclass
class Bloque:
    archivo: Path
    linea: int
    codigo: str
    fw: str | None
    marcas: set[str] = field(default_factory=set)

    @property
    def nombre(self) -> str:
        return f"{self.archivo.relative_to(RAIZ)}:{self.linea}"

    @property
    def ident(self) -> str:
        base = re.sub(r"\W", "_", self.archivo.stem)
        return f"E{base}_L{self.linea}"


def leer_bloques(archivo: Path) -> list[Bloque]:
    bloques: list[Bloque] = []
    fw: str | None = None
    lineas = archivo.read_text(encoding="utf-8").split("\n")
    i = 0
    while i < len(lineas):
        directiva = re.fullmatch(r"\s*<!--\s*fw=(\w+)\s*-->\s*", lineas[i])
        if directiva:
            fw = directiva.group(1)
        apertura = re.fullmatch(r"(\s*)```csharp(.*)", lineas[i])
        if apertura:
            sangria, info = apertura.group(1), apertura.group(2).split()
            inicio = i + 1
            cuerpo: list[str] = []
            i += 1
            while not re.fullmatch(r"\s*```\s*", lineas[i]):
                cuerpo.append(lineas[i][len(sangria):] if lineas[i].startswith(sangria) else lineas[i])
                i += 1
            desconocidas = set(info) - MARCAS
            if desconocidas:
                raise SystemExit(f"{archivo}:{inicio}: marca desconocida {desconocidas}")
            propio = next((m for m in info if m in FRAMEWORKS), None)
            if "dominio" in info:
                propio = "xunit"
            b = Bloque(archivo, inicio, "\n".join(cuerpo), propio or fw, set(info))
            if b.fw is None and "omitir" not in b.marcas:
                raise SystemExit(f"{b.nombre}: el bloque no declara framework (xunit, nunit, mstest, dominio u omitir)")
            bloques.append(b)
        i += 1
    return bloques


def fuente(b: Bloque) -> str:
    lineas = b.codigo.split("\n")
    usings = [l for l in lineas if re.match(r"\s*(global\s+)?using\s+[\w.=\s<>]+;\s*$", l) and "(" not in l]
    ensamblado = [l for l in lineas if l.lstrip().startswith("[assembly:")]
    resto = "\n".join(l for l in lineas if l not in usings and l not in ensamblado)
    if "metodos" in b.marcas:
        resto = CLASE[b.fw].format(n=b.linea, codigo=resto)
    # Los atributos de ensamblado quedan fuera del espacio de nombres: se califican los typeof(...) del bloque.
    ensamblado = [re.sub(r"typeof\((\w+)\)", rf"typeof(Tienda.Pruebas.Ejemplos.{b.ident}.\1)", l) for l in ensamblado]
    cabecera = f"// Generado desde {b.nombre}\n" + "\n".join(u.strip() for u in usings)
    espacio = "Tienda.Pruebas.Ejemplos" if "dominio" in b.marcas else f"Tienda.Pruebas.Ejemplos.{b.ident}"
    return f"{cabecera}\n" + "\n".join(ensamblado) + f"\nnamespace {espacio}\n{{\n{resto}\n}}\n"


def preparar(directorio: Path, fw: str, bloques: list[Bloque]) -> None:
    if directorio.exists():
        shutil.rmtree(directorio)
    directorio.mkdir(parents=True)
    comun = COMUN.format(raiz=RAIZ.as_posix())
    (directorio / f"Verificacion.{fw}.csproj").write_text(PROYECTOS[fw].format(comun=comun), encoding="utf-8")
    vistos: set[str] = set()
    for b in bloques:
        texto = fuente(b)
        # Atributos de ensamblado idénticos en varios bloques: se conserva solo el primero.
        for l in re.findall(r"^\[assembly:.*$", texto, flags=re.M):
            if l in vistos:
                texto = texto.replace(l + "\n", "", 1)
            vistos.add(l)
        (directorio / f"{b.ident}.cs").write_text(texto, encoding="utf-8")


def ejecutar(directorio: Path, correr: bool) -> tuple[bool, str]:
    orden = ["dotnet", "test" if correr else "build", "--project" if correr else "", str(directorio)]
    r = subprocess.run([x for x in orden if x], cwd=RAIZ, capture_output=True, text=True)
    salida = r.stdout + r.stderr
    errores = sorted({m.group(0) for m in re.finditer(r"[^\s]+\.cs\(\d+,\d+\): error [^\[]+", salida)})
    if r.returncode != 0:
        return False, "\n".join(errores[:40]) or salida[-4000:]
    total = re.search(r"(?:total|Total)[^\d]*(\d+)", salida)
    return True, total.group(1) if total else "?"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solo", choices=FRAMEWORKS)
    ap.add_argument("--lista", action="store_true", help="solo lista los bloques y sus marcas")
    ap.add_argument("--sin-ejecutar", action="store_true", help="compila sin ejecutar las pruebas")
    args = ap.parse_args()

    archivos = [RAIZ / "README.md", *sorted((RAIZ / "docs").glob("*.md"))]
    bloques = [b for a in archivos for b in leer_bloques(a)]
    omitidos = [b for b in bloques if "omitir" in b.marcas]
    activos = [b for b in bloques if "omitir" not in b.marcas and (args.solo is None or b.fw == args.solo)]

    if args.lista:
        for b in bloques:
            print(f"{b.nombre:55} {b.fw or '-':7} {' '.join(sorted(b.marcas))}")
        print(f"\n{len(bloques)} bloques · {len(omitidos)} omitidos")
        return

    grupos: dict[str, list[Bloque]] = {}
    dominio = [b for b in bloques if "dominio" in b.marcas]
    for b in activos:
        if "dominio" in b.marcas:
            continue
        clave = f"{b.fw}-{b.ident}" if "aislado" in b.marcas else b.fw
        grupos.setdefault(clave, []).append(b)
    # Los bloques de dominio se comparten: entran en cada proyecto que no esté aislado.
    for clave, lote in grupos.items():
        if "-" not in clave:
            lote.extend(dominio)
    activos = [b for b in activos if "dominio" not in b.marcas] + dominio

    fallos = 0
    pruebas = 0
    for clave, lote in sorted(grupos.items()):
        fw = clave.split("-")[0]
        directorio = SALIDA / clave
        preparar(directorio, fw, lote)
        ok, detalle = ejecutar(directorio, not args.sin_ejecutar)
        estado = "✅" if ok else "❌"
        print(f"{estado} {clave:40} {len(lote):3} bloques" + (f" · {detalle} pruebas" if ok else ""))
        if ok and detalle.isdigit():
            pruebas += int(detalle)
        if not ok:
            fallos += 1
            print("   " + detalle.replace("\n", "\n   "))

    print(f"\n{len(activos)} bloques verificados · {pruebas} pruebas ejecutadas · {len(omitidos)} omitidos"
          f" · {fallos} proyectos con errores")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
