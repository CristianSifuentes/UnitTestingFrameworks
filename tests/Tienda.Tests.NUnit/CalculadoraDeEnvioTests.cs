namespace Tienda.Pruebas;

public class CalculadoraDeEnvioTests
{
    // TestCaseData<...> genérico (NUnit 4.1+) con resultado tipado (NUnit 5).
    private static IEnumerable<TestCaseDataWithReturn<decimal, Zona, decimal, decimal>> Tarifas()
    {
        yield return new TestCaseData<decimal, Zona, decimal>(0.5m, Zona.Local, 100m).Returns(49m);
        yield return new TestCaseData<decimal, Zona, decimal>(1.0m, Zona.Local, 100m).Returns(49m);
        yield return new TestCaseData<decimal, Zona, decimal>(1.1m, Zona.Nacional, 100m).Returns(124m);
        yield return new TestCaseData<decimal, Zona, decimal>(3.0m, Zona.Nacional, 500m).Returns(149m);
        yield return new TestCaseData<decimal, Zona, decimal>(2.0m, Zona.Nacional, 999m).Returns(0m);
        yield return new TestCaseData<decimal, Zona, decimal>(2.0m, Zona.Internacional, 5_000m).Returns(374m);
    }

    [TestCaseSource(nameof(Tarifas))]
    public decimal Calcula_la_tarifa(decimal peso, Zona zona, decimal subtotal) =>
        CalculadoraDeEnvio.Calcular(peso, zona, new Dinero(subtotal)).Monto;

    [Test]
    public void Un_peso_no_positivo_se_rechaza()
    {
        Assert.That(() => CalculadoraDeEnvio.Calcular(0m, Zona.Local, new Dinero(1m)),
            Throws.InstanceOf<ArgumentOutOfRangeException>().ParamName.EqualTo("pesoKg"));
    }
}
