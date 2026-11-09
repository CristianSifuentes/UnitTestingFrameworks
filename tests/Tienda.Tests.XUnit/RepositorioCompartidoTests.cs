namespace Tienda.Pruebas;

// Fixture de clase: se crea una vez para todas las pruebas de la clase y se libera al final.
public sealed class RepositorioFixture : IAsyncLifetime
{
    public RepositorioEnMemoria Repositorio { get; } = new();

    public async ValueTask InitializeAsync()
    {
        var semilla = new Pedido(Guid.Empty, [], Dinero.Cero(), DateTimeOffset.UnixEpoch);
        await Repositorio.GuardarAsync(semilla);
    }

    public ValueTask DisposeAsync() => ValueTask.CompletedTask;
}

public class RepositorioCompartidoTests(RepositorioFixture fixture, ITestOutputHelper salida)
    : IClassFixture<RepositorioFixture>
{
    [Fact]
    public async Task La_semilla_existe()
    {
        var semilla = await fixture.Repositorio.BuscarAsync(Guid.Empty, TestContext.Current.CancellationToken);

        Assert.NotNull(semilla);
        salida.WriteLine($"Pedidos en el repositorio: {fixture.Repositorio.Cantidad}");
    }

    [Fact]
    public async Task Un_id_desconocido_devuelve_null()
    {
        Assert.Null(await fixture.Repositorio.BuscarAsync(Guid.NewGuid(), TestContext.Current.CancellationToken));
    }
}
