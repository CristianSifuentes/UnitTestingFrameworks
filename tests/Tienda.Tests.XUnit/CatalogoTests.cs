namespace Tienda.Pruebas;

public class CatalogoTests
{
    [Theory]
    [InlineData("LIB-0001", true)]
    [InlineData("TAZ-9999", true)]
    [InlineData("lib-0001", false)]
    [InlineData("LIBR-001", false)]
    [InlineData("", false)]
    [InlineData(null, false)]
    public void Valida_el_formato_del_sku(string? sku, bool esperado)
    {
        Assert.Equal(esperado, Tienda.Catalogo.EsSkuValido(sku));
    }

    [Fact]
    public void Un_producto_con_sku_invalido_no_se_puede_crear()
    {
        var ex = Assert.Throws<ArgumentException>(() => new Producto("x", "?", new Dinero(1m)));

        Assert.Equal("Sku", ex.ParamName);
    }
}
