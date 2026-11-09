namespace Tienda.Pruebas;

[TestFixture]
public class DineroTests
{
    [Test]
    public void Sumar_misma_moneda_suma_los_montos()
    {
        var total = new Dinero(10.50m) + new Dinero(4.25m);

        Assert.That(total, Is.EqualTo(new Dinero(14.75m)));
    }

    [Test]
    public void Sumar_monedas_distintas_lanza_excepcion()
    {
        var ex = Assert.Throws<MonedaIncompatibleException>(() => _ = new Dinero(1m, "MXN") + new Dinero(1m, "USD"));

        Assert.That(ex.Derecha, Is.EqualTo("USD"));
    }

    [TestCase(2.345, 2.34)]   // redondeo bancario: el 4 es par
    [TestCase(2.355, 2.36)]
    [TestCase(0.005, 0.00)]
    public void El_monto_se_redondea_a_dos_decimales(decimal entrada, decimal esperado)
    {
        Assert.That(new Dinero(entrada).Monto, Is.EqualTo(esperado));
    }

    [TestCase(-1)]
    [TestCase(100.01)]
    public void Un_porcentaje_fuera_de_rango_se_rechaza(decimal porcentaje)
    {
        Assert.That(() => new Dinero(100m).DescontarPorcentaje(porcentaje), Throws.TypeOf<ArgumentOutOfRangeException>());
    }
}
