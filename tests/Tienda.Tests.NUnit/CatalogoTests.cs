namespace Tienda.Pruebas;

public class CatalogoTests
{
    [TestCase("LIB-0001", ExpectedResult = true)]
    [TestCase("TAZ-9999", ExpectedResult = true)]
    [TestCase("lib-0001", ExpectedResult = false)]
    [TestCase("LIBR-001", ExpectedResult = false)]
    [TestCase("", ExpectedResult = false)]
    [TestCase(null, ExpectedResult = false)]
    public bool Valida_el_formato_del_sku(string? sku) => Tienda.Catalogo.EsSkuValido(sku);

    [Test]
    public void Un_producto_con_sku_invalido_no_se_puede_crear()
    {
        Assert.That(() => new Producto("x", "?", new Dinero(1m)),
            Throws.ArgumentException.ParamName.EqualTo("Sku"));
    }
}
