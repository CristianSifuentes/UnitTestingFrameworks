namespace Tienda.Pruebas;

public class DineroTests
{
    [Fact]
    public void Sumar_misma_moneda_suma_los_montos()
    {
        var total = new Dinero(10.50m) + new Dinero(4.25m);

        Assert.Equal(new Dinero(14.75m), total);
    }

    [Fact]
    public void Sumar_monedas_distintas_lanza_excepcion()
    {
        var ex = Assert.Throws<MonedaIncompatibleException>(() => new Dinero(1m, "MXN") + new Dinero(1m, "USD"));

        Assert.Equal("USD", ex.Derecha);
    }

    [Theory]
    [InlineData(2.345, 2.34)]   // redondeo bancario: el 4 es par
    [InlineData(2.355, 2.36)]
    [InlineData(0.005, 0.00)]
    public void El_monto_se_redondea_a_dos_decimales(decimal entrada, decimal esperado)
    {
        Assert.Equal(esperado, new Dinero(entrada).Monto);
    }

    [Theory]
    [InlineData(-1)]
    [InlineData(100.01)]
    public void Un_porcentaje_fuera_de_rango_se_rechaza(decimal porcentaje)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new Dinero(100m).DescontarPorcentaje(porcentaje));
    }
}
