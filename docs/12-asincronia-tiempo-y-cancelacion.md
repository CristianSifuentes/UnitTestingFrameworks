<div align="center">

# 12 · Asincronía, tiempo y cancelación

**Pruebas `async` correctas, el reloj como dependencia con `TimeProvider`, tiempos máximos cooperativos y tokens de cancelación en los tres frameworks**

[⬅ 11 · Paralelismo y aislamiento](11-paralelismo-y-aislamiento.md) · [🏠 Índice](../README.md) · [13 · Dobles de prueba y ecosistema ➡](13-dobles-de-prueba-y-ecosistema.md)

</div>

---

## Contenido

1. [Pruebas asíncronas: las reglas](#1-pruebas-asíncronas-las-reglas)
2. [El reloj es una dependencia](#2-el-reloj-es-una-dependencia)
3. [`FakeTimeProvider` en acción](#3-faketimeprovider-en-acción)
4. [Tiempos máximos](#4-tiempos-máximos)
5. [Tokens de cancelación](#5-tokens-de-cancelación)
6. [Esperar sin dormir](#6-esperar-sin-dormir)
7. [Contexto de sincronización e hilos STA](#7-contexto-de-sincronización-e-hilos-sta)

---

## 1. Pruebas asíncronas: las reglas

| Regla | Por qué | Analizador |
|---|---|---|
| La prueba devuelve `Task` (o `ValueTask` en xUnit.net) | El framework espera su finalización y recoge sus excepciones | `xUnit1048`, `NUnit1012`, `MSTEST0003` |
| **Nunca `async void`** | Las excepciones escapan al framework; la prueba "pasa" antes de terminar | Los tres |
| Nunca `.Result`, `.Wait()` ni `GetAwaiter().GetResult()` | Bloquea un hilo; puede provocar interbloqueos y agota el *pool* en paralelo | `xUnit1031`, `MSTEST0067` |
| Espera las aserciones asíncronas | `Assert.ThrowsAsync` sin `await` no comprueba nada | `xUnit2021`, NUnit 5, `MSTEST0064` |
| Pasa el token del contexto | Permite que el tiempo máximo y la cancelación funcionen | `xUnit1051`, `MSTEST0049` |
| Sin `ConfigureAwait(false)` en la prueba | No aporta nada en una prueba y puede romper el contexto de sincronización | `xUnit1030` |

---

## 2. El reloj es una dependencia

`DateTime.Now` es una **entrada oculta**: cambia en cada llamada y no se puede controlar. Desde .NET 8, la abstracción estándar es **`TimeProvider`**, y el paquete
`Microsoft.Extensions.TimeProvider.Testing` aporta **`FakeTimeProvider`**, un reloj que solo avanza cuando la prueba lo ordena.

| En producción | En pruebas |
|---|---|
| `TimeProvider.System` | `new FakeTimeProvider(fechaInicial)` |
| `reloj.GetUtcNow()` | Devuelve exactamente la fecha fijada |
| `Task.Delay(t, reloj)` | Se completa cuando la prueba llama a `Advance(t)` |
| `reloj.CreateTimer(…)` | Se dispara al avanzar el tiempo |
| `new PeriodicTimer(t, reloj)` | Cada `Advance` produce los *ticks* correspondientes |

El `ServicioDePedidos` del laboratorio recibe un `TimeProvider` y permite cancelar un pedido solo durante 24 horas: con un reloj falso, la regla se prueba **al segundo** y sin
esperar un día.

---

## 3. `FakeTimeProvider` en acción

```csharp xunit
using Microsoft.Extensions.Time.Testing;

public class PlazoDeCancelacionTests
{
    private readonly FakeTimeProvider _reloj = new(new DateTimeOffset(2026, 11, 8, 12, 0, 0, TimeSpan.Zero));
    private readonly ServicioDePedidos _servicio;

    public PlazoDeCancelacionTests() =>
        _servicio = new(new RepositorioEnMemoria(), new NotificadorEspia(), _reloj);

    private async Task<Pedido> PedidoConfirmadoAsync()
    {
        var carrito = new Carrito();
        carrito.Agregar(Catalogo.Libro);
        return await _servicio.ConfirmarAsync(carrito, "eva@ejemplo.mx", TestContext.Current.CancellationToken);
    }

    [Theory]
    [InlineData(0)]
    [InlineData(23 * 3600)]
    [InlineData(24 * 3600)]          // justo en el límite: aún se puede
    public async Task Se_puede_cancelar_hasta_las_24_horas(int segundos)
    {
        var pedido = await PedidoConfirmadoAsync();

        _reloj.Advance(TimeSpan.FromSeconds(segundos));

        var cancelado = await _servicio.CancelarAsync(pedido.Id, TestContext.Current.CancellationToken);
        Assert.Equal(EstadoDePedido.Cancelado, cancelado.Estado);
    }

    [Fact]
    public async Task Un_segundo_despues_ya_no()
    {
        var pedido = await PedidoConfirmadoAsync();

        _reloj.Advance(TimeSpan.FromHours(24) + TimeSpan.FromSeconds(1));

        await Assert.ThrowsAsync<InvalidOperationException>(
            () => _servicio.CancelarAsync(pedido.Id, TestContext.Current.CancellationToken));
    }

    [Fact]
    public async Task Los_retrasos_avanzan_con_el_reloj_falso()
    {
        var espera = Task.Delay(TimeSpan.FromMinutes(30), _reloj, TestContext.Current.CancellationToken);
        Assert.False(espera.IsCompleted);

        _reloj.Advance(TimeSpan.FromMinutes(30));     // media hora en microsegundos

        await espera;
        Assert.True(espera.IsCompletedSuccessfully);
    }
}
```

> [!TIP]
> Los límites (exactamente 24 horas, un segundo después) son donde viven los errores de `<` frente a `<=`. Con un reloj real son imposibles de probar; con `FakeTimeProvider`
> son una fila más de una teoría.

---

## 4. Tiempos máximos

| | xUnit.net v3 | NUnit 5 | MSTest 4 |
|---|---|---|---|
| Atributo | `[Fact(Timeout = ms)]` · `[Theory(Timeout = ms)]` | `[CancelAfter(ms)]` · `[Timeout(ms)]` (.NET Framework) · `[MaxTime(ms)]` | `[Timeout(ms)]` |
| Global | — | `.runsettings` `DefaultTimeout` | `testconfig.json` `timeout.test` |
| Mecanismo | Cancela `TestContext.Current.CancellationToken` y deja de esperar la prueba | Cancela el token (`CancelAfter`); `MaxTime` solo mide | Cancela `TestContext.CancellationToken`; con `CooperativeCancellation = true` espera a que la prueba termine |
| ¿Aborta el hilo? | No | Solo `[Timeout]` en .NET Framework | No |
| Bajo el depurador | Desactivado | — | — |
| Tiempo máximo de la sesión | `--timeout` (MTP) | `--timeout` (MTP) | `--timeout` (MTP) |

> [!IMPORTANT]
> En .NET moderno **ningún** framework puede detener a la fuerza código que no coopera: `Thread.Abort` no existe. Un tiempo máximo sin token solo hace que el framework *deje de
> esperar*; el código sigue ejecutándose en segundo plano, consumiendo recursos y, quizá, contaminando otras pruebas. **Pasa siempre el token.**

```csharp nunit
public class TiempoMaximoTests
{
    [Test, CancelAfter(1_000)]
    public async Task El_token_llega_como_parametro(CancellationToken ct)
    {
        var repositorio = new RepositorioEnMemoria();

        await repositorio.GuardarAsync(new Pedido(Guid.NewGuid(), [], Dinero.Cero(), DateTimeOffset.UtcNow), ct);

        Assert.That(repositorio.Cantidad, Is.EqualTo(1));
    }
}
```

```csharp mstest
[TestClass]
public sealed class TiempoMaximoTests
{
    public TestContext TestContext { get; set; } = null!;

    [TestMethod]
    [Timeout(1_000, CooperativeCancellation = true)]
    public async Task El_token_esta_en_el_contexto()
    {
        var repositorio = new RepositorioEnMemoria();

        await repositorio.GuardarAsync(new Pedido(Guid.NewGuid(), [], Dinero.Cero(), DateTimeOffset.UtcNow), TestContext.CancellationToken);

        Assert.AreEqual(1, repositorio.Cantidad);
    }
}
```

---

## 5. Tokens de cancelación

Probar que **tu código** respeta la cancelación es tan importante como dar a tus pruebas un tiempo máximo:

```csharp xunit
public class CancelacionTests
{
    [Fact]
    public async Task Confirmar_respeta_un_token_ya_cancelado()
    {
        using var cts = new CancellationTokenSource();
        await cts.CancelAsync();
        var espia = new NotificadorEspia();
        var servicio = new ServicioDePedidos(new RepositorioEnMemoria(), espia, TimeProvider.System);
        var carrito = new Carrito();
        carrito.Agregar(Catalogo.Taza);

        await Assert.ThrowsAnyAsync<OperationCanceledException>(() => servicio.ConfirmarAsync(carrito, "x@y.z", cts.Token));

        Assert.Empty(espia.Enviados);   // y no produjo efectos secundarios
    }

    [Fact]
    public async Task Cancelar_a_mitad_de_camino()
    {
        var reloj = new Microsoft.Extensions.Time.Testing.FakeTimeProvider();
        using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5), reloj);   // el plazo usa el reloj falso
        var espera = Task.Delay(TimeSpan.FromMinutes(1), reloj, cts.Token);

        reloj.Advance(TimeSpan.FromSeconds(5));

        await Assert.ThrowsAsync<TaskCanceledException>(() => espera);
    }
}
```

`ThrowsAnyAsync<OperationCanceledException>` es la forma correcta en xUnit.net porque el código puede lanzar `TaskCanceledException`, que deriva de `OperationCanceledException`. En
MSTest, `Assert.ThrowsAsync<OperationCanceledException>` ya acepta derivados; en NUnit, `Assert.CatchAsync<OperationCanceledException>`.

---

## 6. Esperar sin dormir

`Thread.Sleep(2000)` y `await Task.Delay(2000)` en una prueba son apuestas: demasiado cortos fallan en una máquina lenta, demasiado largos ralentizan toda la suite.

| En lugar de… | Usa… |
|---|---|
| Dormir y esperar que el trabajo haya terminado | `await` directo sobre la tarea, o `TaskCompletionSource` que el doble completa |
| Dormir para que pase el tiempo | `FakeTimeProvider.Advance` |
| Sondear con un bucle y `Sleep` | Sondeo con tiempo máximo y token (`while (!cond) await Task.Delay(10, ct)`) como último recurso |
| Esperar a un evento | `Assert.RaisesAsync` (xUnit.net) o un `TaskCompletionSource` suscrito al evento |

```csharp nunit
public class SinDormirTests
{
    private sealed class NotificadorQueAvisa : INotificador
    {
        public TaskCompletionSource<string> Enviado { get; } = new(TaskCreationOptions.RunContinuationsAsynchronously);

        public Task EnviarAsync(string destinatario, string mensaje, CancellationToken ct = default)
        {
            Enviado.TrySetResult(destinatario);
            return Task.CompletedTask;
        }
    }

    [Test, CancelAfter(2_000)]
    public async Task Espera_la_senal_no_el_reloj(CancellationToken ct)
    {
        var notificador = new NotificadorQueAvisa();
        var servicio = new ServicioDePedidos(new RepositorioEnMemoria(), notificador, TimeProvider.System);
        var carrito = new Carrito();
        carrito.Agregar(Catalogo.Libro);

        _ = servicio.ConfirmarAsync(carrito, "ana@ejemplo.mx", ct);   // se lanza sin esperar

        Assert.That(await notificador.Enviado.Task.WaitAsync(ct), Is.EqualTo("ana@ejemplo.mx"));
    }
}
```

---

## 7. Contexto de sincronización e hilos STA

| | xUnit.net v3 | NUnit 5 | MSTest 4 |
|---|---|---|---|
| Contexto de sincronización en la prueba | Gestionado por el framework según la configuración de paralelismo | Ninguno (salvo STA) | Ninguno (salvo STA) |
| Hilo STA (WPF, WinForms, COM) | Bibliotecas externas (`Xunit.StaFact`) | `[Apartment(ApartmentState.STA)]` | `[STATestMethod]`, `[STATestClass]`; `UseSTASynchronizationContext` (4.1) |
| Pruebas de UI de Windows | — | — | `[UITestMethod]` (UWP/WinUI) · `MSTest.Windows.UIAutomation` (4.5, vista previa) |

---

<div align="center">

[⬅ 11 · Paralelismo y aislamiento](11-paralelismo-y-aislamiento.md) · [🏠 Índice](../README.md) · [13 · Dobles de prueba y ecosistema ➡](13-dobles-de-prueba-y-ecosistema.md)

</div>
