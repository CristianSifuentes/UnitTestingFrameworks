<div align="center">

# 08 · Aserciones

**Tres estilos, mensajes reales de fallo, igualdad y equivalencia, excepciones, tolerancias, aserciones múltiples y bibliotecas externas**

[⬅ 07 · Piedra Rosetta](07-piedra-rosetta.md) · [🏠 Índice](../README.md) · [09 · Pruebas parametrizadas ➡](09-pruebas-parametrizadas.md)

</div>

> [!NOTE]
> Todos los mensajes de fallo de este capítulo son **salida real**, capturada ejecutando pruebas que fallan a propósito con `xunit.v3` 4.0.2, `NUnit` 5.0.0 y `MSTest` 4.5.2.
> MSTest localiza sus mensajes según la cultura del sistema; aquí aparecen en español.

---

## Contenido

1. [Tres estilos de aserción](#1-tres-estilos-de-aserción)
2. [El mensaje es el producto](#2-el-mensaje-es-el-producto)
3. [Igualdad](#3-igualdad)
4. [Equivalencia y colecciones](#4-equivalencia-y-colecciones)
5. [Excepciones](#5-excepciones)
6. [Números, fechas y tolerancias](#6-números-fechas-y-tolerancias)
7. [Aserciones múltiples](#7-aserciones-múltiples)
8. [Aserciones de dominio](#8-aserciones-de-dominio)
9. [Bibliotecas externas](#9-bibliotecas-externas)
10. [Reglas de los analizadores](#10-reglas-de-los-analizadores)

---

## 1. Tres estilos de aserción

| Estilo | Forma | Framework | Ventaja | Inconveniente |
|---|---|---|---|---|
| **Por intención** | `Assert.Equal(esperado, real)` | xUnit.net, MSTest, `ClassicAssert` de NUnit | Directo; el nombre dice qué se comprueba | Un método por caso; el orden de argumentos se confunde |
| **Restricciones** | `Assert.That(real, Is.EqualTo(esperado))` | NUnit | Componible (`And`, `Or`, `Not`), extensible, se lee como una frase | Más verboso; hay que aprender el vocabulario |
| **Expresión** | `Assert.That(() => a == b && c > 0)` | MSTest 4 | Cualquier condición, con el valor de cada subexpresión en el mensaje | Menos específico que un método dedicado |
| **Fluido** (externo) | `real.Should().Be(esperado)` | FluentAssertions, AwesomeAssertions, Shouldly | Se lee de izquierda a derecha | Dependencia externa; licencias |

---

## 2. El mensaje es el producto

Una aserción se escribe una vez y se **lee** cada vez que falla. Comparemos los mensajes reales de tres fallos típicos.

### Cadenas distintas

```text
xUnit.net v3
      Assert.Equal() Failure: Strings differ
                         ↓ (pos 8)
      Expected: "Pedido confirmado"
      Actual:   "Pedido cancelado"
                         ↑ (pos 8)

NUnit 5
    Assert.That("Pedido cancelado", Is.EqualTo("Pedido confirmado"))
    Expected string length 17 but was 16. Strings differ at index 8.
    Expected: "Pedido confirmado"
    But was:  "Pedido cancelado"
    -------------------^

MSTest 4
  Assertion failed. Se esperaba que las cadenas fueran iguales.
  Las cadenas tienen longitudes diferentes (se esperaba: 17, real: 16) y difieren en 1 ubicación(s). Primera diferencia en el índice 8.
  expected:   "Pedido confirmado"
  actual:     "Pedido cancelado"
  difference: ---------^
  Assert.AreEqual("Pedido confirmado", "Pedido cancelado")
```

### Colecciones distintas

```text
xUnit.net v3
      Assert.Equal() Failure: Collections differ
                       ↓ (pos 2)
      Expected: [1, 2, 4]
      Actual:   [1, 2, 3]
                       ↑ (pos 2)

NUnit 5
    Assert.That(a, Is.EqualTo(new[]{1,2,4}))
    Expected and actual are both <System.Int32[3]>
    Values differ at index [2]
    Expected: 4
    But was:  3

MSTest 4
  CollectionAssert.AreEqual erróneo. El elemento del índice 2 no coincide.
  Esperado: 4
  Real: 3
```

### Una condición booleana

```text
xUnit.net v3                         Assert.True() Failure
                                     Expected: True
                                     Actual:   False

NUnit 5                              Assert.That(c.Unidades > 0, Is.True)
                                     Expected: True
                                     But was:  False

MSTest 4 · Assert.IsTrue             Assert.IsTrue(c.Unidades > 0)
                                     Se esperaba true · Real false

MSTest 4 · Assert.That(() => …)      Assert.That(() => c.Unidades > 0) erróneo.
                                     Detalles:
                                       c.Unidades = 0
```

| Lección | Detalle |
|---|---|
| **El código fuente en el mensaje** | NUnit 4+ y MSTest 4 incluyen la expresión gracias a `CallerArgumentExpression`; xUnit.net no, pero marca la posición de la diferencia con flechas |
| **`Assert.True(condición)` es la aserción más pobre** | Solo dice "esperaba verdadero". MSTest `Assert.That(() => …)` es la excepción: muestra el valor de cada subexpresión |
| **Usa la aserción más específica** | `Assert.Equal(5, c.Count)` explica más que `Assert.True(c.Count == 5)`; los analizadores (`xUnit2013`, `MSTEST0037`, `NUnit2045`…) lo sugieren |
| **`ToString()` importa** | Los tres imprimen `810.00 MXN` porque `Dinero` redefine `ToString` |

---

## 3. Igualdad

Los tres frameworks usan, en este orden: `IEquatable<T>`, `Equals` redefinido y, para colecciones (salvo `Assert.AreEqual` de MSTest), comparación elemento a elemento. Los
`record` de C# implementan igualdad por valor, por eso `Assert.Equal(new Dinero(810m), total)` funciona sin código extra.

Comparadores personalizados, cuando la igualdad natural no sirve:

<!-- fw=xunit -->

```csharp
public class IgualdadPorSkuTests
{
    private sealed class PorSku : IEqualityComparer<Producto>
    {
        public bool Equals(Producto? x, Producto? y) => x?.Sku == y?.Sku;
        public int GetHashCode(Producto p) => p.Sku.GetHashCode(StringComparison.Ordinal);
    }

    [Fact]
    public void Dos_productos_con_el_mismo_sku_son_iguales_para_el_catalogo()
    {
        var original = Catalogo.Libro;
        var rebajado = original with { Precio = new Dinero(300m) };

        Assert.NotEqual(original, rebajado);                 // igualdad del record: todas las propiedades
        Assert.Equal(original, rebajado, new PorSku());      // igualdad de catálogo: solo el SKU
    }
}
```

```csharp nunit
public class IgualdadPorSkuTests
{
    [Test]
    public void Dos_productos_con_el_mismo_sku_son_iguales_para_el_catalogo()
    {
        var original = Catalogo.Libro;
        var rebajado = original with { Precio = new Dinero(300m) };

        Assert.That(rebajado, Is.Not.EqualTo(original));
        Assert.That(rebajado, Is.EqualTo(original).Using<Producto>((a, b) => a.Sku == b.Sku));
    }
}
```

```csharp mstest
[TestClass]
public sealed class IgualdadPorSkuTests
{
    private sealed class PorSku : IEqualityComparer<Producto>
    {
        public bool Equals(Producto? x, Producto? y) => x?.Sku == y?.Sku;
        public int GetHashCode(Producto p) => p.Sku.GetHashCode(StringComparison.Ordinal);
    }

    [TestMethod]
    public void Dos_productos_con_el_mismo_sku_son_iguales_para_el_catalogo()
    {
        var original = Catalogo.Libro;
        var rebajado = original with { Precio = new Dinero(300m) };

        Assert.AreNotEqual(original, rebajado);
        Assert.AreEqual(original, rebajado, new PorSku());
    }
}
```

---

## 4. Equivalencia y colecciones

"Equivalente" es la palabra más ambigua de la API de pruebas. Esto es lo que hace **realmente** cada método, comprobado en el laboratorio:

| Prueba | xUnit.net v3 `Assert.Equivalent` | NUnit 5 | MSTest 4.5 `Assert.AreEquivalent` |
|---|---|---|---|
| `[1, 2, 3]` frente a `[3, 2, 1]` | ✅ **Pasa: ignora el orden** | `Is.EquivalentTo`: ✅ pasa | ❌ **Falla: respeta el orden** |
| Objetos de **tipos distintos** con las mismas propiedades | ✅ Pasa | `UsingPropertiesComparer()`: ❌ `NotSupportedException` | ✅ Pasa |
| El real tiene **propiedades de más** | ✅ Pasa (modo no estricto) · ❌ con `strict: true` | — | — |
| Recorre objetos anidados | ✅ (profundidad máxima configurable) | ✅ | ✅ |

```text
xUnit.net v3 · Assert.Equivalent(new { Sku = "LIB-0001" }, linea, strict: true)
      Assert.Equivalent() Failure: Mismatched member list
      Expected: ["Sku"]
      Actual:   ["Sku", "Cantidad", "Nota"]

NUnit 5 · Is.EqualTo(anónimo).UsingPropertiesComparer() con un record
  System.NotSupportedException : No comparer found for instances of type '<>f__AnonymousType0`2[…]' and 'Linea'
```

### La trampa de `Assert.AreEqual` con colecciones en MSTest

```text
MSTest 4 · Assert.AreEqual(a, b) con int[] a = [1, 2, 3] e int[] b = [1, 2, 3]
  Assertion failed. Se esperaba que los valores fueran iguales.
  expected: [1, 2, 3]
  actual:   [1, 2, 3]
```

El mensaje muestra dos colecciones **idénticas** y aun así falla: `Assert.AreEqual` compara las **referencias** de los arreglos, no su contenido. El analizador `MSTEST0065`
(4.3) lo detecta. Las alternativas:

<!-- fw=mstest -->

```csharp
[TestClass]
public sealed class ColeccionesTests
{
    [TestMethod]
    public void Compara_contenido_no_referencias()
    {
        int[] real = [1, 2, 3];

        Assert.AreSequenceEqual([1, 2, 3], real);                        // mismo orden (4.3)
        CollectionAssert.AreEqual(new[] { 1, 2, 3 }, real);              // mismo orden
        CollectionAssert.AreEquivalent(new[] { 3, 1, 2 }, real);         // cualquier orden
        Assert.AreEquivalent<object>(new { Codigo = "ATLAS10", Porcentaje = 10m },  // estructural (4.3),
                                     new Cupon("ATLAS10", 10m));                    // aun entre tipos distintos
    }
}
```

Y en los otros dos frameworks:

```csharp xunit
public class ColeccionesTests
{
    [Fact]
    public void Inspecciona_cada_elemento()
    {
        var carrito = new Carrito();
        carrito.Agregar(Catalogo.Libro, 2);
        carrito.Agregar(Catalogo.Taza, 1);

        Assert.Equal(["LIB-0001", "TAZ-0007"], carrito.Lineas.Select(l => l.Producto.Sku).Order());
        Assert.Equivalent(new[] { 1, 2 }, carrito.Lineas.Select(l => l.Cantidad));   // sin orden
        Assert.All(carrito.Lineas, l => Assert.True(l.Cantidad > 0));
        Assert.Collection(carrito.Lineas.OrderBy(l => l.Producto.Sku),
            libro => Assert.Equal(2, libro.Cantidad),
            taza => Assert.Equal(1, taza.Cantidad));
        Assert.Contains(carrito.Lineas, l => l.Producto == Catalogo.Taza);
        Assert.DoesNotContain(carrito.Lineas, l => l.Producto == Catalogo.Teclado);
    }
}
```

```csharp nunit
public class ColeccionesTests
{
    [Test]
    public void Describe_la_coleccion_con_restricciones()
    {
        var carrito = new Carrito();
        carrito.Agregar(Catalogo.Libro, 2);
        carrito.Agregar(Catalogo.Taza, 1);
        var skus = carrito.Lineas.Select(l => l.Producto.Sku).ToList();

        Assert.That(skus, Is.EquivalentTo(new[] { "TAZ-0007", "LIB-0001" }));    // sin orden
        Assert.That(skus, Is.Unique);
        Assert.That(skus, Has.Exactly(1).StartsWith("TAZ"));
        Assert.That(skus, Is.All.Matches<string>(s => Tienda.Catalogo.EsSkuValido(s)));
        Assert.That(carrito.Lineas, Has.Some.Property(nameof(LineaDeCarrito.Cantidad)).EqualTo(2));
        Assert.That(skus, Does.Not.Contain("TEC-0300"));
    }
}
```

---

## 5. Excepciones

| | Tipo exacto | Tipo o derivado | Asíncrona |
|---|---|---|---|
| **xUnit.net** | `Assert.Throws<T>` | `Assert.ThrowsAny<T>` | `Assert.ThrowsAsync<T>`, `ThrowsAnyAsync<T>` |
| **NUnit** | `Assert.Throws<T>` · `Throws.TypeOf<T>()` | `Assert.Catch<T>` · `Throws.InstanceOf<T>()` | `await Assert.ThrowsAsync<T>` (NUnit 5) · `Assert.ThatAsync` |
| **MSTest** | `Assert.ThrowsExactly<T>` | `Assert.Throws<T>` | `ThrowsExactlyAsync<T>`, `ThrowsAsync<T>` |

`ArgumentNullException` deriva de `ArgumentException`. Esta prueba, idéntica en apariencia, se comporta distinto:

```csharp xunit
public class ExcepcionesTests
{
    [Fact]
    public void Exacto_frente_a_derivado()
    {
        static void Agregar() => new Carrito().Agregar(null!);   // lanza ArgumentNullException

        Assert.Throws<ArgumentNullException>(Agregar);           // exacto: pasa
        Assert.ThrowsAny<ArgumentException>(Agregar);            // derivado: pasa
        Assert.Throws<ArgumentNullException>("producto", Agregar); // y comprueba ParamName
    }

    [Fact]
    public async Task Asincronas()
    {
        var servicio = new ServicioDePedidos(new RepositorioEnMemoria(), new NotificadorEspia(), TimeProvider.System);

        var ex = await Assert.ThrowsAsync<InvalidOperationException>(
            () => servicio.ConfirmarAsync(new Carrito(), "x@y.z", TestContext.Current.CancellationToken));

        Assert.Equal("No se puede confirmar un carrito vacío.", ex.Message);
    }
}
```

```csharp mstest
[TestClass]
public sealed class ExcepcionesTests
{
    [TestMethod]
    public void Exacto_frente_a_derivado()
    {
        static void Agregar() => new Carrito().Agregar(null!);

        Assert.ThrowsExactly<ArgumentNullException>(Agregar);     // exacto
        var ex = Assert.Throws<ArgumentException>(Agregar);       // derivado: ¡Throws acepta subclases en MSTest!
        Assert.AreEqual("producto", ex.ParamName);
    }
}
```

> [!IMPORTANT]
> Ningún framework moderno conserva el atributo `[ExpectedException]`: xUnit.net nunca lo tuvo, NUnit lo quitó en la 3.0 y MSTest en la 4.0. El motivo es siempre el mismo: el
> atributo pasa si **cualquier línea** lanza la excepción, incluida la preparación, y oculta errores reales.

---

## 6. Números, fechas y tolerancias

`0.1 + 0.2` vale `0.30000000000000004` en `double`. Comparar números en coma flotante sin tolerancia es una fuente clásica de pruebas inestables.

<!-- fw=nunit -->

```csharp
public class ToleranciaTests
{
    [Test]
    public void Numeros_y_fechas_con_margen()
    {
        var suma = 0.1;
        suma += 0.2;
        var ahora = DateTimeOffset.UtcNow;
        var casiAhora = ahora.AddMilliseconds(30);

        Assert.That(suma, Is.EqualTo(0.3).Within(1e-9));
        Assert.That(suma, Is.EqualTo(0.3).Within(0.0001).Percent);
        Assert.That(casiAhora, Is.EqualTo(ahora).Within(TimeSpan.FromSeconds(1)));
    }
}
```

```csharp xunit
public class ToleranciaTests
{
    [Fact]
    public void Numeros_y_fechas_con_margen()
    {
        var suma = 0.1;
        suma += 0.2;
        var ahora = DateTimeOffset.UtcNow;

        Assert.Equal(0.3, suma, precision: 10);            // decimales
        Assert.Equal(0.3, suma, tolerance: 1e-9);          // margen absoluto
        Assert.Equal(ahora, ahora.AddMilliseconds(30), TimeSpan.FromSeconds(1));
    }
}
```

```csharp mstest
[TestClass]
public sealed class ToleranciaTests
{
    [TestMethod]
    public void Numeros_y_fechas_con_margen()
    {
        var suma = 0.1;
        suma += 0.2;
        var ahora = DateTimeOffset.UtcNow;

        Assert.AreEqual(0.3, suma, delta: 1e-9);
        Assert.IsInRange(ahora.AddSeconds(-1), ahora.AddSeconds(1), ahora.AddMilliseconds(30));
    }
}
```

> [!TIP]
> Para dinero usa `decimal`, no `double`: `decimal` es exacto en base 10 y no necesita tolerancia. Y para fechas, **no uses el reloj real**: inyecta un `TimeProvider` y
> controla el tiempo con `FakeTimeProvider` ([capítulo 12](12-asincronia-tiempo-y-cancelacion.md)).

---

## 7. Aserciones múltiples

Por defecto, la primera aserción que falla detiene la prueba. Cuando varias comprobaciones describen **un mismo resultado**, conviene verlas todas:

```text
xUnit.net v3 · Assert.Multiple(…)
      Assert.Multiple() Failure: Multiple failures were encountered
      ---- Assert.Equal() Failure: Values differ
      Expected: 1
      Actual:   2
      ---- Assert.Equal() Failure: Strings differ
      Expected: "a"
      Actual:   "b"

NUnit 5 · using (Assert.EnterMultipleScope())
  Multiple failures or warnings in test:
    1)   Assert.That(uno, Is.EqualTo(2))
    Expected: 2
    But was:  1
    2)   Assert.That(a, Is.EqualTo("b"))
    Expected: "b"
    But was:  "a"
```

MSTest no tiene un ámbito de aserciones múltiples; la alternativa idiomática es `Assert.That(() => cond1 && cond2)`, que informa el valor de cada subexpresión, o
`Assert.AreEquivalent` sobre un objeto que agrupe los valores esperados.

---

## 8. Aserciones de dominio

Cuando la misma comprobación se repite, conviértela en vocabulario del dominio. Cada framework tiene su forma natural:

| Framework | Forma idiomática | Ejemplo |
|---|---|---|
| xUnit.net | Método estático que lanza `XunitException` o usa otras aserciones | `AssertTienda.EsSkuValido(sku)` |
| NUnit | Restricción propia (`Constraint`) | `Assert.That(sku, EsSku.Valido)` ([capítulo 05](05-nunit.md#10-extensibilidad)) |
| MSTest | Método estático que usa `Assert.Fail` o `Assert.That` | `AssertTienda.EsSkuValido(sku)` |

```csharp xunit
using Xunit.Sdk;

public static class AssertTienda
{
    public static void EsSkuValido(string? sku)
    {
        if (!Tienda.Catalogo.EsSkuValido(sku))
            throw new XunitException($"Se esperaba un SKU con formato AAA-0000, pero se obtuvo \"{sku}\".");
    }

    public static void Vale(Carrito carrito, decimal monto) =>
        Assert.Equal(new Dinero(monto, carrito.Moneda), carrito.Total);
}

public class AsercionesDeDominioTests
{
    [Fact]
    public void Se_leen_como_el_negocio()
    {
        var carrito = new Carrito();
        carrito.Agregar(Catalogo.Libro, 2);

        AssertTienda.EsSkuValido(Catalogo.Libro.Sku);
        AssertTienda.Vale(carrito, 900m);
    }
}
```

---

## 9. Bibliotecas externas

| Biblioteca | Estilo | Licencia (nov-2026) | Versión | Nota |
|---|---|---|---|---|
| **FluentAssertions** | `x.Should().Be(y)` | **Comercial** desde la 8.0 (enero de 2025); gratuita para uso no comercial | 8.11.0 | La 7.x sigue siendo Apache 2.0 |
| **AwesomeAssertions** | `x.Should().Be(y)` | Apache 2.0 | 9.6.0 | *Fork* comunitario de FluentAssertions 7, nacido en enero de 2025 |
| **Shouldly** | `x.ShouldBe(y)` | BSD | 4.3.0 | Mensajes con el código fuente de la aserción |
| **Verify** | *Snapshot*: `await Verify(objeto)` | MIT | — | Compara contra un archivo aprobado; ideal para objetos grandes, JSON y HTML |

```csharp omitir
// FluentAssertions / AwesomeAssertions
carrito.Total.Should().Be(new Dinero(810m));
carrito.Lineas.Should().ContainSingle().Which.Cantidad.Should().Be(5);
act.Should().Throw<InvalidOperationException>().WithMessage("*Máximo*");

// Shouldly
carrito.Total.ShouldBe(new Dinero(810m));
Should.Throw<InvalidOperationException>(act).Message.ShouldContain("Máximo");

// Verify (snapshot): la primera ejecución crea Pedido.verified.txt
await Verify(pedido);
```

> [!WARNING]
> **Revisa la licencia antes de actualizar FluentAssertions.** Pasar de la 7.x a la 8.x en un proyecto comercial exige una licencia de pago. Las opciones habituales son quedarse en
> la 7.x, migrar a AwesomeAssertions (cambio de espacio de nombres casi mecánico) o usar las aserciones del framework, que en 2026 son mucho más completas que en 2015.

---

## 10. Reglas de los analizadores

| Problema | xUnit.net | NUnit | MSTest |
|---|---|---|---|
| Esperado y real invertidos | `xUnit2000` | `NUnit2005`, `NUnit2007` | `MSTEST0017` |
| Usar el método específico | `xUnit2013`, `xUnit2017` | `NUnit2045`… | `MSTEST0037` |
| Aserción que siempre pasa o falla | `xUnit2020` | — | `MSTEST0025`, `MSTEST0032` |
| Colecciones comparadas por referencia | — | — | `MSTEST0065` |
| Aserción asíncrona sin `await` | `xUnit2021` | NUnit 5 (4.14+) | `MSTEST0064` |
| Estilo clásico a restricciones | — | `NUnit2001`–`NUnit2049` | — |
| `CollectionAssert` a `Assert` | — | — | `MSTEST0068` |

---

<div align="center">

[⬅ 07 · Piedra Rosetta](07-piedra-rosetta.md) · [🏠 Índice](../README.md) · [09 · Pruebas parametrizadas ➡](09-pruebas-parametrizadas.md)

</div>
