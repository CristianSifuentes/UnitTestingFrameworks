namespace Tienda.Pruebas;

// NUnit reutiliza UNA instancia del fixture para todas sus pruebas: el estado se reinicia en [SetUp].
public class CarritoTests
{
    private Carrito _carrito = null!;

    [SetUp]
    public void CrearCarrito() => _carrito = new Carrito();

    [Test]
    public void Un_carrito_nuevo_esta_vacio()
    {
        Assert.That(_carrito.EstaVacio, Is.True);
        Assert.That(_carrito.Total, Is.EqualTo(Dinero.Cero()));
    }

    [Test]
    public void Agregar_el_mismo_producto_acumula_unidades()
    {
        _carrito.Agregar(Catalogo.Taza, 2);
        _carrito.Agregar(Catalogo.Taza, 3);

        Assert.That(_carrito.Lineas, Has.Exactly(1).Items.With.Property(nameof(LineaDeCarrito.Cantidad)).EqualTo(5));
        Assert.That(_carrito.Total, Is.EqualTo(new Dinero(600m)));
    }

    [Test]
    public void No_se_superan_las_unidades_maximas_por_producto()
    {
        _carrito.Agregar(Catalogo.Libro, Carrito.MaximoPorProducto);

        Assert.That(() => _carrito.Agregar(Catalogo.Libro),
            Throws.InvalidOperationException.With.Message.Contains("Máximo 10"));
    }

    [Test]
    public void Un_cupon_descuenta_sobre_el_subtotal()
    {
        _carrito.Agregar(Catalogo.Libro, 2);
        _carrito.AplicarCupon(new Cupon("ATLAS10", 10m));

        using (Assert.EnterMultipleScope())
        {
            Assert.That(_carrito.Subtotal, Is.EqualTo(new Dinero(900m)));
            Assert.That(_carrito.Total, Is.EqualTo(new Dinero(810m)));
        }
    }

    [Test]
    public void No_se_aplican_dos_cupones()
    {
        _carrito.AplicarCupon(new Cupon("A", 5m));

        Assert.That(() => _carrito.AplicarCupon(new Cupon("B", 5m)), Throws.InvalidOperationException);
    }
}
