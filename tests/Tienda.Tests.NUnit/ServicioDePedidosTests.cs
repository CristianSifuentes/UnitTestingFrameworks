using Microsoft.Extensions.Time.Testing;

namespace Tienda.Pruebas;

public class ServicioDePedidosTests
{
    private RepositorioEnMemoria _repositorio = null!;
    private NotificadorEspia _notificador = null!;
    private FakeTimeProvider _reloj = null!;
    private ServicioDePedidos _servicio = null!;

    [SetUp]
    public void Preparar()
    {
        _repositorio = new();
        _notificador = new();
        _reloj = new(new DateTimeOffset(2026, 11, 8, 12, 0, 0, TimeSpan.Zero));
        _servicio = new(_repositorio, _notificador, _reloj);
    }

    private static Carrito CarritoCon(Producto producto)
    {
        var carrito = new Carrito();
        carrito.Agregar(producto);
        return carrito;
    }

    [Test, CancelAfter(5_000)]
    public async Task Confirmar_guarda_y_notifica(CancellationToken ct)
    {
        var pedido = await _servicio.ConfirmarAsync(CarritoCon(Catalogo.Taza), "ana@ejemplo.mx", ct);

        Assert.That(await _repositorio.BuscarAsync(pedido.Id, ct), Is.EqualTo(pedido));
        Assert.That(_notificador.Enviados, Has.Count.EqualTo(1));
        Assert.That(_notificador.Enviados[0].Destinatario, Is.EqualTo("ana@ejemplo.mx"));
        Assert.That(_notificador.Enviados[0].Mensaje, Does.EndWith("120.00 MXN"));
    }

    [Test]
    public async Task Confirmar_un_carrito_vacio_falla()
    {
        await Assert.ThrowsAsync<InvalidOperationException>(() => _servicio.ConfirmarAsync(new Carrito(), "x@y.z"));
        Assert.That(_notificador.Enviados, Is.Empty);
    }

    [Test]
    public async Task Se_puede_cancelar_dentro_de_las_24_horas()
    {
        var pedido = await _servicio.ConfirmarAsync(CarritoCon(Catalogo.Libro), "eva@ejemplo.mx");

        _reloj.Advance(TimeSpan.FromHours(23));
        var cancelado = await _servicio.CancelarAsync(pedido.Id);

        Assert.That(cancelado.Estado, Is.EqualTo(EstadoDePedido.Cancelado));
    }

    [Test]
    public async Task No_se_puede_cancelar_despues_de_24_horas()
    {
        var pedido = await _servicio.ConfirmarAsync(CarritoCon(Catalogo.Libro), "eva@ejemplo.mx");

        _reloj.Advance(TimeSpan.FromHours(24) + TimeSpan.FromSeconds(1));

        await Assert.ThatAsync(() => _servicio.CancelarAsync(pedido.Id), Throws.InvalidOperationException);
    }

    [Test]
    public async Task Respeta_la_cancelacion()
    {
        using var cts = new CancellationTokenSource();
        await cts.CancelAsync();

        await Assert.CatchAsync<OperationCanceledException>(
            () => _servicio.ConfirmarAsync(CarritoCon(Catalogo.Taza), "x@y.z", cts.Token));
    }
}
