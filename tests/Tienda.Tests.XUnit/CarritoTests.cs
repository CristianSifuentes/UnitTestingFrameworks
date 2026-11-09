namespace Tienda.Pruebas;

// xUnit crea una instancia nueva de la clase por cada prueba: el constructor es el "setup".
public class CarritoTests
{
    private readonly Carrito _carrito = new();

    [Fact]
    public void Un_carrito_nuevo_esta_vacio()
    {
        Assert.True(_carrito.EstaVacio);
        Assert.Equal(Dinero.Cero(), _carrito.Total);
    }

    [Fact]
    public void Agregar_el_mismo_producto_acumula_unidades()
    {
        _carrito.Agregar(Catalogo.Taza, 2);
        _carrito.Agregar(Catalogo.Taza, 3);

        var linea = Assert.Single(_carrito.Lineas);
        Assert.Equal(5, linea.Cantidad);
        Assert.Equal(new Dinero(600m), _carrito.Total);
    }

    [Fact]
    public void No_se_superan_las_unidades_maximas_por_producto()
    {
        _carrito.Agregar(Catalogo.Libro, Carrito.MaximoPorProducto);

        var ex = Assert.Throws<InvalidOperationException>(() => _carrito.Agregar(Catalogo.Libro));
        Assert.Contains("Máximo 10", ex.Message);
    }

    [Fact]
    public void Un_cupon_descuenta_sobre_el_subtotal()
    {
        _carrito.Agregar(Catalogo.Libro, 2);
        _carrito.AplicarCupon(new Cupon("ATLAS10", 10m));

        Assert.Multiple(
            () => Assert.Equal(new Dinero(900m), _carrito.Subtotal),
            () => Assert.Equal(new Dinero(810m), _carrito.Total));
    }

    [Fact]
    public void No_se_aplican_dos_cupones()
    {
        _carrito.AplicarCupon(new Cupon("A", 5m));

        Assert.Throws<InvalidOperationException>(() => _carrito.AplicarCupon(new Cupon("B", 5m)));
    }
}
