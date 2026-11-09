namespace Tienda;

public enum EstadoDePedido { Confirmado, Cancelado }

public sealed record Pedido(Guid Id, IReadOnlyList<LineaDeCarrito> Lineas, Dinero Total, DateTimeOffset CreadoEn)
{
    public EstadoDePedido Estado { get; init; } = EstadoDePedido.Confirmado;
}

public interface IRepositorioDePedidos
{
    Task GuardarAsync(Pedido pedido, CancellationToken ct = default);
    Task<Pedido?> BuscarAsync(Guid id, CancellationToken ct = default);
}

public interface INotificador
{
    Task EnviarAsync(string destinatario, string mensaje, CancellationToken ct = default);
}

public sealed class RepositorioEnMemoria : IRepositorioDePedidos
{
    private readonly Dictionary<Guid, Pedido> _pedidos = [];
    private readonly Lock _candado = new();

    public int Cantidad { get { lock (_candado) return _pedidos.Count; } }

    public async Task GuardarAsync(Pedido pedido, CancellationToken ct = default)
    {
        await Task.Yield();
        ct.ThrowIfCancellationRequested();
        lock (_candado) _pedidos[pedido.Id] = pedido;
    }

    public async Task<Pedido?> BuscarAsync(Guid id, CancellationToken ct = default)
    {
        await Task.Yield();
        ct.ThrowIfCancellationRequested();
        lock (_candado) return _pedidos.GetValueOrDefault(id);
    }
}

/// <summary>Orquesta la confirmación: valida, persiste y notifica. El reloj se inyecta para que las pruebas sean deterministas.</summary>
public sealed class ServicioDePedidos(IRepositorioDePedidos repositorio, INotificador notificador, TimeProvider reloj)
{
    public async Task<Pedido> ConfirmarAsync(Carrito carrito, string correo, CancellationToken ct = default)
    {
        ArgumentNullException.ThrowIfNull(carrito);
        if (carrito.EstaVacio)
            throw new InvalidOperationException("No se puede confirmar un carrito vacío.");

        var pedido = new Pedido(Guid.NewGuid(), [.. carrito.Lineas], carrito.Total, reloj.GetUtcNow());
        await repositorio.GuardarAsync(pedido, ct);
        await notificador.EnviarAsync(correo, $"Pedido {pedido.Id:N} por {pedido.Total}", ct);
        return pedido;
    }

    /// <summary>Un pedido solo puede cancelarse durante las primeras 24 horas.</summary>
    public async Task<Pedido> CancelarAsync(Guid id, CancellationToken ct = default)
    {
        var pedido = await repositorio.BuscarAsync(id, ct)
            ?? throw new KeyNotFoundException($"No existe el pedido {id}.");
        if (reloj.GetUtcNow() - pedido.CreadoEn > TimeSpan.FromHours(24))
            throw new InvalidOperationException("El plazo de cancelación de 24 horas venció.");

        var cancelado = pedido with { Estado = EstadoDePedido.Cancelado };
        await repositorio.GuardarAsync(cancelado, ct);
        return cancelado;
    }
}
