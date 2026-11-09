namespace Tienda.Pruebas;

public class CalculadoraDeEnvioTests
{
    // TheoryData<...> es fuertemente tipado: el compilador revisa cada fila.
    public static TheoryData<decimal, Zona, decimal, decimal> Tarifas => new()
    {
        { 0.5m, Zona.Local, 100m, 49m },
        { 1.0m, Zona.Local, 100m, 49m },
        { 1.1m, Zona.Nacional, 100m, 124m },
        { 3.0m, Zona.Nacional, 500m, 149m },
        { 2.0m, Zona.Nacional, 999m, 0m },          // envío gratis
        { 2.0m, Zona.Internacional, 5_000m, 374m }, // internacional nunca es gratis
    };

    [Theory]
    [MemberData(nameof(Tarifas))]
    public void Calcula_la_tarifa(decimal peso, Zona zona, decimal subtotal, decimal esperado)
    {
        var envio = CalculadoraDeEnvio.Calcular(peso, zona, new Dinero(subtotal));

        Assert.Equal(esperado, envio.Monto);
    }

    [Fact]
    public void Un_peso_no_positivo_se_rechaza()
    {
        Assert.Throws<ArgumentOutOfRangeException>("pesoKg", () => CalculadoraDeEnvio.Calcular(0m, Zona.Local, new Dinero(1m)));
    }
}
