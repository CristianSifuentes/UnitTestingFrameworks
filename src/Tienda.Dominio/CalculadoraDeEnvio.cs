namespace Tienda;

public enum Zona { Local, Nacional, Internacional }

public static class CalculadoraDeEnvio
{
    public static readonly Dinero UmbralEnvioGratis = new(999m);

    /// <summary>Tarifa base por zona más 25 MXN por kilo adicional (redondeado hacia arriba). Envío gratis nacional desde 999 MXN.</summary>
    public static Dinero Calcular(decimal pesoKg, Zona zona, Dinero subtotal)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(pesoKg);
        if (zona != Zona.Internacional && subtotal.Monto >= UmbralEnvioGratis.Monto)
            return Dinero.Cero(subtotal.Moneda);

        var baseZona = zona switch
        {
            Zona.Local => 49m,
            Zona.Nacional => 99m,
            Zona.Internacional => 349m,
            _ => throw new ArgumentOutOfRangeException(nameof(zona)),
        };
        var kilosExtra = Math.Max(0, (int)Math.Ceiling(pesoKg) - 1);
        return new Dinero(baseZona + kilosExtra * 25m, subtotal.Moneda);
    }
}
