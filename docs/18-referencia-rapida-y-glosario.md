<div align="center">

# 18 · Referencia rápida y glosario

**Plantillas mínimas, comandos, filtros, configuración y un glosario de 50 términos**

[⬅ 17 · Catálogo A–Z](17-catalogo-a-z.md) · [🏠 Índice](../README.md) · [19 · Laboratorio ➡](19-laboratorio.md)

</div>

---

## Contenido

1. [Plantillas mínimas](#1-plantillas-mínimas)
2. [Crear proyectos](#2-crear-proyectos)
3. [Ejecutar](#3-ejecutar)
4. [Filtrar](#4-filtrar)
5. [Configuración en una página](#5-configuración-en-una-página)
6. [Glosario](#6-glosario)

---

## 1. Plantillas mínimas

Todo lo esencial de cada framework en una clase: preparación, limpieza, prueba simple, parametrizada, asíncrona y de excepción.

**xUnit.net v3**

```csharp xunit
public sealed class PlantillaXunitTests : IDisposable
{
    private readonly Carrito _sut = new();                                   // preparar

    [Fact]
    public void Simple() => Assert.True(_sut.EstaVacio);

    [Theory]
    [InlineData(1)]
    [InlineData(5)]
    public void Parametrizada(int n)
    {
        _sut.Agregar(Catalogo.Taza, n);
        Assert.Equal(n, _sut.Unidades);
    }

    [Fact]
    public async Task Asincrona() =>
        Assert.Null(await new RepositorioEnMemoria().BuscarAsync(Guid.NewGuid(), TestContext.Current.CancellationToken));

    [Fact]
    public void Excepcion() => Assert.Throws<ArgumentOutOfRangeException>(() => _sut.Agregar(Catalogo.Taza, 0));

    public void Dispose() { }                                                  // limpiar
}
```

**NUnit 5**

```csharp nunit
public class PlantillaNunitTests
{
    private Carrito _sut = null!;

    [SetUp] public void Preparar() => _sut = new Carrito();
    [TearDown] public void Limpiar() { }

    [Test]
    public void Simple() => Assert.That(_sut.EstaVacio);

    [TestCase(1)]
    [TestCase(5)]
    public void Parametrizada(int n)
    {
        _sut.Agregar(Catalogo.Taza, n);
        Assert.That(_sut.Unidades, Is.EqualTo(n));
    }

    [Test]
    public async Task Asincrona() =>
        Assert.That(await new RepositorioEnMemoria().BuscarAsync(Guid.NewGuid()), Is.Null);

    [Test]
    public void Excepcion() => Assert.That(() => _sut.Agregar(Catalogo.Taza, 0), Throws.TypeOf<ArgumentOutOfRangeException>());
}
```

**MSTest 4**

```csharp mstest
[TestClass]
public sealed class PlantillaMstestTests
{
    private readonly Carrito _sut = new();

    public TestContext TestContext { get; set; } = null!;

    [TestInitialize] public void Preparar() { }
    [TestCleanup] public void Limpiar() { }

    [TestMethod]
    public void Simple() => Assert.IsTrue(_sut.EstaVacio);

    [TestMethod]
    [DataRow(1)]
    [DataRow(5)]
    public void Parametrizada(int n)
    {
        _sut.Agregar(Catalogo.Taza, n);
        Assert.AreEqual(n, _sut.Unidades);
    }

    [TestMethod]
    public async Task Asincrona() =>
        Assert.IsNull(await new RepositorioEnMemoria().BuscarAsync(Guid.NewGuid(), TestContext.CancellationToken));

    [TestMethod]
    public void Excepcion() => Assert.ThrowsExactly<ArgumentOutOfRangeException>(() => _sut.Agregar(Catalogo.Taza, 0));
}
```

---

## 2. Crear proyectos

```bash
# xUnit.net v3
dotnet new install xunit.v3.templates
dotnet new xunit3 -n MiApp.Tests

# NUnit
dotnet new nunit -n MiApp.Tests

# MSTest con MSTest.Sdk
dotnet new mstest -n MiApp.Tests --sdk

# Referenciar el proyecto bajo prueba
dotnet add MiApp.Tests reference src/MiApp

# Solución en formato .slnx (SDK de .NET 9.0.200 o posterior)
dotnet new sln --format slnx
dotnet sln add MiApp.Tests
```

---

## 3. Ejecutar

| Tarea | Comando (modo MTP del SDK de .NET 10) |
|---|---|
| Toda la solución | `dotnet test` |
| Un proyecto | `dotnet test --project tests/Tienda.Tests.XUnit` |
| Sin compilar | `dotnet test --no-build` |
| Listar pruebas | `dotnet test --list-tests` |
| El ejecutable directamente | `dotnet run --project tests/Tienda.Tests.NUnit` |
| Con TRX | `dotnet test --report-trx --results-directory artefactos` |
| Con cobertura | `dotnet test --coverage --coverage-output-format cobertura` |
| Las 10 más lentas | `dotnet test --show-slowest-tests 10` |
| Exigir un mínimo de pruebas | `dotnet test --minimum-expected-tests 99` |
| Tiempo máximo de la sesión | `dotnet test --timeout 20m` |
| Depurar desde la terminal | `dotnet test --project X --debug` |
| Diagnóstico de la plataforma | `dotnet test --diagnostic --diagnostic-verbosity trace` |

---

## 4. Filtrar

| Objetivo | xUnit.net v3 | NUnit 5 / MSTest 4 (sintaxis VSTest) |
|---|---|---|
| Una clase | `--filter-class "*.CarritoTests"` | `--filter "FullyQualifiedName~CarritoTests"` |
| Un método | `--filter-method "*.Simple"` | `--filter "Name=Simple"` |
| Un espacio de nombres | `--filter-namespace "Tienda.Pruebas"` | `--filter "FullyQualifiedName~Tienda.Pruebas"` |
| Una categoría | `--filter-trait "Category=Lenta"` | `--filter "TestCategory=Lenta"` |
| Excluir una categoría | `--filter-not-trait "Category=Lenta"` | `--filter "TestCategory!=Lenta"` |
| Combinar | `--filter-query "/*/Tienda.Pruebas/CarritoTests/*[Category=Rapida]"` | `--filter "TestCategory=Rapida&FullyQualifiedName~Carrito"` |
| Por identificador único | `--filter-uid …` | `--filter-uid …` |

Operadores de la sintaxis de VSTest: `=` igual, `!=` distinto, `~` contiene, `!~` no contiene, `&` y, `|` o, paréntesis para agrupar.

---

## 5. Configuración en una página

```json
// global.json: SDK y modo MTP de dotnet test
{
  "sdk": { "version": "10.0.100", "rollForward": "latestFeature" },
  "test": { "runner": "Microsoft.Testing.Platform" },
  "msbuild-sdks": { "MSTest.Sdk": "4.5.2" }
}
```

```json
// xunit.runner.json (copiar a la salida)
{
  "$schema": "https://xunit.net/schema/current/xunit.runner.schema.json",
  "parallelizeTestCollections": true,
  "maxParallelThreads": "default",
  "methodDisplay": "method",
  "methodDisplayOptions": "replaceUnderscoreWithSpace",
  "culture": "invariant"
}
```

```json
// testconfig.json (MSTest sobre MTP)
{
  "mstest": {
    "parallelism": { "enabled": true, "scope": "method", "workers": 0 },
    "timeout": { "test": 30000, "useCooperativeCancellation": true }
  }
}
```

```xml
<!-- .runsettings (VSTest, y NUnit sobre MTP con --settings) -->
<RunSettings>
  <NUnit>
    <NumberOfTestWorkers>4</NumberOfTestWorkers>
    <DefaultTimeout>30000</DefaultTimeout>
  </NUnit>
  <TestRunParameters>
    <Parameter name="Entorno" value="ci" />
  </TestRunParameters>
</RunSettings>
```

---

## 6. Glosario

| Término | Definición |
|---|---|
| **AAA** | *Arrange, Act, Assert*: preparar, actuar, afirmar. Estructura canónica de una prueba |
| **Adaptador** | Componente que conecta un framework con la plataforma (`NUnit3TestAdapter`, `xunit.runner.visualstudio`, `MSTest.TestAdapter`) |
| **Analizador** | Regla de Roslyn que detecta errores en el código de pruebas durante la compilación |
| **Aserción** | Comprobación que lanza una excepción si no se cumple |
| **Caso de prueba** | Cada ejecución individual; una prueba parametrizada genera varios |
| **CI** | Integración continua: compilar y probar automáticamente cada cambio |
| **Colección** (xUnit.net) | Grupo de clases que no se ejecutan en paralelo entre sí y pueden compartir fixture |
| **Cobertura** | Proporción de líneas o ramas ejecutadas por las pruebas |
| **Contexto de prueba** | Objeto con información de la prueba en curso (`TestContext`) |
| **CTRF** | *Common Test Report Format*: formato JSON de resultados |
| **Datapoint** (NUnit) | Valor candidato para una teoría de NUnit |
| **Descubrimiento** | Fase en que la plataforma encuentra las pruebas, antes de ejecutarlas |
| **Desplegar / plegar** | Mostrar cada fila de datos como un caso independiente, o agruparlas en uno |
| **Doble de prueba** | Sustituto de una dependencia: *dummy*, *stub*, *spy*, *mock* o *fake* |
| **Dummy** | Doble que se pasa pero nunca se usa |
| **Explícita** | Prueba que solo se ejecuta si se selecciona expresamente |
| **Extensión** (MTP) | Paquete que añade capacidades a la plataforma: TRX, cobertura, volcados, reintentos |
| **Fact** (xUnit.net) | Prueba sin parámetros: una afirmación siempre cierta |
| **Fake** | Doble con una implementación funcional simplificada (`RepositorioEnMemoria`) |
| **`FakeTimeProvider`** | Reloj controlable de `Microsoft.Extensions.TimeProvider.Testing` |
| **Fixture** | Contexto preparado para una o varias pruebas; en NUnit, también la clase de pruebas |
| **Flaky** | Prueba inestable: pasa o falla sin cambios en el código |
| **Inconclusa** | Resultado de una prueba cuyo supuesto no se cumplió (`Assume`, `Assert.Inconclusive`) |
| **Instancia por prueba** | Modelo en que cada prueba recibe un objeto nuevo de su clase |
| **JUnit XML** | Formato XML de resultados, el más aceptado por servidores de CI |
| **Matriz** | Producto cartesiano de varios conjuntos de valores |
| **Mock** | Doble que verifica las interacciones esperadas |
| **MTP** | Microsoft.Testing.Platform: la plataforma de pruebas como ejecutable |
| **Mutación** | Técnica que altera el código para comprobar si las pruebas lo detectan |
| **Native AOT** | Compilación anticipada a código nativo, sin JIT ni reflexión dinámica |
| **Object Mother** | Clase que fabrica objetos de prueba con nombre de negocio |
| **Orderer** (xUnit.net) | Componente que decide el orden de colecciones, clases, métodos o casos |
| **Pairwise** | Combinación por pares: cubre cada par de valores con menos casos |
| **Prueba de propiedades** | Prueba que comprueba una ley sobre muchas entradas generadas |
| **Restricción** (NUnit) | Objeto que describe una condición en `Assert.That(real, restricción)` |
| **Runner** | Programa que ejecuta las pruebas e informa los resultados |
| **`.runsettings`** | Archivo XML de configuración de VSTest |
| **SetUpFixture** (NUnit) | Clase con preparación para todo un espacio de nombres |
| **Snapshot** | Prueba que compara una salida con un archivo aprobado (Verify) |
| **Spy** | Doble que registra cómo se le llamó |
| **STA** | *Single-Threaded Apartment*: modelo de hilos que exigen WPF, WinForms y COM |
| **Stub** | Doble que devuelve respuestas preparadas |
| **SUT** | *System Under Test*: el código que se prueba |
| **`testconfig.json`** | Archivo JSON de configuración de MTP y MSTest |
| **TDD** | Desarrollo guiado por pruebas: rojo, verde, refactorizar |
| **Teoría** | xUnit.net: prueba parametrizada. NUnit: prueba con *datapoints* y supuestos |
| **`TimeProvider`** | Abstracción de .NET 8 para el reloj y los temporizadores |
| **Trait** | Par clave-valor de metadatos en xUnit.net |
| **TRX** | Formato XML de resultados de Visual Studio y Azure DevOps |
| **VSTest** | Plataforma de pruebas clásica de Microsoft (`vstest.console`, `testhost`) |

---

<div align="center">

[⬅ 17 · Catálogo A–Z](17-catalogo-a-z.md) · [🏠 Índice](../README.md) · [19 · Laboratorio ➡](19-laboratorio.md)

</div>
