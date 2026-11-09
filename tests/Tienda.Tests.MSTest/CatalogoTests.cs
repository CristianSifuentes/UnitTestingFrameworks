namespace Tienda.Pruebas;

[TestClass]
public sealed class CatalogoTests
{
    [TestMethod]
    [DataRow("LIB-0001", true)]
    [DataRow("TAZ-9999", true)]
    [DataRow("lib-0001", false)]
    [DataRow("LIBR-001", false)]
    [DataRow("", false)]
    [DataRow(null, false)]
    public void Valida_el_formato_del_sku(string? sku, bool esperado)
    {
        Assert.AreEqual(esperado, Tienda.Catalogo.EsSkuValido(sku));
    }

    [TestMethod]
    public void Un_producto_con_sku_invalido_no_se_puede_crear()
    {
        var ex = Assert.ThrowsExactly<ArgumentException>(() => new Producto("x", "?", new Dinero(1m)));

        Assert.AreEqual("Sku", ex.ParamName);
    }
}
