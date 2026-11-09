// Dobles de prueba escritos a mano: compartidos por las tres suites para que la comparación sea justa.
namespace Tienda.Pruebas;

public sealed class NotificadorEspia : INotificador
{
    public List<(string Destinatario, string Mensaje)> Enviados { get; } = [];

    public Task EnviarAsync(string destinatario, string mensaje, CancellationToken ct = default)
    {
        ct.ThrowIfCancellationRequested();
        Enviados.Add((destinatario, mensaje));
        return Task.CompletedTask;
    }
}

public static class Catalogo
{
    public static readonly Producto Libro = new("LIB-0001", "C# Atlas", new Dinero(450m), PesoKg: 1.2m);
    public static readonly Producto Taza = new("TAZ-0007", "Taza .NET", new Dinero(120m), PesoKg: 0.4m);
    public static readonly Producto Teclado = new("TEC-0300", "Teclado", new Dinero(1_299m), PesoKg: 0.9m);
}
