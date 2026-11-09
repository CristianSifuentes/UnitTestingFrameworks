using Microsoft.Extensions.Time.Testing;

namespace Tienda.Pruebas;

[TestClass]
public sealed class ServicioDePedidosTests
{
    private readonly RepositorioEnMemoria _repositorio = new();
    private readonly NotificadorEspia _notificador = new();
    private readonly FakeTimeProvider _reloj = new(new DateTimeOffset(2026, 11, 8, 12, 0, 0, TimeSpan.Zero));
    private readonly ServicioDePedidos _servicio;

    // MSTest inyecta el TestContext por constructor (MSTest 3.6+).
    public ServicioDePedidosTests(TestContext contexto)
    {
        Contexto = contexto;
        _servicio = new(_repositorio, _notificador, _reloj);
    }

    public TestContext Contexto { get; }

    private static Carrito CarritoCon(Producto producto)
    {
        var carrito = new Carrito();
        carrito.Agregar(producto);
        return carrito;
    }

    [TestMethod]
    public async Task Confirmar_guarda_y_notifica()
    {
        var ct = Contexto.CancellationToken;

        var pedido = await _servicio.ConfirmarAsync(CarritoCon(Catalogo.Taza), "ana@ejemplo.mx", ct);

        Assert.AreEqual(pedido, await _repositorio.BuscarAsync(pedido.Id, ct));
        var (destinatario, mensaje) = Assert.ContainsSingle(_notificador.Enviados);
        Assert.AreEqual("ana@ejemplo.mx", destinatario);
        Assert.EndsWith("120.00 MXN", mensaje);
    }

    [TestMethod]
    public async Task Confirmar_un_carrito_vacio_falla()
    {
        await Assert.ThrowsExactlyAsync<InvalidOperationException>(
            () => _servicio.ConfirmarAsync(new Carrito(), "x@y.z", Contexto.CancellationToken));
        Assert.IsEmpty(_notificador.Enviados);
    }

    [TestMethod]
    public async Task Se_puede_cancelar_dentro_de_las_24_horas()
    {
        var ct = Contexto.CancellationToken;
        var pedido = await _servicio.ConfirmarAsync(CarritoCon(Catalogo.Libro), "eva@ejemplo.mx", ct);

        _reloj.Advance(TimeSpan.FromHours(23));
        var cancelado = await _servicio.CancelarAsync(pedido.Id, ct);

        Assert.AreEqual(EstadoDePedido.Cancelado, cancelado.Estado);
    }

    [TestMethod]
    public async Task No_se_puede_cancelar_despues_de_24_horas()
    {
        var ct = Contexto.CancellationToken;
        var pedido = await _servicio.ConfirmarAsync(CarritoCon(Catalogo.Libro), "eva@ejemplo.mx", ct);

        _reloj.Advance(TimeSpan.FromHours(24) + TimeSpan.FromSeconds(1));

        await Assert.ThrowsExactlyAsync<InvalidOperationException>(() => _servicio.CancelarAsync(pedido.Id, ct));
    }

    [TestMethod]
    public async Task Respeta_la_cancelacion()
    {
        using var cts = new CancellationTokenSource();
        await cts.CancelAsync();

        await Assert.ThrowsAsync<OperationCanceledException>(
            () => _servicio.ConfirmarAsync(CarritoCon(Catalogo.Taza), "x@y.z", cts.Token));
    }
}
