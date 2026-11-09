namespace Tienda;

public sealed record LineaDeCarrito(Producto Producto, int Cantidad)
{
    public Dinero Subtotal => Producto.Precio * Cantidad;
}

/// <summary>Carrito de compras. No es seguro para uso concurrente.</summary>
public sealed class Carrito(string moneda = "MXN")
{
    public const int MaximoPorProducto = 10;
    private readonly Dictionary<string, LineaDeCarrito> _lineas = [];

    public string Moneda { get; } = moneda;
    public IReadOnlyCollection<LineaDeCarrito> Lineas => _lineas.Values;
    public bool EstaVacio => _lineas.Count == 0;
    public int Unidades => _lineas.Values.Sum(l => l.Cantidad);
    public Cupon? Cupon { get; private set; }

    public void Agregar(Producto producto, int cantidad = 1)
    {
        ArgumentNullException.ThrowIfNull(producto);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(cantidad);
        if (producto.Precio.Moneda != Moneda)
            throw new MonedaIncompatibleException(Moneda, producto.Precio.Moneda);

        var actual = _lineas.TryGetValue(producto.Sku, out var linea) ? linea.Cantidad : 0;
        if (actual + cantidad > MaximoPorProducto)
            throw new InvalidOperationException($"Máximo {MaximoPorProducto} unidades de {producto.Sku}.");

        _lineas[producto.Sku] = new LineaDeCarrito(producto, actual + cantidad);
    }

    public bool Quitar(string sku) => _lineas.Remove(sku);

    public void AplicarCupon(Cupon cupon)
    {
        if (Cupon is not null)
            throw new InvalidOperationException("El carrito ya tiene un cupón.");
        Cupon = cupon;
    }

    public Dinero Subtotal => _lineas.Values.Aggregate(Dinero.Cero(Moneda), (suma, l) => suma + l.Subtotal);

    public Dinero Total => Cupon is { } c ? Subtotal.DescontarPorcentaje(c.Porcentaje) : Subtotal;
}

public sealed record Cupon(string Codigo, decimal Porcentaje);
