using System.Text.RegularExpressions;

namespace Tienda;

public sealed record Producto(string Sku, string Nombre, Dinero Precio, decimal PesoKg = 0.5m)
{
    public string Sku { get; } = Catalogo.EsSkuValido(Sku)
        ? Sku
        : throw new ArgumentException($"SKU inválido: '{Sku}'.", nameof(Sku));
}

public static partial class Catalogo
{
    /// <summary>Formato: tres letras mayúsculas, guion y cuatro dígitos. Ej.: <c>LIB-0042</c>.</summary>
    public static bool EsSkuValido(string? sku) => sku is not null && PatronSku().IsMatch(sku);

    [GeneratedRegex("^[A-Z]{3}-[0-9]{4}$")]
    private static partial Regex PatronSku();
}
