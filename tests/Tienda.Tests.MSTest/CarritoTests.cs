namespace Tienda.Pruebas;

// MSTest crea una instancia por prueba, como xUnit; [TestInitialize] corre antes de cada una.
[TestClass]
public sealed class CarritoTests
{
    private Carrito _carrito = null!;

    [TestInitialize]
    public void CrearCarrito() => _carrito = new Carrito();

    [TestMethod]
    public void Un_carrito_nuevo_esta_vacio()
    {
        Assert.IsTrue(_carrito.EstaVacio);
        Assert.AreEqual(Dinero.Cero(), _carrito.Total);
    }

    [TestMethod]
    public void Agregar_el_mismo_producto_acumula_unidades()
    {
        _carrito.Agregar(Catalogo.Taza, 2);
        _carrito.Agregar(Catalogo.Taza, 3);

        var linea = Assert.ContainsSingle(_carrito.Lineas);
        Assert.AreEqual(5, linea.Cantidad);
        Assert.AreEqual(new Dinero(600m), _carrito.Total);
    }

    [TestMethod]
    public void No_se_superan_las_unidades_maximas_por_producto()
    {
        _carrito.Agregar(Catalogo.Libro, Carrito.MaximoPorProducto);

        var ex = Assert.ThrowsExactly<InvalidOperationException>(() => _carrito.Agregar(Catalogo.Libro));
        Assert.Contains("Máximo 10", ex.Message);
    }

    [TestMethod]
    public void Un_cupon_descuenta_sobre_el_subtotal()
    {
        _carrito.Agregar(Catalogo.Libro, 2);
        _carrito.AplicarCupon(new Cupon("ATLAS10", 10m));

        Assert.AreEqual(new Dinero(900m), _carrito.Subtotal);
        Assert.AreEqual(new Dinero(810m), _carrito.Total);
    }

    [TestMethod]
    public void No_se_aplican_dos_cupones()
    {
        _carrito.AplicarCupon(new Cupon("A", 5m));

        Assert.ThrowsExactly<InvalidOperationException>(() => _carrito.AplicarCupon(new Cupon("B", 5m)));
    }
}
