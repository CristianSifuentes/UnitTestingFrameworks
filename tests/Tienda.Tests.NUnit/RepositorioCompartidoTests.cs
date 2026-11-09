namespace Tienda.Pruebas;

// [OneTimeSetUp] se ejecuta una vez por fixture: equivale a la fixture de clase de xUnit.
public class RepositorioCompartidoTests
{
    private RepositorioEnMemoria _repositorio = null!;

    [OneTimeSetUp]
    public async Task SembrarAsync()
    {
        _repositorio = new RepositorioEnMemoria();
        await _repositorio.GuardarAsync(new Pedido(Guid.Empty, [], Dinero.Cero(), DateTimeOffset.UnixEpoch));
    }

    [Test]
    public async Task La_semilla_existe()
    {
        Assert.That(await _repositorio.BuscarAsync(Guid.Empty), Is.Not.Null);
        TestContext.Out.WriteLine($"Pedidos en el repositorio: {_repositorio.Cantidad}");
    }

    [Test]
    public async Task Un_id_desconocido_devuelve_null()
    {
        Assert.That(await _repositorio.BuscarAsync(Guid.NewGuid()), Is.Null);
    }
}
