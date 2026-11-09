namespace Tienda.Pruebas;

// [ClassInitialize] es estático y se ejecuta una vez por clase.
[TestClass]
public sealed class RepositorioCompartidoTests
{
    private static RepositorioEnMemoria s_repositorio = null!;

    public TestContext TestContext { get; set; } = null!;

    [ClassInitialize]
    public static async Task SembrarAsync(TestContext _)
    {
        s_repositorio = new RepositorioEnMemoria();
        await s_repositorio.GuardarAsync(new Pedido(Guid.Empty, [], Dinero.Cero(), DateTimeOffset.UnixEpoch));
    }

    [TestMethod]
    public async Task La_semilla_existe()
    {
        Assert.IsNotNull(await s_repositorio.BuscarAsync(Guid.Empty, TestContext.CancellationToken));
        TestContext.WriteLine($"Pedidos en el repositorio: {s_repositorio.Cantidad}");
    }

    [TestMethod]
    public async Task Un_id_desconocido_devuelve_null()
    {
        Assert.IsNull(await s_repositorio.BuscarAsync(Guid.NewGuid(), TestContext.CancellationToken));
    }
}
