using Microsoft.Extensions.Time.Testing;

namespace Tienda.Pruebas;

public class ServicioDePedidosTests
{
    private readonly RepositorioEnMemoria _repositorio = new();
    private readonly NotificadorEspia _notificador = new();
    private readonly FakeTimeProvider _reloj = new(new DateTimeOffset(2026, 11, 8, 12, 0, 0, TimeSpan.Zero));
    private readonly ServicioDePedidos _servicio;

    public ServicioDePedidosTests() => _servicio = new(_repositorio, _notificador, _reloj);

    private static Carrito CarritoCon(Producto producto)
    {
        var carrito = new Carrito();
        carrito.Agregar(producto);
        return carrito;
    }

    [Fact]
    public async Task Confirmar_guarda_y_notifica()
    {
        var ct = TestContext.Current.CancellationToken;

        var pedido = await _servicio.ConfirmarAsync(CarritoCon(Catalogo.Taza), "ana@ejemplo.mx", ct);

        Assert.Equal(pedido, await _repositorio.BuscarAsync(pedido.Id, ct));
        var (destinatario, mensaje) = Assert.Single(_notificador.Enviados);
        Assert.Equal("ana@ejemplo.mx", destinatario);
        Assert.EndsWith("120.00 MXN", mensaje);
    }

    [Fact]
    public async Task Confirmar_un_carrito_vacio_falla()
    {
        await Assert.ThrowsAsync<InvalidOperationException>(
            () => _servicio.ConfirmarAsync(new Carrito(), "x@y.z", TestContext.Current.CancellationToken));
        Assert.Empty(_notificador.Enviados);
    }

    [Fact]
    public async Task Se_puede_cancelar_dentro_de_las_24_horas()
    {
        var ct = TestContext.Current.CancellationToken;
        var pedido = await _servicio.ConfirmarAsync(CarritoCon(Catalogo.Libro), "eva@ejemplo.mx", ct);

        _reloj.Advance(TimeSpan.FromHours(23));
        var cancelado = await _servicio.CancelarAsync(pedido.Id, ct);

        Assert.Equal(EstadoDePedido.Cancelado, cancelado.Estado);
    }

    [Fact]
    public async Task No_se_puede_cancelar_despues_de_24_horas()
    {
        var ct = TestContext.Current.CancellationToken;
        var pedido = await _servicio.ConfirmarAsync(CarritoCon(Catalogo.Libro), "eva@ejemplo.mx", ct);

        _reloj.Advance(TimeSpan.FromHours(24) + TimeSpan.FromSeconds(1));

        await Assert.ThrowsAsync<InvalidOperationException>(() => _servicio.CancelarAsync(pedido.Id, ct));
    }

    [Fact]
    public async Task Respeta_la_cancelacion()
    {
        using var cts = new CancellationTokenSource();
        await cts.CancelAsync();

        await Assert.ThrowsAnyAsync<OperationCanceledException>(
            () => _servicio.ConfirmarAsync(CarritoCon(Catalogo.Taza), "x@y.z", cts.Token));
    }
}
