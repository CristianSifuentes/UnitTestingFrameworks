namespace Tienda;

/// <summary>Cantidad monetaria inmutable. Dos importes solo se suman si comparten moneda.</summary>
public readonly record struct Dinero
{
    public decimal Monto { get; }
    public string Moneda { get; }

    public Dinero(decimal monto, string moneda = "MXN")
    {
        ArgumentOutOfRangeException.ThrowIfNegative(monto);
        ArgumentException.ThrowIfNullOrWhiteSpace(moneda);
        Monto = decimal.Round(monto, 2, MidpointRounding.ToEven);
        Moneda = moneda.ToUpperInvariant();
    }

    public static Dinero Cero(string moneda = "MXN") => new(0m, moneda);

    public static Dinero operator +(Dinero a, Dinero b)
    {
        if (a.Moneda != b.Moneda)
            throw new MonedaIncompatibleException(a.Moneda, b.Moneda);
        return new(a.Monto + b.Monto, a.Moneda);
    }

    public static Dinero operator *(Dinero a, int factor) => new(a.Monto * factor, a.Moneda);

    public Dinero DescontarPorcentaje(decimal porcentaje)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(porcentaje);
        ArgumentOutOfRangeException.ThrowIfGreaterThan(porcentaje, 100m);
        return new(Monto * (1 - porcentaje / 100m), Moneda);
    }

    public override string ToString() => $"{Monto:0.00} {Moneda}";
}

public sealed class MonedaIncompatibleException(string izquierda, string derecha)
    : InvalidOperationException($"No se pueden combinar {izquierda} y {derecha}.")
{
    public string Izquierda { get; } = izquierda;
    public string Derecha { get; } = derecha;
}
