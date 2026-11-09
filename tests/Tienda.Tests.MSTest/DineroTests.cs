namespace Tienda.Pruebas;

[TestClass]
public sealed class DineroTests
{
    [TestMethod]
    public void Sumar_misma_moneda_suma_los_montos()
    {
        var total = new Dinero(10.50m) + new Dinero(4.25m);

        Assert.AreEqual(new Dinero(14.75m), total);
    }

    [TestMethod]
    public void Sumar_monedas_distintas_lanza_excepcion()
    {
        var ex = Assert.ThrowsExactly<MonedaIncompatibleException>(() => new Dinero(1m, "MXN") + new Dinero(1m, "USD"));

        Assert.AreEqual("USD", ex.Derecha);
    }

    [TestMethod]
    [DataRow(2.345, 2.34)]   // redondeo bancario: el 4 es par
    [DataRow(2.355, 2.36)]
    [DataRow(0.005, 0.00)]
    public void El_monto_se_redondea_a_dos_decimales(double entrada, double esperado)
    {
        // Los atributos de C# no admiten decimal: DataRow recibe double y se convierte.
        Assert.AreEqual((decimal)esperado, new Dinero((decimal)entrada).Monto);
    }

    [TestMethod]
    [DataRow(-1.0)]
    [DataRow(100.01)]
    public void Un_porcentaje_fuera_de_rango_se_rechaza(double porcentaje)
    {
        Assert.ThrowsExactly<ArgumentOutOfRangeException>(() => new Dinero(100m).DescontarPorcentaje((decimal)porcentaje));
    }
}
